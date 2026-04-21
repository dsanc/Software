from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views, login
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from .forms import (
    EmailAuthenticationForm, UserProfileForm, CustomPasswordChangeForm,
    CustomPasswordResetForm, CustomSetPasswordForm, PasswordStrengthForm,
    QuickProfileForm, AvatarUploadForm
)
from .security_logging import security_logger
from .services import AccountSecurityService, TwoFactorService
import logging
import json

logger = logging.getLogger(__name__)


class CustomLoginView(auth_views.LoginView):
    """Vista personalizada de login que maneja tanto formularios standalone como AJAX del modal"""
    form_class = EmailAuthenticationForm
    template_name = 'dashboard/home.html'  # Redirecciona al home que contiene el modal
    success_url = reverse_lazy('dashboard:dashboard')
    
    # form_valid eliminado (estaba duplicado y ocultaba la implementación real más abajo)
    
    def form_invalid(self, form):
        """Manejar errores de login - soporte para AJAX"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Es una petición AJAX del modal
            logger.warning(f"Intento de login fallido via AJAX: {form.errors}")
            
            return JsonResponse({
                'status': 'error',
                'errors': form.errors,
                'message': 'Credenciales inválidas. Por favor verifica tu email y contraseña.'
            }, status=400)
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Determinar a dónde redirigir después del login exitoso"""
        # Obtener URL de redirección por defecto
        default_url = super().get_success_url()
        logger.info(f"Default URL calculada: {default_url}")
        
        # Si la URL de destino es checkout o carrito, permitirla siempre
        if '/subscriptions/checkout/' in str(default_url) or '/subscriptions/cart/' in str(default_url):
            return default_url
        
        # Si el usuario es evaluador, redirigir a su dashboard propio
        try:
            from apps.evaluadores.models import Evaluador
            perfiles_activos = Evaluador.objects.filter(
                usuario_evaluador=self.request.user,
                estado='active',
                is_active=True
            ).select_related('usuario_principal')
            count = perfiles_activos.count()
            if count == 1:
                # Un solo usuario principal: ir directo al dashboard
                perfil = perfiles_activos.first()
                evaluador_url = reverse(
                    'evaluadores:dashboard_evaluador',
                    kwargs={'usuario_principal_id': perfil.usuario_principal_id}
                )
            elif count > 1:
                # Múltiples usuarios principales: elegir desde mi perfil
                evaluador_url = reverse('evaluadores:mi_perfil_evaluador')
            else:
                evaluador_url = None
            if evaluador_url:
                logger.info(f"Usuario evaluador detectado, redirigiendo a: {evaluador_url}")
                return evaluador_url
        except Exception:
            pass

        # Si el usuario no es superusuario, verificar si tiene suscripción activa
        if not self.request.user.is_superuser:
            logger.info(f"Usuario {self.request.user.email} no es superusuario, verificando suscripciones")
            from apps.subscriptions.models import Subscription
            from django.utils import timezone
            
            has_active_subscription = Subscription.objects.filter(
                user=self.request.user,
                status='active',
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).exists()
            
            logger.info(f"¿Tiene suscripción activa? {has_active_subscription}")
            
            if not has_active_subscription:
                # No tiene suscripción activa, redirigir a selección de plan
                redirect_url = reverse('subscriptions:select_initial_plan')
                logger.info(f"Sin suscripción, redirigiendo a: {redirect_url}")
                return redirect_url
        else:
            logger.info(f"Usuario {self.request.user.email} es superusuario")
        
        logger.info(f"URL final de éxito: {default_url}")
        return default_url
    
    def form_valid(self, form):
        """Login exitoso con logging detallado y verificación de 2FA"""
        user = form.get_user()
        remember_me = form.cleaned_data.get('remember_me')
        
        # Verificar si la cuenta está bloqueada
        if AccountSecurityService.is_account_locked(user):
            lockout = AccountSecurityService.get_active_lockout(user)
            error_message = (f'Tu cuenta está temporalmente bloqueada. '
                           f'Intenta de nuevo en {lockout.time_remaining.total_seconds() // 60:.0f} minutos.')
            
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [error_message]}
                })
            else:
                messages.error(self.request, error_message)
                return self.form_invalid(form)
        
        # Configurar sesión
        if remember_me:
            self.request.session.set_expiry(1209600)  # 2 semanas
        else:
            self.request.session.set_expiry(0)  # Hasta cerrar navegador
        
        # Registrar intento exitoso
        AccountSecurityService.record_login_attempt(
            username=user.email,
            ip_address=security_logger._get_client_ip(self.request),
            user_agent=security_logger._get_user_agent(self.request),
            success=True,
            user=user,
            request=self.request
        )
        
        # Verificar si necesita 2FA
        if user.two_factor_enabled:
            # No hacer login todavía, guardar para después de 2FA
            self.request.session['pre_2fa_user_id'] = user.id
            self.request.session['pre_2fa_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
            self.request.session['next_url'] = self.get_success_url()
            
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('users:2fa_verify'),
                    'message': 'Por favor, ingresa tu código de autenticación.'
                })
            else:
                messages.info(self.request, 'Por favor, ingresa tu código de autenticación.')
                return redirect('users:2fa_verify')
        
        # Logging detallado del login exitoso usando SecurityLogger
        security_logger.log_login_success(
            user=user,
            request=self.request,
            remember_me=remember_me,
            session_expiry='2_weeks' if remember_me else 'browser_close'
        )
        
        # Logging adicional para debugging
        logger.info(f"Session key creado: {self.request.session.session_key}")
        
        # Mensaje de bienvenida
        welcome_message = f'¡Bienvenido/a {user.get_full_name() or user.username}!'
        
        # Ejecutar el login
        response = super().form_valid(form)
        
        # Confirmar que el login fue exitoso
        logger.info(f"Usuario autenticado: {self.request.user.is_authenticated}")
        
        # Obtener URL de éxito después del login
        success_url = self.get_success_url()
        logger.info(f"Redirigiendo a: {success_url}")
        
        # Respuesta AJAX
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': str(success_url),
                'message': welcome_message
            })
        
        # Respuesta normal
        messages.success(self.request, welcome_message)
        return response

    def form_invalid(self, form):
        """Manejo mejorado de login fallido con sistema de bloqueo"""
        try:
            # Obtener datos del intento de login
            post_data = dict(self.request.POST)
            username = post_data.get('username', [''])[0]
            
            # Determinar razón del fallo
            errors = form.errors
            if 'username' in errors:
                reason = "Usuario no existe"
            elif 'password' in errors:
                reason = "Contraseña incorrecta"
            elif '__all__' in errors:
                reason = "Credenciales inválidas"
            else:
                reason = "Error de formulario"
            
            # Verificar si el usuario existe para registrar intento
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = None
            try:
                if username and '@' in username:
                    user = User.objects.get(email=username)
            except User.DoesNotExist:
                pass
            
            # Registrar intento fallido (esto puede causar bloqueo)
            AccountSecurityService.record_login_attempt(
                username=username,
                ip_address=security_logger._get_client_ip(self.request),
                user_agent=security_logger._get_user_agent(self.request),
                success=False,
                failure_reason=reason,
                user=user,
                request=self.request
            )
            
            # Verificar si ahora está bloqueado
            if user and AccountSecurityService.is_account_locked(user):
                lockout = AccountSecurityService.get_active_lockout(user)
                error_message = (f'Demasiados intentos fallidos. Tu cuenta ha sido bloqueada temporalmente. '
                               f'Intenta de nuevo en {lockout.time_remaining.total_seconds() // 60:.0f} minutos.')
                
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': {'__all__': [error_message]}
                    })
                else:
                    messages.error(self.request, error_message)
            else:
                # Mostrar intentos restantes
                if user:
                    recent_failures = AccountSecurityService.get_recent_failed_attempts(user)
                    remaining_attempts = AccountSecurityService.MAX_LOGIN_ATTEMPTS - recent_failures.count()
                    
                    if remaining_attempts <= 2:
                        error_message = (f'Credenciales incorrectas. Te quedan {remaining_attempts} intentos '
                                       f'antes de que tu cuenta sea bloqueada temporalmente.')
                        
                        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'errors': {'__all__': [error_message]}
                            })
                        else:
                            messages.warning(self.request, error_message)
                    else:
                        error_message = 'Las credenciales ingresadas no son correctas. Verifica tu email y contraseña.'
                        
                        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'errors': form.errors
                            })
                        else:
                            messages.error(self.request, error_message)
                else:
                    error_message = 'Las credenciales ingresadas no son correctas. Verifica tu email y contraseña.'
                    
                    if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'errors': form.errors
                        })
                    else:
                        messages.error(self.request, error_message)
            
            # Verificaciones adicionales de seguridad
            if user and not user.is_active:
                security_logger.log_suspicious_activity(
                    user_or_ip=username,
                    activity="LOGIN_ATTEMPT_INACTIVE_ACCOUNT",
                    request=self.request
                )
            
        except Exception as e:
            logger.exception(f"Error en form_invalid: {e}")
            error_message = 'Error interno del sistema. Inténtalo de nuevo.'
            
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [error_message]}
                })
            else:
                messages.error(self.request, error_message)

        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Agregar información adicional al contexto"""
        context = super().get_context_data(**kwargs)
        # Agregar settings para el template
        from django.conf import settings
        context['settings'] = settings
        return context


class CustomLogoutView(auth_views.LogoutView):
    """Vista personalizada de logout"""
    next_page = reverse_lazy('dashboard:home')
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Has cerrado sesión exitosamente.')
        return super().dispatch(request, *args, **kwargs)


@login_required
def profile_view(request):
    """Vista del perfil del usuario con completitud"""
    user = request.user
    
    # Calcular completitud del perfil
    completion_percentage = user.profile_completion
    
    # Obtener sugerencias de campos faltantes
    missing_fields = []
    field_labels = {
        'phone': 'Teléfono',
        'avatar': 'Foto de perfil',
        'job_title': 'Cargo/Puesto',
        'company': 'Empresa',
        'city': 'Ciudad',
        'country': 'País'
    }
    
    for field, label in field_labels.items():
        value = getattr(user, field, None)
        if not value or (hasattr(value, 'name') and not value.name):
            missing_fields.append(label)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
            
            # Log del cambio
            from .security_logging import security_logger
            import logging
            logger = logging.getLogger('apps.users')
            logger.info(f"Perfil actualizado para {user.email}")
            
            return redirect('users:profile')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserProfileForm(instance=user)
    
    context = {
        'user': user,
        'form': form,
        'completion_percentage': completion_percentage,
        'missing_fields': missing_fields[:5],  # Mostrar solo 5 sugerencias
        'profile_complete': completion_percentage >= 80,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def profile_edit_view(request):
    """Vista dedicada para edición de perfil"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            old_email = user.email
            user = form.save()
            
            # Mensaje específico si cambió el email
            if old_email != user.email:
                messages.warning(
                    request,
                    'Tu email ha sido cambiado. Te enviaremos un enlace de verificación.'
                )
            
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = UserProfileForm(instance=user)
    
    return render(request, 'users/profile_edit.html', {
        'form': form,
        'user': user
    })


@login_required
def avatar_upload_view(request):
    """Vista específica para subida de avatar"""
    if request.method == 'POST':
        form = AvatarUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Eliminar avatar anterior si existe
            if request.user.avatar:
                request.user.delete_avatar()
            
            # Guardar nuevo avatar
            request.user.avatar = form.cleaned_data['avatar']
            request.user.save()
            
            messages.success(request, 'Avatar actualizado exitosamente.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'avatar_url': request.user.get_avatar_url(),
                    'message': 'Avatar actualizado exitosamente.'
                })
            
            return redirect('users:profile')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = AvatarUploadForm()
    
    return render(request, 'users/avatar_upload.html', {
        'form': form
    })


@login_required
def delete_avatar_view(request):
    """Vista para eliminar avatar del usuario"""
    if request.method == 'POST':
        request.user.delete_avatar()
        messages.success(request, 'Avatar eliminado exitosamente.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Avatar eliminado exitosamente.',
                'default_avatar': '/static/images/default-avatar.png'
            })
    
    return redirect('users:profile')


@login_required 
def quick_profile_edit(request):
    """Vista AJAX para edición rápida de perfil"""
    if request.method == 'POST':
        form = QuickProfileForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            user = form.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Perfil actualizado exitosamente',
                'user_data': {
                    'full_name': user.get_full_name(),
                    'avatar_url': user.get_avatar_url(),
                    'completion': user.profile_completion
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def profile_public_view(request, user_id):
    """Vista pública del perfil de un usuario"""
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        raise Http404("Usuario no encontrado")
    
    # Solo mostrar información pública
    context = {
        'profile_user': user,
        'is_own_profile': request.user.is_authenticated and request.user.id == user.id,
        'can_view_details': request.user.is_authenticated,
    }
    
    return render(request, 'users/profile_public.html', context)


@login_required
def profile_completion_tips(request):
    """Vista AJAX para obtener consejos de completitud de perfil"""
    user = request.user
    completion = user.profile_completion
    
    tips = []
    
    if not user.avatar:
        tips.append({
            'field': 'avatar',
            'title': 'Agrega una foto de perfil',
            'description': 'Una foto ayuda a otros usuarios a identificarte',
            'icon': 'fas fa-camera',
            'url': reverse('users:avatar_upload')
        })
    
    if not user.phone:
        tips.append({
            'field': 'phone',
            'title': 'Agrega tu teléfono',
            'description': 'Para notificaciones importantes y recuperación de cuenta',
            'icon': 'fas fa-phone',
            'url': reverse('users:profile_edit')
        })
    
    if not user.job_title:
        tips.append({
            'field': 'job_title',
            'title': 'Agrega tu cargo',
            'description': 'Muestra tu rol profesional actual',
            'icon': 'fas fa-briefcase',
            'url': reverse('users:profile_edit')
        })
    
    if not user.city or not user.country:
        tips.append({
            'field': 'location',
            'title': 'Agrega tu ubicación',
            'description': 'Ayuda a conectar con usuarios cercanos',
            'icon': 'fas fa-map-marker-alt',
            'url': reverse('users:profile_edit')
        })
    
    return JsonResponse({
        'completion': completion,
        'tips': tips[:3],  # Máximo 3 consejos
        'is_complete': completion >= 80
    })


@login_required
def export_profile_data(request):
    """Vista para exportar datos del perfil del usuario"""
    user = request.user
    
    # Preparar datos del usuario
    profile_data = {
        'basic_info': {
            'name': user.get_full_name(),
            'email': user.email,
            'username': user.username,
            'date_joined': user.date_created.isoformat() if hasattr(user, 'date_created') else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
        },
        'personal_info': {
            'phone': user.phone,
        },
        'professional_info': {
            'job_title': user.job_title,
            'company': user.company,
            'department': user.department,
        },
        'location_info': {
            'country': user.country,
            'city': user.city,
        },
        'preferences': {
            'email_notifications': user.email_notifications,
            'sms_notifications': user.sms_notifications,
        },
        'social_links': {
            'website': user.website,
            'linkedin': user.linkedin,
            'twitter': user.twitter,
        }
    }
    
    # Log de exportación
    logger = logging.getLogger('apps.users')
    logger.info(f"Datos de perfil exportados para usuario {user.email}")
    
    response = JsonResponse(profile_data, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="profile_data_{user.username}.json"'
    
    return response


# =============================================================================
# VISTAS DE GESTIÓN DE CONTRASEÑAS
# =============================================================================

class CustomPasswordChangeView(auth_views.PasswordChangeView):
    """Vista personalizada para cambio de contraseña"""
    form_class = CustomPasswordChangeForm
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:password_change_done')
    
    def dispatch(self, request, *args, **kwargs):
        """Manejar diferentes tipos de solicitudes"""
        # Verificar si es una solicitud AJAX (del modal)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return self.handle_ajax_request(request)
        return super().dispatch(request, *args, **kwargs)
    
    def handle_ajax_request(self, request):
        """Manejar solicitud AJAX del modal"""
        if request.method == 'POST':
            form = self.get_form()
            if form.is_valid():
                return self.ajax_form_valid(form)
            else:
                return self.ajax_form_invalid(form)
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    def ajax_form_valid(self, form):
        """Procesar cambio de contraseña exitoso vía AJAX"""
        user = self.request.user
        
        # Cambiar la contraseña
        form.save()
        
        # Logging de seguridad
        security_logger.log_password_change_success(
            user=user,
            request=self.request,
            method="ajax_modal"
        )
        
        return JsonResponse({
            'success': True,
            'message': '¡Tu contraseña ha sido cambiada exitosamente! Por seguridad, hemos cerrado todas tus sesiones activas.'
        })
    
    def ajax_form_invalid(self, form):
        """Manejo de errores en cambio de contraseña vía AJAX"""
        user = self.request.user
        
        # Determinar razón del error
        errors = form.errors
        if 'old_password' in errors:
            reason = "Contraseña actual incorrecta"
        elif 'new_password1' in errors:
            reason = "Nueva contraseña no cumple requisitos"
        elif 'new_password2' in errors:
            reason = "Confirmación de contraseña no coincide"
        else:
            reason = "Error en formulario"
        
        # Logging de intento fallido
        security_logger.log_password_change_failure(
            user=user,
            request=self.request,
            reason=reason,
            method="ajax_modal"
        )
        
        # Formatear errores para AJAX
        formatted_errors = {}
        for field, error_list in form.errors.items():
            if field == 'old_password':
                formatted_errors['OldPassword'] = error_list
            elif field == 'new_password1':
                formatted_errors['NewPassword1'] = error_list
            elif field == 'new_password2':
                formatted_errors['NewPassword2'] = error_list
            else:
                formatted_errors[field] = error_list
        
        return JsonResponse({
            'success': False,
            'errors': formatted_errors,
            'message': 'Hubo un problema al cambiar tu contraseña. Por favor, revisa los errores.'
        })
    
    def form_valid(self, form):
        """Procesar cambio de contraseña exitoso (formulario tradicional)"""
        user = self.request.user
        
        # Logging de seguridad
        security_logger.log_password_change_success(
            user=user,
            request=self.request,
            method="form"
        )
        
        # Mensaje de éxito
        messages.success(
            self.request,
            '¡Tu contraseña ha sido cambiada exitosamente! Por seguridad, '
            'hemos cerrado todas tus sesiones activas.'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Manejo de errores en cambio de contraseña (formulario tradicional)"""
        user = self.request.user
        
        # Determinar razón del error
        errors = form.errors
        if 'old_password' in errors:
            reason = "Contraseña actual incorrecta"
        elif 'new_password1' in errors:
            reason = "Nueva contraseña no cumple requisitos"
        elif 'new_password2' in errors:
            reason = "Confirmación de contraseña no coincide"
        else:
            reason = "Error en formulario"
        
        # Logging de intento fallido
        security_logger.log_password_change_failure(
            user=user,
            request=self.request,
            reason=reason,
            method="form"
        )
        
        messages.error(
            self.request,
            'Hubo un problema al cambiar tu contraseña. Por favor, revisa los errores.'
        )
        
        return super().form_invalid(form)


class CustomPasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    """Vista de confirmación de cambio de contraseña"""
    template_name = 'users/password_change_done.html'


class CustomPasswordResetView(auth_views.PasswordResetView):
    """Vista personalizada para solicitar reset de contraseña"""
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')
    
    def form_valid(self, form):
        """Procesar solicitud de reset exitosa"""
        email = form.cleaned_data.get('email')
        
        # Logging de seguridad
        security_logger.log_password_reset_request(
            email=email,
            request=self.request
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Manejo de errores en solicitud de reset"""
        email = form.cleaned_data.get('email', 'Unknown')
        errors = form.errors
        
        if 'email' in errors:
            reason = "Email no existe o cuenta inactiva"
        else:
            reason = "Error en formulario"
        
        security_logger.log_suspicious_activity(
            user_or_ip=email,
            activity="PASSWORD_RESET_INVALID_EMAIL",
            request=self.request,
            reason=reason
        )
        
        return super().form_invalid(form)


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    """Vista de confirmación de solicitud de reset"""
    template_name = 'users/password_reset_done.html'


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Vista para confirmar reset de contraseña con token"""
    form_class = CustomSetPasswordForm
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
    
    def form_valid(self, form):
        """Procesar reset de contraseña exitoso"""
        user = self.get_user()
        
        # Logging de seguridad
        security_logger.log_password_reset_complete(
            user=user,
            request=self.request
        )
        
        # Mensaje de éxito
        messages.success(
            self.request,
            '¡Tu contraseña ha sido restablecida exitosamente! '
            'Ya puedes iniciar sesión con tu nueva contraseña.'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Manejo de errores en reset de contraseña"""
        user = self.get_user()
        
        # Determinar razón del error
        errors = form.errors
        if 'new_password1' in errors:
            reason = "Nueva contraseña no cumple requisitos"
        elif 'new_password2' in errors:
            reason = "Confirmación de contraseña no coincide"
        else:
            reason = "Error en formulario"
        
        # Logging de intento fallido
        security_logger.log_password_change_failure(
            user=user if user else "Unknown",
            request=self.request,
            reason=reason,
            method="reset"
        )
        
        return super().form_invalid(form)


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """Vista de confirmación final de reset"""
    template_name = 'users/password_reset_complete.html'


# =============================================================================
# AJAX ENDPOINTS PARA VALIDACIÓN DE CONTRASEÑAS
# =============================================================================

@csrf_exempt
def password_strength_check(request):
    """
    Endpoint AJAX para verificar la fuerza de contraseñas en tiempo real
    Usa las validaciones nativas de Django configuradas en AUTH_PASSWORD_VALIDATORS
    """
    if request.method == 'POST':
        try:
            # Intentar obtener datos tanto de JSON como de form data
            password = ''
            if request.content_type and 'application/json' in request.content_type:
                data = json.loads(request.body)
                password = data.get('password', '')
            else:
                password = request.POST.get('password', '')
            
            if not password:
                return JsonResponse({
                    'success': False,
                    'error': 'No se proporcionó contraseña'
                })
            
            # Importar validadores de Django
            from django.contrib.auth.password_validation import (
                validate_password, get_default_password_validators
            )
            from django.core.exceptions import ValidationError
            
            # Obtener usuario actual si está disponible
            user = request.user if request.user.is_authenticated else None
            
            # Realizar validaciones de Django
            validation_errors = []
            criteria = {}
            
            try:
                # Validar contraseña usando los validadores de Django
                validate_password(password, user=user)
                validation_success = True
            except ValidationError as e:
                validation_errors = e.messages
                validation_success = False
            
            # Obtener validadores configurados y verificar criterios específicos
            validators = get_default_password_validators()
            
            # Evaluar criterios específicos
            criteria = {
                'length': len(password) >= 8,
                'uppercase': any(c.isupper() for c in password),
                'lowercase': any(c.islower() for c in password),
                'numbers': any(c.isdigit() for c in password),
                'special': any(not c.isalnum() for c in password),
                'not_common': True,  # Se validará con Django's CommonPasswordValidator
                'not_similar': True,  # Se validará con Django's UserAttributeSimilarityValidator
                'not_numeric': True   # Se validará con Django's NumericPasswordValidator
            }
            
            # Verificar validaciones específicas de Django
            for validator in validators:
                validator_name = validator.__class__.__name__
                
                try:
                    validator.validate(password, user=user)
                except ValidationError:
                    if 'CommonPassword' in validator_name:
                        criteria['not_common'] = False
                    elif 'UserAttributeSimilarity' in validator_name:
                        criteria['not_similar'] = False
                    elif 'NumericPassword' in validator_name:
                        criteria['not_numeric'] = False
                    elif 'MinimumLength' in validator_name:
                        criteria['length'] = False
            
            # Calcular puntuación basada en criterios
            total_criteria = len(criteria)
            passed_criteria = sum(criteria.values())
            base_score = (passed_criteria / total_criteria) * 80  # 80% máximo por criterios básicos
            
            # Bonificaciones adicionales
            bonus_score = 0
            if len(password) >= 12:
                bonus_score += 10
            if len(password) >= 16:
                bonus_score += 10
            
            # Penalizaciones
            penalty = len(validation_errors) * 5
            
            final_score = max(0, min(100, base_score + bonus_score - penalty))
            
            # Determinar nivel de fuerza
            if final_score >= 80:
                strength_level = "muy fuerte"
                strength_class = "success"
            elif final_score >= 60:
                strength_level = "fuerte"
                strength_class = "info"
            elif final_score >= 40:
                strength_level = "medio"
                strength_class = "warning"
            elif final_score >= 20:
                strength_level = "débil"
                strength_class = "warning"
            else:
                strength_level = "muy débil"
                strength_class = "danger"
            
            return JsonResponse({
                'success': True,
                'score': int(final_score),
                'strength': strength_level,
                'class': strength_class,
                'criteria': criteria,
                'validation_errors': validation_errors,
                'django_validation_passed': validation_success,
                'recommendations': get_password_recommendations(criteria, validation_errors)
            })
            
        except Exception as e:
            logger.error(f"Error en password_strength_check: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })


def get_password_recommendations(criteria, validation_errors):
    """
    Generar recomendaciones específicas basadas en criterios fallidos
    """
    recommendations = []
    
    if not criteria.get('length', True):
        recommendations.append("Usa al menos 8 caracteres (recomendado 12 o más)")
    
    if not criteria.get('uppercase', True):
        recommendations.append("Incluye al menos una letra mayúscula (A-Z)")
    
    if not criteria.get('lowercase', True):
        recommendations.append("Incluye al menos una letra minúscula (a-z)")
    
    if not criteria.get('numbers', True):
        recommendations.append("Incluye al menos un número (0-9)")
    
    if not criteria.get('special', True):
        recommendations.append("Incluye al menos un símbolo especial (!@#$%^&*)")
    
    if not criteria.get('not_common', True):
        recommendations.append("Evita contraseñas comunes como '123456' o 'password'")
    
    if not criteria.get('not_similar', True):
        recommendations.append("No uses información personal como tu nombre o email")
    
    if not criteria.get('not_numeric', True):
        recommendations.append("No uses solo números")
    
    # Agregar errores específicos de Django
    for error in validation_errors:
        if error not in [r for r in recommendations]:
            recommendations.append(error)
    
    return recommendations


@login_required
def change_password_ajax(request):
    """
    Vista AJAX para cambio de contraseña desde el perfil
    """
    if request.method == 'POST':
        logger.info(f"🔄 Cambio de contraseña iniciado para usuario: {request.user.email}")
        logger.info(f"📝 Datos POST recibidos: {list(request.POST.keys())}")
        
        # Debug: Verificar contraseñas
        old_password = request.POST.get('old_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')
        
        logger.info(f"🔍 Longitudes: old={len(old_password)}, new1={len(new_password1)}, new2={len(new_password2)}")
        logger.info(f"🔍 Contraseñas nuevas coinciden: {new_password1 == new_password2}")
        
        # Verificar contraseña actual
        if request.user.check_password(old_password):
            logger.info("✅ Contraseña actual es correcta")
        else:
            logger.error("❌ Contraseña actual es incorrecta")
        
        form = CustomPasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            logger.info("✅ Formulario válido, guardando nueva contraseña...")
            user = form.save()
            
            # Logging de seguridad
            security_logger.log_password_change_success(
                user=user,
                request=request,
                method="ajax"
            )
            
            logger.info(f"🎉 Contraseña cambiada exitosamente para: {user.email}")
            return JsonResponse({
                'success': True,
                'message': 'Contraseña cambiada exitosamente'
            })
        else:
            logger.error(f"❌ Formulario inválido. Errores completos: {dict(form.errors)}")
            
            # Debug detallado de cada campo
            for field, errors in form.errors.items():
                logger.error(f"  Campo {field}: {errors}")
            
            # Logging de error
            security_logger.log_password_change_failure(
                user=request.user,
                request=request,
                reason="Formulario inválido",
                method="ajax"
            )
            
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    logger.warning(f"⚠️ Método {request.method} no permitido para change_password_ajax")
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })


# ============================================
# VISTA DE REGISTRO
# ============================================

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """Formulario personalizado de registro"""
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })


class CustomRegisterView(FormView):
    """Vista personalizada de registro"""
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('subscriptions:select_initial_plan')
    
    def form_valid(self, form):
        """Registro exitoso"""
        user = form.save()
        
        # Log del registro
        security_logger.log_user_registration(
            user=user,
            request=self.request,
            method="form"
        )
        
        # Hacer login automático después del registro
        from django.contrib.auth import login
        login(self.request, user)
        
        # Fusión de carritos: Si el usuario tenía un carrito como invitado, asignarlo al nuevo usuario
        try:
            from apps.subscriptions.services import CartService
            # Llamar a get_or_create_cart con el nuevo usuario y la request
            # Esto activará la lógica de fusión que implementamos en services.py
            CartService.get_or_create_cart(
                user=user,
                session_key=self.request.session.session_key,
                request=self.request
            )
        except Exception as e:
            logger.error(f"Error fusionando carrito tras registro: {e}")
        
        messages.success(
            self.request,
            f'¡Bienvenido {user.email}! Tu cuenta ha sido creada exitosamente. '
            'Ahora selecciona un plan para comenzar a usar el sistema.'
        )
        
        # Verificar si hay un parámetro 'next' en la URL (ej: checkout)
        next_url = self.request.GET.get('next')
        if next_url:
            return redirect(next_url)
            
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Registro fallido"""
        security_logger.log_user_registration_failure(
            request=self.request,
            reason="Formulario inválido",
            form_errors=form.errors
        )
        
        return super().form_invalid(form)


@login_required
def settings_view(request):
    """Vista de configuraciones del usuario"""
    from django_otp import user_has_device, devices_for_user
    from django_otp.plugins.otp_totp.models import TOTPDevice
    
    # Obtener información del usuario
    user = request.user
    
    # Información de 2FA
    has_2fa = user_has_device(user)
    totp_devices = list(devices_for_user(user, confirmed=True))
    unconfirmed_devices = list(devices_for_user(user, confirmed=False))
    
    # Estadísticas de seguridad
    from django.contrib.auth.models import Group
    from apps.subscriptions.models import Subscription
    from django.utils import timezone
    
    # Información de suscripción
    active_subscription = None
    try:
        active_subscription = Subscription.objects.filter(
            user=user,
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
    except:
        pass
    
    # Información de sesiones activas
    from django.contrib.sessions.models import Session
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_sessions_count = 0
    for session in active_sessions:
        session_data = session.get_decoded()
        if session_data.get('_auth_user_id') == str(user.id):
            user_sessions_count += 1
    
    # Configuraciones de notificaciones (simuladas - se pueden expandir)
    notification_settings = {
        'email_notifications': True,
        'security_alerts': True,
        'subscription_reminders': True,
        'feature_updates': False,
    }
    
    context = {
        'user': user,
        'has_2fa': has_2fa,
        'totp_devices': totp_devices,
        'unconfirmed_devices': unconfirmed_devices,
        'active_subscription': active_subscription,
        'user_sessions_count': user_sessions_count,
        'notification_settings': notification_settings,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }
    
    return render(request, 'users/settings.html', context)


@login_required
@require_http_methods(["POST"])
def update_notification_setting(request):
    """Actualizar configuraciones de notificaciones via AJAX"""
    import json
    
    try:
        data = json.loads(request.body)
        setting = data.get('setting')
        enabled = data.get('enabled')
        
        # Aquí puedes guardar la configuración en la base de datos
        # Por ahora solo simulamos el éxito
        
        logger.info(f"Usuario {request.user.email} actualizó configuración {setting} a {enabled}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Configuración actualizada correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error actualizando configuración de notificación: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Error al actualizar la configuración'
        }, status=400)
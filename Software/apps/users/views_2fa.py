"""
Vistas para autenticación de dos factores (2FA)
"""
import io
import qrcode
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django_otp.models import Device
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.util import random_hex
from django_otp import user_has_device, match_token, devices_for_user
from django_otp.decorators import otp_required

from .forms import TwoFactorSetupForm, TwoFactorVerificationForm
from .services import TwoFactorService, AccountSecurityService
from .security_logging import security_logger


class TwoFactorSetupView(View):
    """
    Vista para configurar 2FA por primera vez
    """
    template_name = 'users/2fa_setup.html'
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        user = request.user
        
        # Verificar si ya tiene 2FA configurado
        if user.two_factor_enabled:
            messages.info(request, 'Ya tienes la autenticación de dos factores habilitada.')
            return redirect('users:2fa_manage')
        
        # Crear o obtener dispositivo TOTP
        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
        if not device:
            device = TOTPDevice.objects.create(
                user=user,
                name=f'{user.email}-totp',
                confirmed=False
            )
        
        # Generar URL para QR
        qr_url = device.config_url
        
        # Generar código QR
        qr_code_data = self._generate_qr_code(qr_url)
        
        form = TwoFactorSetupForm()
        
        context = {
            'form': form,
            'device': device,
            'qr_code_data': qr_code_data,
            'qr_url': qr_url,
            'backup_tokens': None
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        user = request.user
        form = TwoFactorSetupForm(request.POST)
        
        if form.is_valid():
            token = form.cleaned_data['token']
            
            # Buscar dispositivo TOTP no confirmado
            device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
            
            if device and device.verify_token(token):
                # Confirmar dispositivo
                device.confirmed = True
                device.save()
                
                # Generar tokens de backup
                backup_tokens = self._generate_backup_tokens(user)
                
                # Habilitar 2FA en el usuario
                TwoFactorService.enable_2fa(user, request)
                
                messages.success(request, '¡Autenticación de dos factores configurada exitosamente!')
                
                # Mostrar tokens de backup
                context = {
                    'backup_tokens': backup_tokens,
                    'setup_complete': True
                }
                return render(request, self.template_name, context)
            else:
                form.add_error('token', 'Código inválido. Por favor, intenta de nuevo.')
        
        # Si hay errores, regenerar QR
        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
        qr_code_data = self._generate_qr_code(device.config_url) if device else None
        
        context = {
            'form': form,
            'device': device,
            'qr_code_data': qr_code_data,
            'qr_url': device.config_url if device else None,
        }
        
        return render(request, self.template_name, context)
    
    def _generate_qr_code(self, url):
        """Genera código QR como imagen base64"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def _generate_backup_tokens(self, user):
        """Genera tokens de backup estáticos"""
        device, created = StaticDevice.objects.get_or_create(
            user=user,
            name=f'{user.email}-backup'
        )
        
        # Limpiar tokens existentes
        device.token_set.all().delete()
        
        # Generar 10 nuevos tokens
        tokens = []
        for i in range(10):
            token = StaticToken.random_token()
            StaticToken.objects.create(device=device, token=token)
            tokens.append(token)
        
        return tokens


class TwoFactorVerificationView(View):
    """
    Vista para verificar código 2FA durante el login
    """
    template_name = 'users/2fa_verify.html'
    
    def get(self, request):
        # Verificar que el usuario está parcialmente autenticado
        if not request.session.get('pre_2fa_user_id'):
            messages.error(request, 'Sesión inválida. Por favor, inicia sesión de nuevo.')
            return redirect('users:login')
        
        form = TwoFactorVerificationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = TwoFactorVerificationForm(request.POST)
        
        if form.is_valid():
            token = form.cleaned_data['token']
            user_id = request.session.get('pre_2fa_user_id')
            
            if not user_id:
                messages.error(request, 'Sesión inválida. Por favor, inicia sesión de nuevo.')
                return redirect('users:login')
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                messages.error(request, 'Usuario no encontrado.')
                return redirect('users:login')
            
            # Verificar token
            device = match_token(user, token)
            if device:
                # Login exitoso con 2FA
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Limpiar sesión temporal
                if 'pre_2fa_user_id' in request.session:
                    del request.session['pre_2fa_user_id']
                if 'pre_2fa_user_backend' in request.session:
                    del request.session['pre_2fa_user_backend']
                
                # Logging
                security_logger.logger.info(
                    f"2FA_SUCCESS | User: {user.email} | "
                    f"Device: {device.name} | "
                    f"IP: {security_logger._get_client_ip(request)}"
                )
                
                AccountSecurityService._record_security_event(
                    user, 'login_success',
                    f'Login exitoso con 2FA usando {device.name}',
                    security_logger._get_client_ip(request),
                    security_logger._get_user_agent(request)
                )
                
                messages.success(request, '¡Autenticación exitosa!')
                
                # Redirigir a la URL solicitada o dashboard
                next_url = request.session.get('next_url', reverse('dashboard:dashboard_view'))
                if 'next_url' in request.session:
                    del request.session['next_url']
                
                return redirect(next_url)
            else:
                # Token inválido
                security_logger.logger.warning(
                    f"2FA_FAILURE | User: {user.email} | "
                    f"Token: {token[:3]}*** | "
                    f"IP: {security_logger._get_client_ip(request)}"
                )
                
                AccountSecurityService._record_security_event(
                    user, 'login_failure',
                    'Fallo en verificación 2FA',
                    security_logger._get_client_ip(request),
                    security_logger._get_user_agent(request),
                    severity='medium'
                )
                
                form.add_error('token', 'Código inválido. Por favor, intenta de nuevo.')
        
        return render(request, self.template_name, {'form': form})


@login_required
def two_factor_manage_view(request):
    """
    Vista para gestionar configuración 2FA
    """
    user = request.user
    
    # Obtener dispositivos del usuario
    totp_devices = TOTPDevice.objects.filter(user=user, confirmed=True)
    static_devices = StaticDevice.objects.filter(user=user)
    
    # Contar tokens de backup disponibles
    backup_tokens_count = 0
    if static_devices.exists():
        backup_tokens_count = StaticToken.objects.filter(
            device__in=static_devices
        ).count()
    
    context = {
        'totp_devices': totp_devices,
        'backup_tokens_count': backup_tokens_count,
        'two_factor_enabled': user.two_factor_enabled,
    }
    
    return render(request, 'users/2fa_manage.html', context)


@login_required
@require_http_methods(["POST"])
def disable_two_factor(request):
    """
    Deshabilitar 2FA para el usuario
    """
    user = request.user
    
    # Eliminar todos los dispositivos
    TOTPDevice.objects.filter(user=user).delete()
    StaticDevice.objects.filter(user=user).delete()
    
    # Deshabilitar en el usuario
    TwoFactorService.disable_2fa(user, request)
    
    messages.success(request, 'Autenticación de dos factores deshabilitada.')
    return redirect('users:profile')


@login_required
def regenerate_backup_tokens(request):
    """
    Regenerar tokens de backup
    """
    if request.method == 'POST':
        user = request.user
        
        device, created = StaticDevice.objects.get_or_create(
            user=user,
            name=f'{user.email}-backup'
        )
        
        # Limpiar tokens existentes
        device.token_set.all().delete()
        
        # Generar nuevos tokens
        tokens = []
        for i in range(10):
            token = StaticToken.random_token()
            StaticToken.objects.create(device=device, token=token)
            tokens.append(token)
        
        # Logging
        security_logger.logger.info(
            f"BACKUP_TOKENS_REGENERATED | User: {user.email} | "
            f"IP: {security_logger._get_client_ip(request)}"
        )
        
        context = {
            'backup_tokens': tokens,
            'regenerated': True
        }
        
        return render(request, 'users/2fa_backup_tokens.html', context)
    
    return redirect('users:2fa_manage')


@login_required
def qr_code_view(request):
    """
    Genera y sirve código QR para configuración 2FA
    """
    user = request.user
    device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
    
    if not device:
        return HttpResponse('Dispositivo no encontrado', status=404)
    
    # Generar QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(device.config_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Servir como imagen
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response


# Middleware personalizado para verificar 2FA obligatorio
class Require2FAMiddleware:
    """
    Middleware que requiere 2FA para usuarios que lo tienen habilitado
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs que no requieren 2FA
        self.exempt_urls = [
            '/users/login/',
            '/users/logout/',
            '/users/2fa/',
            '/admin/',
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Verificar si la URL está exenta
        for exempt_url in self.exempt_urls:
            if request.path.startswith(exempt_url):
                return None
        
        # Verificar si el usuario está autenticado
        if not request.user.is_authenticated:
            return None
        
        # Verificar si el usuario tiene 2FA habilitado
        if not request.user.two_factor_enabled:
            return None
        
        # Verificar si ya está verificado con 2FA
        if request.user.is_verified():
            return None
        
        # Si no está verificado, redirigir a verificación 2FA
        if not request.session.get('pre_2fa_user_id'):
            # Guardar información para después de la verificación
            request.session['pre_2fa_user_id'] = request.user.id
            request.session['next_url'] = request.path
        
        return redirect('users:2fa_verify')
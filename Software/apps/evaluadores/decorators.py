"""
Decoradores para verificar permisos de evaluadores
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .services import EvaluadorService, EvaluadorSubscriptionService


def main_users_only(view_func):
    """
    Decorador que permite el acceso SOLO a usuarios principales.
    Deniega el acceso a usuarios que son evaluadores de otros usuarios.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Verificar si el usuario ES un evaluador activo de algún usuario principal
        if EvaluadorService.es_evaluador_activo(request.user):
            messages.error(
                request, 
                'No tienes permisos para acceder al módulo de gestión de evaluadores. '
                'Solo los usuarios principales pueden gestionar evaluadores.'
            )
            return redirect('dashboard:home')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def evaluador_required(function=None, module_name=None):
    """
    Decorador que requiere que el usuario sea evaluador activo
    
    Args:
        module_name: Nombre del módulo al que debe tener acceso (opcional)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Verificar si es evaluador activo
            if not EvaluadorService.es_evaluador_activo(request.user):
                messages.error(
                    request,
                    'Debes ser un evaluador activo para acceder a esta función.'
                )
                return redirect('dashboard:home')
            
            # Verificar acceso al módulo específico si se especifica
            if module_name:
                if not EvaluadorSubscriptionService.has_module_access_with_inheritance(
                    request.user, 
                    module_name
                ):
                    messages.error(
                        request,
                        f'No tienes acceso al módulo {module_name}.'
                    )
                    return redirect('evaluadores:mi_perfil_evaluador')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator


def subscription_required_with_inheritance(module_name):
    """
    Decorador que verifica acceso a un módulo, incluyendo herencia de evaluadores
    
    Args:
        module_name: Nombre del módulo requerido
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Verificar acceso con herencia
            if not EvaluadorSubscriptionService.has_module_access_with_inheritance(
                request.user, 
                module_name
            ):
                messages.error(
                    request,
                    f'No tienes acceso al módulo {module_name}. '
                    'Contacta a tu administrador si necesitas acceso.'
                )
                return redirect('dashboard:home')
            
            # Añadir información de suscripción al request
            request.subscription_context = (
                EvaluadorSubscriptionService.get_usage_limits_with_inheritance(
                    request.user, 
                    module_name
                )
            )
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def evaluador_permission_required(action):
    """
    Decorador que verifica permisos específicos de evaluador
    
    Args:
        action: Acción que se quiere realizar ('crear_reportes', 'editar_evaluaciones', etc.)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Si no es evaluador, permitir (usuario con suscripción propia)
            if not EvaluadorService.es_evaluador_activo(request.user):
                return view_func(request, *args, **kwargs)
            
            # Verificar permisos del evaluador
            perfiles = EvaluadorService.obtener_perfiles_evaluador(request.user)
            
            tiene_permiso = False
            mensaje_error = f"Sin permisos para {action}"
            
            for perfil in perfiles:
                puede_realizar, mensaje = perfil.puede_realizar_accion(action)
                if puede_realizar:
                    tiene_permiso = True
                    break
                else:
                    mensaje_error = mensaje
            
            if not tiene_permiso:
                messages.error(request, mensaje_error)
                return redirect('evaluadores:mi_perfil_evaluador')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def main_user_access_required(view_func):
    """
    Decorador que requiere acceso de usuario principal específico
    Útil para vistas donde el evaluador actúa en nombre del usuario principal
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Obtener usuario_principal_id de los argumentos de la URL
        usuario_principal_id = kwargs.get('usuario_principal_id')
        
        if not usuario_principal_id:
            messages.error(request, 'ID de usuario principal requerido.')
            return redirect('dashboard:home')
        
        # Verificar acceso
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            usuario_principal = User.objects.get(id=usuario_principal_id)
        except User.DoesNotExist:
            messages.error(request, 'Usuario principal no encontrado.')
            return redirect('dashboard:home')
        
        # Verificar que tiene acceso como evaluador
        tiene_acceso, mensaje = EvaluadorService.tiene_acceso_como_evaluador(
            request.user,
            usuario_principal
        )
        
        if not tiene_acceso:
            messages.error(request, mensaje)
            return redirect('evaluadores:mi_perfil_evaluador')
        
        # Añadir usuario principal al request
        request.usuario_principal = usuario_principal
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def api_evaluador_required(module_name=None):
    """
    Decorador para APIs que requieren acceso de evaluador
    Retorna JSON en lugar de redireccionar
    
    Args:
        module_name: Módulo requerido (opcional)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'Autenticación requerida'
                }, status=401)
            
            # Verificar acceso al módulo si se especifica
            if module_name:
                if not EvaluadorSubscriptionService.has_module_access_with_inheritance(
                    request.user, 
                    module_name
                ):
                    return JsonResponse({
                        'success': False,
                        'error': f'Sin acceso al módulo {module_name}'
                    }, status=403)
            
            # Si es evaluador, verificar estado activo
            if EvaluadorService.es_evaluador_activo(request.user):
                perfiles = EvaluadorService.obtener_perfiles_evaluador(request.user)
                if not perfiles:
                    return JsonResponse({
                        'success': False,
                        'error': 'Perfil de evaluador inactivo'
                    }, status=403)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def feature_access_required_with_inheritance(module_name, feature_code):
    """
    Decorador que verifica acceso a una característica específica con herencia
    
    Args:
        module_name: Nombre del módulo
        feature_code: Código de la característica
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Verificar acceso a la característica
            if not EvaluadorSubscriptionService.has_feature_access_with_inheritance(
                request.user, 
                module_name, 
                feature_code
            ):
                messages.error(
                    request,
                    f'No tienes acceso a la característica {feature_code} del módulo {module_name}.'
                )
                return redirect('dashboard:home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def usage_limit_check(module_name, action_type):
    """
    Decorador que verifica límites de uso antes de permitir una acción
    
    Args:
        module_name: Nombre del módulo
        action_type: Tipo de acción ('create_report', 'upload_file', etc.)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Verificar límites de uso
            puede_realizar, mensaje = EvaluadorSubscriptionService.can_user_perform_action_with_inheritance(
                request.user,
                module_name,
                action_type
            )
            
            if not puede_realizar:
                messages.warning(request, mensaje)
                return redirect('dashboard:home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class EvaluadorMixin:
    """
    Mixin para vistas basadas en clases que requieren funcionalidad de evaluador
    """
    
    module_name = None
    required_action = None
    
    def dispatch(self, request, *args, **kwargs):
        """Override de dispatch para verificar permisos de evaluador"""
        if not request.user.is_authenticated:
            return redirect('users:login')
        
        # Verificar acceso al módulo
        if self.module_name:
            if not EvaluadorSubscriptionService.has_module_access_with_inheritance(
                request.user, 
                self.module_name
            ):
                messages.error(
                    request,
                    f'No tienes acceso al módulo {self.module_name}.'
                )
                return redirect('dashboard:home')
        
        # Verificar acción requerida
        if self.required_action:
            if EvaluadorService.es_evaluador_activo(request.user):
                perfiles = EvaluadorService.obtener_perfiles_evaluador(request.user)
                
                tiene_permiso = any(
                    perfil.puede_realizar_accion(self.required_action)[0]
                    for perfil in perfiles
                    if perfil.tiene_acceso_a_modulo(self.module_name)
                )
                
                if not tiene_permiso:
                    messages.error(
                        request,
                        f'Sin permisos para {self.required_action}.'
                    )
                    return redirect('evaluadores:mi_perfil_evaluador')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Añadir contexto de evaluador"""
        context = super().get_context_data(**kwargs)
        
        if hasattr(self.request, 'subscription_context'):
            context['subscription_context'] = self.request.subscription_context
        
        # Añadir información de evaluador si aplica
        if EvaluadorService.es_evaluador_activo(self.request.user):
            context['evaluator_context'] = (
                EvaluadorSubscriptionService.get_inherited_subscription_context(
                    self.request.user
                )
            )
        
        return context


# ===== DECORADORES DE CONTROL DE SUSCRIPCIÓN =====

def evaluadores_subscription_required(view_func=None, *, action_type='view'):
    """
    Decorador que verifica si el usuario tiene acceso al módulo de evaluadores
    según su suscripción activa.
    
    Args:
        action_type: Tipo de acción ('view', 'create', 'manage')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Los superusuarios siempre tienen acceso
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene al menos una suscripción activa
            from apps.subscriptions.models import Subscription
            from django.utils import timezone
            
            active_subscriptions = Subscription.objects.filter(
                user=user,
                status='active',
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).select_related('plan', 'plan__module', 'plan__plan_type')
            
            if not active_subscriptions.exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': True,
                        'message': 'Necesitas una suscripción activa para gestionar evaluadores',
                        'redirect_url': '/subscriptions/plans/'
                    }, status=403)
                
                messages.error(request, 'Necesitas una suscripción activa para gestionar evaluadores.')
                return redirect('subscriptions:plans')
            
            # Verificar límites de evaluadores específicos
            if action_type == 'create':
                can_create, message = can_create_evaluator(user, active_subscriptions)
                if not can_create:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'error': True,
                            'message': message,
                            'redirect_url': '/subscriptions/plans/'
                        }, status=403)
                    
                    messages.warning(request, message)
                    return redirect('evaluadores:lista')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


def can_create_evaluator(user, active_subscriptions=None):
    """
    Verifica si el usuario puede crear más evaluadores según sus suscripciones
    
    Returns:
        tuple: (can_create: bool, message: str)
    """
    if user.is_superuser:
        return True, ""
    
    if active_subscriptions is None:
        from apps.subscriptions.models import Subscription
        from django.utils import timezone
        
        active_subscriptions = Subscription.objects.filter(
            user=user,
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).select_related('plan')
    
    # Buscar el límite máximo de evaluadores permitido
    max_evaluators = 0
    plan_with_evaluators = None
    
    for subscription in active_subscriptions:
        evaluator_limit = subscription.plan.limits.get('evaluators', 0)
        if isinstance(evaluator_limit, int) and evaluator_limit > max_evaluators:
            max_evaluators = evaluator_limit
            plan_with_evaluators = subscription.plan
    
    # Si ningún plan permite evaluadores
    if max_evaluators == 0:
        return False, (
            "Tu plan actual no incluye la gestión de evaluadores. "
            "Actualiza a un plan corporativo para poder crear evaluadores."
        )
    
    # Contar evaluadores actuales
    from .models import Evaluador
    current_count = Evaluador.objects.filter(usuario_principal=user).count()
    
    if current_count >= max_evaluators:
        return False, (
            f"Has alcanzado el límite máximo de {max_evaluators} evaluadores "
            f"para tu plan {plan_with_evaluators.name}. "
            "Actualiza tu suscripción para crear más evaluadores."
        )
    
    return True, ""


def get_user_evaluator_limits(user):
    """
    Obtiene los límites de evaluadores para un usuario específico
    
    Returns:
        dict: {
            'max_evaluators': int,
            'current_count': int,
            'remaining': int,
            'can_create': bool,
            'plan_name': str
        }
    """
    if user.is_superuser:
        return {
            'max_evaluators': -1,
            'current_count': 0,
            'remaining': -1,
            'can_create': True,
            'plan_name': 'Superusuario'
        }
    
    from apps.subscriptions.models import Subscription
    from django.utils import timezone
    
    active_subscriptions = Subscription.objects.filter(
        user=user,
        status='active',
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).select_related('plan')
    
    # Buscar el límite máximo
    max_evaluators = 0
    best_plan = None
    
    for subscription in active_subscriptions:
        evaluator_limit = subscription.plan.limits.get('evaluators', 0)
        if isinstance(evaluator_limit, int) and evaluator_limit > max_evaluators:
            max_evaluators = evaluator_limit
            best_plan = subscription.plan
    
    # Contar evaluadores actuales
    from .models import Evaluador
    current_count = Evaluador.objects.filter(usuario_principal=user).count()
    
    remaining = max(0, max_evaluators - current_count) if max_evaluators > 0 else 0
    
    return {
        'max_evaluators': max_evaluators,
        'current_count': current_count,
        'remaining': remaining,
        'can_create': max_evaluators == -1 or current_count < max_evaluators,
        'plan_name': best_plan.name if best_plan else 'Sin plan'
    }
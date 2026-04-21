"""
Decoradores para verificar suscripciones y planes
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from .models import Subscription
from .demo_service import DemoService
from .services import SubscriptionService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def subscription_required(module_name, redirect_url=None):
    """
    Decorador que requiere suscripción activa a un módulo específico
    
    Usage:
        @subscription_required('risk_hoteles')
        def hotel_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar si tiene suscripción al módulo
            if not SubscriptionService.has_module_access(request.user, module_name):
                
                # Si es petición AJAX, retornar JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': True,
                        'message': f'Necesitas una suscripción activa para acceder a {module_name}',
                        'redirect_url': reverse('subscriptions:plans')
                    }, status=403)
                
                # Petición normal, agregar mensaje y redirigir
                messages.error(
                    request, 
                    f'Necesitas una suscripción activa para acceder a {module_name}. '
                    'Revisa nuestros planes disponibles.'
                )
                
                return redirect(redirect_url or reverse('subscriptions:plans'))
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def feature_required(module_name, feature_code, redirect_url=None):
    """
    Decorador que requiere acceso a una característica específica
    
    Usage:
        @feature_required('risk_hoteles', 'export_data')
        def export_data_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar si tiene acceso a la característica
            if not SubscriptionService.has_feature_access(request.user, module_name, feature_code):
                
                # Si es petición AJAX, retornar JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': True,
                        'message': f'Esta característica no está incluida en tu plan actual',
                        'redirect_url': reverse('subscriptions:upgrade', kwargs={'module': module_name})
                    }, status=403)
                
                # Petición normal
                messages.warning(
                    request,
                    f'Esta característica no está incluida en tu plan actual. '
                    'Considera actualizar tu suscripción.'
                )
                
                return redirect(redirect_url or reverse('subscriptions:upgrade', kwargs={'module': module_name}))
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def plan_level_required(module_name, min_plan_type, redirect_url=None):
    """
    Decorador que requiere un nivel mínimo de plan
    
    Usage:
        @plan_level_required('risk_hoteles', 'pro')
        def pro_feature_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Obtener suscripciones del usuario para el módulo
            subscriptions = SubscriptionService.get_user_subscriptions(request.user, module_name)
            
            # Definir jerarquía de planes
            plan_hierarchy = {
                'basic': 1,
                'starter': 1,
                'essential': 1,
                'pro': 2,
                'advanced': 2,
                'professional': 2,
                'enterprise': 3,
                'premium': 3,
            }
            
            min_level = plan_hierarchy.get(min_plan_type.lower(), 1)
            has_required_level = False
            
            for subscription in subscriptions:
                plan_type_name = subscription.plan.plan_type.name.lower()
                current_level = plan_hierarchy.get(plan_type_name, 1)
                
                if current_level >= min_level:
                    has_required_level = True
                    break
            
            if not has_required_level:
                # Si es petición AJAX, retornar JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': True,
                        'message': f'Necesitas un plan {min_plan_type} o superior para acceder a esta función',
                        'redirect_url': reverse('subscriptions:upgrade', kwargs={'module': module_name})
                    }, status=403)
                
                # Petición normal
                messages.warning(
                    request,
                    f'Necesitas un plan {min_plan_type} o superior para acceder a esta función. '
                    'Actualiza tu suscripción para desbloquear todas las características.'
                )
                
                return redirect(redirect_url or reverse('subscriptions:upgrade', kwargs={'module': module_name}))
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def usage_limit_check(module_name, resource_type, redirect_url=None):
    """
    Decorador que verifica límites de uso (reportes, usuarios, etc.)
    
    Usage:
        @usage_limit_check('risk_hoteles', 'reports')
        def generate_report_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar límites de uso
            can_use = False
            
            if resource_type == 'reports':
                can_use = SubscriptionService.can_generate_report(request.user, module_name)
            elif resource_type == 'users':
                can_use = SubscriptionService.can_add_user(request.user, module_name)
            
            if not can_use:
                # Obtener información de límites
                limits = SubscriptionService.get_usage_limits(request.user, module_name)
                
                if limits:
                    if resource_type == 'reports':
                        current = limits['current_reports']
                        maximum = limits['max_reports']
                    elif resource_type == 'users':
                        current = limits['current_users']
                        maximum = limits['max_users']
                    else:
                        current = 0
                        maximum = 0
                    
                    message = f'Has alcanzado el límite de {resource_type} ({current}/{maximum}). '
                else:
                    message = f'Has alcanzado el límite de {resource_type}. '
                
                # Si es petición AJAX, retornar JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': True,
                        'message': message + 'Considera actualizar tu plan.',
                        'redirect_url': reverse('subscriptions:upgrade', kwargs={'module': module_name}),
                        'limits': limits
                    }, status=403)
                
                # Petición normal
                messages.warning(request, message + 'Considera actualizar tu plan para obtener más recursos.')
                
                return redirect(redirect_url or reverse('subscriptions:upgrade', kwargs={'module': module_name}))
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def trial_access_required(module_name, redirect_url=None):
    """
    Decorador que permite acceso durante período de prueba
    
    Usage:
        @trial_access_required('risk_hoteles')
        def trial_feature_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar si tiene suscripción o está en período de prueba
            subscriptions = SubscriptionService.get_user_subscriptions(request.user, module_name)
            
            # Verificar si alguna suscripción está activa o en período de prueba
            has_access = False
            for subscription in subscriptions:
                if subscription.is_active() or (subscription.is_trial and subscription.trial_end_date and subscription.trial_end_date > timezone.now()):
                    has_access = True
                    break
            
            if not has_access:
                # Si es petición AJAX, retornar JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': True,
                        'message': 'Tu período de prueba ha expirado. Adquiere una suscripción para continuar.',
                        'redirect_url': reverse('subscriptions:plans')
                    }, status=403)
                
                # Petición normal
                messages.info(
                    request,
                    'Tu período de prueba ha expirado. Adquiere una suscripción para continuar disfrutando de nuestros servicios.'
                )
                
                return redirect(redirect_url or reverse('subscriptions:plans'))
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def simple_subscription_required(view_func):
    """
    Decorador simple que requiere suscripción activa (sin módulo específico)
    Para uso cuando solo necesitamos verificar que el usuario tenga alguna suscripción activa
    
    Usage:
        @simple_subscription_required
        def some_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Verificar si tiene al menos una suscripción activa
        active_subscriptions = Subscription.objects.filter(
            user=request.user,
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).exists()
        
        if not active_subscriptions:
            # Si es petición AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': True,
                    'message': 'Necesitas una suscripción activa para acceder a esta función',
                    'redirect_url': reverse('subscriptions:plans')
                }, status=403)
            
            # Petición normal, agregar mensaje y redirigir
            messages.error(
                request, 
                'Necesitas una suscripción activa para acceder a esta función. '
                'Revisa nuestros planes disponibles.'
            )
            
            return redirect(reverse('subscriptions:plans'))
        
        return view_func(request, *args, **kwargs)
    return wrapper


def api_subscription_required(module_name):
    """
    Decorador específico para APIs que requieren suscripción
    
    Usage:
        @api_subscription_required('risk_hoteles')
        def api_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': True,
                    'message': 'Authentication required',
                    'code': 'AUTHENTICATION_REQUIRED'
                }, status=401)
            
            # Verificar suscripción
            if not SubscriptionService.has_module_access(request.user, module_name):
                return JsonResponse({
                    'error': True,
                    'message': f'Active subscription required for {module_name}',
                    'code': 'SUBSCRIPTION_REQUIRED',
                    'module': module_name
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
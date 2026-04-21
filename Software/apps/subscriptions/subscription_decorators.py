"""
Nuevos decoradores para el sistema mejorado de suscripciones
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Subscription
from .demo_service import DemoService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def subscription_required_enhanced(view_func=None, *, module_required=None, feature_required=None):
    """
    Decorador que verifica si el usuario tiene una suscripción activa.
    
    Args:
        module_required: Nombre del módulo requerido (opcional)
        feature_required: Característica específica requerida (opcional)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Skip para superusuarios
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene alguna suscripción activa
            active_subscriptions = Subscription.objects.filter(
                user=request.user,
                status='active',
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
            
            if not active_subscriptions.exists():
                messages.warning(
                    request,
                    'Necesitas una suscripción activa para acceder a esta función.'
                )
                return redirect('subscriptions:select_initial_plan')
            
            # Verificar módulo específico si se requiere
            if module_required:
                has_module_access = active_subscriptions.filter(
                    plan__module__name=module_required
                ).exists()
                
                if not has_module_access:
                    messages.warning(
                        request,
                        f'Necesitas una suscripción al módulo {module_required} para acceder a esta función.'
                    )
                    return redirect('subscriptions:plans')
            
            # Verificar característica específica si se requiere
            if feature_required:
                has_feature = False
                for subscription in active_subscriptions:
                    if subscription.plan.features.get(feature_required, False):
                        has_feature = True
                        break
                
                if not has_feature:
                    messages.warning(
                        request,
                        f'Esta función requiere una suscripción con la característica {feature_required}.'
                    )
                    return redirect('subscriptions:plans')
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


def demo_limitation_check(action_type):
    """
    Decorador que verifica si un usuario demo puede realizar una acción específica
    
    Args:
        action_type: Tipo de acción a verificar ('create_report', 'upload_file', etc.)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Skip para superusuarios
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si está en demo y si puede realizar la acción
            can_perform, error_message = DemoService.can_user_perform_action(
                request.user, 
                action_type
            )
            
            if not can_perform:
                messages.error(request, error_message)
                
                # Redirigir según el tipo de error
                if 'expirado' in error_message.lower():
                    return redirect('subscriptions:plans')
                else:
                    # Es un límite, redirigir al dashboard con info
                    return redirect('dashboard:dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    return decorator


def track_demo_usage(usage_type, amount=1):
    """
    Decorador que automaticamente trackea el uso de recursos para usuarios demo
    
    Args:
        usage_type: Tipo de uso ('reports', 'storage_gb')
        amount: Cantidad a incrementar (default: 1)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Ejecutar la vista primero
            response = view_func(request, *args, **kwargs)
            
            # Si la vista se ejecutó exitosamente, trackear uso
            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                if hasattr(request, 'user') and request.user.is_authenticated:
                    try:
                        DemoService.increment_usage(request.user, usage_type, amount)
                    except Exception as e:
                        logger.error(f"Error tracking demo usage: {e}")
            
            return response
        
        return _wrapped_view
    
    return decorator


class SubscriptionContext:
    """
    Clase para manejar contexto de suscripción en views basadas en clases
    """
    
    @staticmethod
    def get_user_subscriptions(user):
        """Obtiene todas las suscripciones activas de un usuario"""
        if user.is_superuser:
            return None
        
        return Subscription.objects.filter(
            user=user,
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).select_related('plan', 'plan__module', 'plan__plan_type')
    
    @staticmethod
    def has_module_access(user, module_name):
        """Verifica si el usuario tiene acceso a un módulo específico"""
        if user.is_superuser:
            return True
        
        subscriptions = SubscriptionContext.get_user_subscriptions(user)
        if not subscriptions:
            return False
        
        return subscriptions.filter(plan__module__name=module_name).exists()
    
    @staticmethod
    def has_feature(user, feature_name):
        """Verifica si el usuario tiene acceso a una característica específica"""
        if user.is_superuser:
            return True
        
        subscriptions = SubscriptionContext.get_user_subscriptions(user)
        if not subscriptions:
            return False
        
        for subscription in subscriptions:
            if subscription.plan.features.get(feature_name, False):
                return True
        
        return False
    
    @staticmethod
    def get_subscription_summary(user):
        """Obtiene un resumen de las suscripciones del usuario"""
        if user.is_superuser:
            return {
                'is_superuser': True,
                'has_subscriptions': True,
                'subscriptions': [],
                'demo_stats': None
            }
        
        subscriptions = SubscriptionContext.get_user_subscriptions(user)
        
        # Verificar si está en demo
        demo_stats = DemoService.get_demo_usage_stats(user)
        
        return {
            'is_superuser': False,
            'has_subscriptions': subscriptions.exists() if subscriptions else False,
            'subscriptions': list(subscriptions) if subscriptions else [],
            'demo_stats': demo_stats,
            'is_demo': demo_stats is not None
        }


# Decorador de conveniencia para vista basada en funciones
def require_subscription(module=None, feature=None):
    """
    Decorador de conveniencia que combina login_required y subscription_required
    """
    return subscription_required_enhanced(module_required=module, feature_required=feature)
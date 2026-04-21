"""
Context processors para información de suscripciones en templates
"""
from .access_control import get_user_access_summary, get_demo_status
from .services import SubscriptionService


def subscription_context(request):
    """
    Agrega información de suscripciones al contexto de todos los templates
    """
    if not request.user.is_authenticated:
        return {}
    
    try:
        # Resumen de acceso a módulos
        user_access = get_user_access_summary(request.user)
        
        # Información de DEMO activos
        active_demos = []
        for access_info in user_access:
            if access_info['demo_status']['active']:
                active_demos.append({
                    'module': access_info['module'],
                    'days_remaining': access_info['demo_status']['days_remaining']
                })
        
        return {
            'user_access_summary': user_access,
            'active_demos': active_demos,
            'has_any_subscription': any(info['has_subscription'] for info in user_access),
            'has_any_demo': len(active_demos) > 0
        }
        
    except Exception:
        # En caso de error, no romper el template
        return {}


def demo_notifications(request):
    """
    Context processor para notificaciones de DEMO próximos a expirar
    """
    if not request.user.is_authenticated:
        return {}
    
    try:
        from .models import Module
        
        expiring_demos = []
        
        for module in Module.objects.filter(is_active=True):
            demo_status = get_demo_status(request.user, module.name)
            
            if demo_status['active'] and demo_status['days_remaining'] <= 3:
                expiring_demos.append({
                    'module': module,
                    'days_remaining': demo_status['days_remaining']
                })
        
        return {
            'expiring_demos': expiring_demos
        }
        
    except Exception:
        return {}
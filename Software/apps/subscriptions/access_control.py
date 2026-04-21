"""
Sistema de control de acceso basado en suscripciones con período DEMO
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Subscription
from .services import SubscriptionService


def requires_subscription(module_name, feature_code=None, allow_demo=True):
    """
    Decorador que requiere suscripción activa o período DEMO para acceder a una vista
    
    Args:
        module_name: Nombre del módulo requerido
        feature_code: Código de característica específica (opcional)
        allow_demo: Si permite acceso durante período DEMO
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Verificar suscripción activa
            if SubscriptionService.has_module_access(user, module_name):
                # Verificar característica específica si se especifica
                if feature_code and not SubscriptionService.has_feature_access(user, module_name, feature_code):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': f'Tu plan no incluye la característica: {feature_code}',
                            'requires_upgrade': True
                        }, status=403)
                    
                    messages.warning(request, f'Tu plan no incluye esta característica. Considera actualizar tu suscripción.')
                    return redirect('subscriptions:upgrade', module_name=module_name)
                
                return view_func(request, *args, **kwargs)
            
            # Si no tiene suscripción, verificar período DEMO
            if allow_demo:
                demo_status = get_demo_status(user, module_name)
                
                if demo_status['active']:
                    # Agregar información del DEMO al contexto
                    if hasattr(request, 'demo_info'):
                        request.demo_info.update(demo_status)
                    else:
                        request.demo_info = demo_status
                    
                    return view_func(request, *args, **kwargs)
                
                elif demo_status['can_start']:
                    # Redirigir a página para iniciar DEMO
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': 'Inicia tu período de demostración gratuito',
                            'requires_demo': True,
                            'demo_url': f'/subscriptions/demo/{module_name}/'
                        }, status=403)
                    
                    return redirect('subscriptions:demo_info', module_name=module_name)
            
            # Sin acceso - redirigir a planes
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Necesitas una suscripción para acceder a este módulo',
                    'requires_subscription': True
                }, status=403)
            
            messages.info(request, 'Necesitas una suscripción para acceder a este módulo.')
            return redirect('subscriptions:demo_info', module_name=module_name)
        
        return wrapper
    return decorator


def requires_paid_subscription(module_name, feature_code=None):
    """
    Decorador que requiere suscripción PAGADA (no permite DEMO)
    Útil para funcionalidades premium
    """
    return requires_subscription(module_name, feature_code, allow_demo=False)


def get_demo_status(user, module_name):
    """
    Obtiene el estado del período DEMO para un usuario y módulo
    
    Returns:
        dict con: active, can_start, days_remaining, started_at, expires_at
    """
    try:
        # Buscar suscripción DEMO existente
        demo_subscription = Subscription.objects.filter(
            user=user,
            plan__module__name=module_name,
            is_trial=True,
            status__in=['active', 'expired']
        ).first()
        
        if demo_subscription:
            now = timezone.now()
            
            if demo_subscription.status == 'active' and demo_subscription.end_date > now:
                # DEMO activo
                days_remaining = (demo_subscription.end_date - now).days
                return {
                    'active': True,
                    'can_start': False,
                    'days_remaining': days_remaining,
                    'started_at': demo_subscription.start_date,
                    'expires_at': demo_subscription.end_date,
                    'subscription': demo_subscription
                }
            else:
                # DEMO expirado
                return {
                    'active': False,
                    'can_start': False,
                    'days_remaining': 0,
                    'started_at': demo_subscription.start_date,
                    'expires_at': demo_subscription.end_date,
                    'expired': True
                }
        else:
            # Puede iniciar DEMO
            return {
                'active': False,
                'can_start': True,
                'days_remaining': 15,  # Días disponibles
                'started_at': None,
                'expires_at': None
            }
            
    except Exception as e:
        # En caso de error, denegar acceso
        return {
            'active': False,
            'can_start': False,
            'days_remaining': 0,
            'error': str(e)
        }


def start_demo_period(user, module_name, demo_days=15):
    """
    Inicia un período DEMO para un usuario y módulo
    
    Returns:
        Subscription object o None si no se pudo crear
    """
    try:
        from .models import Module, Plan
        
        # Verificar que no tenga DEMO activo
        demo_status = get_demo_status(user, module_name)
        if demo_status['active'] or not demo_status['can_start']:
            return None
        
        # Obtener módulo
        module = Module.objects.get(name=module_name, is_active=True)
        
        # Buscar plan básico o más económico del módulo para DEMO
        demo_plan = module.plans.filter(is_active=True).order_by('monthly_price').first()
        
        if not demo_plan:
            return None
        
        # Crear suscripción DEMO
        start_date = timezone.now()
        end_date = start_date + timedelta(days=demo_days)
        
        demo_subscription = Subscription.objects.create(
            user=user,
            plan=demo_plan,
            order=None,  # Sin orden porque es gratis
            billing_cycle='monthly',
            start_date=start_date,
            end_date=end_date,
            status='active',
            is_trial=True,
            trial_end_date=end_date
        )
        
        return demo_subscription
        
    except Exception as e:
        return None


class AccessControlMixin:
    """
    Mixin para vistas basadas en clases que requieren suscripción
    """
    required_module = None
    required_feature = None
    allow_demo = True
    
    def dispatch(self, request, *args, **kwargs):
        if not self.required_module:
            raise ValueError("required_module must be specified")
        
        user = request.user
        
        if not user.is_authenticated:
            return redirect('users:login')
        
        # Verificar acceso usando la misma lógica del decorador
        if SubscriptionService.has_module_access(user, self.required_module):
            if self.required_feature and not SubscriptionService.has_feature_access(user, self.required_module, self.required_feature):
                messages.warning(request, 'Tu plan no incluye esta característica.')
                return redirect('subscriptions:upgrade', module_name=self.required_module)
            
            return super().dispatch(request, *args, **kwargs)
        
        # Lógica de DEMO
        if self.allow_demo:
            demo_status = get_demo_status(user, self.required_module)
            
            if demo_status['active']:
                request.demo_info = demo_status
                return super().dispatch(request, *args, **kwargs)
            elif demo_status['can_start']:
                return redirect('subscriptions:demo_info', module_name=self.required_module)
        
        messages.info(request, 'Necesitas una suscripción para acceder a este módulo.')
        return redirect('subscriptions:demo_info', module_name=self.required_module)


# Decoradores específicos por módulo (ejemplos)

def requires_risk_hoteles(feature_code=None):
    """Decorador específico para módulo de Risk Hoteles"""
    return requires_subscription('risk_hoteles', feature_code)


def requires_risk_conjuntos(feature_code=None):
    """Decorador específico para módulo de Risk Conjuntos"""
    return requires_subscription('risk_conjuntos', feature_code)


def requires_security_probabilistic(feature_code=None):
    """Decorador específico para módulo de Security Probabilistic"""
    return requires_subscription('security_probabilistic', feature_code)


# Funciones de utilidad para templates

def get_user_access_summary(user):
    """
    Obtiene resumen completo de acceso del usuario a todos los módulos
    Útil para mostrar en dashboard
    """
    from .models import Module
    
    modules_access = []
    
    for module in Module.objects.filter(is_active=True):
        has_subscription = SubscriptionService.has_module_access(user, module.name)
        demo_status = get_demo_status(user, module.name)
        
        modules_access.append({
            'module': module,
            'has_subscription': has_subscription,
            'demo_status': demo_status,
            'can_access': has_subscription or demo_status['active']
        })
    
    return modules_access
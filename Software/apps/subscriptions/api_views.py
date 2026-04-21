"""
API views para funcionalidades AJAX del sistema de suscripciones
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import Module, Plan
from .services import CartService, SubscriptionService
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def cart_count(request):
    """Obtiene el número de items en el carrito"""
    try:
        # Asegurar que la sesión existe
        if not request.session.session_key:
            request.session.create()
            
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            request=request
        )
        
        return JsonResponse({
            'success': True,
            'count': cart.total_items,
            'total': float(cart.total_amount)
        })
        
    except Exception as e:
        logger.error(f"Error getting cart count: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


@require_http_methods(["GET"])
def cart_summary(request):
    """Obtiene resumen completo del carrito"""
    try:
        # Asegurar que la sesión existe
        if not request.session.session_key:
            request.session.create()
            
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            request=request
        )
        
        items_data = []
        for item in cart.items.all():
            items_data.append({
                'id': item.id,
                'plan': {
                    'id': item.plan.id,
                    'name': str(item.plan),
                    'module': item.plan.module.display_name,
                    'icon': item.plan.module.icon,
                    'color': item.plan.module.color,
                },
                'billing_cycle': item.billing_cycle,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'subtotal': float(item.subtotal),
                'discount_percentage': item.plan.get_discount_percentage(item.billing_cycle)
            })
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'total_items': cart.total_items,
            'total_amount': float(cart.total_amount)
        })
        
    except Exception as e:
        logger.error(f"Error getting cart summary: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def usage_stats(request, module_name):
    """Obtiene estadísticas de uso para un módulo"""
    try:
        stats = SubscriptionService.get_usage_limits(request.user, module_name)
        
        if not stats:
            return JsonResponse({
                'success': False,
                'message': 'No tienes suscripción activa a este módulo'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'module': module_name,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def subscription_status(request, module_name):
    """Obtiene estado de suscripción para un módulo"""
    try:
        subscriptions = SubscriptionService.get_user_subscriptions(request.user, module_name)
        has_access = subscriptions.exists()
        
        subscription_data = None
        if has_access:
            subscription = subscriptions.first()
            subscription_data = {
                'id': str(subscription.id),
                'plan': str(subscription.plan),
                'status': subscription.status,
                'start_date': subscription.start_date.isoformat(),
                'end_date': subscription.end_date.isoformat(),
                'days_remaining': subscription.days_remaining(),
                'is_trial': subscription.is_trial,
                'billing_cycle': subscription.billing_cycle,
                'current_usage': {
                    'users': subscription.current_users,
                    'reports': subscription.current_reports,
                    'storage_gb': subscription.current_storage_gb,
                },
                'usage_percentages': {
                    'users': subscription.usage_percentage('users'),
                    'reports': subscription.usage_percentage('reports'),
                    'storage': subscription.usage_percentage('storage'),
                }
            }
        
        return JsonResponse({
            'success': True,
            'module': module_name,
            'has_access': has_access,
            'subscription': subscription_data
        })
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


@require_http_methods(["GET"])
def available_plans(request, module_name):
    """Obtiene planes disponibles para un módulo"""
    try:
        module = get_object_or_404(Module, name=module_name, is_active=True)
        plans = module.plans.filter(is_active=True).select_related('plan_type').order_by('order', 'monthly_price')
        
        plans_data = []
        for plan in plans:
            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'plan_type': plan.plan_type.name,
                'description': plan.description,
                'prices': {
                    'monthly': float(plan.monthly_price),
                    'quarterly': float(plan.quarterly_price),
                    'yearly': float(plan.yearly_price),
                },
                'discounts': {
                    'quarterly': plan.get_discount_percentage('quarterly'),
                    'yearly': plan.get_discount_percentage('yearly'),
                },
                'features': plan.features,
                'limits': {
                    'max_users': plan.max_users,
                    'max_reports': plan.max_reports,
                    'max_storage_gb': plan.max_storage_gb,
                },
                'trial_days': plan.trial_days,
                'is_featured': plan.is_featured,
                'order': plan.order,
            })
        
        return JsonResponse({
            'success': True,
            'module': {
                'name': module.name,
                'display_name': module.display_name,
                'description': module.description,
                'icon': module.icon,
                'color': module.color,
            },
            'plans': plans_data
        })
        
    except Exception as e:
        logger.error(f"Error getting available plans: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)
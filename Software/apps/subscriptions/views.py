"""
Vistas para el sistema de suscripciones y carrito de compras
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
import json
import logging
import hashlib

from .models import (
    Module, Plan, PlanType, Cart, CartItem, Order, OrderItem, 
    WompiTransaction, Subscription, WebhookEvent
)
from .services import CartService, WompiService, SubscriptionService
from .forms import CheckoutForm, BillingForm

logger = logging.getLogger(__name__)


def get_user_cart(request):
    """Helper para obtener el carrito del usuario asegurando que existe session_key"""
    # Asegurar que la sesión existe
    if not request.session.session_key:
        request.session.create()
        
    return CartService.get_or_create_cart(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key,
        request=request
    )


def plans_overview(request):
    """Vista general de todos los planes disponibles"""
    # Obtener todos los módulos activos incluyendo demo
    modules = Module.objects.filter(
        is_active=True
    ).prefetch_related(
        'plans__plan_type'
    ).order_by('order')
    
    # Añadir contador de planes no-demo y planes para comparación a cada módulo
    for module in modules:
        module.non_demo_plans_count = module.plans.exclude(plan_type__name='Demo').count()
        # Para la tabla de comparación: incluir Demo solo en HOTELES
        if module.name == 'risk_hoteles':
            module.comparison_plans = module.plans.filter(is_active=True)
        else:
            module.comparison_plans = module.plans.exclude(plan_type__name='Demo').filter(is_active=True)
        # Para la grilla de planes: incluir todos los planes activos (incluyendo Demo)
        module.grid_plans = module.plans.filter(is_active=True).order_by('order', 'monthly_price')
    
    # Obtener planes demo de los módulos principales para la pestaña demo
    demo_plans = Plan.objects.filter(
        plan_type__name='Demo',
        module__name__in=['risk_conjuntos', 'risk_hoteles', 'security_probabilistic']
    ).select_related('module', 'plan_type')
    
    context = {
        'modules': modules,
        'demo_plans': demo_plans,
        'page_title': 'Planes de Suscripción'
    }
    return render(request, 'subscriptions/plans_overview.html', context)


def plans_list(request):
    """Lista completa de planes organizados por módulo"""
    modules = Module.objects.filter(is_active=True).prefetch_related(
        'plans__plan_type'
    ).order_by('order')
    
    plan_types = PlanType.objects.filter(is_active=True).order_by('order')
    
    context = {
        'modules': modules,
        'plan_types': plan_types,
        'page_title': 'Todos los Planes'
    }
    return render(request, 'subscriptions/plans_overview.html', context)


@login_required
def select_initial_plan(request):
    """
    Vista para seleccionar el plan inicial después del registro.
    Muestra los planes gratuitos disponibles por módulo.
    """
    # Verificar si el usuario ya tiene alguna suscripción activa
    has_active_subscription = Subscription.objects.filter(
        user=request.user,
        status='active'
    ).exists()
    
    if has_active_subscription:
        # Si ya tiene suscripción, redirigir al dashboard
        messages.info(request, 'Ya tienes un plan activo.')
        return redirect('dashboard:dashboard')
    
    # Obtener módulos activos con todos sus planes
    modules = Module.objects.filter(is_active=True).exclude(name='demo').prefetch_related(
        'plans__plan_type'
    ).order_by('order')
    
    # Obtener todos los planes activos ordenados
    for module in modules:
        module.all_plans = module.plans.filter(is_active=True).order_by('order')
        module.demo_plan = module.plans.filter(plan_type__name='Demo', is_active=True).first()
    
    # Información del plan demo global (el mismo que se crea con DemoService)
    demo_plan_info = {
        'name': 'Plan Demo Global',
        'description': 'Acceso básico a todas las funciones del sistema por 30 días',
        'price': 'Gratis',
        'duration': '30 días',
        'features': [
            'Acceso a todas las funciones básicas',
            'Hasta 3 reportes por mes',
            'Almacenamiento limitado a 500MB',
            'Soporte por email'
        ],
        'limitations': [
            'Funciones avanzadas limitadas',
            'Reportes con marca de agua',
            'Exportación solo en PDF'
        ]
    }
    
    context = {
        'modules': modules,
        'demo_plan_info': demo_plan_info,
        'page_title': 'Selecciona tu Módulo',
        'is_initial_selection': True,
        'user_email': request.user.email,
    }
    return render(request, 'subscriptions/select_initial_plan.html', context)


@login_required  
def activate_demo_plan(request):
    """
    Activa el plan demo gratuito para un usuario recién registrado
    """
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('subscriptions:select_initial_plan')
    
    # Verificar si ya tiene una suscripción activa
    if Subscription.objects.filter(user=request.user, status='active').exists():
        messages.info(request, 'Ya tienes un plan activo.')
        return redirect('dashboard:dashboard')
    
    try:
        from .demo_service import DemoService
        
        # Activar plan demo usando el servicio
        demo_subscription = DemoService.activate_demo_for_user(request.user)
        
        messages.success(
            request, 
            f'¡Perfecto! Has activado el Plan Demo. '
            f'Tienes 30 días para explorar el sistema. ¡Disfrútalo!'
        )
        
        logger.info(f"Plan demo activado para usuario {request.user.email}")
        
        # Redirigir al dashboard
        return redirect('dashboard:dashboard')
        
    except ValueError as ve:
        # Error de validación (ej: ya tiene suscripción)
        messages.info(request, str(ve))
        return redirect('dashboard:dashboard')
        
    except Exception as e:
        logger.error(f"Error activando plan demo para {request.user.email}: {e}")
        messages.error(
            request,
            'Hubo un error activando tu plan demo. Por favor, intenta nuevamente.'
        )
        return redirect('subscriptions:select_initial_plan')


@login_required
def activate_module_plan(request, module_name):
    """
    Activa el plan gratuito de un módulo específico
    """
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('subscriptions:select_initial_plan')
    
    # Verificar si ya tiene una suscripción activa
    if Subscription.objects.filter(user=request.user, status='active').exists():
        messages.info(request, 'Ya tienes un plan activo.')
        return redirect('dashboard:dashboard')
    
    try:
        # Obtener el módulo
        module = get_object_or_404(Module, name=module_name, is_active=True)
        
        # Obtener el tipo de plan desde el formulario (por defecto Demo)
        plan_type_name = request.POST.get('plan_type', 'Demo')
        
        # Obtener el plan específico del módulo
        plan = get_object_or_404(
            Plan, 
            module=module, 
            plan_type__name=plan_type_name,
            is_active=True
        )
        
        # Crear la suscripción
        from django.utils import timezone
        from datetime import timedelta
        
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            billing_cycle='yearly',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            status='active',
            is_trial=True,
            trial_end_date=timezone.now() + timedelta(days=30)
        )
        
        messages.success(
            request,
            f'¡Perfecto! Has activado el plan gratuito de {module.display_name}. '
            f'Tienes 30 días para explorar todas sus funciones. ¡Disfrútalo!'
        )
        
        logger.info(f"Plan gratuito de {module_name} activado para usuario {request.user.email}")
        
        return redirect('dashboard:dashboard')
        
    except Exception as e:
        logger.error(f"Error activando plan de {module_name} para {request.user.email}: {e}")
        messages.error(
            request,
            f'Hubo un error activando el plan de {module_name}. Por favor, intenta nuevamente.'
        )
        return redirect('subscriptions:select_initial_plan')


def module_plans(request, module_name):
    """Planes específicos de un módulo - TEMPORALMENTE DESHABILITADO"""
    from django.http import Http404
    raise Http404("Esta página está temporalmente deshabilitada")
    
    # module = get_object_or_404(Module, name=module_name, is_active=True)
    # plans = module.plans.filter(is_active=True).select_related('plan_type').order_by('order', 'monthly_price')
    
    # # Verificar si el usuario ya tiene suscripción a este módulo
    # user_subscription = None
    # if request.user.is_authenticated:
    #     user_subscription = SubscriptionService.get_user_subscriptions(request.user, module_name).first()
    
    # context = {
    #     'module': module,
    #     'plans': plans,
    #     'user_subscription': user_subscription,
    #     'page_title': f'Planes - {module.display_name}'
    # }
    # return render(request, 'subscriptions/module_plans.html', context)


def cart_view(request):
    """Vista del carrito de compras"""
    cart = get_user_cart(request)
    
    context = {
        'cart': cart,
        'page_title': 'Carrito de Compras'
    }
    return render(request, 'subscriptions/cart.html', context)


@csrf_exempt
@require_POST
def add_to_cart(request):
    """Agregar plan al carrito (AJAX) - Con validaciones de negocio"""
    # Debug información
    logger.info(f"add_to_cart called - User: {request.user}, Authenticated: {request.user.is_authenticated}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"CSRF Token present: {'csrfmiddlewaretoken' in request.POST or 'HTTP_X_CSRFTOKEN' in request.META}")
    
    try:
        data = json.loads(request.body)
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'yearly')
        quantity = int(data.get('quantity', 1))
        
        logger.info(f"Attempting to add plan {plan_id} to cart")
        
        plan = get_object_or_404(Plan, id=plan_id, is_active=True)
        
        # Obtener o crear carrito
        cart = get_user_cart(request)
        
        # Intentar agregar al carrito con validaciones
        result = CartService.add_to_cart(cart, plan, billing_cycle, quantity)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'cart_count': cart.total_items,
                'cart_total': float(cart.total_amount),
                'replaced': result.get('replaced', False),
                'updated': result.get('updated', False),
                'added': result.get('added', False)
            })
        else:
            # Determinar el código de estado según el tipo de error
            status_code = 400  # Bad Request por defecto
            
            if result['error'] == 'demo_already_used':
                status_code = 403  # Forbidden - usuario ya usó el demo
            elif result['error'] == 'demo_with_paid_plan':
                status_code = 409  # Conflict - conflicto con plan existente
            elif result['error'] == 'system_error':
                status_code = 500  # Internal Server Error
                
            return JsonResponse({
                'success': False,
                'message': result['message'],
                'error_type': result['error']
            }, status=status_code)
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        logger.error(f"Request user: {request.user}")
        logger.error(f"Request method: {request.method}")
        logger.error(f"Request body: {request.body}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


@require_POST
def remove_from_cart(request):
    """Remover plan del carrito (AJAX)"""
    try:
        data = json.loads(request.body)
        
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            request=request
        )
        
        # Opción 1: Remover por ID de item (más directo y seguro)
        if 'item_id' in data:
            item_id = data.get('item_id')
            try:
                cart_item = CartItem.objects.get(id=item_id, cart=cart)
                cart_item.delete()
                success = True
                message = 'Item eliminado del carrito'
            except CartItem.DoesNotExist:
                success = False
                message = 'Item no encontrado en el carrito'
        
        # Opción 2: Remover por plan_id y billing_cycle (compatibilidad)
        else:
            plan_id = data.get('plan_id')
            billing_cycle = data.get('billing_cycle')
            plan = get_object_or_404(Plan, id=plan_id)
            
            success = CartService.remove_from_cart(cart, plan, billing_cycle)
            message = 'Plan removido del carrito' if success else 'Error al remover del carrito'
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_count': cart.total_items,
                'cart_total': float(cart.total_amount)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


@require_POST
@require_POST
def update_cart_item(request):
    """Actualizar cantidad de item en carrito (AJAX)"""
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        cart = CartService.get_or_create_cart(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            request=request
        )
        
        # Manejar por item_id (más directo) o por plan_id + billing_cycle
        if 'item_id' in data:
            cart_item = get_object_or_404(CartItem, id=data['item_id'], cart=cart)
            if quantity <= 0:
                cart_item.delete()
                message = 'Item eliminado del carrito'
                item_subtotal = 0
            else:
                cart_item.quantity = quantity
                cart_item.save()
                message = 'Cantidad actualizada'
                item_subtotal = cart_item.subtotal
        else:
            # Método anterior por compatibilidad
            plan_id = data.get('plan_id')
            billing_cycle = data.get('billing_cycle')
            plan = get_object_or_404(Plan, id=plan_id)
            
            success = CartService.update_quantity(cart, plan, billing_cycle, quantity)
            if not success:
                return JsonResponse({
                    'success': False,
                    'message': 'Error al actualizar carrito'
                }, status=400)
            
            message = 'Carrito actualizado'
            item_subtotal = None

        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart.total_items,
            'cart_total': float(cart.total_amount),
            'item_subtotal': float(item_subtotal) if item_subtotal else None
        })
            
    except Exception as e:
        logger.error(f"Error updating cart: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


@require_POST
@login_required
def clear_cart(request):
    """Vaciar carrito (AJAX)"""
    try:
        cart = CartService.get_or_create_cart(
            user=request.user,
            session_key=request.session.session_key,
            request=request
        )
        
        CartService.clear_cart(cart)
        
        return JsonResponse({
            'success': True,
            'message': 'Carrito vaciado',
            'cart_count': 0,
            'cart_total': 0
        })
        
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


@login_required
def checkout_view(request):
    """Vista de checkout"""
    cart = CartService.get_or_create_cart(
        user=request.user,
        session_key=request.session.session_key,
        request=request
    )
    
    if not cart.items.exists():
        messages.warning(request, 'Tu carrito está vacío')
        return redirect('subscriptions:plans')
    
    # Pre-llenar formulario con datos del usuario
    initial_data = {
        'name': request.user.get_full_name(),
        'email': request.user.email,
        'phone': getattr(request.user, 'phone', ''),
        'city': getattr(request.user, 'city', ''),
        'country': 'Colombia'
    }
    
    form = BillingForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
        'page_title': 'Finalizar Compra'
    }
    return render(request, 'subscriptions/checkout.html', context)


@login_required
@require_POST
def confirm_order(request):
    """Confirmar orden y proceder al pago"""
    cart = CartService.get_or_create_cart(
        user=request.user,
        session_key=request.session.session_key,
        request=request
    )
    
    if not cart.items.exists():
        messages.warning(request, 'Tu carrito está vacío')
        return redirect('subscriptions:plans')
    
    form = BillingForm(request.POST)
    
    if form.is_valid():
        try:
            with transaction.atomic():
                # Crear orden desde el carrito
                order = CartService.create_order_from_cart(cart, form.cleaned_data)
                
                if order:
                    # Redirigir a página de pago
                    return redirect('subscriptions:payment', order_id=order.id)
                else:
                    messages.error(request, 'Error al crear la orden')
                    return redirect('subscriptions:checkout')
                    
        except Exception as e:
            logger.error(f"Error confirming order: {e}")
            messages.error(request, 'Error al procesar la orden')
            return redirect('subscriptions:checkout')
    else:
        # Formulario inválido, volver al checkout
        context = {
            'cart': cart,
            'form': form,
            'page_title': 'Finalizar Compra'
        }
        return render(request, 'subscriptions/checkout.html', context)


@login_required
def payment_view(request, order_id):
    """Vista de pago con Wompi"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status not in ['pending', 'processing']:
        messages.info(request, 'Esta orden ya ha sido procesada')
        return redirect('subscriptions:order_detail', order_id=order.id)
    
    # Inicializar servicio de Wompi
    wompi_service = WompiService()
    
    # Generar datos para el widget
    widget_data = wompi_service.generate_widget_data(order)
    
    context = {
        'order': order,
        'widget_data': widget_data,
        'page_title': f'Pagar Orden {order.order_number}'
    }
    return render(request, 'subscriptions/payment.html', context)


@login_required
def payment_result(request, order_id):
    """Resultado del pago"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Verificar si viene ID de transacción en la URL (retorno de Wompi)
    wompi_id = request.GET.get('id')
    if wompi_id:
        wompi_service = WompiService()
        wompi_service.sync_transaction(wompi_id)
    
    # Obtener última transacción
    latest_transaction = order.wompi_transactions.order_by('-created_at').first()
    
    context = {
        'order': order,
        'transaction': latest_transaction,
        'page_title': 'Resultado del Pago'
    }
    return render(request, 'subscriptions/payment_result.html', context)


@csrf_exempt
@require_POST
def wompi_webhook(request):
    """Webhook para recibir notificaciones de Wompi"""
    try:
        payload = request.body.decode('utf-8')
        signature = request.headers.get('X-Signature', '')
        
        # Verificar firma
        wompi_service = WompiService()
        if not wompi_service.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            return HttpResponse(status=400)
        
        # Procesar evento
        event_data = json.loads(payload)
        event_id = event_data.get('id')
        
        # Evitar procesamiento duplicado
        webhook_event, created = WebhookEvent.objects.get_or_create(
            wompi_event_id=event_id,
            defaults={
                'event_type': event_data.get('event'),
                'payload': event_data
            }
        )
        
        if created or not webhook_event.processed:
            success = wompi_service.process_webhook_event(event_data)
            
            webhook_event.processed = success
            if not success:
                webhook_event.processing_error = "Failed to process event"
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return HttpResponse(status=500)


@login_required
def my_subscriptions(request):
    """Página completa de gestión de suscripciones del usuario"""
    # Obtener todas las suscripciones del usuario
    subscriptions = SubscriptionService.get_user_subscriptions(request.user)
    
    # Organizar suscripciones por módulo
    subscriptions_by_module = {}
    usage_stats = {}
    
    for subscription in subscriptions:
        module_name = subscription.plan.module.name
        
        if module_name not in subscriptions_by_module:
            subscriptions_by_module[module_name] = {
                'module': subscription.plan.module,
                'subscription': subscription,
                'available_plans': subscription.plan.module.plans.filter(
                    is_active=True
                ).select_related('plan_type').order_by('order', 'monthly_price'),
                'usage': SubscriptionService.get_usage_limits(request.user, module_name)
            }
    
    # Obtener módulos sin suscripción (para mostrar planes disponibles)
    subscribed_modules = [sub.plan.module.id for sub in subscriptions]
    available_modules = Module.objects.filter(
        is_active=True
    ).exclude(
        id__in=subscribed_modules
    ).prefetch_related('plans__plan_type')
    
    # Estadísticas generales del usuario
    total_subscriptions = subscriptions.count()
    active_subscriptions = subscriptions.filter(status='active').count()
    expiring_soon = subscriptions.filter(
        status='active',
        end_date__lte=timezone.now() + timezone.timedelta(days=30)
    ).count()
    
    # Próximas renovaciones
    upcoming_renewals = subscriptions.filter(
        status='active',
        next_billing_date__isnull=False,
        next_billing_date__lte=timezone.now() + timezone.timedelta(days=7)
    ).order_by('next_billing_date')
    
    context = {
        'subscriptions_by_module': subscriptions_by_module,
        'available_modules': available_modules,
        'stats': {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'expiring_soon': expiring_soon,
        },
        'upcoming_renewals': upcoming_renewals,
        'page_title': 'Gestión de Suscripciones'
    }
    return render(request, 'subscriptions/my_subscriptions.html', context)


@login_required
def my_subscriptions_test(request):
    """Vista de prueba simple para gestión de suscripciones"""
    # Obtener todas las suscripciones del usuario
    subscriptions = SubscriptionService.get_user_subscriptions(request.user)
    
    # Organizar suscripciones por módulo
    subscriptions_by_module = {}
    
    for subscription in subscriptions:
        module_name = subscription.plan.module.name
        
        if module_name not in subscriptions_by_module:
            subscriptions_by_module[module_name] = {
                'module': subscription.plan.module,
                'subscription': subscription,
                'available_plans': subscription.plan.module.plans.filter(
                    is_active=True
                ).select_related('plan_type').order_by('order', 'monthly_price'),
                'usage': SubscriptionService.get_usage_limits(request.user, module_name)
            }
    
    # Obtener módulos sin suscripción
    subscribed_modules = [sub.plan.module.id for sub in subscriptions]
    available_modules = Module.objects.filter(
        is_active=True
    ).exclude(
        id__in=subscribed_modules
    )
    
    context = {
        'subscriptions_by_module': subscriptions_by_module,
        'available_modules': available_modules,
        'subscriptions_count': subscriptions.count(),
        'page_title': 'Test - Gestión de Suscripciones'
    }
    return render(request, 'subscriptions/my_subscriptions_test.html', context)


@login_required
def subscription_detail(request, subscription_id):
    """Detalle de una suscripción"""
    subscription = get_object_or_404(
        Subscription, 
        id=subscription_id, 
        user=request.user
    )
    
    # Obtener estadísticas de uso
    usage_stats = SubscriptionService.get_usage_limits(
        request.user, 
        subscription.plan.module.name
    )
    
    context = {
        'subscription': subscription,
        'usage_stats': usage_stats,
        'page_title': f'Suscripción - {subscription.plan}'
    }
    return render(request, 'subscriptions/subscription_detail.html', context)


@login_required
def upgrade_plan(request, module_name):
    """Vista para actualizar plan de un módulo"""
    module = get_object_or_404(Module, name=module_name, is_active=True)
    current_subscription = SubscriptionService.get_user_subscriptions(request.user, module_name).first()
    
    # Obtener planes disponibles para upgrade
    available_plans = module.plans.filter(is_active=True).select_related('plan_type').order_by('order', 'monthly_price')
    
    context = {
        'module': module,
        'current_subscription': current_subscription,
        'available_plans': available_plans,
        'page_title': f'Actualizar Plan - {module.display_name}'
    }
    return render(request, 'subscriptions/upgrade_plan.html', context)


@login_required
@require_POST
def cancel_subscription(request, subscription_id):
    """Cancelar suscripción"""
    subscription = get_object_or_404(
        Subscription, 
        id=subscription_id, 
        user=request.user,
        status='active'
    )
    
    try:
        subscription.status = 'cancelled'
        subscription.save()
        
        messages.success(request, f'Suscripción a {subscription.plan} cancelada exitosamente')
        
        # Si es AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Suscripción cancelada exitosamente'
            })
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        messages.error(request, 'Error al cancelar la suscripción')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error al cancelar la suscripción'
            }, status=500)
    
    return redirect('subscriptions:my_subscriptions')


@login_required
def my_orders(request):
    """Órdenes del usuario"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
        'page_title': 'Mis Órdenes'
    }
    return render(request, 'subscriptions/my_orders.html', context)


@login_required
def order_detail(request, order_id):
    """Detalle de una orden"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        'page_title': f'Orden {order.order_number}'
    }
    return render(request, 'subscriptions/order_detail.html', context)


@login_required
def change_plan(request, subscription_id, new_plan_id):
    """Cambiar plan de una suscripción existente"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    new_plan = get_object_or_404(Plan, id=new_plan_id, is_active=True)
    
    # Verificar que el nuevo plan sea del mismo módulo
    if subscription.plan.module != new_plan.module:
        messages.error(request, 'No se puede cambiar a un plan de otro módulo.')
        return redirect('subscriptions:my_subscriptions')
    
    # Verificar que sea un cambio real
    if subscription.plan == new_plan:
        messages.info(request, 'Ya tienes este plan activo.')
        return redirect('subscriptions:my_subscriptions')
    
    if request.method == 'POST':
        try:
            # Calcular diferencia de precio prorrateada si es upgrade
            old_price = subscription.plan.monthly_price
            new_price = new_plan.monthly_price
            
            if new_price > old_price:
                # Es un upgrade - calcular precio prorrateado
                from datetime import datetime
                from django.utils import timezone
                
                today = timezone.now().date()
                days_remaining = (subscription.end_date - today).days
                daily_old_price = old_price / 30
                daily_new_price = new_price / 30
                
                # Precio a pagar por los días restantes
                prorated_amount = (daily_new_price - daily_old_price) * days_remaining
                
                if prorated_amount > 0:
                    # Crear orden para el upgrade
                    cart = CartService.get_or_create_cart(request.user, request=request)
                    CartService.clear_cart(cart)
                    
                    # Agregar item especial de upgrade
                    cart_item, created = CartItem.objects.get_or_create(
                        cart=cart,
                        plan=new_plan,
                        defaults={
                            'quantity': 1,
                            'price': prorated_amount,
                            'billing_period': 'upgrade'
                        }
                    )
                    
                    # Redirigir al checkout
                    return redirect('subscriptions:checkout')
            
            # Cambio directo (downgrade o cambio lateral)
            subscription.plan = new_plan
            subscription.save()
            
            messages.success(
                request, 
                f'Plan cambiado exitosamente a {new_plan.plan_type.name}. '
                f'Los cambios serán efectivos inmediatamente.'
            )
            
        except Exception as e:
            messages.error(request, f'Error al cambiar el plan: {str(e)}')
    
    return redirect('subscriptions:my_subscriptions')


@login_required  
def upgrade_plan(request, module_name):
    """Vista para actualizar plan de un módulo"""
    module = get_object_or_404(Module, name=module_name, is_active=True)
    user_subscription = SubscriptionService.get_user_subscriptions(request.user, module_name).first()
    
    if not user_subscription:
        messages.error(request, 'No tienes una suscripción activa para este módulo.')
        return redirect('subscriptions:demo_info', module_name=module_name)
    
    # Obtener planes superiores
    available_plans = module.plans.filter(
        is_active=True,
        monthly_price__gt=user_subscription.plan.monthly_price
    ).order_by('monthly_price')
    
    context = {
        'module': module,
        'current_subscription': user_subscription,
        'available_plans': available_plans,
        'page_title': f'Actualizar Plan - {module.display_name}'
    }
    
    return render(request, 'subscriptions/upgrade_plan.html', context)


@login_required
@require_http_methods(["GET"])
def get_subscription_usage(request, subscription_id):
    """API endpoint para obtener el uso actual de una suscripción"""
    subscription = get_object_or_404(
        Subscription, 
        id=subscription_id, 
        user=request.user
    )
    
    usage_stats = SubscriptionService.get_usage_limits(
        request.user, 
        subscription.plan.module.name
    )
    
    return JsonResponse({
        'success': True,
        'usage': usage_stats,
        'subscription': {
            'id': str(subscription.id),
            'plan_name': subscription.plan.name,
            'status': subscription.status,
            'days_remaining': subscription.days_remaining(),
            'is_trial': subscription.is_trial
        }
    })


@login_required
@require_http_methods(["GET"])
def get_upgrade_options(request, module_name):
    """API endpoint para obtener opciones de upgrade para un módulo"""
    module = get_object_or_404(Module, name=module_name, is_active=True)
    user_subscription = SubscriptionService.get_user_subscriptions(request.user, module_name).first()
    
    if not user_subscription:
        return JsonResponse({
            'success': False,
            'message': 'No tienes una suscripción activa para este módulo'
        }, status=404)
    
    # Obtener planes disponibles (tanto upgrade como downgrade)
    all_plans = module.plans.filter(is_active=True).exclude(
        id=user_subscription.plan.id
    ).select_related('plan_type').order_by('monthly_price')
    
    plans_data = []
    for plan in all_plans:
        # Calcular si es upgrade o downgrade
        is_upgrade = plan.monthly_price > user_subscription.plan.monthly_price
        price_difference = abs(plan.monthly_price - user_subscription.plan.monthly_price)
        
        plans_data.append({
            'id': plan.id,
            'name': plan.name,
            'plan_type': plan.plan_type.name,
            'monthly_price': float(plan.monthly_price),
            'yearly_price': float(plan.yearly_price),
            'is_upgrade': is_upgrade,
            'price_difference': float(price_difference),
            'features': plan.features or {},
            'max_users': plan.max_users,
            'max_reports': plan.max_reports,
            'max_storage_gb': plan.max_storage_gb,
            'yearly_discount': plan.yearly_discount_percentage
        })
    
    return JsonResponse({
        'success': True,
        'current_plan': {
            'id': user_subscription.plan.id,
            'name': user_subscription.plan.name,
            'monthly_price': float(user_subscription.plan.monthly_price)
        },
        'available_plans': plans_data
    })


@login_required
@require_POST
def quick_upgrade_subscription(request, subscription_id):
    """Upgrade rápido de suscripción via AJAX"""
    subscription = get_object_or_404(
        Subscription, 
        id=subscription_id, 
        user=request.user,
        status='active'
    )
    
    try:
        data = json.loads(request.body)
        new_plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        new_plan = get_object_or_404(Plan, id=new_plan_id, is_active=True)
        
        # Verificar que sea del mismo módulo
        if subscription.plan.module != new_plan.module:
            return JsonResponse({
                'success': False,
                'message': 'No se puede cambiar a un plan de otro módulo'
            }, status=400)
        
        # Si es el mismo plan, no hacer nada
        if subscription.plan == new_plan:
            return JsonResponse({
                'success': False,
                'message': 'Ya tienes este plan activo'
            }, status=400)
        
        old_price = subscription.plan.get_price(billing_cycle)
        new_price = new_plan.get_price(billing_cycle)
        
        if new_price > old_price:
            # Es un upgrade - requiere pago
            days_remaining = subscription.days_remaining()
            if days_remaining > 0:
                daily_old = old_price / 30
                daily_new = new_price / 30
                prorated_amount = (daily_new - daily_old) * days_remaining
                
                return JsonResponse({
                    'success': True,
                    'requires_payment': True,
                    'prorated_amount': float(prorated_amount),
                    'message': f'Upgrade requiere pago prorrateado de ${prorated_amount:,.2f}',
                    'checkout_url': reverse('subscriptions:checkout')
                })
        
        # Cambio directo (downgrade o lateral)
        subscription.plan = new_plan
        subscription.billing_cycle = billing_cycle
        subscription.save()
        
        return JsonResponse({
            'success': True,
            'requires_payment': False,
            'message': f'Plan cambiado exitosamente a {new_plan.name}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in quick upgrade: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor'
        }, status=500)


# ===================== ENHANCED CART VIEWS FOR PWA =====================


@login_required
@require_http_methods(["GET"])
def cart_status(request):
    """
    API endpoint para verificar el estado del carrito
    Usado por WebSocket polling fallback y PWA sync
    """
    try:
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        
        if not cart:
            return JsonResponse({
                'success': True,
                'updated': False,
                'cart': {
                    'total_items': 0,
                    'total_amount': 0,
                    'items': []
                }
            })
        
        # Generate cart hash for change detection
        cart_data = {
            'total_items': cart.total_items,
            'total_amount': float(cart.total_amount),
            'items': [
                {
                    'id': str(item.id),
                    'plan_name': item.plan.name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'subtotal': float(item.subtotal)
                }
                for item in cart.items.all()
            ]
        }
        
        # Check if cart has been updated since last check
        cart_hash = hashlib.md5(
            json.dumps(cart_data, sort_keys=True).encode()
        ).hexdigest()
        
        last_hash = cache.get(f'cart_hash_{request.user.id}')
        updated = last_hash != cart_hash
        
        if updated:
            cache.set(f'cart_hash_{request.user.id}', cart_hash, 300)  # 5 min cache
        
        return JsonResponse({
            'success': True,
            'updated': updated,
            'cart': cart_data,
            'hash': cart_hash,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in cart_status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def sync_offline_actions(request):
    """
    Sincronizar acciones realizadas offline
    Usado por Service Worker background sync
    """
    try:
        data = json.loads(request.body)
        actions = data.get('actions', [])
        
        if not actions:
            return JsonResponse({
                'success': True,
                'message': 'No hay acciones para sincronizar',
                'synced_count': 0
            })
        
        synced_count = 0
        failed_actions = []
        
        with transaction.atomic():
            for action in actions:
                try:
                    action_type = action.get('action')
                    action_data = action.get('data', {})
                    
                    if action_type == 'update_item':
                        item_id = action_data.get('itemId')
                        quantity = action_data.get('quantity')
                        
                        cart_item = CartItem.objects.get(
                            id=item_id,
                            cart__user=request.user,
                            cart__is_active=True
                        )
                        cart_item.quantity = quantity
                        cart_item.save()
                        
                    elif action_type == 'remove_item':
                        plan_id = action_data.get('planId')
                        billing_cycle = action_data.get('billingCycle')
                        
                        CartItem.objects.filter(
                            cart__user=request.user,
                            cart__is_active=True,
                            plan_id=plan_id,
                            billing_cycle=billing_cycle
                        ).delete()
                        
                    elif action_type == 'clear_cart':
                        Cart.objects.filter(
                            user=request.user,
                            is_active=True
                        ).delete()
                    
                    synced_count += 1
                    
                except Exception as e:
                    failed_actions.append({
                        'action': action,
                        'error': str(e)
                    })
        
        return JsonResponse({
            'success': True,
            'message': f'{synced_count} acciones sincronizadas',
            'synced_count': synced_count,
            'failed_count': len(failed_actions),
            'failed_actions': failed_actions[:5]  # Limit error details
        })
        
    except Exception as e:
        logger.error(f"Error in sync_offline_actions: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error en sincronización: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def backup_cart_data(request):
    """
    Crear backup del carrito en el servidor
    Para recuperación cross-device
    """
    try:
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        
        if not cart:
            return JsonResponse({
                'success': True,
                'backup': None,
                'message': 'No hay carrito activo para respaldar'
            })
        
        backup_data = {
            'user_id': request.user.id,
            'cart_id': str(cart.id),
            'items': [
                {
                    'plan_id': item.plan.id,
                    'billing_cycle': item.billing_cycle,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price)
                }
                for item in cart.items.all()
            ],
            'timestamp': timezone.now().isoformat(),
            'device_info': {
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': request.META.get('REMOTE_ADDR', '')
            }
        }
        
        # Store backup in cache with 7-day expiry
        backup_key = f'cart_backup_{request.user.id}'
        cache.set(backup_key, backup_data, 604800)  # 7 days
        
        return JsonResponse({
            'success': True,
            'backup': {
                'items_count': len(backup_data['items']),
                'timestamp': backup_data['timestamp']
            },
            'message': 'Carrito respaldado exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error in backup_cart_data: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error al respaldar carrito: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def restore_cart_data(request):
    """
    Restaurar carrito desde backup
    Para recuperación cross-device
    """
    try:
        backup_key = f'cart_backup_{request.user.id}'
        backup_data = cache.get(backup_key)
        
        if not backup_data:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró backup del carrito'
            }, status=404)
        
        # Check if backup is recent (within 7 days)
        backup_time = datetime.fromisoformat(backup_data['timestamp'].replace('Z', '+00:00'))
        if (timezone.now() - backup_time).days > 7:
            return JsonResponse({
                'success': False,
                'error': 'El backup es demasiado antiguo'
            }, status=400)
        
        # Clear existing cart
        Cart.objects.filter(user=request.user, is_active=True).delete()
        
        # Restore items
        with transaction.atomic():
            cart = Cart.objects.create(user=request.user, is_active=True)
            
            restored_items = []
            for item_data in backup_data['items']:
                try:
                    plan = Plan.objects.get(id=item_data['plan_id'])
                    
                    cart_item = CartItem.objects.create(
                        cart=cart,
                        plan=plan,
                        billing_cycle=item_data['billing_cycle'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price']
                    )
                    
                    restored_items.append({
                        'plan_name': plan.name,
                        'quantity': cart_item.quantity
                    })
                    
                except Plan.DoesNotExist:
                    continue  # Skip items with deleted plans
        
        return JsonResponse({
            'success': True,
            'message': f'Carrito restaurado con {len(restored_items)} items',
            'restored_items': restored_items,
            'backup_date': backup_data['timestamp']
        })
        
    except Exception as e:
        logger.error(f"Error in restore_cart_data: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error al restaurar carrito: {str(e)}'
        }, status=500)
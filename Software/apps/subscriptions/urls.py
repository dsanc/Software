from django.urls import path, include
from . import views
from . import api_views
from . import demo_views

app_name = 'subscriptions'

urlpatterns = [
    # Páginas principales
    path('', views.plans_overview, name='plans'),
    path('plans/', views.plans_list, name='plans_list'),
    # path('plans/<str:module_name>/', views.module_plans, name='module_plans'),  # TEMPORALMENTE DESHABILITADO
    
    # Selección inicial de plan (post-registro)
    path('select-initial-plan/', views.select_initial_plan, name='select_initial_plan'),
    path('activate-demo-plan/', views.activate_demo_plan, name='activate_demo_plan'),
    path('activate-module-plan/<str:module_name>/', views.activate_module_plan, name='activate_module_plan'),
    
    # Carrito de compras
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Proceso de compra
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/confirm/', views.confirm_order, name='confirm_order'),
    
    # Pagos con Wompi
    path('payment/<uuid:order_id>/', views.payment_view, name='payment'),
    path('payment/<uuid:order_id>/result/', views.payment_result, name='payment_result'),
    path('payment/webhook/', views.wompi_webhook, name='wompi_webhook'),
    
    # Gestión de suscripciones
    path('my-subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    # path('my-subscriptions-test/', views.my_subscriptions_test, name='my_subscriptions_test'),
    path('subscription/<uuid:subscription_id>/', views.subscription_detail, name='subscription_detail'),
    path('upgrade/<str:module_name>/', views.upgrade_plan, name='upgrade'),
    path('change-plan/<uuid:subscription_id>/<int:new_plan_id>/', views.change_plan, name='change_plan'),
    path('cancel/<uuid:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
    
    # APIs AJAX para gestión dinámica
    path('api/subscription/<uuid:subscription_id>/usage/', views.get_subscription_usage, name='api_subscription_usage'),
    path('api/module/<str:module_name>/upgrade-options/', views.get_upgrade_options, name='api_upgrade_options'),
    path('api/subscription/<uuid:subscription_id>/quick-upgrade/', views.quick_upgrade_subscription, name='api_quick_upgrade'),
    
    # Órdenes
    path('orders/', views.my_orders, name='my_orders'),
    path('order/<uuid:order_id>/', views.order_detail, name='order_detail'),
    
    # Gestión de DEMO
    path('demo/<str:module_name>/', demo_views.demo_info, name='demo_info'),
    path('demo/<str:module_name>/start/', demo_views.start_demo, name='start_demo'),
    path('access-denied/', demo_views.access_denied, name='access_denied'),
    
    # APIs AJAX
    path('api/', include([
        path('cart/count/', api_views.cart_count, name='api_cart_count'),
        path('cart/summary/', api_views.cart_summary, name='api_cart_summary'),
        
        # Enhanced cart APIs for PWA functionality
        path('cart/status/', views.cart_status, name='cart_status'),
        path('cart/sync/', views.sync_offline_actions, name='sync_offline_actions'),
        path('cart/backup/', views.backup_cart_data, name='backup_cart_data'),
        path('cart/restore/', views.restore_cart_data, name='restore_cart_data'),
        
        path('usage-stats/<str:module_name>/', api_views.usage_stats, name='api_usage_stats'),
        path('subscription-status/<str:module_name>/', api_views.subscription_status, name='api_subscription_status'),
        path('available-plans/<str:module_name>/', api_views.available_plans, name='api_available_plans'),
        path('demo-status/<str:module_name>/', demo_views.demo_status_api, name='api_demo_status'),
    ])),
]
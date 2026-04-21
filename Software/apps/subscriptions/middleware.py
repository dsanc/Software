"""
Middleware para verificar que los usuarios tengan un plan activo
"""
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib.auth.decorators import login_required
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from apps.subscriptions.models import Subscription
import logging

logger = logging.getLogger(__name__)


class SubscriptionRequiredMiddleware(MiddlewareMixin):
    """
    Middleware que verifica si el usuario autenticado tiene una suscripción activa.
    Si no la tiene, lo redirige a la selección de plan inicial.
    """
    
    # URLs que NO requieren verificación de suscripción
    EXEMPT_URLS = [
        # Auth y registro
        'users:login',
        'users:logout', 
        'users:register',
        'users:password_reset',
        'users:password_reset_done',
        'users:password_reset_confirm',
        'users:password_reset_complete',
        'users:2fa_verify',
        'users:2fa_setup',
        
        # Suscripciones (para permitir selección y compra)
        'subscriptions:plans',
        'subscriptions:plans_list',
        'subscriptions:select_initial_plan',
        'subscriptions:activate_demo_plan',
        'subscriptions:cart',
        'subscriptions:add_to_cart',
        'subscriptions:checkout',
        'subscriptions:payment',
        'subscriptions:payment_result',
        'subscriptions:wompi_webhook',
        'subscriptions:demo_info',
        'subscriptions:start_demo',
        'subscriptions:access_denied',
        
        # APIs necesarias para el proceso
        'subscriptions:api_cart_count',
        'subscriptions:api_cart_summary',
        'subscriptions:api_demo_status',
        
        # AJAX endpoints de usuarios
        'users:password_strength_check',
        'users:change_password_ajax',
        
        # Admin (para superusuarios)
        'admin:index',
        
        # Home pública
        'dashboard:home',
        
        # Static files y media
        'static',
        'media',
    ]
    
    # Patrones de URL que están exentos
    EXEMPT_URL_PATTERNS = [
        '/admin/',
        '/static/',
        '/media/',
        '/__debug__/',  # Django Debug Toolbar
        '/favicon.ico',
    ]
    
    def process_request(self, request):
        """
        Procesa la petición antes de que llegue a la vista
        """
        # Skip si no es un usuario autenticado
        if not request.user.is_authenticated:
            return None
        
        # Skip para superusuarios
        if request.user.is_superuser:
            return None
        
        # Skip para URLs exentas por patrón
        path = request.path
        for pattern in self.EXEMPT_URL_PATTERNS:
            if path.startswith(pattern):
                return None
        
        # Obtener el nombre de la URL actual
        try:
            url_name = resolve(request.path_info).url_name
            namespace = resolve(request.path_info).namespace
            
            # Crear el nombre completo de la URL
            full_url_name = f"{namespace}:{url_name}" if namespace else url_name
            
        except Exception as e:
            logger.debug(f"No se pudo resolver la URL: {request.path_info} - {e}")
            return None
        
        # Skip si la URL está en la lista de exentas
        if full_url_name in self.EXEMPT_URLS:
            return None
        
        # Verificar si el usuario tiene una suscripción activa
        has_active_subscription = self._user_has_active_subscription(request.user)
        
        if not has_active_subscription:
            # Usuario no tiene suscripción activa, redirigir a selección de plan
            try:
                messages.warning(
                    request, 
                    'Necesitas seleccionar un plan para acceder al sistema.'
                )
            except Exception as e:
                # En entornos de testing o sin MessageMiddleware
                logger.warning(f"No se pudo mostrar mensaje de warning: {e}")
            
            return redirect('subscriptions:select_initial_plan')
        
        return None
    
    def _user_has_active_subscription(self, user):
        """
        Verifica si el usuario tiene al menos una suscripción activa
        """
        try:
            # Buscar cualquier suscripción activa del usuario
            active_subscriptions = Subscription.objects.filter(
                user=user,
                status='active'
            ).filter(
                # Verificar que esté dentro del período de validez
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
            
            return active_subscriptions.exists()
            
        except Exception as e:
            logger.error(f"Error verificando suscripciones para {user.email}: {e}")
            return False


# Importar timezone después del resto de importaciones para evitar circular imports
from django.utils import timezone
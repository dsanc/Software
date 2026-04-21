"""
Servicio de notificaciones para carritos abandonados
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Cart

logger = logging.getLogger(__name__)


class CartNotificationService:
    """Servicio para enviar notificaciones de carrito abandonado"""
    
    def send_abandonment_notification(self, cart_id):
        """Envía notificación de carrito abandonado - método de compatibilidad"""
        try:
            cart = Cart.objects.get(id=cart_id)
            return self.send_cart_abandonment_email(cart)
        except Cart.DoesNotExist:
            logger.error(f"Cart {cart_id} not found")
            return False
    
    def send_expiry_warning(self, cart_id):
        """Envía advertencia de expiración de carrito"""
        try:
            cart = Cart.objects.get(id=cart_id)
            return self.send_cart_expiry_warning(cart)
        except Cart.DoesNotExist:
            logger.error(f"Cart {cart_id} not found")
            return False
    
    @staticmethod
    def send_cart_abandonment_email(cart):
        """Envía email de carrito abandonado"""
        if not cart.user or not cart.user.email:
            logger.warning(f"Cannot send email for cart {cart.id}: no user email")
            return False
        
        if not cart.items.exists():
            logger.info(f"Not sending email for empty cart {cart.id}")
            return False
        
        try:
            # Datos para el template
            context = {
                'user': cart.user,
                'cart': cart,
                'items': cart.items.select_related('plan__module', 'plan__plan_type').all(),
                'total_amount': cart.total_amount,
                'cart_url': f"{settings.SITE_URL}/subscriptions/cart/",
                'expiry_hours': int((cart.expires_at - timezone.now()).total_seconds() / 3600) if cart.expires_at else 24
            }
            
            # Renderizar templates
            subject = f"¡Tu carrito expira pronto! - {cart.items.count()} plan(es) esperándote"
            
            html_message = render_to_string(
                'subscriptions/emails/cart_abandonment.html',
                context
            )
            
            text_message = render_to_string(
                'subscriptions/emails/cart_abandonment.txt',
                context
            )
            
            # Enviar email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[cart.user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Cart abandonment email sent to {cart.user.email} for cart {cart.id}")
            return True
                
        except Exception as e:
            logger.error(f"Error sending cart abandonment email for cart {cart.id}: {e}")
            return False
    
    @staticmethod
    def send_cart_expiry_warning(cart, hours_before=24):
        """Envía email de advertencia de expiración de carrito"""
        if not cart.user or not cart.user.email:
            logger.warning(f"Cannot send expiry warning for cart {cart.id}: no user email")
            return False
        
        if not cart.items.exists():
            logger.info(f"Not sending expiry warning for empty cart {cart.id}")
            return False
        
        if not cart.expires_at:
            logger.warning(f"Cannot send expiry warning for cart {cart.id}: no expiry date")
            return False
        
        try:
            # Calcular horas restantes
            time_remaining = cart.expires_at - timezone.now()
            hours_remaining = int(time_remaining.total_seconds() / 3600)
            
            # Datos para el template
            context = {
                'user': cart.user,
                'cart': cart,
                'items': cart.items.select_related('plan__module', 'plan__plan_type').all(),
                'total_amount': cart.total_amount,
                'cart_url': f"{settings.SITE_URL}/subscriptions/cart/",
                'checkout_url': f"{settings.SITE_URL}/subscriptions/checkout/",
                'hours_remaining': max(1, hours_remaining)  # Al menos 1 hora
            }
            
            # Renderizar templates
            subject = f"⏰ Tu carrito expira en {hours_remaining} horas - No pierdas tus planes"
            
            html_message = render_to_string(
                'subscriptions/emails/cart_expiry_warning.html',
                context
            )
            
            text_message = render_to_string(
                'subscriptions/emails/cart_expiry_warning.txt',
                context
            )
            
            # Enviar email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[cart.user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Cart expiry warning sent to {cart.user.email} for cart {cart.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending cart expiry warning for cart {cart.id}: {e}")
            return False
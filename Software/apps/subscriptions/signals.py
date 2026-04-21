"""
Señales para el sistema de suscripciones
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Order, Subscription, WompiTransaction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    """
    Se ejecuta cuando se crea una nueva orden
    """
    if created:
        logger.info(f"Nueva orden creada: {instance.order_number} por {instance.user.email}")
        
        # Aquí podrías enviar email de confirmación de orden
        # send_order_confirmation_email(instance)


@receiver(post_save, sender=WompiTransaction)
def transaction_status_changed(sender, instance, created, **kwargs):
    """
    Se ejecuta cuando cambia el estado de una transacción Wompi
    """
    if not created:  # Solo para actualizaciones
        if instance.wompi_status == 'APPROVED':
            logger.info(f"Transacción aprobada: {instance.wompi_transaction_id}")
            
            # Marcar orden como pagada
            instance.order.status = 'paid'
            instance.order.completed_at = timezone.now()
            instance.order.save()
            
            # Crear suscripciones automáticamente
            create_subscriptions_from_paid_order(instance.order)
            
        elif instance.wompi_status == 'DECLINED':
            logger.info(f"Transacción rechazada: {instance.wompi_transaction_id}")
            
            # Marcar orden como fallida
            instance.order.status = 'failed'
            instance.order.save()


@receiver(post_save, sender=Subscription)
def subscription_created(sender, instance, created, **kwargs):
    """
    Se ejecuta cuando se crea una nueva suscripción
    """
    if created:
        logger.info(f"Nueva suscripción creada: {instance.user.email} - {instance.plan}")
        
        # Enviar email de bienvenida
        send_welcome_email(instance)
        
        # Programar recordatorios de renovación
        # schedule_renewal_reminders(instance)


@receiver(pre_save, sender=Subscription)
def subscription_status_changing(sender, instance, **kwargs):
    """
    Se ejecuta antes de guardar una suscripción (para detectar cambios de estado)
    """
    if instance.pk:
        try:
            old_instance = Subscription.objects.get(pk=instance.pk)
            
            # Detectar cambio de estado
            if old_instance.status != instance.status:
                logger.info(f"Suscripción {instance.id} cambió de {old_instance.status} a {instance.status}")
                
                if instance.status == 'cancelled':
                    # Suscripción cancelada
                    handle_subscription_cancelled(instance)
                    
                elif instance.status == 'expired':
                    # Suscripción expirada
                    handle_subscription_expired(instance)
                    
                elif instance.status == 'active' and old_instance.status != 'active':
                    # Suscripción activada
                    handle_subscription_activated(instance)
                    
        except Subscription.DoesNotExist:
            pass  # Nueva suscripción


def create_subscriptions_from_paid_order(order):
    """
    Crea suscripciones a partir de una orden pagada
    """
    try:
        for item in order.items.all():
            # Calcular fechas según el ciclo de facturación
            start_date = timezone.now()
            
            if item.billing_cycle == 'monthly':
                end_date = start_date + timedelta(days=30)
            elif item.billing_cycle == 'quarterly':
                end_date = start_date + timedelta(days=90)
            elif item.billing_cycle == 'yearly':
                end_date = start_date + timedelta(days=365)
            else:
                end_date = start_date + timedelta(days=30)  # Default mensual
            
            # Verificar si ya existe una suscripción para este plan
            existing_subscription = Subscription.objects.filter(
                user=order.user,
                plan=item.plan,
                status__in=['active', 'trial']
            ).first()
            
            if existing_subscription:
                # Extender suscripción existente
                if existing_subscription.end_date < start_date:
                    # La suscripción ya expiró, renovar desde ahora
                    existing_subscription.start_date = start_date
                    existing_subscription.end_date = end_date
                else:
                    # Extender desde la fecha de expiración actual
                    duration = end_date - start_date
                    existing_subscription.end_date += duration
                
                existing_subscription.status = 'active'
                existing_subscription.is_trial = False
                existing_subscription.billing_cycle = item.billing_cycle
                existing_subscription.save()
                
                logger.info(f"Suscripción extendida: {existing_subscription.id}")
                
            else:
                # Crear nueva suscripción
                subscription = Subscription.objects.create(
                    user=order.user,
                    plan=item.plan,
                    order=order,
                    billing_cycle=item.billing_cycle,
                    start_date=start_date,
                    end_date=end_date,
                    status='active',
                    is_trial=False
                )
                
                logger.info(f"Nueva suscripción creada: {subscription.id}")
                
    except Exception as e:
        logger.error(f"Error creando suscripciones desde orden {order.id}: {e}")


def handle_subscription_cancelled(subscription):
    """
    Maneja la cancelación de una suscripción
    """
    logger.info(f"Procesando cancelación de suscripción: {subscription.id}")
    
    # Enviar email de cancelación
    send_cancellation_email(subscription)
    
    # Registrar feedback de cancelación
    # log_cancellation_feedback(subscription)


def handle_subscription_expired(subscription):
    """
    Maneja la expiración de una suscripción
    """
    logger.info(f"Procesando expiración de suscripción: {subscription.id}")
    
    # Enviar email de expiración
    send_expiration_email(subscription)
    
    # Ofrecer renovación
    # send_renewal_offer(subscription)


def handle_subscription_activated(subscription):
    """
    Maneja la activación de una suscripción
    """
    logger.info(f"Procesando activación de suscripción: {subscription.id}")
    
    # Enviar email de activación
    send_activation_email(subscription)
    
    # Configurar acceso a funcionalidades
    # setup_module_access(subscription)


# Funciones auxiliares para emails (implementar según necesidades)

def send_order_confirmation_email(order):
    """Envía email de confirmación de orden"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    try:
        subject = f'Confirmación de Orden #{order.order_number}'
        html_message = render_to_string('subscriptions/emails/order_confirmation.html', {
            'order': order,
            'user': order.user
        })
        plain_message = f"""
        Confirmación de Orden #{order.order_number}
        
        Hola {order.user.get_full_name()},
        
        Tu orden ha sido confirmada exitosamente.
        Total: ${order.total_amount}
        
        Gracias por tu compra.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email de confirmación enviado para orden {order.order_number}")
        
    except Exception as e:
        logger.error(f"Error enviando email de confirmación para orden {order.order_number}: {e}")


def send_welcome_email(subscription):
    """Envía email de bienvenida para nueva suscripción"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    try:
        subject = f'¡Bienvenido a {subscription.plan.name}!'
        html_message = render_to_string('subscriptions/emails/welcome.html', {
            'subscription': subscription,
            'user': subscription.user,
            'plan': subscription.plan
        })
        plain_message = f"""
        ¡Bienvenido a {subscription.plan.name}!
        
        Hola {subscription.user.get_full_name()},
        
        Tu suscripción ha sido activada exitosamente.
        Plan: {subscription.plan.name}
        Válido hasta: {subscription.end_date.strftime('%d/%m/%Y')}
        
        ¡Disfruta de todas las funcionalidades!
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email de bienvenida enviado para suscripción {subscription.id}")
        
    except Exception as e:
        logger.error(f"Error enviando email de bienvenida para suscripción {subscription.id}: {e}")


def send_cancellation_email(subscription):
    """Envía email de confirmación de cancelación"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    try:
        subject = f'Confirmación de Cancelación - {subscription.plan.name}'
        html_message = render_to_string('subscriptions/emails/cancellation.html', {
            'subscription': subscription,
            'user': subscription.user,
            'plan': subscription.plan
        })
        plain_message = f"""
        Confirmación de Cancelación
        
        Hola {subscription.user.get_full_name()},
        
        Tu suscripción a {subscription.plan.name} ha sido cancelada.
        Expira el: {subscription.end_date.strftime('%d/%m/%Y')}
        
        Lamentamos verte partir.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email de cancelación enviado para suscripción {subscription.id}")
        
    except Exception as e:
        logger.error(f"Error enviando email de cancelación para suscripción {subscription.id}: {e}")


def send_expiration_email(subscription):
    """Envía email de notificación de expiración"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    try:
        subject = f'Tu suscripción a {subscription.plan.name} ha expirado'
        html_message = render_to_string('subscriptions/emails/expiration.html', {
            'subscription': subscription,
            'user': subscription.user,
            'plan': subscription.plan
        })
        plain_message = f"""
        Suscripción Expirada
        
        Hola {subscription.user.get_full_name()},
        
        Tu suscripción a {subscription.plan.name} ha expirado.
        Fecha de expiración: {subscription.end_date.strftime('%d/%m/%Y')}
        
        Renueva ahora para seguir disfrutando de todas las funcionalidades.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email de expiración enviado para suscripción {subscription.id}")
        
    except Exception as e:
        logger.error(f"Error enviando email de expiración para suscripción {subscription.id}: {e}")


def send_activation_email(subscription):
    """Envía email de activación de suscripción"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    try:
        subject = f'Tu suscripción a {subscription.plan.name} está activa'
        html_message = render_to_string('subscriptions/emails/activation.html', {
            'subscription': subscription,
            'user': subscription.user,
            'plan': subscription.plan
        })
        plain_message = f"""
        Suscripción Activada
        
        Hola {subscription.user.get_full_name()},
        
        Tu suscripción a {subscription.plan.name} está ahora activa.
        Válido hasta: {subscription.end_date.strftime('%d/%m/%Y')}
        
        ¡Puedes comenzar a usar todas las funcionalidades!
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email de activación enviado para suscripción {subscription.id}")
        
    except Exception as e:
        logger.error(f"Error enviando email de activación para suscripción {subscription.id}: {e}")
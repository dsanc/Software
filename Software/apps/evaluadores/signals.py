"""
Signals para el módulo de evaluadores
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Evaluador
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=Evaluador)
def evaluador_post_save(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un evaluador
    """
    if created:
        logger.info(f"Nuevo evaluador creado: {instance}")
        
        # Enviar email de bienvenida al evaluador
        try:
            enviar_email_bienvenida_evaluador(instance)
        except Exception as e:
            logger.error(f"Error enviando email de bienvenida: {e}")
        
        # Notificar al usuario principal
        try:
            enviar_notificacion_usuario_principal(instance, 'creado')
        except Exception as e:
            logger.error(f"Error enviando notificación a usuario principal: {e}")
    
    # Si se activa el evaluador
    elif hasattr(instance, '_state') and instance._state.fields_cache.get('estado') != instance.estado:
        if instance.estado == 'active':
            try:
                enviar_email_activacion_evaluador(instance)
            except Exception as e:
                logger.error(f"Error enviando email de activación: {e}")


@receiver(pre_delete, sender=Evaluador)
def evaluador_pre_delete(sender, instance, **kwargs):
    """
    Signal que se ejecuta antes de eliminar un evaluador
    """
    logger.info(f"Evaluador eliminado: {instance}")
    
    # Notificar al evaluador y al usuario principal
    try:
        enviar_email_eliminacion_evaluador(instance)
        enviar_notificacion_usuario_principal(instance, 'eliminado')
    except Exception as e:
        logger.error(f"Error enviando notificaciones de eliminación: {e}")

def enviar_email_bienvenida_evaluador(evaluador):
    """
    Envía email de bienvenida al nuevo evaluador
    """
    if not hasattr(settings, 'DEFAULT_FROM_EMAIL') or not evaluador.usuario_evaluador.email:
        return
    
    try:
        subject = f'¡Bienvenido como evaluador de {evaluador.usuario_principal.get_full_name()}!'
        
        # Preparar contexto para el template
        context = {
            'evaluador': evaluador,
            'usuario_principal': evaluador.usuario_principal,
            'usuario_evaluador': evaluador.usuario_evaluador,
            'modulos_permitidos': evaluador.modulos_permitidos,
            'suscripciones_heredadas': evaluador.obtener_suscripciones_heredadas(),
        }
        
        # Renderizar email HTML
        html_message = render_to_string('evaluadores/emails/bienvenida.html', context)
        
        # Mensaje de texto plano
        plain_message = f"""
        ¡Hola {evaluador.usuario_evaluador.get_full_name()}!
        
        Has sido agregado como {evaluador.get_tipo_evaluador_display()} por {evaluador.usuario_principal.get_full_name()}.
        
        Módulos disponibles: {', '.join(evaluador.modulos_permitidos) if evaluador.modulos_permitidos else 'Ninguno especificado'}
        
        Puedes acceder al sistema con tu cuenta actual.
        
        ¡Bienvenido al equipo!
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[evaluador.usuario_evaluador.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de bienvenida enviado a {evaluador.usuario_evaluador.email}")
        
    except Exception as e:
        logger.error(f"Error enviando email de bienvenida: {e}")
        raise


def enviar_email_activacion_evaluador(evaluador):
    """
    Envía email cuando se activa un evaluador
    """
    if not hasattr(settings, 'DEFAULT_FROM_EMAIL') or not evaluador.usuario_evaluador.email:
        return
    
    try:
        subject = f'Tu cuenta de evaluador ha sido activada'
        
        context = {
            'evaluador': evaluador,
            'usuario_principal': evaluador.usuario_principal,
            'usuario_evaluador': evaluador.usuario_evaluador,
        }
        
        html_message = render_to_string('evaluadores/emails/activacion.html', context)
        
        plain_message = f"""
        ¡Hola {evaluador.usuario_evaluador.get_full_name()}!
        
        Tu cuenta de evaluador ha sido activada por {evaluador.usuario_principal.get_full_name()}.
        
        Ya puedes acceder a todas las funcionalidades asignadas.
        
        ¡Comienza a evaluar!
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[evaluador.usuario_evaluador.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de activación enviado a {evaluador.usuario_evaluador.email}")
        
    except Exception as e:
        logger.error(f"Error enviando email de activación: {e}")


def enviar_email_eliminacion_evaluador(evaluador):
    """
    Envía email cuando se elimina un evaluador
    """
    if not hasattr(settings, 'DEFAULT_FROM_EMAIL') or not evaluador.usuario_evaluador.email:
        return
    
    try:
        subject = f'Tu acceso como evaluador ha sido removido'
        
        context = {
            'evaluador': evaluador,
            'usuario_principal': evaluador.usuario_principal,
            'usuario_evaluador': evaluador.usuario_evaluador,
        }
        
        html_message = render_to_string('evaluadores/emails/eliminacion.html', context)
        
        plain_message = f"""
        Hola {evaluador.usuario_evaluador.get_full_name()},
        
        Tu acceso como evaluador ha sido removido por {evaluador.usuario_principal.get_full_name()}.
        
        Ya no tendrás acceso a las funcionalidades de evaluación.
        
        Gracias por tu participación.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[evaluador.usuario_evaluador.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email de eliminación enviado a {evaluador.usuario_evaluador.email}")
        
    except Exception as e:
        logger.error(f"Error enviando email de eliminación: {e}")


def enviar_notificacion_usuario_principal(evaluador, accion):
    """
    Envía notificación al usuario principal sobre acciones del evaluador
    """
    if not hasattr(settings, 'DEFAULT_FROM_EMAIL') or not evaluador.usuario_principal.email:
        return
    
    try:
        subjects = {
            'creado': f'Nuevo evaluador agregado: {evaluador.usuario_evaluador.get_full_name()}',
            'eliminado': f'Evaluador removido: {evaluador.usuario_evaluador.get_full_name()}',
        }
        
        subject = subjects.get(accion, f'Acción en evaluador: {evaluador.usuario_evaluador.get_full_name()}')
        
        context = {
            'evaluador': evaluador,
            'usuario_principal': evaluador.usuario_principal,
            'accion': accion,
        }
        
        html_message = render_to_string('evaluadores/emails/notificacion_principal.html', context)
        
        messages = {
            'creado': f'Se ha agregado un nuevo evaluador a tu cuenta: {evaluador.usuario_evaluador.get_full_name()}',
            'eliminado': f'Se ha removido el evaluador: {evaluador.usuario_evaluador.get_full_name()}',
        }
        
        plain_message = messages.get(accion, f'Acción realizada en evaluador: {evaluador.usuario_evaluador.get_full_name()}')
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[evaluador.usuario_principal.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Notificación enviada a usuario principal {evaluador.usuario_principal.email}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación a usuario principal: {e}")



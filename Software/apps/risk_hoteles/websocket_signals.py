"""
Señales relacionadas con WebSocket para risk_hoteles.
Permite enviar actualizaciones en tiempo real a los clientes conectados
cuando cambian datos relevantes (evaluaciones, alertas, etc.).
"""
import logging

logger = logging.getLogger(__name__)

# Los handlers de WebSocket se añadirán aquí cuando se implementen
# los Django Channels consumers (routing.py ya tiene websocket_urlpatterns=[]).
#
# Ejemplo de uso futuro:
#
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# from .models import SecurityAssessment
#
# @receiver(post_save, sender=SecurityAssessment)
# def notify_assessment_update(sender, instance, **kwargs):
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         f"hotel_{instance.hotel_id}",
#         {"type": "assessment.update", "assessment_id": str(instance.pk)},
#     )

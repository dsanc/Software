"""
Señales Django para risk_hoteles.
Registra handlers que reaccionan a eventos del modelo (save, delete, etc.).
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import SecurityAssessment, SecurityCategoryScore

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SecurityAssessment)
def on_assessment_saved(sender, instance, created, **kwargs):
    """
    Ejecutado después de guardar una evaluación.
    Lugar para invalidar caché, disparar notificaciones, etc.
    """
    if created:
        logger.debug("Nueva evaluación creada: %s", instance.pk)
    else:
        logger.debug("Evaluación actualizada: %s", instance.pk)


@receiver(post_delete, sender=SecurityAssessment)
def on_assessment_deleted(sender, instance, **kwargs):
    """
    Ejecutado después de eliminar una evaluación.
    """
    logger.debug("Evaluación eliminada: %s", instance.pk)

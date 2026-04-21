from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Modelo abstracto que proporciona campos de timestamp
    """
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """
    Manager personalizado para el soft delete
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(TimeStampedModel):
    """
    Modelo abstracto que proporciona funcionalidad de soft delete
    """
    deleted_at = models.DateTimeField('Eliminado', null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete: marca como eliminado en lugar de eliminar"""
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def hard_delete(self, using=None, keep_parents=False):
        """Eliminación real del objeto"""
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restaura un objeto eliminado"""
        self.deleted_at = None
        self.save()
    
    @property
    def is_deleted(self):
        """Verifica si el objeto está eliminado"""
        return self.deleted_at is not None
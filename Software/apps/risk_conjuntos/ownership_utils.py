"""
Utilidades para validación de propiedad/ownership de conjuntos
"""

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Conjunto


def ensure_conjunto_ownership(user, conjunto):
    """
    Verifica que el usuario tenga permisos sobre el conjunto
    Compatible con el sistema de permisos existente
    """
    # Si es superuser o staff, permitir acceso
    if user.is_superuser or user.is_staff:
        return True
    
    # Si el usuario es el propietario directo
    if conjunto.propietario == user:
        return True
    
    # Si no tiene permisos, lanzar excepción
    raise PermissionDenied(f"No tienes permisos para acceder al conjunto '{conjunto.nombre}'")


def get_conjunto_with_permissions(user, conjunto_id):
    """
    Obtiene un conjunto verificando permisos
    """
    conjunto = get_object_or_404(Conjunto, id=conjunto_id)
    ensure_conjunto_ownership(user, conjunto)
    return conjunto


def filter_conjuntos_by_ownership(queryset, user):
    """
    Filtra un queryset de conjuntos basado en permisos del usuario
    """
    if user.is_superuser or user.is_staff:
        return queryset
    
    return queryset.filter(propietario=user)
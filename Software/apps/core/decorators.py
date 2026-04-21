"""
Decoradores que combinan permisos y filtrado por propiedad
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.http import JsonResponse
from urllib.parse import urlencode

from apps.evaluadores.permissions import (
    evaluador_permission_required, 
    evaluador_module_required,
    EvaluadorPermissionMixin
)
from apps.core.mixins import OwnershipFilterMixin


def evaluator_access_control(module_name, permission=None, ownership_field='owner', creator_field='created_by'):
    """
    Decorador integral que combina:
    - Verificación de acceso al módulo
    - Verificación de permisos CRUD (opcional)
    - Filtrado automático por propiedad en los querysets
    
    Args:
        module_name: Nombre del módulo (risk_hoteles, risk_conjuntos, security_probabilistic)
        permission: Permiso CRUD específico (create, read, update, delete) - opcional
        ownership_field: Campo que indica el propietario del modelo principal
        creator_field: Campo que indica quién creó el registro
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 1. Verificar acceso al módulo
            module_check = evaluador_module_required(module_name)
            module_result = module_check(lambda req, *a, **kw: None)(request, *args, **kwargs)
            if module_result is not None:
                return module_result
            
            # 2. Verificar permisos CRUD específicos si se especifica
            if permission:
                permission_check = evaluador_permission_required(module_name, permission)
                permission_result = permission_check(lambda req, *a, **kw: None)(request, *args, **kwargs)
                if permission_result is not None:
                    return permission_result
            
            # 3. Configurar el contexto de filtrado por propiedad
            request._ownership_config = {
                'module': module_name,
                'ownership_field': ownership_field,
                'creator_field': creator_field,
                'allow_related_access': True
            }
            
            # 4. Ejecutar la vista
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def filter_by_ownership(model, request, queryset=None):
    """
    Función helper para aplicar filtrado por propiedad a un queryset
    
    Args:
        model: El modelo Django a filtrar
        request: Request object que debe tener _ownership_config
        queryset: Queryset base (opcional, si no se proporciona usa model.objects.all())
    
    Returns:
        Queryset filtrado según el tipo de usuario
    """
    if not hasattr(request, '_ownership_config'):
        raise ValueError("La vista debe usar el decorador evaluator_access_control")
    
    config = request._ownership_config
    
    # Crear mixin temporal con configuración específica
    class TempOwnershipMixin(OwnershipFilterMixin):
        ownership_field = config['ownership_field']
        creator_field = config['creator_field']
        allow_related_access = config['allow_related_access']
    
    mixin = TempOwnershipMixin()
    mixin.request = request
    
    if queryset is None:
        queryset = model.objects.all()
    
    return mixin.get_ownership_queryset(queryset)


def ensure_ownership(obj, request):
    """
    Función helper para verificar que el usuario tenga acceso a un objeto específico
    
    Args:
        obj: Objeto del modelo a verificar
        request: Request object que debe tener _ownership_config
    
    Raises:
        PermissionDenied: Si el usuario no tiene acceso al objeto
    """
    if not hasattr(request, '_ownership_config'):
        raise ValueError("La vista debe usar el decorador evaluator_access_control")
    
    config = request._ownership_config
    
    # Crear mixin temporal con configuración específica
    class TempOwnershipMixin(OwnershipFilterMixin):
        ownership_field = config['ownership_field']
        creator_field = config['creator_field'] 
        allow_related_access = config['allow_related_access']
    
    mixin = TempOwnershipMixin()
    mixin.request = request
    
    if not mixin.get_object_ownership(obj):
        raise PermissionDenied(f"No tienes permisos para acceder a este registro en el módulo {config['module']}")


# Decoradores específicos para cada módulo (shortcuts)

def risk_hoteles_access(permission=None):
    """Decorador específico para Risk Hoteles"""
    return evaluator_access_control(
        'risk_hoteles', 
        permission, 
        ownership_field='owner', 
        creator_field='created_by'
    )


def risk_conjuntos_access(permission=None):
    """Decorador específico para Risk Conjuntos"""
    return evaluator_access_control(
        'risk_conjuntos', 
        permission,
        ownership_field='propietario',
        creator_field='creado_por'
    )


def security_probabilistic_access(permission=None):
    """Decorador específico para Security Probabilistic"""
    return evaluator_access_control(
        'security_probabilistic',
        permission,
        ownership_field='owner',
        creator_field='created_by'
    )


# Función helper para obtener información del usuario en templates
def get_user_access_info(user):
    """
    Obtiene información completa de acceso del usuario para usar en templates
    
    Returns:
        dict: Información del tipo de usuario y sus capacidades
    """
    from apps.evaluadores.models import Evaluador
    
    info = {
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'is_evaluator': False,
        'is_principal_user': False,
        'evaluator_info': None,
        'can_see_all_records': user.is_superuser or user.is_staff,
        'access_level': 'admin' if (user.is_superuser or user.is_staff) else 'user'
    }
    
    try:
        evaluador = Evaluador.objects.get(usuario_evaluador=user)
        info.update({
            'is_evaluator': True,
            'access_level': 'evaluator',
            'evaluator_info': {
                'tipo': evaluador.tipo_evaluador,
                'usuario_principal': evaluador.usuario_principal,
                'modulos_permitidos': evaluador.modulos_permitidos,
                'estado': evaluador.estado,
                'permissions_summary': {
                    'risk_hoteles': evaluador.get_permisos_modulo('risk_hoteles'),
                    'risk_conjuntos': evaluador.get_permisos_modulo('risk_conjuntos'),
                    'security_probabilistic': evaluador.get_permisos_modulo('security_probabilistic')
                }
            },
            'can_see_all_records': False
        })
    except Evaluador.DoesNotExist:
        if not (user.is_superuser or user.is_staff):
            info.update({
                'is_principal_user': True,
                'access_level': 'principal',
                'can_see_all_records': True  # Principal users ven sus registros y los de sus evaluadores
            })
    
    return info
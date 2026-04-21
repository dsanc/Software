"""
Template tags para validar permisos de evaluadores
"""
from django import template
from django.contrib.auth.models import User
from ..permissions import get_user_module_permissions

register = template.Library()


@register.simple_tag
def has_module_permission(user, module_name, action):
    """
    Verifica si el usuario tiene un permiso específico en un módulo
    
    Uso en template:
    {% has_module_permission user 'risk_hoteles' 'create' as can_create %}
    {% if can_create %}
        <button>Crear</button>
    {% endif %}
    """
    if not user.is_authenticated:
        return False
    
    permisos = get_user_module_permissions(user, module_name)
    return permisos.get(action, False)


@register.inclusion_tag('evaluadores/partials/crud_buttons.html')
def render_crud_buttons(user, module_name, object_id=None):
    """
    Renderiza botones CRUD basado en permisos
    
    Uso en template:
    {% render_crud_buttons user 'risk_hoteles' object.id %}
    """
    permisos = get_user_module_permissions(user, module_name)
    
    return {
        'permisos': permisos,
        'module_name': module_name,
        'object_id': object_id,
        'user': user
    }


@register.filter
def has_permission(user, permission_string):
    """
    Filtro para verificar permisos en templates
    
    Uso en template:
    {% if user|has_permission:'risk_hoteles.create' %}
        <button>Crear</button>
    {% endif %}
    """
    if not user.is_authenticated or '.' not in permission_string:
        return False
    
    module_name, action = permission_string.split('.', 1)
    permisos = get_user_module_permissions(user, module_name)
    return permisos.get(action, False)


@register.simple_tag
def get_module_permissions(user, module_name):
    """
    Obtiene todos los permisos de un módulo
    
    Uso en template:
    {% get_module_permissions user 'risk_hoteles' as hoteles_perms %}
    """
    if not user.is_authenticated:
        return {}
    
    return get_user_module_permissions(user, module_name)


@register.inclusion_tag('evaluadores/partials/permission_badge.html')
def permission_status(user, module_name):
    """
    Muestra el estado de permisos como badge
    """
    permisos = get_user_module_permissions(user, module_name)
    
    if not permisos:
        status = 'sin-acceso'
        text = 'Sin acceso'
        color = 'danger'
    elif permisos.get('approve', False):
        status = 'admin'
        text = 'Administrador'
        color = 'success'
    elif permisos.get('create', False) and permisos.get('update', False):
        status = 'editor'
        text = 'Editor'
        color = 'warning'
    elif permisos.get('read', False):
        status = 'lector'
        text = 'Solo lectura'
        color = 'info'
    else:
        status = 'sin-acceso'
        text = 'Sin acceso'
        color = 'danger'
    
    return {
        'status': status,
        'text': text,
        'color': color,
        'permissions': permisos
    }
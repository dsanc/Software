"""
Context processors para permisos de evaluadores
"""
from .permissions import get_user_module_permissions


def evaluador_permissions(request):
    """
    Context processor que agrega permisos de evaluadores a todos los templates
    """
    if not request.user.is_authenticated:
        return {}
    
    # Módulos del sistema
    modules = [
        'risk_hoteles',
        'risk_conjuntos', 
        'security_probabilistic'
    ]
    
    permissions = {}
    for module in modules:
        permissions[f'{module}_perms'] = get_user_module_permissions(request.user, module)
    
    return {
        'user_permissions': permissions,
        'has_evaluador_permissions': any(permissions.values())
    }
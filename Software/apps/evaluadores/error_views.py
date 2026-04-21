"""
Vistas para manejo de errores de permisos de evaluadores
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required


@login_required
@require_http_methods(["GET"])
def permission_denied_view(request):
    """
    Vista para mostrar página de error de permisos denegados
    """
    context = {
        'error_type': request.GET.get('error_type', 'permission_denied'),
        'module': request.GET.get('module', 'desconocido'),
        'action': request.GET.get('action', 'acceder'),
        'user_type': 'evaluador' if hasattr(request.user, 'evaluador') else 'usuario',
        'return_url': request.META.get('HTTP_REFERER', '/'),
    }
    
    # Mapeo de acciones a español
    action_map = {
        'read': 'ver',
        'create': 'crear', 
        'update': 'editar',
        'delete': 'eliminar',
        'export': 'exportar',
        'approve': 'aprobar',
        'access': 'acceder'
    }
    
    # Mapeo de módulos a español
    module_map = {
        'risk_hoteles': 'Risk Hoteles',
        'risk_conjuntos': 'Risk Conjuntos', 
        'security_probabilistic': 'Security Probabilistic'
    }
    
    # Mapeo de URLs de redirección por módulo
    module_urls = {
        'risk_hoteles': '/risk-hoteles/dashboard/',
        'risk_conjuntos': '/risk-conjuntos/dashboard/',
        'security_probabilistic': '/security-probabilistic/',
    }
    
    # Si no hay URL de referencia, usar la URL del módulo correspondiente
    if context['return_url'] == '/':
        context['return_url'] = module_urls.get(context['module'], '/dashboard/')
    
    context['action_display'] = action_map.get(context['action'], context['action'])
    context['module_display'] = module_map.get(context['module'], context['module'])
    
    # Email del administrador específico por módulo
    admin_emails = {
        'risk_hoteles': 'admin.hoteles@empresa.com',
        'risk_conjuntos': 'admin.conjuntos@empresa.com',
        'security_probabilistic': 'admin.security@empresa.com',
    }
    context['admin_email'] = admin_emails.get(context['module'], 'admin@empresa.com')
    
    return render(request, 'evaluadores/permission_denied.html', context)


@login_required
@require_http_methods(["GET"])
def permission_denied_modal(request):
    """
    Vista AJAX para obtener datos del modal de permisos denegados
    """
    error_type = request.GET.get('error_type', 'permission_denied')
    module = request.GET.get('module', 'desconocido')
    action = request.GET.get('action', 'acceder')
    
    # Mapeo de acciones a español
    action_map = {
        'read': 'ver',
        'create': 'crear', 
        'update': 'editar',
        'delete': 'eliminar',
        'export': 'exportar',
        'approve': 'aprobar'
    }
    
    # Mapeo de módulos a español
    module_map = {
        'risk_hoteles': 'Risk Hoteles',
        'risk_conjuntos': 'Risk Conjuntos', 
        'security_probabilistic': 'Security Probabilistic'
    }
    
    action_display = action_map.get(action, action)
    module_display = module_map.get(module, module)
    
    if error_type == 'module_access':
        title = "Acceso Denegado al Módulo"
        message = f"No tienes permisos para acceder al módulo <strong>{module_display}</strong>."
        suggestion = "Contacta a tu administrador para solicitar acceso a este módulo."
    else:
        title = "Permisos Insuficientes"
        message = f"No tienes permisos para <strong>{action_display}</strong> en el módulo <strong>{module_display}</strong>."
        suggestion = f"Solo puedes realizar las acciones para las que tienes permisos en {module_display}."
    
    return JsonResponse({
        'success': True,
        'title': title,
        'message': message,
        'suggestion': suggestion,
        'error_type': error_type,
        'module': module_display,
        'action': action_display
    })
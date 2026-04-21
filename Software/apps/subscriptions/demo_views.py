"""
Vistas para gestión de período DEMO
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Module
from .access_control import get_demo_status, start_demo_period


def demo_info(request, module_name):
    """Vista de información sobre el período DEMO"""
    module = get_object_or_404(Module, name=module_name, is_active=True)
    
    # Si el usuario no está autenticado, mostrar info pero no status
    if not request.user.is_authenticated:
        context = {
            'module': module,
            'demo_status': None,
            'page_title': f'Período DEMO - {module.display_name}',
            'require_login': True
        }
    else:
        demo_status = get_demo_status(request.user, module_name)
        context = {
            'module': module,
            'demo_status': demo_status,
            'page_title': f'Período DEMO - {module.display_name}',
            'require_login': False
        }
    
    return render(request, 'subscriptions/demo_info.html', context)


@require_POST
def start_demo(request, module_name):
    """Inicia período DEMO para un módulo"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para activar el período DEMO.')
        return redirect('users:login')
    
    module = get_object_or_404(Module, name=module_name, is_active=True)
    
    # Verificar si puede iniciar DEMO
    demo_status = get_demo_status(request.user, module_name)
    
    if not demo_status['can_start']:
        if demo_status['active']:
            messages.info(request, f'Ya tienes un período DEMO activo para {module.display_name}')
        else:
            messages.warning(request, f'No puedes iniciar otro período DEMO para {module.display_name}')
        
        return redirect('subscriptions:demo_info', module_name=module_name)
    
    # Iniciar DEMO
    demo_subscription = start_demo_period(request.user, module_name)
    
    if demo_subscription:
        messages.success(request, 
            f'¡Período DEMO activado! Tienes 15 días para probar {module.display_name} de forma gratuita.')
        
        # Redirigir al módulo específico
        if module_name == 'risk_conjuntos':
            return redirect('risk_conjuntos:dashboard')
        elif module_name == 'risk_hoteles':
            return redirect('risk_hoteles:dashboard')
        else:
            return redirect('dashboard:dashboard')  # Dashboard general
    else:
        messages.error(request, 'No se pudo activar el período DEMO. Contacta soporte.')
        return redirect('subscriptions:plans_list')


@login_required
def demo_status_api(request, module_name):
    """API para obtener estado del DEMO (AJAX)"""
    try:
        demo_status = get_demo_status(request.user, module_name)
        
        return JsonResponse({
            'success': True,
            'demo_status': demo_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error al obtener estado del DEMO'
        }, status=500)


@login_required
def access_denied(request):
    """Vista genérica de acceso denegado"""
    context = {
        'page_title': 'Acceso Denegado'
    }
    return render(request, 'subscriptions/access_denied.html', context)
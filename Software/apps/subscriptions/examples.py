"""
Ejemplos de uso del sistema de control de acceso en vistas de módulos
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from apps.subscriptions.access_control import (
    requires_subscription, 
    requires_paid_subscription,
    AccessControlMixin
)


# Ejemplo 1: Decorador simple para acceso a módulo
@requires_subscription('risk_hoteles')
def hoteles_dashboard(request):
    """Dashboard del módulo Risk Hoteles (permite DEMO)"""
    context = {
        'page_title': 'Dashboard Risk Hoteles',
    }
    
    # Si está en DEMO, agregar información al contexto
    if hasattr(request, 'demo_info'):
        context['demo_info'] = request.demo_info
    
    return render(request, 'risk_hoteles/dashboard.html', context)


# Ejemplo 2: Funcionalidad premium que NO permite DEMO
@requires_paid_subscription('risk_hoteles', feature_code='export_data')
def export_data(request):
    """Exportar datos (solo suscriptores pagos)"""
    # Esta vista NO permite acceso con DEMO
    return render(request, 'risk_hoteles/export.html')


# Ejemplo 4: Vista basada en clases con Mixin
class RiskConjuntosReportView(AccessControlMixin, TemplateView):
    template_name = 'risk_conjuntos/reports.html'
    required_module = 'risk_conjuntos'
    required_feature = 'generate_reports'
    allow_demo = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reportes Risk Conjuntos'
        
        # Información de DEMO si aplica
        if hasattr(self.request, 'demo_info'):
            context['demo_info'] = self.request.demo_info
        
        return context


# Ejemplo 5: API endpoint con control de acceso
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@requires_subscription('security_probabilistic')
@require_http_methods(["POST"])
def run_security_analysis(request):
    """API para ejecutar análisis de seguridad"""
    try:
        # Lógica del análisis
        result = {'status': 'success', 'analysis_id': '12345'}
        
        # Si está en DEMO, agregar advertencia
        if hasattr(request, 'demo_info'):
            result['demo_warning'] = {
                'message': 'Estás usando la versión DEMO',
                'days_remaining': request.demo_info['days_remaining']
            }
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# Ejemplo 6: Middleware personalizado para control global
class SubscriptionMiddleware:
    """
    Middleware que verifica acceso a URLs específicas
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que requieren suscripción por módulo
        self.protected_urls = {
            '/risk-hoteles/': 'risk_hoteles',
            '/risk-conjuntos/': 'risk_conjuntos', 
            '/security-probabilistic/': 'security_probabilistic',
        }
    
    def __call__(self, request):
        # Verificar si la URL requiere suscripción
        for url_pattern, module_name in self.protected_urls.items():
            if request.path.startswith(url_pattern):
                if not request.user.is_authenticated:
                    # Redirigir a login
                    from django.shortcuts import redirect
                    return redirect('users:login')
                
                # Verificar acceso (esto se podría optimizar cacheando)
                from apps.subscriptions.services import SubscriptionService
                from apps.subscriptions.access_control import get_demo_status
                
                has_subscription = SubscriptionService.has_module_access(request.user, module_name)
                demo_status = get_demo_status(request.user, module_name)
                
                if not has_subscription and not demo_status['active']:
                    from django.shortcuts import redirect
                    return redirect('subscriptions:demo_info', module_name=module_name)
        
        response = self.get_response(request)
        return response
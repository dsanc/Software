from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from apps.subscriptions.access_control import requires_security_probabilistic
from apps.evaluadores.permissions import evaluador_module_required
from django.utils.decorators import method_decorator
from . import views
from .test_views import test_perfiles_view

# Crear wrappers decorados para las vistas principales
@method_decorator(evaluador_module_required('security_probabilistic'), name='dispatch')
class DashboardViewDecorated(views.DashboardView):
    pass

@method_decorator(evaluador_module_required('security_probabilistic'), name='dispatch')
class ListaPerfilesViewDecorated(views.ListaPerfilesView):
    pass

@method_decorator(evaluador_module_required('security_probabilistic'), name='dispatch')
class CrearPerfilViewDecorated(views.CrearPerfilView):
    pass

@method_decorator(evaluador_module_required('security_probabilistic'), name='dispatch')
class DetallePerfilViewDecorated(views.DetallePerfilView):
    pass

@method_decorator(evaluador_module_required('security_probabilistic'), name='dispatch')
class EditarPerfilViewDecorated(views.EditarPerfilView):
    pass

@method_decorator(evaluador_module_required('security_probabilistic'), name='dispatch')
class CrearEvaluacionViewDecorated(views.CrearEvaluacionView):
    pass

@method_decorator(evaluador_module_required('security_probabilistic'), name='dispatch')
class RealizarEvaluacionViewDecorated(views.RealizarEvaluacionView):
    pass

@method_decorator(evaluador_module_required('security_probabilistic'), name='dispatch')
class DetalleEvaluacionViewDecorated(views.DetalleEvaluacionView):
    pass

@login_required
@requires_security_probabilistic()
def redirect_old_lista(request):
    """Redirección de URL antigua a nueva"""
    return redirect('security_probabilistic:lista_perfiles', permanent=True)

app_name = 'security_probabilistic'

urlpatterns = [
    # Dashboard principal
    path('', DashboardViewDecorated.as_view(), name='dashboard'),
    
    # Gestión de perfiles (vista principal)
    path('perfiles/', ListaPerfilesViewDecorated.as_view(), name='lista_perfiles'),
    path('perfiles/nuevo/', CrearPerfilViewDecorated.as_view(), name='crear_perfil'),
    path('perfiles/<int:pk>/', DetallePerfilViewDecorated.as_view(), name='detalle_perfil'),
    path('perfiles/<int:pk>/editar/', EditarPerfilViewDecorated.as_view(), name='editar_perfil'),
    
    # Evaluaciones
    path('perfiles/<int:perfil_id>/nueva-evaluacion/', CrearEvaluacionViewDecorated.as_view(), name='crear_evaluacion'),
    path('evaluaciones/<int:evaluacion_id>/realizar/', RealizarEvaluacionViewDecorated.as_view(), name='realizar_evaluacion'),
    path('evaluaciones/<int:pk>/', DetalleEvaluacionViewDecorated.as_view(), name='detalle_evaluacion'),
    
    # APIs para datos geográficos
    path('api/departamentos/', views.api_departamentos, name='api_departamentos'),
    path('api/municipios/', evaluador_module_required('security_probabilistic')(views.api_municipios), name='api_municipios'),
    
    # Redirección de URL antigua
    path('perfil/lista/', redirect_old_lista, name='redirect_old_lista'),
    
    # Vista de prueba
    path('test-perfiles/', test_perfiles_view, name='test_perfiles'),
]
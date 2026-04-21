"""
URLs para el módulo de evaluadores
"""
from django.urls import path
from . import views

app_name = 'evaluadores'

urlpatterns = [
    # URLs principales para administración de evaluadores
    path('', views.lista_evaluadores, name='lista'),
    path('crear/', views.crear_evaluador, name='crear'),
    path('<int:pk>/', views.detalle_evaluador, name='detalle'),
    path('<int:pk>/editar/', views.editar_evaluador, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_evaluador, name='eliminar'),
    path('<int:pk>/cambiar-estado/', views.cambiar_estado_evaluador, name='cambiar_estado'),
    

    
    # URLs para evaluadores (perspectiva del evaluador)
    path('mi-perfil/', views.mi_perfil_evaluador, name='mi_perfil_evaluador'),
    path('dashboard/<int:usuario_principal_id>/', views.dashboard_evaluador, name='dashboard_evaluador'),
    
    # URL para ejemplo de permisos
    path('permisos-ejemplo/', views.permisos_ejemplo, name='permisos_ejemplo'),
    
    # URLs para manejo de errores de permisos
    path('permission-denied/', views.permission_denied_view, name='permission_denied'),
    path('api/permission-denied-modal/', views.permission_denied_modal, name='permission_denied_modal'),
    
    # Vista de prueba para el sistema de permisos
    path('test-permissions/', views.test_permission_system, name='test_permissions'),
    
    # Vistas de prueba para el sistema de filtrado por propietario
    path('test-ownership/', views.test_ownership_system, name='test_ownership_system'),
    path('api/test-ownership/', views.test_ownership_api, name='test_ownership'),
    
    # APIs y endpoints AJAX
    path('api/verificar-usuario/', views.api_verificar_usuario, name='api_verificar_usuario'),
    path('api/<int:pk>/estadisticas/', views.api_estadisticas_evaluador, name='api_estadisticas_evaluador'),
]
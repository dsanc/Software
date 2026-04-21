"""
URLs consolidadas para el módulo risk_conjuntos
Versión refactorizada que consolida el sistema legacy y el nuevo
"""
from django.urls import path, include
from . import views
from . import views_evaluacion

app_name = 'risk_conjuntos'

# URLs principales - Sistema consolidado
urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Gestión de conjuntos
    path('conjuntos/', views.lista_conjuntos, name='lista_conjuntos'),
    path('conjuntos/crear/', views.crear_conjunto, name='crear_conjunto'),
    path('conjuntos/<uuid:conjunto_id>/', views.detalle_conjunto, name='detalle_conjunto'),
    path('conjuntos/<uuid:conjunto_id>/editar/', views.editar_conjunto, name='editar_conjunto'),
    path('conjuntos/<uuid:conjunto_id>/eliminar/', views.eliminar_conjunto, name='eliminar_conjunto'),
    
    # Sistema principal de evaluación de riesgos (NUEVO)
    path('conjuntos/<uuid:conjunto_id>/evaluacion/', include([
        path('iniciar/', views_evaluacion.iniciar_evaluacion, name='iniciar_evaluacion'),
        path('paso-1/', views_evaluacion.paso_1_seleccion_riesgos, name='paso_1_seleccion_riesgos'),
        path('paso-2/<int:riesgo_index>/', views_evaluacion.paso_2_preguntas, name='paso_2_preguntas'),
        path('paso-3/', views_evaluacion.paso_3_observaciones, name='paso_3_observaciones'),
        path('paso-4/', views_evaluacion.paso_4_resumen, name='paso_4_resumen'),
        path('<uuid:evaluacion_id>/exito/', views_evaluacion.evaluacion_exitosa, name='evaluacion_exitosa'),
        path('<uuid:evaluacion_id>/', views_evaluacion.detalle_evaluacion, name='detalle_evaluacion'),
    ])),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/conjunto/<uuid:conjunto_id>/', views.reporte_conjunto, name='reporte_conjunto'),
    path('reportes/evaluacion/<uuid:evaluacion_id>/', views.reporte_evaluacion, name='reporte_evaluacion'),
    path('reportes/comparativo/', views.reporte_comparativo, name='reporte_comparativo'),
    
    # APIs para JavaScript/AJAX
    path('api/', include([
        path('conjunto/<uuid:conjunto_id>/stats/', views.api_stats_conjunto, name='api_stats_conjunto'),
        path('dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
        path('tipos-conjunto/', views.api_tipos_conjunto, name='api_tipos_conjunto'),
        path('conjunto/<uuid:conjunto_id>/', views.api_conjunto_detalle, name='api_conjunto_detalle'),
        path('conjunto/crear/', views.api_conjunto_crear, name='api_conjunto_crear'),
        path('conjunto/<uuid:conjunto_id>/editar/', views.api_conjunto_editar, name='api_conjunto_editar'),
    ])),
    
    # Utilidades
    path('utils/', include([
        path('export-csv/', views.export_csv, name='export_csv'),
        path('import-data/', views.import_data, name='import_data'),
    ])),
]

# URLs del sistema legacy (DEPRECATED) - Mantenidas para compatibilidad
legacy_patterns = [
    # Evaluaciones de seguridad (legacy) - Redirigen al nuevo sistema
    path('evaluaciones/', views.lista_evaluaciones, name='lista_evaluaciones_legacy'),
    path('evaluaciones/crear/<uuid:conjunto_id>/', views.crear_evaluacion, name='crear_evaluacion_legacy'),
    path('evaluaciones/<uuid:evaluacion_id>/detalle/', views.detalle_evaluacion, name='detalle_evaluacion_legacy'),
    path('evaluaciones/<uuid:evaluacion_id>/continuar/', views.continuar_evaluacion, name='continuar_evaluacion_legacy'),
    path('evaluaciones/<uuid:evaluacion_id>/completar/', views.completar_evaluacion, name='completar_evaluacion_legacy'),
]

# Agregar URLs legacy con advertencia
urlpatterns += [
    path('legacy/', include(legacy_patterns)),
]
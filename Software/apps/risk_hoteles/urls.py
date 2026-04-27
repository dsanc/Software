from django.urls import path
from . import views, views_pdf_individual, views_performance, views_pwa, views_analytics, views_reporte_general

app_name = 'risk_hoteles'

urlpatterns = [
    # Vistas principales
    path('', views.dashboard, name='dashboard'),
    path('hoteles/', views.hotel_list, name='hotel_list'), 
    path('hoteles/<uuid:hotel_id>/', views.hotel_detail, name='hotel_detail'),
    
    # AJAX para crear y editar hotel
    path('ajax/crear-hotel/', views.create_hotel_ajax, name='create_hotel_ajax'),
    path('ajax/obtener-hotel/<uuid:hotel_id>/', views.get_hotel_data, name='get_hotel_data'),
    path('ajax/actualizar-hotel/', views.update_hotel_ajax, name='update_hotel_ajax'),
    path('ajax/eliminar-hotel/<uuid:hotel_id>/', views.delete_hotel_ajax, name='delete_hotel_ajax'),
    
    # Análisis de riesgo y evaluaciones de seguridad
    path('analizar/', views.create_analysis_redirect, name='create_analysis_redirect'),
    path('hoteles/<uuid:hotel_id>/analizar/', views.create_analysis, name='create_analysis'),
    path('evaluacion/<uuid:assessment_id>/cuestionario/', views.assessment_survey, name='assessment_survey'),
    
    # APIs para manejo de imágenes de evidencia
    path('evaluacion/<uuid:assessment_id>/evidence/upload/', views.upload_evidence_image, name='upload_evidence_image'),
    path('evaluacion/<uuid:assessment_id>/evidence/<uuid:evidence_id>/delete/', views.delete_evidence_image, name='delete_evidence_image'),
    path('evaluacion/<uuid:assessment_id>/evidence/list/', views.get_evidence_images, name='get_evidence_images'),
    path('evaluacion/<uuid:assessment_id>/resultados/', views.assessment_results, name='assessment_results'),
    path('evaluacion/<uuid:assessment_id>/detalle/', views.assessment_detail, name='assessment_detail'),
    path('evaluacion/<uuid:assessment_id>/descartar/', views.discard_assessment, name='discard_assessment'),
    
    # Reportes PDF Individuales
    path('evaluacion/<uuid:assessment_id>/pdf/preview/', views_pdf_individual.assessment_pdf_preview, name='assessment_pdf_preview'),
    path('evaluacion/<uuid:assessment_id>/pdf/print/', views_pdf_individual.assessment_pdf_print, name='assessment_pdf_print'),
    
    # Reporte General - API de datos
    path('hoteles/<uuid:hotel_id>/reporte-general/api/', views_reporte_general.reporte_general_api, name='reporte_general_api'),

    # Nuevo Reporte General (reports/)
    path('hoteles/<uuid:hotel_id>/reporte/', views_reporte_general.reporte_general, name='reporte_general'),
    path('hoteles/<uuid:hotel_id>/reporte/print/', views_reporte_general.reporte_general_print, name='reporte_general_print'),
    
    # Exportación
    path('exportar/', views.export_data, name='export_data'),
    
    # API Endpoints
    path('api/hoteles/', views.api_hotels_list, name='api_hotels_list'),
    
    # Performance Monitoring (Admin only)
    path('admin/performance/', views_performance.performance_dashboard, name='performance_dashboard'),
    path('admin/performance/api/', views_performance.performance_api, name='performance_api'),
    path('admin/performance/clear/', views_performance.clear_metrics, name='clear_metrics'),
    
    # PWA Endpoints
    path('manifest.json', views_pwa.manifest_json, name='manifest_json'),
    path('offline/', views_pwa.offline_page, name='offline_page'),
    path('share/', views_pwa.pwa_share, name='pwa_share'),
    path('service-worker.js', views_pwa.service_worker, name='service_worker'),
    path('browserconfig.xml', views_pwa.browserconfig_xml, name='browserconfig_xml'),
    
    # Push Notifications
    path('api/push-subscription/', views_pwa.push_subscription, name='push_subscription'),
    
    # Analytics Dashboard (Staff only)
    path('analytics/', views_analytics.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/events/', views_analytics.analytics_events, name='analytics_events'),
    path('analytics/users/', views_analytics.analytics_users, name='analytics_users'),
    path('analytics/performance/', views_analytics.analytics_performance, name='analytics_performance'),
    path('analytics/conversions/', views_analytics.analytics_conversions, name='analytics_conversions'),
    path('analytics/user-journey/<int:user_id>/', views_analytics.user_journey, name='user_journey'),
    
    # Analytics API
    path('api/analytics/track-event/', views_analytics.track_event_api, name='track_event_api'),
    path('api/analytics/track-click/', views_analytics.track_click_api, name='track_click_api'),
    path('api/analytics/track-performance/', views_analytics.track_performance_api, name='track_performance_api'),
    path('api/analytics/track-batch/', views_analytics.track_batch_api, name='track_batch_api'),
    path('api/analytics/data/', views_analytics.analytics_api_data, name='analytics_api_data'),
]
"""
Views para generar reportes PDF individuales de evaluaciones de seguridad
Módulo separado para mantener organizado el código de reportes
"""

import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .views import get_assessment_or_404

logger = logging.getLogger(__name__)


def _build_pdf_context(assessment):
    """
    Helper compartido que construye el contexto de datos del PDF.
    Evita duplicación entre assessment_pdf_preview y assessment_pdf_print.
    """
    hotel = assessment.hotel
    detailed_report = assessment.get_detailed_scoring_report()
    scoring_summary = assessment.get_scoring_summary()

    # Contadores de áreas por nivel de rendimiento
    strong_areas_count = 0
    moderate_areas_count = 0
    critical_areas_count = 0
    excellent_areas_count = 0
    sorted_categories = []

    if isinstance(detailed_report, dict) and 'categories' in detailed_report:
        categories = detailed_report['categories']
        if isinstance(categories, dict):
            for category_code, category_data in categories.items():
                if isinstance(category_data, dict) and 'percentage' in category_data:
                    percentage = float(category_data.get('percentage', 0))
                    category_data['percentage'] = round(percentage, 1)
                    sorted_categories.append((category_code, category_data, percentage))

                    # Cada categoría cae en exactamente un nivel (sin doble suma)
                    if percentage >= 90:
                        excellent_areas_count += 1
                    elif percentage >= 80:
                        strong_areas_count += 1
                    elif percentage >= 50:
                        moderate_areas_count += 1
                    else:
                        critical_areas_count += 1

            # Ordenar de menor a mayor porcentaje
            sorted_categories.sort(key=lambda x: x[2])
            detailed_report['categories'] = {
                code: data for code, data, _ in sorted_categories
            }

    # Construir datos seguros para el gráfico radar
    categories_data = []
    try:
        if isinstance(detailed_report, dict) and 'categories' in detailed_report:
            categories = detailed_report['categories']
            if isinstance(categories, dict):
                for category_code, category_data in categories.items():
                    if isinstance(category_data, dict) and category_data.get('question_count', 0) > 0:
                        categories_data.append({
                            'name': category_data.get('category_name', category_data.get('name', category_code)),
                            'percentage': float(category_data.get('percentage', 0)),
                        })
    except Exception:
        logger.exception(
            "Error al construir categories_data para PDF de assessment %s", assessment.pk
        )
        categories_data = []

    # overall_percentage: fuente única y consistente para ambas vistas
    overall_percentage = 0
    if scoring_summary:
        overall_percentage = scoring_summary.get('overall_score_percentage', 0)
    if not overall_percentage and isinstance(detailed_report, dict):
        overall_percentage = detailed_report.get('overall_score', 0)

    return {
        'hotel': hotel,
        'detailed_report': detailed_report,
        'scoring_summary': scoring_summary,
        'categories_data': categories_data,
        'overall_percentage': overall_percentage,
        'strong_areas_count': strong_areas_count,
        'moderate_areas_count': moderate_areas_count,
        'critical_areas_count': critical_areas_count,
        'excellent_areas_count': excellent_areas_count,
        'generated_date': timezone.now(),
        'report_title': f'Reporte de Evaluación de Seguridad - {hotel.name}',
        'report_subtitle': f'Evaluación realizada el {assessment.assessment_date.strftime("%d/%m/%Y")}',
    }


@login_required
def assessment_pdf_preview(request, assessment_id):
    """
    Vista previa del reporte PDF antes de descargarlo.
    Muestra exactamente cómo se verá el PDF en el navegador.
    """
    assessment = get_assessment_or_404(request.user, assessment_id)
    context = _build_pdf_context(assessment)
    context.update({
        'assessment': assessment,
        'preview_mode': True,
    })
    return render(request, 'risk_hoteles/reports/pdf_preview_simple.html', context)


@login_required
def assessment_pdf_print(request, assessment_id):
    """
    Vista para impresión automática del reporte PDF usando JavaScript.
    Abre el reporte en una página optimizada que automáticamente activa window.print().
    """
    assessment = get_assessment_or_404(request.user, assessment_id)
    context = _build_pdf_context(assessment)
    context.update({
        'assessment': assessment,
        'print_mode': True,
    })
    return render(request, 'risk_hoteles/reports/pdf_print_exact.html', context)


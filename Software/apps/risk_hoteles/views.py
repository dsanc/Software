from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Max, Subquery, OuterRef
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

# Importar sistema de permisos de evaluadores
from apps.evaluadores.permissions import (
    evaluador_permission_required, 
    evaluador_module_required,
    EvaluadorPermissionMixin
)

# Importar mixins de filtrado por propiedad
from apps.core.mixins import (
    OwnershipFilterMixin,
    CreatedByMixin,
    UserTypeContextMixin,
    OwnershipValidationMixin
)
import json
import csv
from datetime import datetime, timedelta

from apps.subscriptions.decorators import (
    subscription_required, 
    feature_required, 
    plan_level_required,
    usage_limit_check,
    api_subscription_required
)

from .models import (
    Hotel, RiskCategory,
    SecurityCategory, SecurityQuestion, SecurityAssessment, SecurityResponse, SecurityCategoryComment,
    AssessmentEvidence
)

# Importar sistema de IA
from .ai_recommendations import HotelSecurityAIRecommendations

User = get_user_model()


# Helper class para aplicar filtrado por propiedad a vistas funcionales
class RiskHotelesOwnershipMixin(OwnershipFilterMixin):
    """
    Mixin específico para Risk Hoteles con configuración de campos
    """
    ownership_field = 'owner'  # Para hoteles
    creator_field = 'created_by'  # Para evaluaciones
    allow_related_access = True


def get_user_hotels(user):
    """
    Función helper para obtener hoteles según el tipo de usuario.
    - Evaluador: solo los hoteles que él mismo creó (created_by=user)
    - Usuario principal (incluyendo staff/superuser): todos sus hoteles (owner=user)
    """
    from apps.evaluadores.models import Evaluador
    from .models import Hotel

    try:
        Evaluador.objects.get(usuario_evaluador=user)
        # Evaluadores solo ven hoteles que ellos mismos crearon
        return Hotel.objects.filter(is_active=True, created_by=user)
    except Evaluador.DoesNotExist:
        # Usuario principal: todos los hoteles donde es propietario
        return Hotel.objects.filter(is_active=True, owner=user)


def get_user_assessments(user):
    """
    Función helper para obtener evaluaciones según el tipo de usuario.

    SecurityAssessment no tiene campo 'owner' directo — la propiedad se
    accede a través de hotel__owner, por lo que el OwnershipFilterMixin
    genérico no puede filtrar correctamente para este modelo.
    Se implementa lógica explícita:
      - Evaluador: solo las que él creó (created_by=user)
      - Usuario principal (incluyendo staff/superuser): las de sus hoteles
        + las creadas por sus evaluadores
    """
    from django.db.models import Q
    from apps.evaluadores.models import Evaluador
    from .models import SecurityAssessment

    try:
        Evaluador.objects.get(usuario_evaluador=user)
        # Evaluador: solo las evaluaciones que él mismo creó
        return SecurityAssessment.objects.filter(created_by=user)
    except Evaluador.DoesNotExist:
        # Usuario principal: sus hoteles + evaluaciones creadas por sus evaluadores
        evaluadores_ids = Evaluador.objects.filter(
            usuario_principal=user
        ).values_list('usuario_evaluador_id', flat=True)

        return SecurityAssessment.objects.filter(
            Q(hotel__owner=user) | Q(created_by__in=evaluadores_ids)
        )


def ensure_assessment_ownership(user, assessment):
    """
    Verifica que el usuario tenga acceso a una evaluación específica
    """
    mixin = RiskHotelesOwnershipMixin()
    mixin.request = type('obj', (object,), {'user': user})()  # Mock request object
    
    if not mixin.get_object_ownership(assessment):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("No tienes permisos para acceder a esta evaluación")


def get_hotel_or_404(user, hotel_id, **extra_filters):
    """
    Obtiene un hotel verificando ownership según el tipo de usuario.
    Reemplaza get_object_or_404(Hotel, id=hotel_id, owner=user) para que
    también funcione correctamente con evaluadores.
    """
    qs = get_user_hotels(user).filter(id=hotel_id, **extra_filters)
    if not qs.exists():
        from django.http import Http404
        raise Http404("No Hotel matches the given query.")
    return qs.get()


def get_assessment_or_404(user, assessment_id, **extra_filters):
    """
    Obtiene una evaluación verificando ownership según el tipo de usuario.
    Reemplaza get_object_or_404(SecurityAssessment, id=..., hotel__owner=user).
    """
    qs = get_user_assessments(user).filter(id=assessment_id, **extra_filters)
    if not qs.exists():
        from django.http import Http404
        raise Http404("No SecurityAssessment matches the given query.")
    return qs.select_related('hotel').get()


def ensure_hotel_ownership(user, hotel):
    """
    Verifica que el usuario tenga acceso a un hotel específico
    """
    mixin = RiskHotelesOwnershipMixin()
    mixin.request = type('obj', (object,), {'user': user})()  # Mock request object
    
    if not mixin.get_object_ownership(hotel):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("No tienes permisos para acceder a este hotel")


def has_assessments_in_progress(user, hotel=None):
    """
    Verifica si el usuario tiene evaluaciones en progreso
    Si hotel es None, verifica globalmente
    Si hotel es especificado, verifica solo para ese hotel
    Retorna: (tiene_evaluaciones, lista_de_evaluaciones)
    """
    from .models import SecurityAssessment
    
    query = SecurityAssessment.objects.filter(
        created_by=user,
        status='in_progress'
    ).select_related('hotel')
    
    if hotel:
        # Verificar solo para el hotel específico
        query = query.filter(hotel=hotel)
    
    return query.exists(), query


def get_assessment_in_progress_message(user, hotel=None):
    """
    Genera un mensaje descriptivo sobre las evaluaciones en progreso del usuario
    Si hotel es None, mensaje global
    Si hotel es especificado, mensaje específico para ese hotel
    """
    tiene_evaluaciones, evaluaciones = has_assessments_in_progress(user, hotel)
    
    if not tiene_evaluaciones:
        return None
    
    if hotel:
        # Mensaje específico para un hotel
        eval_activa = evaluaciones.first()
        return (
            f'Ya tienes una evaluación en progreso para este hotel '
            f'iniciada el {eval_activa.assessment_date.strftime("%d/%m/%Y")}. '
            f'Completa o descarta esa evaluación antes de crear una nueva.'
        )
    else:
        # Mensaje global
        if evaluaciones.count() == 1:
            eval_activa = evaluaciones.first()
            return (
                f'Tienes una evaluación en progreso para el hotel '
                f'"{eval_activa.hotel.name}" iniciada el {eval_activa.assessment_date.strftime("%d/%m/%Y")}.'
            )
        else:
            return (
                f'Tienes {evaluaciones.count()} evaluaciones en progreso en diferentes hoteles.'
            )


def _validate_required_questions(assessment, post_data):
    """
    Helper function para validar preguntas obligatorias de forma robusta
    Retorna una lista con los errores de validación encontrados
    """
    required_questions = SecurityQuestion.objects.filter(
        category__in=assessment.selected_categories.all(),
        is_required=True,
        is_active=True
    )
    
    validation_errors = []
    
    for req_question in required_questions:
        question_key = f'question_{req_question.id}'
        question_value = post_data.get(question_key, '').strip()
        
        # Validación más estricta: debe tener una respuesta válida
        if not question_value:
            validation_errors.append({
                'question_id': req_question.id,
                'question_text': req_question.question_text[:50] + '...',
                'category': req_question.category.name,
                'error': 'Sin respuesta'
            })
        elif question_value not in ['0', '1', '2', '3', '4', '5', 'na']:
            validation_errors.append({
                'question_id': req_question.id,
                'question_text': req_question.question_text[:50] + '...',
                'category': req_question.category.name,
                'error': f'Valor inválido: {question_value}'
            })
    
    return validation_errors


def _sanitize_text_input(text, max_length=None):
    """
    Helper function para sanitizar entradas de texto de forma más robusta
    """
    if not text:
        return ''
    
    import html
    import re
    
    # Limpiar y escapar HTML para prevenir XSS
    sanitized = html.escape(text.strip())
    
    # Remover protocolos peligrosos
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'about:']
    for protocol in dangerous_protocols:
        sanitized = re.sub(re.escape(protocol), '', sanitized, flags=re.IGNORECASE)
    
    # Remover elementos HTML peligrosos adicionales
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'on\w+\s*=',  # event handlers como onclick, onload, etc.
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Limitar longitud si se especifica
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


@login_required
@subscription_required('risk_hoteles')
@evaluador_module_required('risk_hoteles')
def dashboard(request):
    """
    Dashboard principal del módulo de análisis de riesgo para hoteles
    ACTUALIZADO: Usando SecurityAssessment y métricas avanzadas con gráficas
    """
    from django.db.models import Avg, Count, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    import json
    
    # Filtrar hoteles del usuario usando el sistema de propiedad
    user_hotels = get_user_hotels(request.user).select_related('owner').prefetch_related('security_assessments')
    
    # Análisis recientes usando SecurityAssessment con filtrado por propiedad
    recent_analyses = get_user_assessments(request.user).filter(
        status='completed'
    ).select_related('hotel').order_by('-assessment_date')[:8]
    
    # === ESTADÍSTICAS PRINCIPALES ===
    
    # 1. Total de hoteles registrados
    total_hotels = user_hotels.count()
    
    # 2. Total de evaluaciones completadas
    user_assessments = get_user_assessments(request.user)
    total_assessments = user_assessments.filter(
        status='completed',
        overall_score__isnull=False
    ).count()
    
    # 3. Promedio general de seguridad (usando nuestros nuevos métodos)
    hotels_with_assessments = user_hotels.filter(
        security_assessments__status='completed',
        security_assessments__overall_score__isnull=False
    ).distinct()
    
    if hotels_with_assessments.exists():
        # Calcular promedio de promedios de hoteles
        avg_scores = []
        for hotel in hotels_with_assessments:
            hotel_avg = hotel.get_average_assessment_percentage()
            if hotel_avg is not None:
                avg_scores.append(hotel_avg)
        
        avg_security_percentage = round(sum(avg_scores) / len(avg_scores), 1) if avg_scores else 0
    else:
        avg_security_percentage = 0
    
    # 4. Evaluaciones este mes
    current_month = timezone.now().replace(day=1)
    assessments_this_month = user_assessments.filter(
        status='completed',
        assessment_date__gte=current_month
    ).count()
    
    # === MÉTRICAS ADICIONALES ===
    
    # Distribución por categoría de hotel
    category_distribution = user_hotels.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Top 5 hoteles mejor evaluados
    top_hotels = []
    for hotel in user_hotels:
        avg_percentage = hotel.get_average_assessment_percentage()
        if avg_percentage is not None:
            top_hotels.append({
                'hotel': hotel,
                'avg_percentage': avg_percentage,
                'assessment_count': hotel.get_assessment_count()
            })
    
    # Ordenar por puntuación y tomar top 5
    top_hotels = sorted(top_hotels, key=lambda x: x['avg_percentage'], reverse=True)[:5]
    
    # Hoteles que necesitan atención (< 60%)
    hotels_need_attention = []
    for hotel in user_hotels:
        avg_percentage = hotel.get_average_assessment_percentage()
        if avg_percentage is not None and avg_percentage < 60:
            hotels_need_attention.append({
                'hotel': hotel,
                'avg_percentage': avg_percentage
            })
    
    # Distribución por rangos de puntuación
    score_ranges = {
        '90-100%': 0,
        '80-89%': 0,
        '70-79%': 0,
        '60-69%': 0,
        '50-59%': 0,
        '0-49%': 0
    }
    
    for hotel in user_hotels:
        avg_percentage = hotel.get_average_assessment_percentage()
        if avg_percentage is not None:
            if avg_percentage >= 90:
                score_ranges['90-100%'] += 1
            elif avg_percentage >= 80:
                score_ranges['80-89%'] += 1
            elif avg_percentage >= 70:
                score_ranges['70-79%'] += 1
            elif avg_percentage >= 60:
                score_ranges['60-69%'] += 1
            elif avg_percentage >= 50:
                score_ranges['50-59%'] += 1
            else:
                score_ranges['0-49%'] += 1
    
    # === DATOS PARA GRÁFICAS ===
    
    # 1. EVOLUCIÓN TEMPORAL (últimos 6 meses)
    monthly_trends = {
        'labels': [],
        'data': [],
        'counts': []
    }
    
    current_date = timezone.now()
    for i in range(6):
        month_start = (current_date.replace(day=1) - timedelta(days=30*i))
        month_end = month_start + timedelta(days=31)
        
        # Evaluaciones del mes
        month_assessments = user_assessments.filter(
            status='completed',
            assessment_date__gte=month_start,
            assessment_date__lt=month_end
        )
        
        if month_assessments.exists():
            avg_score = month_assessments.aggregate(avg=Avg('overall_score'))['avg']
            avg_percentage = round((avg_score / 5.0) * 100, 1) if avg_score else 0
        else:
            avg_percentage = 0
        
        monthly_trends['labels'].insert(0, month_start.strftime('%b %Y'))
        monthly_trends['data'].insert(0, avg_percentage)
        monthly_trends['counts'].insert(0, month_assessments.count())
    
    # 2. DISTRIBUCIÓN GEOGRÁFICA
    geographic_data = {
        'labels': [],
        'data': []
    }
    
    geographic_dist = user_hotels.values('country').annotate(
        count=Count('id')
    ).order_by('-count')[:6]  # Top 6 países
    
    for item in geographic_dist:
        if item['country']:
            geographic_data['labels'].append(item['country'])
            geographic_data['data'].append(item['count'])
    
    # 3. ANÁLISIS POR CATEGORÍA (estrellas)
    category_data = {
        'labels': [],
        'data': []
    }
    
    categories = ['1 Estrella', '2 Estrellas', '3 Estrellas', '4 Estrellas', '5 Estrellas']
    for i, category in enumerate(categories, 1):
        hotels_in_category = user_hotels.filter(category=i)
        if hotels_in_category.exists():
            category_avg_scores = []
            for hotel in hotels_in_category:
                hotel_avg = hotel.get_average_assessment_percentage()
                if hotel_avg is not None:
                    category_avg_scores.append(hotel_avg)
            
            if category_avg_scores:
                category_avg = round(sum(category_avg_scores) / len(category_avg_scores), 1)
                category_data['labels'].append(category)
                category_data['data'].append(category_avg)
    
    # 4. FRECUENCIA DE EVALUACIONES (últimos 6 meses)
    evaluation_frequency = {
        'labels': [],
        'data': []
    }
    
    for i in range(6):
        month_start = (current_date.replace(day=1) - timedelta(days=30*i))
        month_end = month_start + timedelta(days=31)
        
        evaluations_count = user_assessments.filter(
            status='completed',
            assessment_date__gte=month_start,
            assessment_date__lt=month_end
        ).count()
        
        evaluation_frequency['labels'].insert(0, month_start.strftime('%b %Y'))
        evaluation_frequency['data'].insert(0, evaluations_count)
    
    context = {
        # Datos principales
        'user_hotels': user_hotels,
        'recent_analyses': recent_analyses,
        
        # Estadísticas principales (4 cards)
        'total_hotels': total_hotels,
        'total_assessments': total_assessments,
        'avg_security_percentage': avg_security_percentage,
        'assessments_this_month': assessments_this_month,
        
        # Distribuciones y rankings
        'category_distribution': category_distribution,
        'top_hotels': top_hotels,
        'hotels_need_attention': hotels_need_attention,
        'score_ranges': score_ranges,
        
        # Métricas adicionales
        'hotels_with_assessments_count': hotels_with_assessments.count(),
        'hotels_without_assessments_count': total_hotels - hotels_with_assessments.count(),
        
        # Datos para gráficas (en formato JSON para JavaScript)
        'monthly_trends': json.dumps(monthly_trends),
        'geographic_data': json.dumps(geographic_data),
        'category_data': json.dumps(category_data),
        'evaluation_frequency': json.dumps(evaluation_frequency),
    }
    
    return render(request, 'risk_hoteles/dashboard.html', context)


@login_required
@subscription_required('risk_hoteles')
@evaluador_permission_required('risk_hoteles', 'read')
def hotel_list(request):
    """
    Lista de hoteles del usuario con consultas optimizadas
    """
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'name')
    
    # Consulta optimizada con prefetch_related y select_related usando filtrado por propiedad
    hotels = get_user_hotels(request.user).select_related(
        'owner'
    ).annotate(
        analysis_count=Count('security_assessments')
    )
    
    # Filtros de búsqueda
    if search_query:
        hotels = hotels.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(country__icontains=search_query)
        )
    
    if category_filter:
        hotels = hotels.filter(category=category_filter)
    
    # Ordenamiento optimizado
    sort_options = {
        'name': 'name',
        'city': 'city',
        'created_at': '-created_at',
        'total_rooms': '-total_rooms',
        'risk_level': 'latest_analysis_date'
    }
    hotels = hotels.order_by(sort_options.get(sort_by, 'name'))
    
    # Paginación dinámica
    per_page = request.GET.get('per_page', '25')
    try:
        per_page = int(per_page)
        # Limitar opciones válidas para evitar sobrecarga
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
    except (ValueError, TypeError):
        per_page = 25
        
    paginator = Paginator(hotels, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Agregar información de evaluaciones en progreso a cada hotel
    for hotel in page_obj.object_list:
        tiene_evaluaciones_progreso, evaluaciones_progreso = has_assessments_in_progress(request.user, hotel)
        # Agregar atributos dinámicos al objeto hotel
        hotel.tiene_evaluaciones_progreso = tiene_evaluaciones_progreso
        hotel.evaluaciones_progreso = evaluaciones_progreso
        if tiene_evaluaciones_progreso:
            hotel.mensaje_evaluaciones_progreso = get_assessment_in_progress_message(request.user, hotel)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'hotel_categories': Hotel._meta.get_field('category').choices,
    }
    
    return render(request, 'risk_hoteles/hotel_list.html', context)


@login_required
@subscription_required('risk_hoteles')
def hotel_detail(request, hotel_id):
    """
    Detalle de un hotel específico
    """
    from django.db.models import Avg
    from apps.risk_hoteles.models import SecurityCategoryScore
    
    hotel = get_object_or_404(get_user_hotels(request.user), id=hotel_id)
    
    # Verificar propiedad del hotel
    ensure_hotel_ownership(request.user, hotel)
    
    # Evaluaciones de seguridad más recientes (solo completadas)
    latest_assessment = SecurityAssessment.objects.filter(
        hotel=hotel,
        status='completed'
    ).order_by('-assessment_date', '-id').first()
    
    # Calcular promedio general de todas las evaluaciones del hotel
    all_assessments = SecurityAssessment.objects.filter(
        hotel=hotel,
        overall_score__isnull=False
    ).order_by('-assessment_date')
    
    hotel_average_score = None
    total_assessments_count = 0
    
    if all_assessments.exists():
        # Calcular promedio de todas las evaluaciones con overall_score
        total_assessments_count = all_assessments.count()
        average_result = all_assessments.aggregate(Avg('overall_score'))
        hotel_average_score = average_result['overall_score__avg']
    
    # Obtener información detallada de la última evaluación
    assessment_details = None
    category_scores = None
    scoring_summary = None
    category_trends = None
    category_risk_levels = None
    
    if latest_assessment:
        # Obtener detalles completos de cálculos
        assessment_details = latest_assessment.get_detailed_scoring_report()
        
        # Obtener resumen de puntuaciones (guardadas o calculadas)
        scoring_summary = latest_assessment.get_scoring_summary()
        
        # Obtener puntajes por categoría para gráficos
        category_scores = latest_assessment.get_saved_category_scores()
        if not category_scores:
            # Si no hay puntajes guardados, calcular en tiempo real
            category_scores = latest_assessment.get_all_category_scores()
        
        # Obtener tendencias históricas por categoría (solo datos reales para validación)
        category_trends = latest_assessment.get_category_trends(months_back=6, include_test_data=False)
        
        # Calcular niveles de riesgo por categoría
        category_risk_levels = {}
        for category in latest_assessment.selected_categories.all():
            category_risk_levels[category.code] = latest_assessment.get_category_risk_level(category)
    
    # Histórico de evaluaciones - sin duplicados
    assessments_history = SecurityAssessment.objects.filter(
        hotel=hotel
    ).distinct().order_by('-assessment_date')[:10]
    
    # Convertir a lista para permitir indexación
    assessments_list = list(assessments_history)
    
    # Obtener primera y última evaluación de forma segura
    first_assessment = None
    if len(assessments_list) > 1:
        # Obtener la primera evaluación (más antigua) ordenando por fecha ascendente y luego por ID
        first_assessment = SecurityAssessment.objects.filter(
            hotel=hotel,
            status='completed'  # Solo evaluaciones completadas
        ).order_by('assessment_date', 'id').first()
        
        # También actualizar latest_assessment para asegurar consistencia
        latest_assessment = SecurityAssessment.objects.filter(
            hotel=hotel,
            status='completed'  # Solo evaluaciones completadas
        ).order_by('-assessment_date', '-id').first()
    
    # Procesar información de categoría del hotel
    category_rating = 0
    category_label = "Sin categoría"
    
    # Calcular promedios por categoría de evaluación para análisis IA
    category_averages = {}
    top_5_critical_categories = []
    ai_critical_recommendations = {}  # Inicializar aquí para evitar UnboundLocalError
    
    if assessments_list:
        # Obtener todas las categorías evaluadas en las evaluaciones del hotel
        category_scores_all = SecurityCategoryScore.objects.filter(
            assessment__hotel=hotel
        ).values('category__name', 'category__code').annotate(
            avg_score=Avg('average_score')
        ).order_by('category__name')
        
        for item in category_scores_all:
            avg_score = item['avg_score'] or 0  # Protección contra None
            category_averages[item['category__code']] = {
                'name': item['category__name'],
                'code': item['category__code'],
                'average_score': avg_score,
                'percentage': round((avg_score / 5.0) * 100, 1) if avg_score else 0
            }
        
        # Obtener las 5 categorías más críticas (menor puntuación)
        critical_categories = sorted(
            category_averages.items(),
            key=lambda x: x[1]['percentage']
        )[:5]
        
        top_5_critical_categories = [
            {
                'name': category[1]['name'],
                'code': category[1]['code'],
                'percentage': category[1]['percentage'] or 0,
                'average_score': category[1]['average_score'] or 0
            }
            for category in critical_categories
        ]
        
        # Generar recomendaciones de IA para categorías críticas
        if top_5_critical_categories:
            ai_system = HotelSecurityAIRecommendations()
            ai_critical_recommendations = ai_system.generate_critical_categories_recommendations(top_5_critical_categories)

    if hotel.category:
        # Mapear las categorías a ratings numéricos
        category_map = {
            '1_star': 1,
            '2_star': 2,
            '3_star': 3,
            '4_star': 4,
            '5_star': 5,
            'luxury': 5,
        }
        category_rating = category_map.get(hotel.category, 0)
        category_label = dict(hotel.CATEGORY_CHOICES).get(hotel.category, hotel.category)
    
    context = {
        'hotel': hotel,
        'latest_assessment': latest_assessment,
        'hotel_average_score': hotel_average_score,
        'total_assessments_count': total_assessments_count,
        'category_averages': category_averages,
        'top_5_critical_categories': top_5_critical_categories,
        'ai_critical_recommendations': ai_critical_recommendations,
        'assessment_details': assessment_details,
        'scoring_summary': scoring_summary,
        'category_scores': category_scores,
        'category_trends': category_trends,
        'category_risk_levels': category_risk_levels,
        'assessments_history': assessments_list,
        'first_assessment': first_assessment,
        'category_rating': category_rating,
        'category_label': category_label,
    }
    
    return render(request, 'risk_hoteles/hotel_detail.html', context)


@login_required
@subscription_required('risk_hoteles')
def assessment_detail(request, assessment_id):
    """
    Detalle completo de una evaluación de seguridad con cálculos
    """
    assessment = get_object_or_404(get_user_assessments(request.user), id=assessment_id)
    
    # Verificar propiedad de la evaluación
    ensure_assessment_ownership(request.user, assessment)
    
    # Obtener reporte detallado con todos los cálculos
    detailed_report = assessment.get_detailed_scoring_report()
    
    # Obtener resumen de puntuaciones
    scoring_summary = assessment.get_scoring_summary()
    
    # Obtener puntajes guardados por categoría
    saved_scores = assessment.get_saved_category_scores()
    
    # Preparar datos para gráficos - SOLO DATOS REALES Y VÁLIDOS
    chart_data = {
        'categories': [],
        'percentages': [],
        'colors': []
    }
    
    # Validar que hay categorías con datos reales
    valid_categories = 0
    for category_code, score_data in detailed_report['categories'].items():
        # Validaciones estrictas para datos reales
        question_count = score_data.get('question_count', 0)
        percentage = score_data.get('percentage', 0)
        
        # Solo incluir si tiene preguntas respondidas y porcentaje válido
        if (question_count > 0 and 
            isinstance(percentage, (int, float)) and 
            0 <= percentage <= 100):
            
            # Usar 'category_name' o 'name' como fallback
            category_name = score_data.get('category_name') or score_data.get('name')
            
            # Solo agregar si tiene nombre válido
            if category_name and category_name.strip():
                chart_data['categories'].append(category_name.strip())
                chart_data['percentages'].append(round(float(percentage), 2))
                
                # Asignar colores según el porcentaje
                if percentage >= 80:
                    chart_data['colors'].append('#28a745')  # Verde
                elif percentage >= 60:
                    chart_data['colors'].append('#ffc107')  # Amarillo
                elif percentage >= 40:
                    chart_data['colors'].append('#fd7e14')  # Naranja
                else:
                    chart_data['colors'].append('#dc3545')  # Rojo
                
                valid_categories += 1
    
    # Si no hay datos válidos, limpiar chart_data
    if valid_categories == 0:
        chart_data = {
            'categories': [],
            'percentages': [],
            'colors': []
        }
    
    # ==========================================
    # SISTEMA DE IA PARA RECOMENDACIONES
    # ==========================================
    
    # Preparar datos para análisis de IA
    ai_assessment_data = {
        'categories': {},
        'overall_score': scoring_summary.get('overall_score_percentage', 0),
        'hotel_info': {
            'name': assessment.hotel.name,
            'city': assessment.hotel.city,
            'country': assessment.hotel.country
        },
        'responses': []
    }
    
    # Recopilar datos de categorías con comentarios
    for category_code, score_data in detailed_report['categories'].items():
        if score_data.get('question_count', 0) > 0:
            # Obtener comentarios de la categoría
            category_comments = SecurityCategoryComment.objects.filter(
                assessment=assessment,
                category__code=category_code
            ).values('comments', 'created_at')
            
            ai_assessment_data['categories'][category_code] = {
                'percentage': score_data['percentage'],
                'question_count': score_data['question_count'],
                'category_name': score_data.get('category_name') or score_data.get('name', 'Categoría sin nombre'),
                'comments': list(category_comments),
                'score_sum': score_data.get('score_sum', 0),
                'average': score_data.get('average', 0)
            }
    
    # Obtener respuestas para análisis adicional
    responses_data = assessment.responses.select_related('question', 'question__category').values(
        'question__question_text', 'question__category__name', 'rating', 'comments'
    )
    ai_assessment_data['responses'] = list(responses_data)
    
    # Generar recomendaciones con IA
    ai_system = HotelSecurityAIRecommendations()
    ai_analysis = ai_system.analyze_assessment_data(ai_assessment_data)
    
    # Combinar recomendaciones tradicionales con IA
    traditional_recommendations = []
    for category_code, score_data in detailed_report['categories'].items():
        if score_data.get('question_count', 0) > 0:
            percentage = score_data['percentage']
            # Usar 'category_name' o 'name' como fallback
            category_name = score_data.get('category_name') or score_data.get('name', 'Categoría sin nombre')
            
            if percentage < 40:
                traditional_recommendations.append({
                    'level': 'critical',
                    'category': category_name,
                    'message': f'Requiere atención inmediata en {category_name.lower()}',
                    'color': 'danger',
                    'type': 'traditional'
                })
            elif percentage < 60:
                traditional_recommendations.append({
                    'level': 'important',
                    'category': category_name,
                    'message': f'Mejoras necesarias en {category_name.lower()}',
                    'color': 'warning',
                    'type': 'traditional'
                })
            elif percentage < 80:
                traditional_recommendations.append({
                    'level': 'moderate',
                    'category': category_name,
                    'message': f'Revisar procesos de {category_name.lower()}',
                    'color': 'info',
                    'type': 'traditional'
                })
    
    # Combinar recomendaciones tradicionales con IA
    all_recommendations = traditional_recommendations + ai_analysis.get('ai_recommendations', [])
    
    # Contar áreas fuertes (≥80%) y críticas (<50%)
    strong_count = sum(
        1 for data in detailed_report['categories'].values()
        if data.get('percentage', 0) >= 80 and data.get('question_count', 0) > 0
    )
    weak_count = sum(
        1 for data in detailed_report['categories'].values()
        if data.get('percentage', 0) < 50 and data.get('question_count', 0) > 0
    )
    
    context = {
        'assessment': assessment,
        'detailed_report': detailed_report,
        'scoring_summary': scoring_summary,
        'saved_scores': saved_scores,
        'chart_data': chart_data,
        'recommendations': all_recommendations,
        'ai_analysis': ai_analysis,
        'traditional_recommendations': traditional_recommendations,
        'ai_recommendations': ai_analysis.get('ai_recommendations', []),
        'hotel': assessment.hotel,
        'strong_count': strong_count,
        'weak_count': weak_count,
    }
    
    return render(request, 'risk_hoteles/assessment_detail.html', context)


@login_required
@plan_level_required('risk_hoteles', 'pro')
def export_data(request):
    """
    Exportación de datos - requiere plan Pro o superior
    """
    messages.info(request, 'La exportación de datos no está disponible en este momento.')
    return redirect('risk_hoteles:dashboard')


@login_required
def create_analysis_redirect(request):
    """
    Redirige a la lista de hoteles para seleccionar uno para análisis
    """
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    
    # Obtener hotel_id si se pasó como parámetro
    hotel_id = request.GET.get('hotel_id')
    
    if hotel_id:
        # Si se especifica un hotel, redirigir directamente al análisis
        return HttpResponseRedirect(reverse('risk_hoteles:create_analysis', kwargs={'hotel_id': hotel_id}))
    else:
        # Si no, redirigir a la lista de hoteles
        return HttpResponseRedirect(reverse('risk_hoteles:hotel_list') + '?action=create_analysis')

@login_required
@usage_limit_check('risk_hoteles', 'reports')
def create_analysis(request, hotel_id):
    """
    Crear nueva evaluación de seguridad - verifica límites de uso
    """
    from .models import SecurityCategory, SecurityAssessment
    
    hotel = get_hotel_or_404(request.user, hotel_id)
    security_categories = SecurityCategory.objects.filter(is_active=True).order_by('order')
    
    # Verificar si el usuario ya tiene evaluaciones en progreso PARA ESTE HOTEL específico
    tiene_evaluaciones_progreso, evaluaciones_progreso = has_assessments_in_progress(request.user, hotel)
    
    if tiene_evaluaciones_progreso:
        # Si hay evaluaciones en progreso para este hotel específico, no permitir crear nueva
        mensaje_error = get_assessment_in_progress_message(request.user, hotel)
        messages.error(request, mensaje_error)
        
        # Redirigir a la evaluación en progreso existente para este hotel
        evaluacion_activa = evaluaciones_progreso.first()
        return redirect('risk_hoteles:assessment_survey', assessment_id=evaluacion_activa.id)
    
    if request.method == 'POST':
        try:
            # Obtener y sanitizar datos del formulario
            assessment_type = request.POST.get('analysis_type')
            assessment_date = request.POST.get('analysis_date')
            description = _sanitize_text_input(request.POST.get('description', ''), max_length=1000)
            selected_categories = request.POST.getlist('categories')
            observations = _sanitize_text_input(request.POST.get('observations', ''), max_length=2000)
            recommendations = _sanitize_text_input(request.POST.get('recommendations', ''), max_length=2000)
            
            # Validaciones
            if not assessment_type or not assessment_date:
                messages.error(request, 'Por favor, complete toda la información requerida.')
                return render(request, 'risk_hoteles/create_analysis.html', {
                    'hotel': hotel,
                    'security_categories': security_categories,
                    'today': timezone.now().date()
                })
            
            if not selected_categories:
                messages.error(request, 'Por favor, seleccione al menos una categoría de seguridad.')
                return render(request, 'risk_hoteles/create_analysis.html', {
                    'hotel': hotel,
                    'security_categories': security_categories,
                    'today': timezone.now().date()
                })
            
            # Validación adicional: verificar nuevamente que no hay evaluaciones en progreso
            # (doble verificación por seguridad en caso de concurrencia)
            tiene_evaluaciones, _ = has_assessments_in_progress(request.user)
            
            if tiene_evaluaciones:
                mensaje_error = get_assessment_in_progress_message(request.user)
                messages.error(request, f'Error: {mensaje_error}')
                return render(request, 'risk_hoteles/create_analysis.html', {
                    'hotel': hotel,
                    'security_categories': security_categories,
                    'today': timezone.now().date()
                })
            
            # Crear la evaluación en estado IN_PROGRESS inicialmente
            assessment = SecurityAssessment.objects.create(
                hotel=hotel,
                assessment_type=assessment_type,
                assessment_date=assessment_date,
                description=description,
                status='in_progress',  # Comenzar directamente en progreso
                observations=observations,
                recommendations=recommendations,
                created_by=request.user,
            )
            
            # Agregar categorías seleccionadas
            selected_category_objects = SecurityCategory.objects.filter(
                code__in=selected_categories,
                is_active=True
            )
            assessment.selected_categories.set(selected_category_objects)
            
            messages.success(request, f'Evaluación de seguridad creada exitosamente. Se evaluarán {len(selected_categories)} categorías.')
            
            # Redirigir a la página de cuestionario
            return redirect('risk_hoteles:assessment_survey', assessment_id=assessment.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear la evaluación: {str(e)}')
            return render(request, 'risk_hoteles/create_analysis.html', {
                'hotel': hotel,
                'security_categories': security_categories,
                'today': timezone.now().date()
            })
    
    # GET request - mostrar formulario
    _, evaluaciones_en_progreso = has_assessments_in_progress(request.user)
    
    context = {
        'hotel': hotel,
        'security_categories': security_categories,
        'today': timezone.now().date(),
        'evaluaciones_en_progreso': evaluaciones_en_progreso
    }
    return render(request, 'risk_hoteles/create_analysis.html', context)


@login_required
def assessment_survey(request, assessment_id):
    """
    Mostrar y procesar el cuestionario de evaluación por categorías
    """
    from .models import SecurityAssessment, SecurityQuestion, SecurityResponse
    import logging
    
    # Configurar logging para debugging
    logger = logging.getLogger(__name__)
    
    assessment = get_assessment_or_404(request.user, assessment_id)
    
    if request.method == 'POST':
        # Verificar si es un guardado de progreso (antes era borrador)
        is_draft = (request.POST.get('save_as_draft', 'false') == 'true' or 
                   request.POST.get('save_progress', 'false') == 'true')
        
        # Logging controlado - solo en modo DEBUG o para errores críticos
        from django.conf import settings
        if settings.DEBUG:
            logger.debug(f"Processing assessment survey for {assessment_id}")
            logger.debug(f"Is progress save request: {is_draft}")
        
        # Si es una petición AJAX para guardado de progreso, responder con JSON
        if is_draft and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.db import transaction
            import sqlite3
            import time
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    with transaction.atomic():
                        responses_saved = 0
                        
                        # Procesar respuestas sin validación estricta para guardado de progreso
                        for key, value in request.POST.items():
                            if key.startswith('question_'):
                                question_id = key.replace('question_', '')
                                try:
                                    question = SecurityQuestion.objects.get(id=question_id)
                                    
                                    # Solo guardar si hay valor (permitir respuestas parciales)
                                    if value and value.strip():
                                        not_applicable = (value == 'na')
                                        rating_value = None if not_applicable else (int(value) if value.isdigit() else None)
                                        
                                        # Obtener comentarios
                                        comment_key = f'comment_{question_id}'
                                        comments = request.POST.get(comment_key, '')
                                        
                                        # Crear o actualizar respuesta
                                        response, created = SecurityResponse.objects.get_or_create(
                                            assessment=assessment,
                                            question=question,
                                            defaults={
                                                'rating': rating_value,
                                                'not_applicable': not_applicable,
                                                'comments': comments
                                            }
                                        )
                                        
                                        if not created:
                                            response.rating = rating_value
                                            response.not_applicable = not_applicable
                                            response.comments = comments
                                            response.save()
                                        
                                        responses_saved += 1
                                        
                                except (SecurityQuestion.DoesNotExist, ValueError):
                                    continue
                        
                        # Procesar comentarios por categoría
                        from .models import SecurityCategoryComment, SecurityCategory
                        for key, value in request.POST.items():
                            if key.startswith('category_comment_'):
                                category_id = key.replace('category_comment_', '')
                                try:
                                    category = SecurityCategory.objects.get(id=category_id)
                                    if value.strip():
                                        comment, created = SecurityCategoryComment.objects.get_or_create(
                                            assessment=assessment,
                                            category=category,
                                            defaults={'comments': value.strip()}
                                        )
                                        if not created:
                                            comment.comments = value.strip()
                                            comment.save()
                                except SecurityCategory.DoesNotExist:
                                    continue
                        
                        # Procesar observaciones y recomendaciones finales
                        observations = request.POST.get('assessment_observations', '').strip()
                        recommendations = request.POST.get('assessment_recommendations', '').strip()
                        
                        if observations or recommendations:
                            if observations:
                                assessment.observations = observations[:3000]  # Limitar longitud
                            if recommendations:
                                assessment.recommendations = recommendations[:3000]  # Limitar longitud
                            
                            # Guardar solo si hay cambios
                            assessment.save(update_fields=['observations', 'recommendations', 'updated_at'])
                            logger.info(f"Saved draft observations and recommendations for assessment {assessment.id}")
                        
                        # Cambiar estado a "in_progress" cuando se guarda el progreso
                        assessment.start_assessment()  # Usar método específico del modelo
                        # Si ya está en "in_progress", mantenerlo así
                        
                        return JsonResponse({
                            'success': True,
                            'message': f'Progreso guardado: {responses_saved} respuestas.',
                            'responses_saved': responses_saved
                        })
                        
                except Exception as e:
                    # Check if it's a database lock error
                    if ('database is locked' in str(e).lower() or 
                        'database lock' in str(e).lower() or
                        'operationerror' in str(e.__class__.__name__).lower()):
                        
                        retry_count += 1
                        if retry_count < max_retries:
                            # Exponential backoff: 0.5s, 1s, 2s
                            wait_time = 0.5 * (2 ** (retry_count - 1))
                            logger.warning(f"Database lock detected, retrying in {wait_time}s (attempt {retry_count}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"Database lock persisted after {max_retries} attempts for assessment {assessment_id}")
                            return JsonResponse({
                                'success': False,
                                'error': 'database is locked - Database is temporarily busy. Please try again in a moment.'
                            })
                    else:
                        # For other errors, don't retry
                        logger.error(f"Error saving draft assessment {assessment_id}: {str(e)}")
                        return JsonResponse({
                            'success': False,
                            'error': str(e)
                        })
            
            # If we get here, all retries failed
            return JsonResponse({
                'success': False,
                'error': 'database is locked - Database is temporarily busy after multiple attempts. Please try again.'
            })
        
        try:
            # Validar preguntas obligatorias antes de procesar con lógica más robusta
            validation_errors = _validate_required_questions(assessment, request.POST)
            
            if validation_errors:
                error_msg = f"Por favor responde todas las preguntas obligatorias. Faltan {len(validation_errors)} pregunta(s)."
                messages.error(request, error_msg)
                from django.conf import settings
                if settings.DEBUG:
                    logger.warning(f"Missing required questions: {len(validation_errors)}")
                # NO procesar ni guardar nada - mostrar página con errores
                pass  # Saltar el procesamiento y mostrar la página GET
            # SOLO procesar respuestas si NO hay preguntas obligatorias faltantes
            else:
                # SOLO procesar respuestas si NO hay preguntas obligatorias faltantes
                responses_saved = 0
                
                for key, value in request.POST.items():
                    if key.startswith('question_'):
                        question_id = key.replace('question_', '')
                        try:
                            question = SecurityQuestion.objects.get(id=question_id)
                            
                            # Verificar si es "no aplica" (valor "na" en el select)
                            not_applicable = (value == 'na')
                            
                            # Obtener comentarios y sanitizarlos
                            comment_key = f'comment_{question_id}'
                            raw_comments = request.POST.get(comment_key, '')
                            comments = _sanitize_text_input(raw_comments, max_length=1000)
                            
                            # Determinar el rating
                            if not_applicable:
                                rating_value = None
                            elif value and value != 'na' and value != '':
                                try:
                                    rating_value = int(value)
                                except ValueError:
                                    rating_value = None
                                    if settings.DEBUG:
                                        logger.warning(f"Invalid rating value for Q{question_id}: '{value}'")
                            else:
                                rating_value = None
                            
                            # Crear o actualizar respuesta
                            response, created = SecurityResponse.objects.get_or_create(
                                assessment=assessment,
                                question=question,
                                defaults={
                                    'rating': rating_value,
                                    'not_applicable': not_applicable,
                                    'comments': comments
                                }
                            )
                            
                            if not created:
                                response.rating = rating_value
                                response.not_applicable = not_applicable
                                response.comments = comments
                                response.save()
                            
                            responses_saved += 1
                            
                        except (SecurityQuestion.DoesNotExist, ValueError) as e:
                            if settings.DEBUG:
                                logger.warning(f"Error processing question {question_id}: {str(e)}")
                            continue
                
                # Procesar comentarios por categoría (solo si el envío es válido)
                from .models import SecurityCategoryComment, SecurityCategory
                
                for key, value in request.POST.items():
                    if key.startswith('category_comment_'):
                        category_id = key.replace('category_comment_', '')
                        try:
                            category = SecurityCategory.objects.get(id=category_id)
                            
                            # Sanitizar comentario de categoría
                            sanitized_comment = _sanitize_text_input(value, max_length=2000)
                            
                            if sanitized_comment:  # Solo guardar si hay contenido después de sanitizar
                                comment, created = SecurityCategoryComment.objects.get_or_create(
                                    assessment=assessment,
                                    category=category,
                                    defaults={'comments': sanitized_comment}
                                )
                                
                                if not created and comment.comments != sanitized_comment:
                                    comment.comments = sanitized_comment
                                    comment.save()
                            
                        except SecurityCategory.DoesNotExist:
                            continue
                
                # Procesar observaciones y recomendaciones finales
                observations = request.POST.get('assessment_observations', '').strip()
                recommendations = request.POST.get('assessment_recommendations', '').strip()
                
                if observations or recommendations:
                    # Sanitizar y actualizar en el modelo de Assessment
                    if observations:
                        assessment.observations = _sanitize_text_input(observations, max_length=3000)
                    if recommendations:
                        assessment.recommendations = _sanitize_text_input(recommendations, max_length=3000)
                    
                    # Guardar los cambios en observaciones y recomendaciones
                    assessment.save(update_fields=['observations', 'recommendations', 'updated_at'])
                    logger.info(f"Updated final observations and recommendations for assessment {assessment.id}")
                
                # Actualizar estado de la evaluación (solo si el envío es válido)
                if responses_saved > 0:
                    # Manejar completar la evaluación o actualizar una existente
                    success = False
                    
                    # Completar la evaluación si está en progreso
                    if assessment.status == 'in_progress':
                        if assessment.complete_assessment():
                            logger.info(f"Assessment {assessment.id} completed successfully")
                            success = True
                        else:
                            logger.error(f"Failed to complete assessment {assessment.id}. Current status: {assessment.status}")
                            messages.warning(request, f'Error al completar la evaluación. Estado actual: {assessment.get_status_display()}')
                    elif assessment.status == 'completed':
                        # Si ya está completada, solo actualizar puntuaciones y continuar
                        try:
                            assessment.save_calculated_scores()
                            logger.info(f"Assessment {assessment.id} updated successfully (was already completed)")
                            success = True
                        except Exception as e:
                            logger.error(f"Error updating completed assessment {assessment.id}: {str(e)}")
                            messages.warning(request, f'Error al actualizar la evaluación: {str(e)}')
                    else:
                        logger.warning(f"Assessment {assessment.id} is in unexpected status: {assessment.status}")
                        messages.warning(request, f'Estado de evaluación inesperado: {assessment.get_status_display()}')
                    
                    if success:
                        messages.success(request, f'Evaluación {"actualizada" if assessment.status == "completed" else "completada"} exitosamente. {responses_saved} respuestas guardadas.')
                        return redirect('risk_hoteles:assessment_results', assessment_id=assessment.id)
                        
                else:
                    messages.warning(request, 'No se encontraron respuestas válidas para guardar.')
                
        except Exception as e:
            messages.error(request, f'Error al procesar las respuestas: {str(e)}')
    
    # OPTIMIZACIÓN: Obtener preguntas por categoría con una sola consulta optimizada
    # Usar prefetch_related para evitar N+1 queries
    assessment = SecurityAssessment.objects.select_related(
        'hotel', 
        'created_by'
    ).prefetch_related(
        'selected_categories',
        'selected_categories__questions',
        'responses__question',
        'responses__question__category'
    ).get(id=assessment.id)
    
    # OPTIMIZACIÓN: Obtener todos los comentarios de categoría de una vez
    from .models import SecurityCategoryComment
    category_comments = {
        comment.category.id: comment.comments
        for comment in SecurityCategoryComment.objects.filter(
            assessment=assessment
        ).select_related('category')
    }
    
    categories_with_questions = []
    for category in assessment.selected_categories.all():
        # Las preguntas ya están pre-cargadas por prefetch_related
        questions = [q for q in category.questions.all() if q.is_active]
        questions.sort(key=lambda x: x.order)
        
        if questions:
            # Las respuestas ya están pre-cargadas
            existing_responses = {
                resp.question.id: resp 
                for resp in assessment.responses.all()
                if resp.question.category.id == category.id
            }
            
            # Comentario de categoría ya pre-cargado
            existing_category_comment = category_comments.get(category.id, '')
            
            categories_with_questions.append({
                'category': category,
                'questions': questions,
                'existing_responses': existing_responses,
                'existing_category_comment': existing_category_comment
            })
    
    # Contar preguntas totales
    total_questions = sum(len(cat['questions']) for cat in categories_with_questions)
    
    # Obtener evidencias existentes
    existing_evidence = AssessmentEvidence.objects.filter(
        assessment=assessment
    ).order_by('uploaded_at')
    
    context = {
        'assessment': assessment,
        'categories_with_questions': categories_with_questions,
        'total_questions': total_questions,
        'rating_choices': SecurityResponse.RATING_CHOICES,
        'existing_evidence': existing_evidence,
    }
    
    return render(request, 'risk_hoteles/assessment_survey.html', context)


@login_required
@require_http_methods(["POST"])
def upload_evidence_image(request, assessment_id):
    """
    Vista para subir imágenes de evidencia de manera asíncrona
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        assessment = get_assessment_or_404(request.user, assessment_id)
        
        if 'image' not in request.FILES:
            logger.warning(f"No image file in request for assessment {assessment_id}")
            return JsonResponse({'error': 'No se encontró archivo de imagen'}, status=400)
        
        image_file = request.FILES['image']
        logger.info(f"Processing image upload: {image_file.name}, size: {image_file.size}, type: {image_file.content_type}")
        
        # Validar tipo de archivo
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            logger.warning(f"Invalid content type: {image_file.content_type}")
            return JsonResponse({'error': 'Tipo de archivo no permitido. Solo se permiten JPG, PNG y WEBP'}, status=400)
        
        # Validar tamaño (5MB máximo)
        max_size = 5 * 1024 * 1024  # 5MB
        if image_file.size > max_size:
            logger.warning(f"File too large: {image_file.size} bytes")
            return JsonResponse({'error': 'El archivo es demasiado grande. Tamaño máximo: 5MB'}, status=400)
        
        # Verificar límite de imágenes por evaluación
        current_count = AssessmentEvidence.objects.filter(assessment=assessment).count()
        if current_count >= 10:
            logger.warning(f"Too many images for assessment {assessment_id}: {current_count}")
            return JsonResponse({'error': 'Se ha alcanzado el límite máximo de 10 imágenes por evaluación'}, status=400)
        
        try:
            # Crear nueva evidencia
            evidence = AssessmentEvidence.objects.create(
                assessment=assessment,
                image=image_file,
                original_name=image_file.name,
                file_size=image_file.size,
                content_type=image_file.content_type,
                uploaded_by=request.user,
                description=request.POST.get('description', '')
            )
            
            logger.info(f"Image uploaded successfully: {evidence.id}")
            
            return JsonResponse({
                'success': True,
                'evidence_id': str(evidence.id),
                'image_url': evidence.image.url,
                'original_name': evidence.original_name,
                'file_size': evidence.file_size
            })
            
        except Exception as e:
            logger.error(f"Error creating AssessmentEvidence: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Error al guardar la imagen: {str(e)}'}, status=500)
            
    except Exception as e:
        logger.error(f"Unexpected error in upload_evidence_image: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_evidence_image(request, assessment_id, evidence_id):
    """
    Vista para eliminar una imagen de evidencia
    """
    assessment = get_assessment_or_404(request.user, assessment_id)
    
    evidence = get_object_or_404(
        AssessmentEvidence,
        id=evidence_id,
        assessment=assessment
    )
    
    try:
        # Eliminar archivo físico si existe
        if evidence.image:
            evidence.image.delete(save=False)
        
        # Eliminar registro de la base de datos
        evidence.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': f'Error al eliminar la imagen: {str(e)}'}, status=500)


@login_required
def get_evidence_images(request, assessment_id):
    """
    Vista para obtener las imágenes de evidencia existentes
    """
    assessment = get_assessment_or_404(request.user, assessment_id)
    
    evidence_images = AssessmentEvidence.objects.filter(
        assessment=assessment
    ).order_by('uploaded_at')
    
    images_data = []
    for evidence in evidence_images:
        images_data.append({
            'id': str(evidence.id),
            'image_url': evidence.image.url,
            'original_name': evidence.original_name,
            'file_size': evidence.file_size,
            'description': evidence.description,
            'uploaded_at': evidence.uploaded_at.isoformat()
        })
    
    return JsonResponse({
        'images': images_data,
        'count': len(images_data)
    })



@login_required  
def assessment_results(request, assessment_id):
    """
    Mostrar los resultados de la evaluación completada
    """
    from .models import SecurityAssessment
    
    assessment = get_assessment_or_404(request.user, assessment_id)
    
    # Obtener puntuaciones por categoría (escala 0-5 para compatibilidad)
    category_scores = assessment.get_category_scores()
    
    # Obtener datos detallados por categoría (incluye porcentajes)
    category_details = assessment.get_all_category_scores()
    
    # Calcular promedio general
    overall_score = assessment.calculate_overall_score()
    overall_score_out_of_5 = None
    risk_level = 'medio'
    
    if overall_score and overall_score > 0:
        overall_score_out_of_5 = (overall_score / 100) * 5  # Convertir porcentaje a escala de 5
        
        # Determinar nivel de riesgo basado en el promedio general
        if overall_score >= 85:
            risk_level = 'muy_bajo'
        elif overall_score >= 70:
            risk_level = 'bajo'
        elif overall_score >= 55:
            risk_level = 'medio'
        elif overall_score >= 40:
            risk_level = 'alto'
        else:
            risk_level = 'muy_alto'
    
    # Obtener estadísticas de respuestas
    total_questions = sum(
        cat.questions.filter(is_active=True).count() 
        for cat in assessment.selected_categories.all()
    )
    
    answered_questions = assessment.responses.filter(
        Q(rating__isnull=False) | Q(not_applicable=True)
    ).count()
    
    completion_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0
    
    context = {
        'assessment': assessment,
        'category_scores': category_scores,
        'category_details': category_details,
        'overall_score': overall_score_out_of_5,
        'overall_percentage': overall_score,
        'risk_level': risk_level,
        'total_questions': total_questions,
        'answered_questions': answered_questions,
        'completion_percentage': completion_percentage,
    }
    
    return render(request, 'risk_hoteles/assessment_results.html', context)


@api_subscription_required('risk_hoteles')
def api_hotels_list(request):
    """
    API endpoint para obtener lista de hoteles
    """
    hotels = get_user_hotels(request.user).filter(is_active=True)
    
    hotels_data = []
    for hotel in hotels:
        hotels_data.append({
            'id': str(hotel.id),
            'name': hotel.name,
            'city': hotel.city,
            'country': hotel.country,
            'category': hotel.category,
            'total_rooms': hotel.total_rooms,
            'created_at': hotel.created_at.isoformat(),
        })
    
    return JsonResponse({
        'status': 'success',
        'data': hotels_data,
        'count': len(hotels_data),
    })


@login_required
@subscription_required('risk_hoteles')
@evaluador_permission_required('risk_hoteles', 'create')
@require_http_methods(["POST"])
def create_hotel_ajax(request):
    """
    Vista AJAX para crear un nuevo hotel
    """
    try:
        # Verificar que los datos requeridos estén presentes
        required_fields = ['name', 'category', 'total_rooms', 'address', 'city', 'country']
        missing_fields = [field for field in required_fields if not request.POST.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False,
                'message': f'Campos obligatorios faltantes: {", ".join(missing_fields)}'
            })
        
        # Validar número de habitaciones
        try:
            total_rooms = int(request.POST.get('total_rooms'))
            if total_rooms < 1:
                raise ValueError("Debe ser mayor a 0")
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'El número de habitaciones debe ser un número válido mayor a 0'
            })
        
        # Validar categoría
        valid_categories = [choice[0] for choice in Hotel._meta.get_field('category').choices]
        category = request.POST.get('category')
        if category not in valid_categories:
            return JsonResponse({
                'success': False,
                'message': 'Categoría de hotel no válida'
            })
        
        # Validar email si se proporciona
        email = request.POST.get('email', '').strip()
        if email:
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de email no válido'
                })
        
        # Validar website si se proporciona
        website = request.POST.get('website', '').strip()
        if website:
            from django.core.validators import URLValidator
            try:
                url_validator = URLValidator()
                url_validator(website)
            except ValidationError:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de URL no válido'
                })
        
        # Determinar el propietario del hotel: si es evaluador, asignar al usuario principal
        from apps.evaluadores.models import Evaluador as EvaluadorModel
        try:
            evaluador_obj = EvaluadorModel.objects.select_related('usuario_principal').get(
                usuario_evaluador=request.user
            )
            hotel_owner = evaluador_obj.usuario_principal
        except EvaluadorModel.DoesNotExist:
            hotel_owner = request.user

        # Crear el hotel con datos sanitizados
        hotel = Hotel.objects.create(
            name=_sanitize_text_input(request.POST.get('name'), max_length=255),
            address=_sanitize_text_input(request.POST.get('address'), max_length=500),
            city=_sanitize_text_input(request.POST.get('city'), max_length=100),
            country=_sanitize_text_input(request.POST.get('country'), max_length=100),
            category=category,
            total_rooms=total_rooms,
            phone=_sanitize_text_input(request.POST.get('phone', ''), max_length=20),
            email=email,
            website=website,
            owner=hotel_owner,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Hotel "{hotel.name}" creado exitosamente',
            'hotel': {
                'id': str(hotel.id),
                'name': hotel.name,
                'city': hotel.city,
                'country': hotel.country,
                'category': hotel.get_category_display(),
                'total_rooms': hotel.total_rooms,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al crear el hotel: {str(e)}'
        })


@login_required
@subscription_required('risk_hoteles')
def get_hotel_data(request, hotel_id):
    """
    Obtener datos de un hotel para edición
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    try:
        hotel = get_hotel_or_404(request.user, hotel_id, is_active=True)
        
        return JsonResponse({
            'success': True,
            'hotel': {
                'id': str(hotel.id),
                'name': hotel.name,
                'address': hotel.address,
                'city': hotel.city,
                'country': hotel.country,
                'category': hotel.category,
                'total_rooms': hotel.total_rooms,
                'phone': hotel.phone or '',
                'email': hotel.email or '',
                'website': hotel.website or '',
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener datos del hotel: {str(e)}'
        })


@login_required
@subscription_required('risk_hoteles')
@evaluador_permission_required('risk_hoteles', 'update')
def update_hotel_ajax(request):
    """
    Actualizar un hotel existente vía AJAX
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    try:
        hotel_id = request.POST.get('hotel_id')
        if not hotel_id:
            return JsonResponse({
                'success': False,
                'message': 'ID de hotel requerido'
            })
        
        hotel = get_hotel_or_404(request.user, hotel_id, is_active=True)
        
        # Validar campos requeridos
        required_fields = ['name', 'address', 'city', 'country', 'category', 'total_rooms']
        for field in required_fields:
            if not request.POST.get(field, '').strip():
                return JsonResponse({
                    'success': False,
                    'message': f'El campo {field} es requerido'
                })
        
        # Validar número de habitaciones
        try:
            total_rooms = int(request.POST.get('total_rooms'))
            if total_rooms <= 0:
                raise ValueError("Debe ser mayor a 0")
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'El número de habitaciones debe ser un número entero positivo'
            })
        
        # Validar categoría
        category = request.POST.get('category')
        valid_categories = [choice[0] for choice in Hotel.CATEGORY_CHOICES]
        if category not in valid_categories:
            return JsonResponse({
                'success': False,
                'message': 'Categoría de hotel no válida'
            })
        
        # Actualizar el hotel
        hotel.name = request.POST.get('name').strip()
        hotel.address = request.POST.get('address').strip()
        hotel.city = request.POST.get('city').strip()
        hotel.country = request.POST.get('country').strip()
        hotel.category = category
        hotel.total_rooms = total_rooms
        hotel.phone = request.POST.get('phone', '').strip()
        hotel.email = request.POST.get('email', '').strip()
        hotel.website = request.POST.get('website', '').strip()
        hotel.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Hotel "{hotel.name}" actualizado exitosamente',
            'hotel': {
                'id': str(hotel.id),
                'name': hotel.name,
                'city': hotel.city,
                'country': hotel.country,
                'category': hotel.get_category_display(),
                'total_rooms': hotel.total_rooms,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al actualizar el hotel: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def discard_assessment(request, assessment_id):
    """
    Vista para descartar/eliminar una evaluación que no se desea conservar.
    Evita evaluaciones abandonadas en estado in_progress.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        assessment = get_object_or_404(SecurityAssessment, id=assessment_id, created_by=request.user)
        
        # Parse JSON data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        confirm_discard = data.get('confirm_discard', False)
        reason = data.get('reason', 'user_request')
        
        if not confirm_discard:
            return JsonResponse({
                'success': False,
                'error': 'Confirmación requerida para descartar evaluación'
            })
        
        # Solo permitir descarte de evaluaciones en progreso
        if assessment.status not in ['in_progress']:
            return JsonResponse({
                'success': False,
                'error': f'No se puede descartar una evaluación en estado "{assessment.get_status_display()}". Solo se pueden descartar evaluaciones en progreso.'
            })
        
        # Verificar que el usuario tenga permisos
        if assessment.created_by != request.user:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para descartar esta evaluación'
            })
        
        # Obtener información antes de eliminar
        hotel_id = assessment.hotel.id
        hotel_name = assessment.hotel.name
        responses_count = assessment.responses.count()
        
        # Log de la acción
        logger.info(f"Discarding assessment {assessment_id} by user {request.user.id}. "
                   f"Reason: {reason}, Responses: {responses_count}, Status: {assessment.status}")
        
        # Eliminar respuestas asociadas primero
        assessment.responses.all().delete()
        
        # Eliminar comentarios de categorías
        SecurityCategoryComment.objects.filter(assessment=assessment).delete()
        
        # Eliminar la evaluación
        assessment.delete()
        
        # Mensaje de éxito
        success_message = f'Evaluación eliminada exitosamente'
        if responses_count > 0:
            success_message += f' (se eliminaron {responses_count} respuestas)'
        
        # URL de redirección
        redirect_url = f'/risk-hoteles/hoteles/{hotel_id}/'
        
        logger.info(f"Assessment {assessment_id} successfully discarded. Redirecting to {redirect_url}")
        
        return JsonResponse({
            'success': True,
            'message': success_message,
            'redirect_url': redirect_url,
            'discarded_responses': responses_count,
            'hotel_name': hotel_name
        })
        
    except SecurityAssessment.DoesNotExist:
        logger.warning(f"Attempted to discard non-existent assessment {assessment_id} by user {request.user.id}")
        return JsonResponse({
            'success': False,
            'error': 'Evaluación no encontrada'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
        
    except Exception as e:
        logger.error(f"Error discarding assessment {assessment_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        })


@login_required
@subscription_required('risk_hoteles')
@evaluador_permission_required('risk_hoteles', 'delete')
@require_http_methods(["DELETE"])
def delete_hotel_ajax(request, hotel_id):
    """
    Eliminar un hotel vía AJAX - usa la misma lógica de filtrado que hotel_list
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Debug: Log de información básica
        logger.info(f"Intentando eliminar hotel {hotel_id} para usuario {request.user.id}")
        
        # Usar exactamente la misma lógica de filtrado que hotel_list
        # Esto asegura que solo se puedan eliminar hoteles que el usuario puede ver
        user_hotels = get_user_hotels(request.user)
        
        # Intentar obtener el hotel usando el mismo filtro que la vista de lista
        try:
            hotel = user_hotels.get(id=hotel_id)
        except Hotel.DoesNotExist:
            logger.warning(f"Hotel {hotel_id} no encontrado en los hoteles del usuario {request.user.id}")
            return JsonResponse({
                'success': False,
                'message': 'Hotel no encontrado o no tienes permisos para eliminarlo'
            })
        
        logger.info(f"Hotel encontrado: {hotel.name}, activo: {hotel.is_active}")
        
        # Verificar si hay evaluaciones asociadas
        assessments_count = SecurityAssessment.objects.filter(hotel=hotel).count()
        logger.info(f"Evaluaciones asociadas: {assessments_count}")
        
        if assessments_count > 0:
            # Si hay evaluaciones, realizar un soft delete
            hotel.is_active = False
            hotel.save()
            logger.info(f"Soft delete realizado para hotel {hotel.name}")
            
            return JsonResponse({
                'success': True,
                'message': f'Hotel "{hotel.name}" eliminado exitosamente. Se mantienen {assessments_count} evaluaciones asociadas.',
                'soft_delete': True
            })
        else:
            # Si no hay evaluaciones, eliminar completamente
            hotel_name = hotel.name
            hotel.delete()
            logger.info(f"Hard delete realizado para hotel {hotel_name}")
            
            return JsonResponse({
                'success': True,
                'message': f'Hotel "{hotel_name}" eliminado exitosamente.',
                'soft_delete': False
            })
        
    except Exception as e:
        logger.error(f"Error deleting hotel {hotel_id}: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar el hotel: {str(e)}'
        })

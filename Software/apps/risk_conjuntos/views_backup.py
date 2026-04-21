from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from apps.subscriptions.access_control import requires_risk_conjuntos
from apps.subscriptions.access_control import AccessControlMixin
from django.views.generic import TemplateView
import json
from datetime import datetime, timedelta

from .models import (
    Conjunto, TipoConjunto, EvaluacionSeguridad, 
    CategoriaSeguridad, PreguntaSeguridad, 
    RespuestaEvaluacion, ScoreCategoria
)
from .forms import (
    ConjuntoForm, EvaluacionSeguridadForm, 
    RespuestaEvaluacionForm, FiltroConjuntosForm,
    ReporteComparativoForm
)
from .modal_forms import ConjuntoModalForm


@login_required
@requires_risk_conjuntos()
def dashboard(request):
    """
    Dashboard principal del módulo Risk Conjuntos
    """
    user = request.user
    
    # Estadísticas principales
    conjuntos = Conjunto.objects.filter(propietario=user, activo=True)
    total_conjuntos = conjuntos.count()
    
    # Evaluaciones
    evaluaciones = EvaluacionSeguridad.objects.filter(conjunto__propietario=user)
    total_evaluaciones = evaluaciones.filter(estado='completada').count()
    
    # Evaluaciones este mes
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    evaluaciones_mes = evaluaciones.filter(
        estado='completada',
        fecha_evaluacion__gte=inicio_mes
    ).count()
    
    # Score promedio basado en evaluaciones completadas
    evaluaciones_completadas = evaluaciones.filter(
        estado='completada',
        score_total__isnull=False
    )
    score_promedio = 0
    if evaluaciones_completadas.exists():
        score_promedio = round(evaluaciones_completadas.aggregate(
            avg=Avg('score_total')
        )['avg'], 1)
    
    # Top 5 conjuntos por última evaluación
    conjuntos_con_evaluaciones = []
    for conjunto in conjuntos:
        ultima_evaluacion = conjunto.evaluaciones_seguridad.filter(
            estado='completada',
            score_total__isnull=False
        ).order_by('-fecha_evaluacion').first()
        if ultima_evaluacion:
            conjuntos_con_evaluaciones.append({
                'conjunto': conjunto,
                'score': ultima_evaluacion.score_total,
                'fecha': ultima_evaluacion.fecha_evaluacion
            })
    
    # Ordenar por score y tomar los 5 mejores
    top_conjuntos = sorted(
        conjuntos_con_evaluaciones, 
        key=lambda x: x['score'], 
        reverse=True
    )[:5]
    
    # Distribución por niveles de riesgo basada en última evaluación
    distribucion_riesgo = {
        'muy_bajo': 0, 'bajo': 0, 'medio': 0, 'alto': 0, 'critico': 0, 'sin_evaluar': 0
    }
    
    for conjunto in conjuntos:
        ultima_evaluacion = conjunto.evaluaciones_seguridad.filter(
            estado='completada',
            score_total__isnull=False
        ).order_by('-fecha_evaluacion').first()
        
        if ultima_evaluacion:
            score = float(ultima_evaluacion.score_total)
            if score >= 90:
                distribucion_riesgo['muy_bajo'] += 1
            elif score >= 80:
                distribucion_riesgo['bajo'] += 1
            elif score >= 70:
                distribucion_riesgo['medio'] += 1
            elif score >= 60:
                distribucion_riesgo['alto'] += 1
            else:
                distribucion_riesgo['critico'] += 1
        else:
            distribucion_riesgo['sin_evaluar'] += 1
    
    # Evaluaciones recientes
    evaluaciones_recientes = evaluaciones.filter(
        estado='completada'
    ).select_related('conjunto').order_by('-fecha_evaluacion')[:8]
    
    # Conjuntos sin evaluar
    conjuntos_sin_evaluar = distribucion_riesgo['sin_evaluar']
    
    # Alertas de riesgo alto (crítico)
    alertas_riesgo_alto = distribucion_riesgo['critico']
    
    context = {
        'total_conjuntos': total_conjuntos,
        'total_evaluaciones': total_evaluaciones,
        'evaluaciones_mes': evaluaciones_mes,
        'score_promedio': score_promedio,
        'top_conjuntos': top_conjuntos,
        'distribucion_riesgo': distribucion_riesgo,
        'evaluaciones_recientes': evaluaciones_recientes,
        'conjuntos_sin_evaluar': conjuntos_sin_evaluar,
        'alertas_riesgo_alto': alertas_riesgo_alto,
        'page_title': 'Dashboard - Risk Conjuntos'
    }
    
    return render(request, 'risk_conjuntos/dashboard.html', context)


@login_required
@requires_risk_conjuntos()
def lista_conjuntos(request):
    """
    Lista todos los conjuntos del usuario con filtros
    """
    conjuntos = Conjunto.objects.filter(
        propietario=request.user, 
        activo=True
    ).select_related('tipo_conjunto')
    
    # Aplicar filtros
    form = FiltroConjuntosForm(request.GET)
    if form.is_valid():
        busqueda = form.cleaned_data.get('busqueda')
        if busqueda:
            conjuntos = conjuntos.filter(
                Q(nombre__icontains=busqueda) |
                Q(ciudad__icontains=busqueda) |
                Q(administrador_nombre__icontains=busqueda)
            )
        
        tipo_conjunto = form.cleaned_data.get('tipo_conjunto')
        if tipo_conjunto:
            conjuntos = conjuntos.filter(tipo_conjunto=tipo_conjunto)
        
        ciudad = form.cleaned_data.get('ciudad')
        if ciudad:
            conjuntos = conjuntos.filter(ciudad__icontains=ciudad)
        
        tiene_evaluaciones = form.cleaned_data.get('tiene_evaluaciones')
        if tiene_evaluaciones == 'si':
            conjuntos = conjuntos.filter(evaluaciones_seguridad__estado='completada').distinct()
        elif tiene_evaluaciones == 'no':
            conjuntos = conjuntos.exclude(evaluaciones_seguridad__estado='completada')
    
    # Paginación
    paginator = Paginator(conjuntos, 12)  # 12 conjuntos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': form,
        'page_title': 'Mis Conjuntos - Risk Conjuntos'
    }
    
    return render(request, 'risk_conjuntos/lista_conjuntos.html', context)


@login_required
@requires_risk_conjuntos()
def crear_conjunto(request):
    """
    Crear un nuevo conjunto residencial - Redirige al modal
    """
    # Redirigir a la lista donde está el modal
    messages.info(request, 'Use el botón "Nuevo Conjunto" para crear un conjunto.')
    return redirect('risk_conjuntos:lista_conjuntos')


@login_required
@requires_risk_conjuntos()
def detalle_conjunto(request, conjunto_id):
    """
    Detalle de un conjunto específico
    """
    conjunto = get_object_or_404(
        Conjunto, 
        id=conjunto_id, 
        propietario=request.user
    )
    
    # Evaluaciones del conjunto (usando el modelo correcto)
    evaluaciones = conjunto.evaluaciones_riesgo.order_by('-fecha_evaluacion')
    
    # Estadísticas del conjunto
    total_evaluaciones = evaluaciones.filter(estado='completada').count()
    evaluacion_en_progreso = evaluaciones.filter(estado='en_progreso').first()
    
    # Evolución del score
    evaluaciones_completadas = evaluaciones.filter(
        estado='completada',
        promedio_general__isnull=False
    )[:10]  # Últimas 10 evaluaciones
    
    # Preparar datos para gráficos
    evolution_data = []
    for evaluacion in reversed(evaluaciones_completadas):
        evolution_data.append({
            'fecha': evaluacion.fecha_evaluacion.strftime('%d/%m/%Y'),
            'score': float(evaluacion.promedio_general)
        })
    
    context = {
        'conjunto': conjunto,
        'evaluaciones': evaluaciones[:5],  # Mostrar solo las 5 más recientes
        'total_evaluaciones': total_evaluaciones,
        'evaluacion_en_progreso': evaluacion_en_progreso,
        'evolution_data': json.dumps(evolution_data),
        'page_title': f'{conjunto.nombre} - Risk Conjuntos'
    }
    
    return render(request, 'risk_conjuntos/detalle_conjunto.html', context)


@login_required
@requires_risk_conjuntos()
def editar_conjunto(request, conjunto_id):
    """
    Editar un conjunto existente - Redirige al modal
    """
    # Verificar que el conjunto existe y pertenece al usuario
    get_object_or_404(
        Conjunto, 
        id=conjunto_id, 
        propietario=request.user
    )
    
    # Redirigir a la lista donde está el modal
    messages.info(request, 'Use el botón "Editar" del conjunto para modificarlo.')
    return redirect('risk_conjuntos:lista_conjuntos')


@login_required
@requires_risk_conjuntos()
@require_http_methods(["POST"])
def eliminar_conjunto(request, conjunto_id):
    """
    Eliminar (desactivar) un conjunto
    """
    conjunto = get_object_or_404(
        Conjunto, 
        id=conjunto_id, 
        propietario=request.user
    )
    
    conjunto.activo = False
    conjunto.save()
    
    messages.success(
        request, 
        f'Conjunto "{conjunto.nombre}" eliminado exitosamente.'
    )
    
    return redirect('risk_conjuntos:lista_conjuntos')


@login_required
@requires_risk_conjuntos()
def crear_evaluacion(request, conjunto_id):
    """
    Crear una nueva evaluación de seguridad
    """
    conjunto = get_object_or_404(
        Conjunto, 
        id=conjunto_id, 
        propietario=request.user
    )
    
    if request.method == 'POST':
        form = EvaluacionSeguridadForm(request.POST)
        if form.is_valid():
            evaluacion = form.save(commit=False)
            evaluacion.conjunto = conjunto
            evaluacion.ip_evaluacion = request.META.get('REMOTE_ADDR')
            evaluacion.save()
            
            messages.success(
                request,
                'Evaluación creada. Ahora puede proceder a responder las preguntas.'
            )
            return redirect('risk_conjuntos:continuar_evaluacion', evaluacion_id=evaluacion.id)
    else:
        form = EvaluacionSeguridadForm()
    
    context = {
        'form': form,
        'conjunto': conjunto,
        'page_title': f'Nueva Evaluación - {conjunto.nombre}'
    }
    
    return render(request, 'risk_conjuntos/crear_evaluacion.html', context)


@login_required
@requires_risk_conjuntos()
def continuar_evaluacion(request, evaluacion_id):
    """
    Continuar/completar una evaluación existente
    """
    evaluacion = get_object_or_404(
        EvaluacionSeguridad,
        id=evaluacion_id,
        conjunto__propietario=request.user
    )
    
    if evaluacion.estado == 'completada':
        return redirect('risk_conjuntos:detalle_evaluacion', evaluacion_id=evaluacion.id)
    
    # Obtener todas las preguntas activas
    preguntas = PreguntaSeguridad.objects.filter(
        activa=True
    ).select_related('categoria').order_by('categoria__orden', 'orden')
    
    if request.method == 'POST':
        form = RespuestaEvaluacionForm(preguntas, request.POST)
        if form.is_valid():
            # Guardar respuestas
            for pregunta in preguntas:
                field_name = f'pregunta_{pregunta.id}'
                comment_field_name = f'comentario_{pregunta.id}'
                
                if field_name in form.cleaned_data:
                    valor_respuesta = form.cleaned_data[field_name]
                    comentarios = form.cleaned_data.get(comment_field_name, '')
                    
                    # Crear o actualizar respuesta
                    respuesta, created = RespuestaEvaluacion.objects.get_or_create(
                        evaluacion=evaluacion,
                        pregunta=pregunta,
                        defaults={'comentarios': comentarios}
                    )
                    
                    # Asignar valor según tipo de pregunta
                    if pregunta.tipo_respuesta == 'rating':
                        respuesta.rating = valor_respuesta
                    elif pregunta.tipo_respuesta == 'booleana':
                        respuesta.respuesta_booleana = valor_respuesta
                    elif pregunta.tipo_respuesta == 'multiple':
                        respuesta.respuesta_multiple = valor_respuesta
                    elif pregunta.tipo_respuesta == 'numerica':
                        respuesta.respuesta_numerica = valor_respuesta
                    
                    respuesta.comentarios = comentarios
                    respuesta.save()
            
            # Actualizar estado
            evaluacion.estado = 'en_progreso'
            evaluacion.save()
            
            messages.success(request, 'Respuestas guardadas exitosamente.')
            
            # Si se solicitó completar, redirigir a completar
            if 'completar' in request.POST:
                return redirect('risk_conjuntos:completar_evaluacion', evaluacion_id=evaluacion.id)
            
            return redirect('risk_conjuntos:continuar_evaluacion', evaluacion_id=evaluacion.id)
    
    else:
        # Cargar respuestas existentes
        respuestas_existentes = {
            f'pregunta_{r.pregunta.id}': r.get_valor_respuesta()
            for r in evaluacion.respuestas.all()
        }
        comentarios_existentes = {
            f'comentario_{r.pregunta.id}': r.comentarios
            for r in evaluacion.respuestas.all()
        }
        respuestas_existentes.update(comentarios_existentes)
        
        form = RespuestaEvaluacionForm(preguntas, initial=respuestas_existentes)
    
    # Agrupar preguntas por categoría
    preguntas_por_categoria = {}
    for pregunta in preguntas:
        categoria = pregunta.categoria
        if categoria not in preguntas_por_categoria:
            preguntas_por_categoria[categoria] = []
        preguntas_por_categoria[categoria].append(pregunta)
    
    # Calcular progreso
    total_preguntas = preguntas.count()
    respuestas_completadas = evaluacion.respuestas.count()
    progreso = (respuestas_completadas / total_preguntas * 100) if total_preguntas > 0 else 0
    
    context = {
        'evaluacion': evaluacion,
        'form': form,
        'preguntas_por_categoria': preguntas_por_categoria,
        'progreso': round(progreso, 1),
        'respuestas_completadas': respuestas_completadas,
        'total_preguntas': total_preguntas,
        'page_title': f'Evaluando {evaluacion.conjunto.nombre}'
    }
    
    return render(request, 'risk_conjuntos/continuar_evaluacion.html', context)


@login_required
@requires_risk_conjuntos()
def completar_evaluacion(request, evaluacion_id):
    """
    Completar y calcular score de una evaluación
    """
    evaluacion = get_object_or_404(
        EvaluacionSeguridad,
        id=evaluacion_id,
        conjunto__propietario=request.user
    )
    
    if evaluacion.estado == 'completada':
        messages.info(request, 'Esta evaluación ya está completada.')
        return redirect('risk_conjuntos:detalle_evaluacion', evaluacion_id=evaluacion.id)
    
    # Calcular scores por categoría
    categorias = CategoriaSeguridad.objects.filter(activa=True)
    
    for categoria in categorias:
        respuestas_categoria = evaluacion.respuestas.filter(
            pregunta__categoria=categoria,
            rating__isnull=False
        )
        
        if respuestas_categoria.exists():
            # Calcular score de la categoría
            total_puntos = 0
            total_peso = 0
            
            for respuesta in respuestas_categoria:
                peso = float(respuesta.pregunta.peso)
                puntos = ((respuesta.rating - 1) / 4) * 100  # Convertir 1-5 a 0-100
                total_puntos += puntos * peso
                total_peso += peso
            
            if total_peso > 0:
                score_categoria = total_puntos / total_peso
                porcentaje = score_categoria
                
                # Crear o actualizar score de categoría
                ScoreCategoria.objects.update_or_create(
                    evaluacion=evaluacion,
                    categoria=categoria,
                    defaults={
                        'score': score_categoria,
                        'porcentaje': porcentaje,
                        'numero_preguntas': respuestas_categoria.count(),
                        'suma_puntuaciones': sum(r.rating for r in respuestas_categoria)
                    }
                )
    
    # Calcular score total
    score_total = evaluacion.calcular_score_total()
    evaluacion.score_total = score_total
    evaluacion.estado = 'completada'
    evaluacion.save()
    
    messages.success(
        request, 
        f'Evaluación completada exitosamente. Score total: {score_total}%'
    )
    
    return redirect('risk_conjuntos:detalle_evaluacion', evaluacion_id=evaluacion.id)


@login_required
@requires_risk_conjuntos()
def detalle_evaluacion(request, evaluacion_id):
    """
    Detalle de una evaluación completada
    """
    evaluacion = get_object_or_404(
        EvaluacionSeguridad,
        id=evaluacion_id,
        conjunto__propietario=request.user
    )
    
    # Scores por categoría
    scores_categoria = evaluacion.scores_categoria.select_related('categoria').order_by('categoria__orden')
    
    # Respuestas por categoría
    respuestas_por_categoria = {}
    for score in scores_categoria:
        categoria = score.categoria
        respuestas = evaluacion.respuestas.filter(
            pregunta__categoria=categoria
        ).select_related('pregunta').order_by('pregunta__orden')
        respuestas_por_categoria[categoria] = {
            'score': score,
            'respuestas': respuestas
        }
    
    # Datos para gráfico radar
    radar_data = []
    for score in scores_categoria:
        radar_data.append({
            'categoria': score.categoria.nombre,
            'score': float(score.porcentaje)
        })
    
    context = {
        'evaluacion': evaluacion,
        'scores_categoria': scores_categoria,
        'respuestas_por_categoria': respuestas_por_categoria,
        'radar_data': json.dumps(radar_data),
        'page_title': f'Evaluación {evaluacion.conjunto.nombre} - {evaluacion.fecha_evaluacion.strftime("%d/%m/%Y")}'
    }
    
    return render(request, 'risk_conjuntos/detalle_evaluacion.html', context)


@login_required
@requires_risk_conjuntos()
def lista_evaluaciones(request):
    """
    Lista todas las evaluaciones del usuario
    """
    evaluaciones = EvaluacionSeguridad.objects.filter(
        conjunto__propietario=request.user
    ).select_related('conjunto', 'conjunto__tipo_conjunto').order_by('-fecha_evaluacion')
    
    # Filtros simples
    estado = request.GET.get('estado')
    if estado:
        evaluaciones = evaluaciones.filter(estado=estado)
    
    conjunto_id = request.GET.get('conjunto')
    if conjunto_id:
        evaluaciones = evaluaciones.filter(conjunto_id=conjunto_id)
    
    # Paginación
    paginator = Paginator(evaluaciones, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Conjuntos para filtro
    conjuntos_usuario = Conjunto.objects.filter(
        propietario=request.user, 
        activo=True
    ).order_by('nombre')
    
    context = {
        'page_obj': page_obj,
        'conjuntos_usuario': conjuntos_usuario,
        'estado_filtro': estado,
        'conjunto_filtro': conjunto_id,
        'page_title': 'Evaluaciones - Risk Conjuntos'
    }
    
    return render(request, 'risk_conjuntos/lista_evaluaciones.html', context)


@login_required
@requires_risk_conjuntos()
def reportes(request):
    """
    Página principal de reportes
    """
    user = request.user
    
    # Estadísticas para reportes
    conjuntos = Conjunto.objects.filter(propietario=user, activo=True)
    evaluaciones = EvaluacionSeguridad.objects.filter(
        conjunto__propietario=user,
        estado='completada'
    )
    
    # Conjuntos con más evaluaciones
    conjuntos_stats = conjuntos.annotate(
        num_evaluaciones=Count('evaluaciones_seguridad', filter=Q(evaluaciones_seguridad__estado='completada'))
    ).order_by('-num_evaluaciones')[:5]
    
    # Últimos reportes generados (esto se puede expandir con un modelo de reportes)
    ultimos_reportes = evaluaciones.order_by('-fecha_evaluacion')[:5]
    
    context = {
        'conjuntos_stats': conjuntos_stats,
        'ultimos_reportes': ultimos_reportes,
        'total_conjuntos': conjuntos.count(),
        'total_evaluaciones': evaluaciones.count(),
        'page_title': 'Reportes - Risk Conjuntos'
    }
    
    return render(request, 'risk_conjuntos/reportes.html', context)


@login_required
@requires_risk_conjuntos()
def reporte_conjunto(request, conjunto_id):
    """
    Reporte detallado de un conjunto específico
    """
    conjunto = get_object_or_404(
        Conjunto,
        id=conjunto_id,
        propietario=request.user
    )
    
    # Todas las evaluaciones del conjunto
    evaluaciones = conjunto.evaluaciones_seguridad.filter(
        estado='completada'
    ).order_by('-fecha_evaluacion')
    
    # Evolución histórica
    evolucion_scores = []
    for evaluacion in reversed(evaluaciones):
        evolucion_scores.append({
            'fecha': evaluacion.fecha_evaluacion.strftime('%Y-%m-%d'),
            'score': float(evaluacion.score_total) if evaluacion.score_total else 0
        })
    
    # Análisis por categorías (promedio histórico)
    categorias_analysis = {}
    if evaluaciones.exists():
        categorias = CategoriaSeguridad.objects.filter(activa=True)
        for categoria in categorias:
            scores_categoria = ScoreCategoria.objects.filter(
                evaluacion__in=evaluaciones,
                categoria=categoria
            )
            if scores_categoria.exists():
                promedio = scores_categoria.aggregate(Avg('porcentaje'))['porcentaje__avg']
                categorias_analysis[categoria.nombre] = round(promedio, 1)
    
    context = {
        'conjunto': conjunto,
        'evaluaciones': evaluaciones,
        'evolucion_scores': json.dumps(evolucion_scores),
        'categorias_analysis': categorias_analysis,
        'page_title': f'Reporte {conjunto.nombre} - Risk Conjuntos'
    }
    
    return render(request, 'risk_conjuntos/reporte_conjunto.html', context)


@login_required
@requires_risk_conjuntos()
def reporte_evaluacion(request, evaluacion_id):
    """
    Reporte detallado de una evaluación específica
    """
    evaluacion = get_object_or_404(
        EvaluacionSeguridad,
        id=evaluacion_id,
        conjunto__propietario=request.user
    )
    
    # Reutilizar la lógica del detalle de evaluación
    return detalle_evaluacion(request, evaluacion_id)


@login_required
@requires_risk_conjuntos()
def reporte_comparativo(request):
    """
    Reporte comparativo entre múltiples conjuntos
    """
    if request.method == 'POST':
        form = ReporteComparativoForm(request.user, request.POST)
        if form.is_valid():
            conjuntos_seleccionados = form.cleaned_data['conjuntos']
            fecha_desde = form.cleaned_data.get('fecha_desde')
            fecha_hasta = form.cleaned_data.get('fecha_hasta')
            
            # Generar datos comparativos
            datos_comparativos = []
            for conjunto in conjuntos_seleccionados:
                evaluaciones = conjunto.evaluaciones_seguridad.filter(estado='completada')
                
                if fecha_desde:
                    evaluaciones = evaluaciones.filter(fecha_evaluacion__gte=fecha_desde)
                if fecha_hasta:
                    evaluaciones = evaluaciones.filter(fecha_evaluacion__lte=fecha_hasta)
                
                if evaluaciones.exists():
                    score_promedio = evaluaciones.aggregate(Avg('score_total'))['score_total__avg']
                    datos_comparativos.append({
                        'conjunto': conjunto,
                        'score_promedio': round(score_promedio, 1) if score_promedio else 0,
                        'num_evaluaciones': evaluaciones.count(),
                        'ultima_evaluacion': evaluaciones.order_by('-fecha_evaluacion').first()
                    })
            
            context = {
                'form': form,
                'datos_comparativos': datos_comparativos,
                'conjuntos_seleccionados': conjuntos_seleccionados,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'page_title': 'Reporte Comparativo - Risk Conjuntos'
            }
            
            return render(request, 'risk_conjuntos/reporte_comparativo.html', context)
    else:
        form = ReporteComparativoForm(request.user)
    
    context = {
        'form': form,
        'page_title': 'Reporte Comparativo - Risk Conjuntos'
    }
    
    return render(request, 'risk_conjuntos/reporte_comparativo.html', context)


# APIs para AJAX
@login_required
@requires_risk_conjuntos()
def api_dashboard_stats(request):
    """
    API para obtener estadísticas del dashboard en tiempo real
    """
    user = request.user
    conjuntos = Conjunto.objects.filter(propietario=user, activo=True)
    
    stats = {
        'total_conjuntos': conjuntos.count(),
        'conjuntos_evaluados': conjuntos.filter(
            evaluaciones_seguridad__estado='completada'
        ).distinct().count(),
        'score_promedio': 0,
        'alertas_riesgo': EvaluacionSeguridad.objects.filter(
            conjunto__propietario=request.user,
            estado='completada',
            score_total__lt=60
        ).count()
    }
    
    # Score promedio basado en evaluaciones completadas
    evaluaciones_completadas = EvaluacionSeguridad.objects.filter(
        conjunto__propietario=request.user,
        estado='completada',
        score_total__isnull=False
    )
    if evaluaciones_completadas.exists():
        stats['score_promedio'] = round(evaluaciones_completadas.aggregate(
            avg=Avg('score_total')
        )['avg'], 1)
    
    return JsonResponse(stats)


@login_required
@requires_risk_conjuntos()
def api_stats_conjunto(request, conjunto_id):
    """
    API para obtener estadísticas de un conjunto específico
    """
    conjunto = get_object_or_404(
        Conjunto,
        id=conjunto_id,
        propietario=request.user
    )
    
    evaluaciones = conjunto.evaluaciones_seguridad.filter(estado='completada')
    ultima_evaluacion = evaluaciones.order_by('-fecha_evaluacion').first()
    
    stats = {
        'nombre': conjunto.nombre,
        'total_evaluaciones': evaluaciones.count(),
        'score_actual': float(ultima_evaluacion.score_total) if ultima_evaluacion and ultima_evaluacion.score_total else None,
        'nivel_riesgo': ultima_evaluacion.get_nivel_riesgo() if ultima_evaluacion else 'sin_evaluar',
        'fecha_ultima_evaluacion': ultima_evaluacion.fecha_evaluacion.strftime('%d/%m/%Y') if ultima_evaluacion else None
    }
    
    # Evolución últimos 6 meses
    seis_meses_atras = timezone.now() - timedelta(days=180)
    evolucion = evaluaciones.filter(
        fecha_evaluacion__gte=seis_meses_atras
    ).order_by('fecha_evaluacion')
    
    stats['evolucion'] = [
        {
            'fecha': eval.fecha_evaluacion.strftime('%d/%m'),
            'score': float(eval.score_total) if eval.score_total else 0
        }
        for eval in evolucion
    ]
    
    return JsonResponse(stats)


@login_required
@requires_risk_conjuntos()
def export_csv(request):
    """
    Exportar datos a CSV
    """
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="conjuntos_risk_analysis.csv"'
    response.write('\ufeff')  # BOM para UTF-8
    
    writer = csv.writer(response)
    writer.writerow([
        'Nombre', 'Tipo', 'Ciudad', 'Unidades', 'Score Actual', 
        'Nivel Riesgo', 'Fecha Última Evaluación', 'Total Evaluaciones'
    ])
    
    conjuntos = Conjunto.objects.filter(
        propietario=request.user, 
        activo=True
    ).select_related('tipo_conjunto')
    
    for conjunto in conjuntos:
        ultima_evaluacion = conjunto.evaluaciones_seguridad.filter(
            estado='completada'
        ).order_by('-fecha_evaluacion').first()
        
        writer.writerow([
            conjunto.nombre,
            conjunto.tipo_conjunto.get_nombre_display(),
            conjunto.ciudad,
            conjunto.numero_unidades,
            ultima_evaluacion.score_total if ultima_evaluacion else 'N/A',
            ultima_evaluacion.get_nivel_riesgo() if ultima_evaluacion else 'Sin evaluar',
            ultima_evaluacion.fecha_evaluacion.strftime('%d/%m/%Y') if ultima_evaluacion else 'N/A',
            conjunto.evaluaciones_seguridad.filter(estado='completada').count()
        ])
    
    return response


@login_required
@requires_risk_conjuntos()
def import_data(request):
    """
    Importar datos desde CSV
    """
    if request.method == 'POST':
        # Esta funcionalidad se puede implementar según necesidades específicas
        messages.info(request, 'Funcionalidad de importación en desarrollo.')
        return redirect('risk_conjuntos:lista_conjuntos')
    
    context = {
        'page_title': 'Importar Datos - Risk Conjuntos'
    }
    
    return render(request, 'risk_conjuntos/import_data.html', context)


# ==================== VISTAS API PARA MODAL ====================

@login_required
@requires_risk_conjuntos()
def api_tipos_conjunto(request):
    """
    API para obtener tipos de conjunto
    """
    tipos = TipoConjunto.objects.all()
    tipos_data = []
    for tipo in tipos:
        tipos_data.append({
            'id': tipo.id,
            'nombre': tipo.get_nombre_display(),
            'value': tipo.nombre
        })
    
    return JsonResponse({
        'success': True,
        'tipos': tipos_data
    })


@login_required
@requires_risk_conjuntos()
def api_conjunto_detalle(request, conjunto_id):
    """
    API para obtener detalles de un conjunto
    """
    try:
        conjunto = get_object_or_404(
            Conjunto, 
            id=conjunto_id, 
            propietario=request.user
        )
        
        data = {
            'id': str(conjunto.id),
            'nit': conjunto.nit,
            'nombre': conjunto.nombre,
            'tipo_conjunto': conjunto.tipo_conjunto.id,
            'direccion': conjunto.direccion,
            'ciudad': conjunto.ciudad,
            'departamento': conjunto.departamento,
            'numero_unidades': conjunto.numero_unidades,
            'numero_torres': conjunto.numero_torres,
            'administrador_telefono': conjunto.administrador_telefono,
            'administrador_email': conjunto.administrador_email,
            'administrador_nombre': conjunto.administrador_nombre,
            # Solo las amenidades que mantuvimos
            'tiene_piscina': conjunto.tiene_piscina,
            'tiene_gimnasio': conjunto.tiene_gimnasio,
            'tiene_salon_social': conjunto.tiene_salon_social,
            'tiene_juegos_infantiles': conjunto.tiene_juegos_infantiles,
            'tiene_canchas_deportivas': conjunto.tiene_canchas_deportivas,
        }
        
        return JsonResponse({
            'success': True,
            'conjunto': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@requires_risk_conjuntos()
def api_conjunto_crear(request):
    """
    API para crear un conjunto via modal
    """
    if request.method == 'POST':
        form = ConjuntoModalForm(request.POST)
        if form.is_valid():
            conjunto = form.save(commit=False)
            conjunto.propietario = request.user
            conjunto.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Conjunto "{conjunto.nombre}" creado exitosamente.',
                'conjunto_id': str(conjunto.id)
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@requires_risk_conjuntos()
def api_conjunto_editar(request, conjunto_id):
    """
    API para editar un conjunto via modal
    """
    conjunto = get_object_or_404(
        Conjunto, 
        id=conjunto_id, 
        propietario=request.user
    )
    
    if request.method == 'POST':
        form = ConjuntoModalForm(request.POST, instance=conjunto)
        if form.is_valid():
            conjunto = form.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Conjunto "{conjunto.nombre}" actualizado exitosamente.',
                'conjunto_id': str(conjunto.id)
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
 
 
 d e f   t e s t _ s e m a f o r o ( r e q u e s t ) : 
         \  
 \ \ V i s t a  
 d e  
 p r u e b a  
 p a r a  
 l o s  
 t e m p l a t e  
 t a g s  
 d e l  
 s e m � f o r o \ \ \ 
         f r o m   d e c i m a l   i m p o r t   D e c i m a l 
         
         c o n t e x t   =   { 
                 ' b a j o ' :   D e c i m a l ( ' 0 . 2 0 ' ) , 
                 ' m e d i o ' :   D e c i m a l ( ' 0 . 4 5 ' ) , 
                 ' a l t o ' :   D e c i m a l ( ' 0 . 7 5 ' ) , 
         } 
         
         r e t u r n   r e n d e r ( r e q u e s t ,   ' t e s t _ s e m a f o r o . h t m l ' ,   c o n t e x t )  
 
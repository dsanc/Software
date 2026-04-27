"""
Sistema de Generación de Reportes PDF para Evaluaciones de Riesgo
Incluye funcionalidades de IA/ML para análisis inteligente
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied

# Importar sistema de permisos
from apps.evaluadores.permissions import (
    evaluador_permission_required, 
    evaluador_module_required
)

# Importar modelos
from .models import EvaluacionRiesgo, Conjunto
from .ownership_utils import ensure_conjunto_ownership

# Importar funciones de ML/IA
from .ai_ml_analysis_v2 import generar_analisis_ia

logger = logging.getLogger(__name__)


@login_required
@evaluador_module_required('risk_conjuntos')
@evaluador_permission_required('risk_conjuntos', 'read')
def generar_reporte_pdf(request, evaluacion_id):
    """
    Genera vista de reporte PDF para impresión via Browser Print
    """
    try:
        # Obtener la evaluación
        evaluacion = get_object_or_404(EvaluacionRiesgo, id=evaluacion_id)
        
        # Verificar permisos sobre el conjunto
        ensure_conjunto_ownership(request.user, evaluacion.conjunto)
        
        # Verificar que la evaluación esté completada
        if evaluacion.estado != 'completada':
            messages.error(request, 'Solo se pueden generar reportes de evaluaciones completadas.')
            return redirect('risk_conjuntos:detalle_conjunto', conjunto_id=evaluacion.conjunto.id)
        
        # Obtener datos completos de la evaluación
        datos_evaluacion = obtener_datos_completos_evaluacion(evaluacion)
        
        # Generar análisis con IA/ML
        analisis_ia = generar_analisis_completo_ia(evaluacion)
        
        # Preparar contexto para el template
        context = {
            'evaluacion': evaluacion,
            'conjunto': evaluacion.conjunto,
            'datos_evaluacion': datos_evaluacion,
            'analisis_ia': analisis_ia,
            'fecha_generacion': timezone.now(),
            'usuario_generador': request.user,
            'configuracion_impresion': {
                'auto_print': False,
                'formato': 'A4',
                'orientacion': 'retrato',
                'margenes': {
                    'top': '1.5cm',
                    'bottom': '1.5cm', 
                    'left': '2cm',
                    'right': '2cm'
                }
            }
        }
        
        # Log de generación de reporte
        logger.info(
            f'Reporte PDF generado - Evaluación: {evaluacion_id}, '
            f'Conjunto: {evaluacion.conjunto.nombre}, '
            f'Usuario: {request.user.username}'
        )
        
        return render(request, 'risk_conjuntos/pdf/pdf_print_conjuntos.html', context)
        
    except Exception as e:
        logger.error(f'Error generando reporte PDF: {str(e)}')
        messages.error(request, 'Error al generar el reporte PDF.')
        return redirect('risk_conjuntos:detalle_conjunto', conjunto_id=evaluacion.conjunto.id)


@login_required
@evaluador_module_required('risk_conjuntos')
@evaluador_permission_required('risk_conjuntos', 'read')
def preview_reporte_pdf(request, evaluacion_id):
    """
    Vista previa del reporte PDF sin auto-impresión
    """
    try:
        evaluacion = get_object_or_404(EvaluacionRiesgo, id=evaluacion_id)
        ensure_conjunto_ownership(request.user, evaluacion.conjunto)
        
        if evaluacion.estado != 'completada':
            messages.error(request, 'Solo se pueden previsualizar reportes de evaluaciones completadas.')
            return redirect('risk_conjuntos:detalle_conjunto', conjunto_id=evaluacion.conjunto.id)
        
        # Misma lógica que generar_reporte_pdf pero sin auto_print
        datos_evaluacion = obtener_datos_completos_evaluacion(evaluacion)
        analisis_ia = generar_analisis_completo_ia(evaluacion)
        
        context = {
            'evaluacion': evaluacion,
            'conjunto': evaluacion.conjunto,
            'datos_evaluacion': datos_evaluacion,
            'analisis_ia': analisis_ia,
            'fecha_generacion': timezone.now(),
            'usuario_generador': request.user,
            'configuracion_impresion': {
                'auto_print': False,  # Preview no imprime automáticamente
                'formato': 'A4',
                'orientacion': 'retrato',
                'show_print_button': True  # Mostrar botón de impresión manual
            }
        }
        
        return render(request, 'risk_conjuntos/pdf/pdf_print_conjuntos.html', context)
        
    except Exception as e:
        logger.error(f'Error en preview de reporte PDF: {str(e)}')
        messages.error(request, 'Error al generar la vista previa del reporte.')
        return redirect('risk_conjuntos:detalle_conjunto', conjunto_id=evaluacion.conjunto.id)


@login_required
@evaluador_module_required('risk_conjuntos')
@evaluador_permission_required('risk_conjuntos', 'read')
@require_http_methods(["GET"])
def api_datos_reporte_json(request, evaluacion_id):
    """
    API para obtener datos del reporte en formato JSON
    Útil para integraciones o descargas de datos
    """
    try:
        evaluacion = get_object_or_404(EvaluacionRiesgo, id=evaluacion_id)
        ensure_conjunto_ownership(request.user, evaluacion.conjunto)
        
        if evaluacion.estado != 'completada':
            return JsonResponse({
                'error': 'Solo se pueden obtener datos de evaluaciones completadas'
            }, status=400)
        
        # Generar datos completos
        datos_evaluacion = obtener_datos_completos_evaluacion(evaluacion)
        analisis_ia = generar_analisis_completo_ia(evaluacion)
        
        # Preparar respuesta JSON
        reporte_data = {
            'metadata': {
                'evaluacion_id': str(evaluacion.id),
                'conjunto_nombre': evaluacion.conjunto.nombre,
                'fecha_evaluacion': evaluacion.fecha_evaluacion.isoformat(),
                'fecha_generacion': timezone.now().isoformat(),
                'generado_por': request.user.username,
                'estado': evaluacion.estado,
                'tipo_evaluacion': evaluacion.get_tipo_evaluacion_display()
            },
            'datos_evaluacion': datos_evaluacion,
            'analisis_ia': analisis_ia,
            'resumen_ejecutivo': {
                'score_general': float(evaluacion.promedio_general or 0),
                'nivel_riesgo': evaluacion.get_nivel_riesgo(),
                'color_semaforo': evaluacion.get_color_semaforo(),
                'porcentaje_riesgo': evaluacion.get_promedio_porcentaje()
            }
        }
        
        # Log de acceso API
        logger.info(
            f'API reporte JSON - Evaluación: {evaluacion_id}, '
            f'Usuario: {request.user.username}'
        )
        
        return JsonResponse(reporte_data)
        
    except Exception as e:
        logger.error(f'Error en API datos reporte: {str(e)}')
        return JsonResponse({'error': 'Error al obtener datos del reporte'}, status=500)


@login_required
@evaluador_module_required('risk_conjuntos')
@evaluador_permission_required('risk_conjuntos', 'read')
def generar_reporte_general_pdf(request, conjunto_id):
    """
    Genera un reporte general del conjunto basado en el historial
    completo de evaluaciones (requiere más de 1 evaluación completada).
    """
    try:
        conjunto = get_object_or_404(Conjunto, id=conjunto_id)
        ensure_conjunto_ownership(request.user, conjunto)

        evaluaciones = conjunto.evaluaciones_riesgo.filter(
            estado='completada',
            promedio_general__isnull=False
        ).order_by('fecha_evaluacion')

        if evaluaciones.count() < 2:
            messages.error(
                request,
                'El Reporte General requiere al menos 2 evaluaciones completadas.'
            )
            return redirect('risk_conjuntos:detalle_conjunto', conjunto_id=conjunto_id)

        # --- Métricas globales ---
        total_evaluaciones = evaluaciones.count()
        scores = [e.get_promedio_porcentaje() for e in evaluaciones]
        promedio_historico = round(sum(scores) / len(scores), 1)
        mejor_evaluacion = evaluaciones[scores.index(min(scores))]
        peor_evaluacion  = evaluaciones[scores.index(max(scores))]
        ultima_evaluacion = evaluaciones.last()
        primera_evaluacion = evaluaciones.first()

        # Tendencia: compara última vs penúltima
        penultima = list(evaluaciones)[-2]
        diff = ultima_evaluacion.get_promedio_porcentaje() - penultima.get_promedio_porcentaje()
        if abs(diff) < 2:
            tendencia = 'estable'
            tendencia_icono = 'fas fa-minus'
            tendencia_color = '#ffc107'
        elif diff > 0:
            tendencia = 'empeorando'
            tendencia_icono = 'fas fa-arrow-up'
            tendencia_color = '#dc3545'
        else:
            tendencia = 'mejorando'
            tendencia_icono = 'fas fa-arrow-down'
            tendencia_color = '#28a745'

        # --- Tabla de historial de evaluaciones ---
        historial = []
        for ev in evaluaciones:
            historial.append({
                'evaluacion': ev,
                'fecha': ev.fecha_evaluacion,
                'score': ev.get_promedio_porcentaje(),
                'nivel': ev.get_nivel_riesgo(),
                'color': ev.get_color_semaforo(),
                'texto_nivel': ev.get_texto_nivel_riesgo(),
                'creado_por': ev.creado_por,
            })

        # --- Categorías agregadas (promedio histórico por categoría) ---
        categorias_agregadas = {}
        for ev in evaluaciones:
            for resultado in ev.resultados_riesgo.select_related('tipo_riesgo').all():
                nombre = resultado.tipo_riesgo.nombre
                pct = float(resultado.promedio_riesgo * 100) if resultado.promedio_riesgo else 0
                if nombre not in categorias_agregadas:
                    categorias_agregadas[nombre] = {'suma': 0, 'count': 0}
                categorias_agregadas[nombre]['suma'] += pct
                categorias_agregadas[nombre]['count'] += 1

        categorias_promedio = {}
        for nombre, datos in categorias_agregadas.items():
            pct = round(datos['suma'] / datos['count'], 1) if datos['count'] else 0
            if pct > 60:
                nivel = 'alto'
            elif pct > 30:
                nivel = 'medio'
            else:
                nivel = 'bajo'
            categorias_promedio[nombre] = {'porcentaje': pct, 'nivel': nivel}

        # Ordenar categorías de mayor a menor riesgo
        categorias_promedio = dict(
            sorted(categorias_promedio.items(), key=lambda x: x[1]['porcentaje'], reverse=True)
        )

        # --- Análisis IA de la última evaluación ---
        analisis_ia = generar_analisis_completo_ia(ultima_evaluacion)

        context = {
            'conjunto': conjunto,
            'total_evaluaciones': total_evaluaciones,
            'promedio_historico': promedio_historico,
            'mejor_evaluacion': mejor_evaluacion,
            'peor_evaluacion': peor_evaluacion,
            'ultima_evaluacion': ultima_evaluacion,
            'primera_evaluacion': primera_evaluacion,
            'historial': historial,
            'tendencia': tendencia,
            'tendencia_icono': tendencia_icono,
            'tendencia_color': tendencia_color,
            'tendencia_diff': round(abs(diff), 1),
            'categorias_promedio': categorias_promedio,
            'analisis_ia': analisis_ia,
            'fecha_generacion': timezone.now(),
            'usuario_generador': request.user,
        }

        logger.info(
            f'Reporte General PDF - Conjunto: {conjunto.nombre}, '
            f'Evaluaciones: {total_evaluaciones}, Usuario: {request.user.username}'
        )

        return render(request, 'risk_conjuntos/pdf/pdf_reporte_general.html', context)

    except Exception as e:
        logger.error(f'Error generando Reporte General PDF: {str(e)}')
        messages.error(request, 'Error al generar el Reporte General.')
        return redirect('risk_conjuntos:detalle_conjunto', conjunto_id=conjunto_id)


def obtener_datos_completos_evaluacion(evaluacion):
    """
    Extrae todos los datos necesarios de la evaluación para el reporte
    """
    try:
        # Obtener todas las respuestas agrupadas por tipo de riesgo
        respuestas_por_riesgo = {}
        resultados_riesgo = evaluacion.resultados_riesgo.select_related('tipo_riesgo').all()
        
        for resultado in resultados_riesgo:
            tipo_riesgo = resultado.tipo_riesgo
            
            # Obtener todas las respuestas de la evaluación y filtrar por tipo de riesgo en Python
            # ya que la relación directa tipo_riesgo no existe en PreguntaEvaluacion
            todas_respuestas = evaluacion.respuestas.select_related('pregunta', 'calificacion').all()
            respuestas_filtradas = []
            
            for respuesta in todas_respuestas:
                # Buscar si la pregunta pertenece a este tipo de riesgo
                # Esto es una simplificación - en un modelo real habría una relación directa
                pregunta_texto = respuesta.pregunta.texto_pregunta.lower()
                tipo_texto = tipo_riesgo.nombre.lower()
                
                # Lógica simple de coincidencia por palabras clave
                keywords_match = any(keyword in pregunta_texto for keyword in tipo_texto.split())
                
                # Si hay coincidencia o no podemos determinar, incluir la respuesta
                if keywords_match or len(respuestas_filtradas) < 5:  # Incluir al menos 5 respuestas
                    respuestas_filtradas.append(respuesta)
                
                if len(respuestas_filtradas) >= 10:  # Limitar a 10 por tipo
                    break
            
            respuestas_data = []
            for respuesta in respuestas_filtradas:
                respuestas_data.append({
                    'pregunta': respuesta.pregunta.texto_pregunta[:100] + "..." if len(respuesta.pregunta.texto_pregunta) > 100 else respuesta.pregunta.texto_pregunta,
                    'calificacion': respuesta.calificacion.nombre if respuesta.calificacion else 'Sin calificar',
                    'valor': float(respuesta.calificacion.valor) if respuesta.calificacion else 0,
                    'observaciones': '',  # Campo removido del modelo
                    'evidencia': None  # Campo no disponible en este modelo
                })
            
            respuestas_por_riesgo[tipo_riesgo.nombre] = {
                'descripcion': tipo_riesgo.descripcion or 'Sin descripción disponible',
                'icono': 'fas fa-exclamation-triangle',  # Icono por defecto
                'color': resultado.get_color_semaforo(),  # Usar el método que sí existe
                'promedio_riesgo': float(resultado.promedio_riesgo or 0),
                'porcentaje_riesgo': float(resultado.promedio_riesgo * 100) if resultado.promedio_riesgo else 0,  # Calcular porcentaje
                'nivel_riesgo': resultado.get_nivel_riesgo(),
                'respuestas': respuestas_data,
                'total_preguntas': len(respuestas_data),
                'preguntas_respondidas': sum(1 for r in respuestas_data if r['calificacion'] != 'Sin calificar')
            }
        
        # Estadísticas generales
        estadisticas = {
            'total_categorias': len(respuestas_por_riesgo),
            'total_preguntas': sum(data['total_preguntas'] for data in respuestas_por_riesgo.values()),
            'preguntas_respondidas': sum(data['preguntas_respondidas'] for data in respuestas_por_riesgo.values()),
            'porcentaje_completitud': 0
        }
        
        if estadisticas['total_preguntas'] > 0:
            estadisticas['porcentaje_completitud'] = round(
                (estadisticas['preguntas_respondidas'] / estadisticas['total_preguntas']) * 100, 2
            )
        
        return {
            'respuestas_por_riesgo': respuestas_por_riesgo,
            'estadisticas': estadisticas,
            'observaciones_generales': evaluacion.observaciones_generales,
            'recomendaciones_generales': evaluacion.recomendaciones_generales,
            'conclusiones': evaluacion.conclusiones,
            'metodologia_aplicada': evaluacion.metodologia_aplicada,
            'limitaciones_evaluacion': evaluacion.limitaciones_evaluacion,
            'proximas_acciones': evaluacion.proximas_acciones
        }
        
    except Exception as e:
        logger.error(f'Error obteniendo datos de evaluación: {str(e)}')
        return {}


def generar_analisis_completo_ia(evaluacion):
    """
    Genera análisis completo usando IA/ML
    """
    try:
        # Análisis completo con IA - todo incluido en una función
        analisis_completo = generar_analisis_ia(evaluacion)
        
        return {
            'analisis_base': analisis_completo,
            'recomendaciones_ml': analisis_completo.get('recomendaciones_ml', []),
            'tendencias_historicas': analisis_completo.get('tendencias_historicas', {}),
            'predicciones_futuras': analisis_completo.get('predicciones_futuras', {}),
            'analisis_comparativo': analisis_completo.get('analisis_comparativo', {}),
            'fecha_analisis': timezone.now(),
            'version_algoritmo': '2.1.0',
            'confianza_analisis': analisis_completo.get('confianza_analisis', {})
        }
        
    except Exception as e:
        logger.error(f'Error en análisis IA: {str(e)}')
        return generar_analisis_fallback(evaluacion)


def generar_analisis_comparativo(evaluacion):
    """
    Compara la evaluación actual con conjuntos similares
    """
    try:
        conjunto = evaluacion.conjunto
        
        # Buscar conjuntos similares (mismo tipo, similar número de unidades)
        conjuntos_similares = Conjunto.objects.filter(
            tipo_conjunto=conjunto.tipo_conjunto,
            numero_unidades__range=(
                max(1, conjunto.numero_unidades - 50),
                conjunto.numero_unidades + 50
            ),
            activo=True
        ).exclude(id=conjunto.id)
        
        # Obtener evaluaciones de conjuntos similares
        evaluaciones_similares = EvaluacionRiesgo.objects.filter(
            conjunto__in=conjuntos_similares,
            estado='completada',
            promedio_general__isnull=False
        ).order_by('-fecha_evaluacion')[:20]  # Últimas 20 evaluaciones
        
        if not evaluaciones_similares.exists():
            return {
                'disponible': False,
                'razon': 'No hay conjuntos similares para comparar'
            }
        
        # Calcular estadísticas comparativas
        promedios = [float(e.promedio_general) for e in evaluaciones_similares]
        promedio_actual = float(evaluacion.promedio_general or 0)
        
        percentil = calcular_percentil(promedio_actual, promedios)
        
        return {
            'disponible': True,
            'total_conjuntos_similares': len(conjuntos_similares),
            'total_evaluaciones_comparadas': len(promedios),
            'promedio_sector': sum(promedios) / len(promedios) if promedios else 0,
            'promedio_actual': promedio_actual,
            'percentil': percentil,
            'mejor_que_porcentaje': round(percentil, 1),
            'clasificacion': obtener_clasificacion_comparativa(percentil),
            'diferencia_sector': promedio_actual - (sum(promedios) / len(promedios) if promedios else 0)
        }
        
    except Exception as e:
        logger.error(f'Error en análisis comparativo: {str(e)}')
        return {'disponible': False, 'razon': 'Error en el análisis'}


def calcular_percentil(valor, lista_valores):
    """
    Calcula en qué percentil se encuentra un valor dentro de una lista
    """
    if not lista_valores:
        return 50.0
    
    lista_ordenada = sorted(lista_valores)
    posicion = sum(1 for x in lista_ordenada if x < valor)
    return (posicion / len(lista_ordenada)) * 100


def obtener_clasificacion_comparativa(percentil):
    """
    Devuelve clasificación textual basada en percentil
    """
    if percentil >= 90:
        return "Excelente"
    elif percentil >= 75:
        return "Muy Bueno"
    elif percentil >= 50:
        return "Promedio"
    elif percentil >= 25:
        return "Por Debajo del Promedio"
    else:
        return "Requiere Atención"


def calcular_confianza_analisis(evaluacion):
    """
    Calcula el nivel de confianza del análisis IA basado en datos disponibles
    """
    try:
        factores_confianza = []
        
        # Factor 1: Completitud de la evaluación
        total_preguntas = evaluacion.resultados_riesgo.count()
        if total_preguntas >= 30:
            factores_confianza.append(95)
        elif total_preguntas >= 20:
            factores_confianza.append(85)
        elif total_preguntas >= 10:
            factores_confianza.append(75)
        else:
            factores_confianza.append(60)
        
        # Factor 2: Calidad de respuestas
        respuestas_con_observaciones = sum(
            1 for resultado in evaluacion.resultados_riesgo.all()
            for respuesta in resultado.respuestas_pregunta.all()
            if respuesta.observaciones and len(respuesta.observaciones.strip()) > 10
        )
        
        if respuestas_con_observaciones >= 15:
            factores_confianza.append(90)
        elif respuestas_con_observaciones >= 10:
            factores_confianza.append(80)
        elif respuestas_con_observaciones >= 5:
            factores_confianza.append(70)
        else:
            factores_confianza.append(60)
        
        # Factor 3: Disponibilidad de datos históricos
        evaluaciones_previas = EvaluacionRiesgo.objects.filter(
            conjunto=evaluacion.conjunto,
            estado='completada',
            fecha_evaluacion__lt=evaluacion.fecha_evaluacion
        ).count()
        
        if evaluaciones_previas >= 3:
            factores_confianza.append(95)
        elif evaluaciones_previas >= 2:
            factores_confianza.append(85)
        elif evaluaciones_previas >= 1:
            factores_confianza.append(75)
        else:
            factores_confianza.append(65)
        
        # Promedio ponderado
        confianza_final = sum(factores_confianza) / len(factores_confianza)
        
        return {
            'porcentaje': round(confianza_final, 1),
            'nivel': get_nivel_confianza(confianza_final),
            'factores_evaluados': len(factores_confianza)
        }
        
    except Exception as e:
        logger.error(f'Error calculando confianza: {str(e)}')
        return {'porcentaje': 70.0, 'nivel': 'Moderado', 'factores_evaluados': 0}


def get_nivel_confianza(porcentaje):
    """
    Convierte porcentaje de confianza a nivel textual
    """
    if porcentaje >= 90:
        return "Muy Alto"
    elif porcentaje >= 80:
        return "Alto"
    elif porcentaje >= 70:
        return "Moderado"
    elif porcentaje >= 60:
        return "Bajo"
    else:
        return "Muy Bajo"


def generar_analisis_fallback(evaluacion):
    """
    Análisis básico cuando falla el sistema de IA
    """
    return {
        'analisis_base': {
            'disponible': False,
            'razon': 'Sistema de IA temporalmente no disponible'
        },
        'recomendaciones_ml': [],
        'tendencias_historicas': {},
        'predicciones_futuras': {},
        'analisis_comparativo': {'disponible': False},
        'fecha_analisis': timezone.now(),
        'version_algoritmo': 'fallback',
        'confianza_analisis': {'porcentaje': 60.0, 'nivel': 'Básico'}
    }
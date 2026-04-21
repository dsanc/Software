"""
Sistema de Análisis con IA/ML para Evaluaciones de Riesgo
Incluye algoritmos de machine learning para análisis predictivo
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone
from django.db.models import Avg, Count, Max, Min
from django.conf import settings

logger = logging.getLogger(__name__)


def generar_analisis_ia(evaluacion):
    """
    Genera análisis inteligente de la evaluación usando IA
    """
    try:
        # Analizar patrones de riesgo
        patrones_riesgo = analizar_patrones_riesgo(evaluacion)
        
        # Identificar áreas críticas
        areas_criticas = identificar_areas_criticas(evaluacion)
        
        # Generar insights automáticos
        insights = generar_insights_automaticos(evaluacion)
        
        # Calcular score de confiabilidad
        score_confiabilidad = calcular_score_confiabilidad(evaluacion)
        
        return {
            'disponible': True,
            'patrones_riesgo': patrones_riesgo,
            'areas_criticas': areas_criticas,
            'insights': insights,
            'score_confiabilidad': score_confiabilidad,
            'resumen_ejecutivo': generar_resumen_ejecutivo_ia(evaluacion, patrones_riesgo, areas_criticas),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f'Error en análisis IA: {str(e)}')
        return {
            'disponible': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


def obtener_recomendaciones_ml(evaluacion):
    """
    Genera recomendaciones usando machine learning
    """
    try:
        recomendaciones = []
        
        # Analizar resultados por tipo de riesgo
        for resultado in evaluacion.resultados_riesgo.all():
            tipo_riesgo = resultado.tipo_riesgo
            promedio_riesgo = float(resultado.promedio_riesgo or 0)
            
            # Recomendaciones basadas en score de riesgo
            if promedio_riesgo > 0.7:  # Alto riesgo
                recomendaciones.extend(generar_recomendaciones_alto_riesgo(tipo_riesgo, resultado))
            elif promedio_riesgo > 0.4:  # Riesgo medio
                recomendaciones.extend(generar_recomendaciones_riesgo_medio(tipo_riesgo, resultado))
            else:  # Bajo riesgo
                recomendaciones.extend(generar_recomendaciones_mantenimiento(tipo_riesgo, resultado))
        
        # Recomendaciones basadas en patrones históricos
        recomendaciones_historicas = analizar_patrones_historicos(evaluacion)
        recomendaciones.extend(recomendaciones_historicas)
        
        # Priorizar recomendaciones usando ML
        recomendaciones_priorizadas = priorizar_recomendaciones_ml(recomendaciones, evaluacion)
        
        return {
            'total_recomendaciones': len(recomendaciones_priorizadas),
            'recomendaciones': recomendaciones_priorizadas[:10],  # Top 10
            'categorias': agrupar_recomendaciones_por_categoria(recomendaciones_priorizadas),
            'urgencia_promedio': calcular_urgencia_promedio(recomendaciones_priorizadas)
        }
        
    except Exception as e:
        logger.error(f'Error generando recomendaciones ML: {str(e)}')
        return {'total_recomendaciones': 0, 'recomendaciones': [], 'error': str(e)}


def calcular_tendencias_riesgo(conjunto, evaluacion_actual):
    """
    Calcula tendencias de riesgo basadas en evaluaciones históricas
    """
    try:
        # Obtener evaluaciones históricas del conjunto
        evaluaciones_historicas = conjunto.evaluaciones_riesgo.filter(
            estado='completada',
            promedio_general__isnull=False,
            fecha_evaluacion__lt=evaluacion_actual.fecha_evaluacion
        ).order_by('fecha_evaluacion')
        
        if evaluaciones_historicas.count() < 2:
            return {
                'disponible': False,
                'razon': 'Insuficientes datos históricos (mínimo 2 evaluaciones previas)'
            }
        
        # Extraer datos para análisis de tendencias
        fechas = []
        scores = []
        
        for eval in evaluaciones_historicas:
            fechas.append(eval.fecha_evaluacion)
            scores.append(float(eval.promedio_general))
        
        # Añadir evaluación actual
        fechas.append(evaluacion_actual.fecha_evaluacion)
        scores.append(float(evaluacion_actual.promedio_general or 0))
        
        # Calcular tendencia general
        tendencia_general = calcular_tendencia_lineal(scores)
        
        # Tendencias por tipo de riesgo
        tendencias_por_tipo = calcular_tendencias_por_tipo_riesgo(conjunto, evaluacion_actual)
        
        # Predicción de siguiente evaluación
        prediccion_siguiente = predecir_siguiente_evaluacion(scores, fechas)
        
        return {
            'disponible': True,
            'total_evaluaciones': len(scores),
            'periodo_analizado_dias': (fechas[-1] - fechas[0]).days,
            'tendencia_general': tendencia_general,
            'tendencias_por_tipo': tendencias_por_tipo,
            'prediccion_siguiente': prediccion_siguiente,
            'variabilidad': {
                'desviacion_estandar': statistics.stdev(scores) if len(scores) > 1 else 0,
                'coeficiente_variacion': (statistics.stdev(scores) / statistics.mean(scores)) * 100 if len(scores) > 1 and statistics.mean(scores) > 0 else 0,
                'score_minimo': min(scores),
                'score_maximo': max(scores),
                'score_promedio': statistics.mean(scores)
            }
        }
        
    except Exception as e:
        logger.error(f'Error calculando tendencias: {str(e)}')
        return {'disponible': False, 'error': str(e)}


def generar_predicciones_futuras(evaluacion):
    """
    Genera predicciones futuras basadas en ML
    """
    try:
        conjunto = evaluacion.conjunto
        
        # Obtener datos históricos para entrenamiento
        datos_entrenamiento = obtener_datos_entrenamiento(conjunto)
        
        if len(datos_entrenamiento) < 3:
            return {
                'disponible': False,
                'razon': 'Insuficientes datos para predicciones (mínimo 3 evaluaciones)'
            }
        
        # Predicciones a diferentes horizontes temporales
        predicciones = {
            '30_dias': predecir_riesgo_horizonte(datos_entrenamiento, 30),
            '90_dias': predecir_riesgo_horizonte(datos_entrenamiento, 90),
            '180_dias': predecir_riesgo_horizonte(datos_entrenamiento, 180),
            '365_dias': predecir_riesgo_horizonte(datos_entrenamiento, 365)
        }
        
        # Factores de riesgo emergentes
        factores_emergentes = identificar_factores_emergentes(datos_entrenamiento, evaluacion)
        
        # Recomendaciones preventivas
        recomendaciones_preventivas = generar_recomendaciones_preventivas(predicciones, factores_emergentes)
        
        return {
            'disponible': True,
            'predicciones': predicciones,
            'factores_emergentes': factores_emergentes,
            'recomendaciones_preventivas': recomendaciones_preventivas,
            'confianza_modelo': calcular_confianza_modelo(datos_entrenamiento),
            'proxima_evaluacion_sugerida': sugerir_fecha_proxima_evaluacion(predicciones)
        }
        
    except Exception as e:
        logger.error(f'Error generando predicciones: {str(e)}')
        return {'disponible': False, 'error': str(e)}


# Funciones auxiliares de análisis

def analizar_patrones_riesgo(evaluacion):
    """
    Identifica patrones en los riesgos de la evaluación
    """
    patrones = []
    resultados = evaluacion.resultados_riesgo.all()
    
    # Patrón: Distribución de riesgos
    scores = [float(r.promedio_riesgo or 0) for r in resultados]
    
    if scores:
        score_promedio = statistics.mean(scores)
        desviacion = statistics.stdev(scores) if len(scores) > 1 else 0
        
        if desviacion > 0.3:
            patrones.append({
                'tipo': 'alta_variabilidad',
                'descripcion': 'Alta variabilidad entre diferentes tipos de riesgo',
                'impacto': 'Alto',
                'recomendacion': 'Revisar procesos de evaluación para áreas con scores muy diferentes'
            })
        
        # Patrón: Concentración de riesgos altos
        riesgos_altos = sum(1 for score in scores if score > 0.7)
        if riesgos_altos > len(scores) * 0.3:  # Más del 30%
            patrones.append({
                'tipo': 'concentracion_riesgos_altos',
                'descripcion': f'{riesgos_altos} de {len(scores)} categorías presentan riesgo alto',
                'impacto': 'Crítico',
                'recomendacion': 'Acción inmediata requerida en múltiples áreas'
            })
    
    return patrones


def identificar_areas_criticas(evaluacion):
    """
    Identifica las áreas más críticas de la evaluación
    """
    areas_criticas = []
    
    for resultado in evaluacion.resultados_riesgo.all():
        promedio = float(resultado.promedio_riesgo or 0)
        
        if promedio > 0.8:  # Muy alto riesgo
            areas_criticas.append({
                'tipo_riesgo': resultado.tipo_riesgo.nombre,
                'score': promedio,
                'nivel': 'Crítico',
                'prioridad': 1,
                'descripcion': resultado.tipo_riesgo.descripcion,
                'acciones_inmediatas': generar_acciones_inmediatas(resultado.tipo_riesgo)
            })
        elif promedio > 0.6:  # Alto riesgo
            areas_criticas.append({
                'tipo_riesgo': resultado.tipo_riesgo.nombre,
                'score': promedio,
                'nivel': 'Alto',
                'prioridad': 2,
                'descripcion': resultado.tipo_riesgo.descripcion,
                'acciones_inmediatas': generar_acciones_inmediatas(resultado.tipo_riesgo)
            })
    
    # Ordenar por prioridad y score
    areas_criticas.sort(key=lambda x: (x['prioridad'], -x['score']))
    
    return areas_criticas


def generar_insights_automaticos(evaluacion):
    """
    Genera insights automáticos basados en IA
    """
    insights = []
    
    # Insight sobre completitud
    total_resultados = evaluacion.resultados_riesgo.count()
    if total_resultados >= 8:
        insights.append({
            'tipo': 'completitud',
            'mensaje': f'Evaluación comprehensiva con {total_resultados} categorías de riesgo analizadas',
            'impacto': 'Positivo'
        })
    
    # Insight sobre consistencia
    scores = [float(r.promedio_riesgo or 0) for r in evaluacion.resultados_riesgo.all()]
    if scores and statistics.stdev(scores) < 0.2:
        insights.append({
            'tipo': 'consistencia',
            'mensaje': 'Scores consistentes entre categorías sugieren evaluación equilibrada',
            'impacto': 'Positivo'
        })
    
    # Insight sobre riesgo general
    promedio_general = float(evaluacion.promedio_general or 0)
    if promedio_general > 0.7:
        insights.append({
            'tipo': 'riesgo_alto',
            'mensaje': 'Score general indica necesidad de atención inmediata',
            'impacto': 'Crítico'
        })
    elif promedio_general < 0.3:
        insights.append({
            'tipo': 'riesgo_bajo',
            'mensaje': 'Excelente gestión de riesgos, mantener estándares actuales',
            'impacto': 'Positivo'
        })
    
    return insights


def calcular_score_confiabilidad(evaluacion):
    """
    Calcula un score de confiabilidad de la evaluación
    """
    factores = []
    
    # Factor: Número de respuestas
    total_respuestas = evaluacion.respuestas.count()
    
    if total_respuestas >= 30:
        factores.append(0.95)
    elif total_respuestas >= 20:
        factores.append(0.85)
    elif total_respuestas >= 10:
        factores.append(0.75)
    else:
        factores.append(0.6)
    
    # Factor: Calidad de respuestas (simplificado ya que no hay observaciones en el modelo actual)
    # Usar la completitud como proxy
    total_preguntas_disponibles = 0
    for resultado in evaluacion.resultados_riesgo.all():
        # Estimar preguntas por tipo de riesgo
        preguntas_tipo = evaluacion.respuestas.filter(
            pregunta__tipo_riesgo=resultado.tipo_riesgo
        ).count()
        total_preguntas_disponibles += preguntas_tipo
    
    if total_preguntas_disponibles > 0:
        ratio_completitud = total_respuestas / total_preguntas_disponibles
        factores.append(min(0.9, 0.6 + (ratio_completitud * 0.3)))
    else:
        factores.append(0.7)
    
    # Factor: Experiencia del evaluador
    if evaluacion.creado_por:
        evaluaciones_previas = evaluacion.creado_por.evaluaciones_riesgo_creadas.filter(
            estado='completada'
        ).count()
        
        if evaluaciones_previas >= 10:
            factores.append(0.95)
        elif evaluaciones_previas >= 5:
            factores.append(0.85)
        elif evaluaciones_previas >= 2:
            factores.append(0.75)
        else:
            factores.append(0.65)
    else:
        factores.append(0.6)
    
    # Calcular score final
    score_final = statistics.mean(factores) if factores else 0.7
    
    return {
        'score': round(score_final, 3),
        'nivel': get_nivel_confiabilidad(score_final),
        'factores_evaluados': len(factores),
        'detalles': {
            'respuestas_totales': total_respuestas,
            'respuestas_con_observaciones': 0,  # No disponible en modelo actual
            'experiencia_evaluador': evaluacion.creado_por.evaluaciones_riesgo_creadas.filter(estado='completada').count() if evaluacion.creado_por else 0
        }
    }


def get_nivel_confiabilidad(score):
    """
    Convierte score numérico a nivel textual
    """
    if score >= 0.9:
        return "Muy Alta"
    elif score >= 0.8:
        return "Alta"
    elif score >= 0.7:
        return "Buena"
    elif score >= 0.6:
        return "Moderada"
    else:
        return "Baja"


# Funciones auxiliares de ML

def generar_recomendaciones_alto_riesgo(tipo_riesgo, resultado):
    """
    Genera recomendaciones específicas para riesgos altos
    """
    recomendaciones_base = {
        'Seguridad Física': [
            'Implementar sistema de videovigilancia 24/7',
            'Reforzar control de acceso con tecnología biométrica',
            'Capacitar personal de seguridad en protocolos de emergencia'
        ],
        'Seguridad Informática': [
            'Actualizar inmediatamente todos los sistemas de software',
            'Implementar autenticación de dos factores',
            'Realizar auditoría de seguridad completa'
        ],
        # Agregar más tipos según sea necesario
    }
    
    recomendaciones = recomendaciones_base.get(tipo_riesgo.nombre, [
        'Revisar inmediatamente los procesos en esta área',
        'Implementar medidas correctivas urgentes',
        'Asignar recursos adicionales para mitigación'
    ])
    
    return [
        {
            'descripcion': rec,
            'urgencia': 'Alta',
            'tipo_riesgo': tipo_riesgo.nombre,
            'score_impacto': 0.9,
            'tiempo_implementacion': '1-2 semanas'
        }
        for rec in recomendaciones
    ]


def calcular_tendencia_lineal(valores):
    """
    Calcula la tendencia lineal de una serie de valores
    """
    if len(valores) < 2:
        return {'direccion': 'Sin datos', 'pendiente': 0}
    
    n = len(valores)
    x = list(range(n))
    
    # Calcular regresión lineal simple
    suma_x = sum(x)
    suma_y = sum(valores)
    suma_xy = sum(x[i] * valores[i] for i in range(n))
    suma_x2 = sum(xi**2 for xi in x)
    
    pendiente = (n * suma_xy - suma_x * suma_y) / (n * suma_x2 - suma_x**2)
    
    if pendiente > 0.01:
        direccion = 'Empeorando'
    elif pendiente < -0.01:
        direccion = 'Mejorando'
    else:
        direccion = 'Estable'
    
    return {
        'direccion': direccion,
        'pendiente': round(pendiente, 4),
        'magnitud': abs(pendiente),
        'interpretacion': interpretar_tendencia(pendiente, valores)
    }


def interpretar_tendencia(pendiente, valores):
    """
    Interpreta la tendencia en términos comprensibles
    """
    if abs(pendiente) < 0.01:
        return "El riesgo se ha mantenido estable en el tiempo"
    elif pendiente > 0.05:
        return "Se observa un incremento significativo del riesgo"
    elif pendiente > 0.01:
        return "Se observa un ligero incremento del riesgo"
    elif pendiente < -0.05:
        return "Se observa una mejora significativa en la gestión del riesgo"
    else:
        return "Se observa una ligera mejora en la gestión del riesgo"


# Funciones auxiliares adicionales

def generar_resumen_ejecutivo_ia(evaluacion, patrones_riesgo, areas_criticas):
    """
    Genera un resumen ejecutivo automatizado
    """
    score_general = float(evaluacion.promedio_general or 0)
    
    # Determinar estado general
    if score_general > 0.7:
        estado_general = "CRÍTICO"
        prioridad = "ALTA"
    elif score_general > 0.4:
        estado_general = "MODERADO"
        prioridad = "MEDIA"
    else:
        estado_general = "BAJO"
        prioridad = "BAJA"
    
    # Contar áreas críticas
    num_areas_criticas = len([area for area in areas_criticas if area['nivel'] == 'Crítico'])
    
    resumen = {
        'estado_general': estado_general,
        'prioridad': prioridad,
        'score_numerico': score_general,
        'areas_criticas_detectadas': num_areas_criticas,
        'patrones_identificados': len(patrones_riesgo),
        'mensaje_principal': generar_mensaje_principal(estado_general, num_areas_criticas),
        'acciones_recomendadas': generar_acciones_principales(estado_general, areas_criticas)
    }
    
    return resumen


def generar_mensaje_principal(estado_general, num_areas_criticas):
    """
    Genera el mensaje principal del resumen ejecutivo
    """
    if estado_general == "CRÍTICO":
        return f"Se requiere atención inmediata. {num_areas_criticas} áreas identificadas como críticas."
    elif estado_general == "MODERADO":
        return "Riesgo moderado detectado. Se recomienda implementar mejoras preventivas."
    else:
        return "Gestión de riesgos adecuada. Mantener estándares actuales y monitoreo continuo."


def generar_acciones_principales(estado_general, areas_criticas):
    """
    Genera las acciones principales basadas en el análisis
    """
    if estado_general == "CRÍTICO":
        return [
            "Formar comité de crisis para atender áreas críticas",
            "Asignar recursos inmediatos para mitigación",
            "Implementar monitoreo continuo de indicadores críticos",
            "Programar re-evaluación en 30 días"
        ]
    elif estado_general == "MODERADO":
        return [
            "Desarrollar plan de mejora preventiva",
            "Capacitar personal en áreas de oportunidad",
            "Reforzar controles existentes",
            "Programar re-evaluación en 90 días"
        ]
    else:
        return [
            "Mantener estándares actuales",
            "Continuar con capacitación regular",
            "Documentar mejores prácticas",
            "Programar re-evaluación en 180 días"
        ]


# Funciones stub para completar la implementación

def generar_acciones_inmediatas(tipo_riesgo):
    """
    Genera acciones inmediatas para un tipo de riesgo específico
    """
    return [
        f"Revisar protocolos de {tipo_riesgo.nombre.lower()}",
        f"Capacitar personal responsable de {tipo_riesgo.nombre.lower()}",
        f"Implementar monitoreo adicional en {tipo_riesgo.nombre.lower()}"
    ]


def calcular_tendencias_por_tipo_riesgo(conjunto, evaluacion_actual):
    """
    Calcula tendencias específicas por tipo de riesgo
    """
    # Implementación simplificada - puede expandirse
    return {}


def predecir_siguiente_evaluacion(scores, fechas):
    """
    Predice el score de la siguiente evaluación
    """
    if len(scores) < 2:
        return None
    
    # Simple predicción lineal
    tendencia = calcular_tendencia_lineal(scores)
    ultimo_score = scores[-1]
    prediccion = ultimo_score + tendencia['pendiente']
    
    return {
        'score_predicho': max(0, min(1, prediccion)),  # Mantener en rango 0-1
        'confianza': 0.7,  # Placeholder
        'metodo': 'Tendencia lineal'
    }


def obtener_datos_entrenamiento(conjunto):
    """
    Obtiene datos de entrenamiento para ML
    """
    return []  # Placeholder


def predecir_riesgo_horizonte(datos_entrenamiento, dias):
    """
    Predice riesgo en un horizonte temporal específico
    """
    return {
        'score_predicho': 0.5,  # Placeholder
        'confianza': 0.6,
        'factores_clave': []
    }


def identificar_factores_emergentes(datos_entrenamiento, evaluacion):
    """
    Identifica factores de riesgo emergentes
    """
    return []  # Placeholder


def generar_recomendaciones_preventivas(predicciones, factores_emergentes):
    """
    Genera recomendaciones preventivas
    """
    return []  # Placeholder


def calcular_confianza_modelo(datos_entrenamiento):
    """
    Calcula la confianza del modelo ML
    """
    return 0.7  # Placeholder


def sugerir_fecha_proxima_evaluacion(predicciones):
    """
    Sugiere fecha para próxima evaluación
    """
    return timezone.now() + timedelta(days=90)  # Placeholder


def analizar_patrones_historicos(evaluacion):
    """
    Analiza patrones en evaluaciones históricas
    """
    return []  # Placeholder


def priorizar_recomendaciones_ml(recomendaciones, evaluacion):
    """
    Prioriza recomendaciones usando ML
    """
    return recomendaciones  # Placeholder


def agrupar_recomendaciones_por_categoria(recomendaciones):
    """
    Agrupa recomendaciones por categoría
    """
    return {}  # Placeholder


def calcular_urgencia_promedio(recomendaciones):
    """
    Calcula urgencia promedio de recomendaciones
    """
    return "Media"  # Placeholder


def generar_recomendaciones_riesgo_medio(tipo_riesgo, resultado):
    """
    Genera recomendaciones para riesgo medio
    """
    return []  # Placeholder


def generar_recomendaciones_mantenimiento(tipo_riesgo, resultado):
    """
    Genera recomendaciones de mantenimiento
    """
    return []  # Placeholder
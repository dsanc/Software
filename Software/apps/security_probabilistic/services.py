from decimal import Decimal
from django.db import transaction
from .models import EvaluacionSeguridad, Pregunta, OpcionRespuesta, RespuestaEvaluacion


class MotorEvaluacionSeguridad:
    """Motor para procesar evaluaciones de seguridad basadas en árboles de decisión"""
    
    def __init__(self, evaluacion):
        self.evaluacion = evaluacion
        self.arbol = evaluacion.arbol
    
    def obtener_primera_pregunta(self):
        """Obtiene la primera pregunta del árbol de decisión"""
        return self.arbol.preguntas.filter(es_pregunta_inicial=True).first()
    
    def obtener_siguiente_pregunta(self, pregunta_actual, opcion_seleccionada):
        """
        Determina la siguiente pregunta basada en la opción seleccionada
        """
        if opcion_seleccionada.es_respuesta_final:
            return None
        
        return opcion_seleccionada.pregunta_siguiente
    
    def procesar_respuesta(self, pregunta_id, opcion_id):
        """
        Procesa una respuesta y actualiza la evaluación
        Returns: (siguiente_pregunta, es_evaluacion_completa)
        """
        try:
            pregunta = Pregunta.objects.get(id=pregunta_id, arbol=self.arbol)
            opcion = OpcionRespuesta.objects.get(id=opcion_id, pregunta=pregunta)
        except (Pregunta.DoesNotExist, OpcionRespuesta.DoesNotExist):
            raise ValueError("Pregunta u opción no válida")
        
        with transaction.atomic():
            # Calcular valor combinado: peso de pregunta + peso de opción
            valor_pregunta = pregunta.valor if hasattr(pregunta, 'valor') else Decimal('0.000')
            valor_opcion = opcion.valor_ponderado
            valor_combinado = valor_pregunta + valor_opcion
            
            # Crear o actualizar la respuesta
            respuesta, created = RespuestaEvaluacion.objects.get_or_create(
                evaluacion=self.evaluacion,
                pregunta=pregunta,
                defaults={
                    'opcion_seleccionada': opcion,
                    'valor_aplicado': valor_combinado,
                    'orden_respuesta': self.evaluacion.respuestas.count() + 1
                }
            )
            
            if not created:
                # Actualizar respuesta existente
                respuesta.opcion_seleccionada = opcion
                respuesta.valor_aplicado = valor_combinado
                respuesta.save()
            
            # Actualizar evaluación con la nueva respuesta
            self.evaluacion.agregar_respuesta(
                pregunta_id, 
                opcion_id, 
                valor_combinado
            )
            
            # Determinar siguiente pregunta
            siguiente_pregunta = self.obtener_siguiente_pregunta(pregunta, opcion)
            es_evaluacion_completa = siguiente_pregunta is None or opcion.es_respuesta_final
            
            # Si la evaluación está completa, marcarla como tal
            if es_evaluacion_completa:
                self.finalizar_evaluacion()
            else:
                self.evaluacion.estado = 'en_progreso'
                self.evaluacion.save()
            
            return siguiente_pregunta, es_evaluacion_completa
    
    def finalizar_evaluacion(self):
        """Finaliza la evaluación y calcula los resultados finales"""
        from django.utils import timezone
        
        self.evaluacion.estado = 'completada'
        self.evaluacion.completada_en = timezone.now()
        
        # Recalcular probabilidad total y nivel de riesgo
        total_probabilidad = sum(
            resp.valor_aplicado 
            for resp in self.evaluacion.respuestas.all()
        )
        
        self.evaluacion.probabilidad_total = total_probabilidad
        self.evaluacion.nivel_riesgo = self.evaluacion.calcular_nivel_riesgo()
        self.evaluacion.save()
    
    def obtener_progreso(self):
        """Calcula el progreso de la evaluación"""
        total_respuestas = self.evaluacion.respuestas.count()
        # Estimamos el total de preguntas basado en el árbol
        # (esto es una aproximación, ya que el número real depende del camino tomado)
        total_estimado = self.arbol.preguntas.count()
        
        if total_estimado == 0:
            return 0
        
        progreso = min((total_respuestas / total_estimado) * 100, 100)
        return round(progreso, 1)
    
    def obtener_resumen_respuestas(self):
        """Obtiene un resumen de todas las respuestas dadas"""
        respuestas = self.evaluacion.respuestas.select_related(
            'pregunta', 'opcion_seleccionada'
        ).order_by('orden_respuesta')
        
        resumen = []
        for respuesta in respuestas:
            resumen.append({
                'pregunta': respuesta.pregunta.texto,
                'respuesta': respuesta.opcion_seleccionada.texto,
                'valor': float(respuesta.valor_aplicado),
                'orden': respuesta.orden_respuesta
            })
        
        return resumen
    
    def calcular_distribucion_riesgo(self):
        """Calcula la distribución del riesgo por categorías"""
        respuestas = self.evaluacion.respuestas.all()
        
        if not respuestas:
            return {}
        
        total = float(self.evaluacion.probabilidad_total)
        distribucion = {}
        
        for respuesta in respuestas:
            pregunta = respuesta.pregunta.texto[:50] + "..." if len(respuesta.pregunta.texto) > 50 else respuesta.pregunta.texto
            valor = float(respuesta.valor_aplicado)
            porcentaje = (valor / total * 100) if total > 0 else 0
            
            distribucion[pregunta] = {
                'valor': valor,
                'porcentaje': round(porcentaje, 2),
                'var_amenaza': getattr(respuesta.pregunta, 'var_amenaza', 'Sin clasificar'),
                'valor_pregunta': float(getattr(respuesta.pregunta, 'valor', 0)),
                'valor_opcion': float(respuesta.opcion_seleccionada.valor_ponderado)
            }
        
        return distribucion
    
    def calcular_distribucion_por_amenaza(self):
        """Calcula la distribución del riesgo por variable de amenaza"""
        respuestas = self.evaluacion.respuestas.select_related('pregunta', 'opcion_seleccionada').all()
        
        if not respuestas:
            return {}
        
        total = float(self.evaluacion.probabilidad_total)
        amenazas = {}
        
        for respuesta in respuestas:
            var_amenaza = getattr(respuesta.pregunta, 'var_amenaza', 'Sin clasificar')
            valor = float(respuesta.valor_aplicado)
            
            if var_amenaza not in amenazas:
                amenazas[var_amenaza] = {
                    'valor_total': 0,
                    'porcentaje': 0,
                    'preguntas': []
                }
            
            amenazas[var_amenaza]['valor_total'] += valor
            amenazas[var_amenaza]['preguntas'].append({
                'pregunta': respuesta.pregunta.texto[:40] + "..." if len(respuesta.pregunta.texto) > 40 else respuesta.pregunta.texto,
                'respuesta': respuesta.opcion_seleccionada.texto[:30] + "..." if len(respuesta.opcion_seleccionada.texto) > 30 else respuesta.opcion_seleccionada.texto,
                'valor': valor,
                'valor_pregunta': float(getattr(respuesta.pregunta, 'valor', 0)),
                'valor_opcion': float(respuesta.opcion_seleccionada.valor_ponderado)
            })
        
        # Calcular porcentajes
        for var_amenaza in amenazas:
            amenazas[var_amenaza]['porcentaje'] = round(
                (amenazas[var_amenaza]['valor_total'] / total * 100) if total > 0 else 0, 2
            )
        
        return amenazas
    
    def obtener_recomendaciones(self):
        """Genera recomendaciones basadas en el nivel de riesgo y variables de amenaza"""
        nivel = self.evaluacion.nivel_riesgo
        
        # Recomendaciones base por nivel
        recomendaciones_base = {
            'muy_bajo': [
                "Mantener las medidas de seguridad actuales",
                "Revisar periódicamente las condiciones de seguridad",
                "Estar atento a cambios en el entorno"
            ],
            'bajo': [
                "Implementar medidas preventivas básicas",
                "Mantener comunicación regular con supervisores",
                "Revisar rutas y horarios de desplazamiento"
            ],
            'medio': [
                "Implementar protocolos de seguridad más estrictos",
                "Considerar acompañamiento en desplazamientos",
                "Evaluar alternativas de ubicación o horarios",
                "Capacitación adicional en seguridad personal"
            ],
            'alto': [
                "Implementar medidas de seguridad reforzadas",
                "Acompañamiento obligatorio en desplazamientos",
                "Comunicación constante con equipo de seguridad",
                "Revisar la necesidad del desplazamiento a estas zonas"
            ],
            'muy_alto': [
                "Evitar desplazamientos a estas zonas cuando sea posible",
                "Si es necesario, implementar máximas medidas de seguridad",
                "Acompañamiento especializado obligatorio",
                "Comunicación permanente con equipos de emergencia",
                "Considerar reubicación temporal o permanente"
            ]
        }
        
        recomendaciones = recomendaciones_base.get(nivel, []).copy()
        
        # Agregar recomendaciones específicas por variable de amenaza
        distribucion_amenazas = self.calcular_distribucion_por_amenaza()
        
        recomendaciones_amenaza = {
            'Exposición': [
                "Reducir la exposición en espacios públicos",
                "Variar rutas y horarios de desplazamiento",
                "Implementar medidas de anonimato cuando sea posible"
            ],
            'Inductor': [
                "Moderar el discurso político en espacios públicos",
                "Evaluar la necesidad de activismo directo",
                "Considerar canales de comunicación más seguros"
            ],
            'Intencionalidad': [
                "Reportar inmediatamente cualquier amenaza",
                "Implementar protocolos de comunicación de emergencia",
                "Aumentar las medidas de seguridad personal"
            ],
            'Capacidad': [
                "Evaluar el contexto territorial específico",
                "Coordinar con autoridades locales",
                "Implementar medidas de seguridad acordes al nivel territorial"
            ],
            'Interés': [
                "Analizar el impacto político de las actividades",
                "Considerar el timing de actividades políticas sensibles",
                "Evaluar alianzas estratégicas para reducir riesgos"
            ],
            'Valuabilidad': [
                "Evaluar el perfil público y su impacto",
                "Considerar medidas de protección proporcionales",
                "Analizar alternativas de menor exposición"
            ]
        }
        
        # Agregar recomendaciones específicas para las amenazas con mayor impacto
        for amenaza, datos in distribucion_amenazas.items():
            if datos['porcentaje'] > 20:  # Si representa más del 20% del riesgo total
                if amenaza in recomendaciones_amenaza:
                    recomendaciones.extend([
                        f"🎯 {amenaza}: {rec}" for rec in recomendaciones_amenaza[amenaza]
                    ])
        
        return recomendaciones


class GeneradorReportes:
    """Generador de reportes para evaluaciones de seguridad"""
    
    def __init__(self, evaluacion):
        self.evaluacion = evaluacion
        self.motor = MotorEvaluacionSeguridad(evaluacion)
    
    def generar_reporte_completo(self):
        """Genera un reporte completo de la evaluación"""
        return {
            'evaluacion': {
                'id': self.evaluacion.id,
                'perfil': self.evaluacion.perfil.nombre_completo,
                'evaluador': self.evaluacion.evaluador_nombre or 'No especificado',
                'fecha_creacion': self.evaluacion.creada_en,
                'fecha_completada': self.evaluacion.completada_en,
                'estado': self.evaluacion.get_estado_display(),
            },
            'resultados': {
                'probabilidad_total': float(self.evaluacion.probabilidad_total),
                'nivel_riesgo': self.evaluacion.get_nivel_riesgo_display(),
                'progreso': self.motor.obtener_progreso(),
            },
            'respuestas': self.motor.obtener_resumen_respuestas(),
            'distribucion_riesgo': self.motor.calcular_distribucion_riesgo(),
            'distribucion_amenazas': self.motor.calcular_distribucion_por_amenaza(),
            'recomendaciones': self.motor.obtener_recomendaciones(),
            'analisis_detallado': {
                'variables_criticas': self._identificar_variables_criticas(),
                'factores_principales': self._identificar_factores_principales()
            }
        }
    
    def _identificar_variables_criticas(self):
        """Identifica las variables de amenaza más críticas"""
        distribucion = self.motor.calcular_distribucion_por_amenaza()
        
        # Ordenar por porcentaje de impacto
        variables_ordenadas = sorted(
            distribucion.items(), 
            key=lambda x: x[1]['porcentaje'], 
            reverse=True
        )
        
        criticas = []
        for var, datos in variables_ordenadas[:3]:  # Top 3
            if datos['porcentaje'] > 10:  # Solo si representa más del 10%
                criticas.append({
                    'variable': var,
                    'porcentaje': datos['porcentaje'],
                    'valor_total': datos['valor_total'],
                    'num_preguntas': len(datos['preguntas'])
                })
        
        return criticas
    
    def _identificar_factores_principales(self):
        """Identifica los factores principales de riesgo"""
        distribucion = self.motor.calcular_distribucion_riesgo()
        
        # Ordenar por valor de impacto
        factores_ordenados = sorted(
            distribucion.items(), 
            key=lambda x: x[1]['valor'], 
            reverse=True
        )
        
        principales = []
        for pregunta, datos in factores_ordenados[:5]:  # Top 5
            if datos['valor'] > 0:
                principales.append({
                    'pregunta': pregunta,
                    'valor_total': datos['valor'],
                    'porcentaje': datos['porcentaje'],
                    'variable_amenaza': datos['var_amenaza'],
                    'valor_pregunta': datos['valor_pregunta'],
                    'valor_opcion': datos['valor_opcion']
                })
        
        return principales
    
    def generar_reporte_estadistico(self, evaluaciones_queryset):
        """Genera estadísticas agregadas de múltiples evaluaciones"""
        if not evaluaciones_queryset:
            return {}
        
        total_evaluaciones = evaluaciones_queryset.count()
        evaluaciones_completadas = evaluaciones_queryset.filter(estado='completada').count()
        
        # Distribución por nivel de riesgo
        niveles_riesgo = {}
        for nivel, nombre in EvaluacionSeguridad.NIVEL_RIESGO_CHOICES:
            count = evaluaciones_queryset.filter(nivel_riesgo=nivel).count()
            niveles_riesgo[nombre] = {
                'count': count,
                'porcentaje': round((count / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0
            }
        
        # Probabilidad promedio
        probabilidades = [float(e.probabilidad_total) for e in evaluaciones_queryset if e.probabilidad_total]
        probabilidad_promedio = sum(probabilidades) / len(probabilidades) if probabilidades else 0
        
        return {
            'total_evaluaciones': total_evaluaciones,
            'evaluaciones_completadas': evaluaciones_completadas,
            'tasa_completitud': round((evaluaciones_completadas / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0,
            'probabilidad_promedio': round(probabilidad_promedio, 4),
            'distribucion_niveles': niveles_riesgo,
        }
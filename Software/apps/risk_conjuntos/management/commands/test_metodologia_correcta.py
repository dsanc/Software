"""
Comando para probar la nueva metodología de cálculo
"""
from django.core.management.base import BaseCommand
from apps.risk_conjuntos.models import EvaluacionRiesgo, RespuestaPregunta, CalificacionOpcion
from apps.risk_conjuntos.views_evaluacion import calcular_promedios_por_metodologia_correcta, guardar_resultados_con_metodologia_correcta


class Command(BaseCommand):
    help = 'Prueba la nueva metodología de cálculo con evaluaciones existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--evaluacion-id',
            type=str,
            help='ID de la evaluación a probar'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧪 Probando nueva metodología de cálculo...'))
        
        # Obtener evaluación a probar
        if options['evaluacion_id']:
            try:
                evaluacion = EvaluacionRiesgo.objects.get(id=options['evaluacion_id'])
            except EvaluacionRiesgo.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Evaluación {options["evaluacion_id"]} no encontrada'))
                return
        else:
            evaluacion = EvaluacionRiesgo.objects.first()
            if not evaluacion:
                self.stdout.write(self.style.ERROR('No hay evaluaciones en la base de datos'))
                return
        
        self.stdout.write(f'📊 Evaluando: {evaluacion}')
        self.stdout.write(f'   Estado: {evaluacion.estado}')
        self.stdout.write(f'   Promedio actual: {evaluacion.promedio_general}')
        
        # Construir evaluacion_data a partir de la evaluación existente
        respuestas = RespuestaPregunta.objects.filter(evaluacion=evaluacion).select_related(
            'pregunta', 'pregunta__escenario', 'pregunta__escenario__tipo_riesgo', 'calificacion'
        )
        
        if not respuestas.exists():
            self.stdout.write(self.style.ERROR('No hay respuestas para esta evaluación'))
            return
        
        # Agrupar respuestas por riesgo
        respuestas_por_riesgo = {}
        riesgos_seleccionados = set()
        
        for respuesta in respuestas:
            tipo_riesgo = respuesta.pregunta.escenario.tipo_riesgo
            riesgos_seleccionados.add(tipo_riesgo.id)
            
            if str(tipo_riesgo.id) not in respuestas_por_riesgo:
                respuestas_por_riesgo[str(tipo_riesgo.id)] = []
            
            respuestas_por_riesgo[str(tipo_riesgo.id)].append({
                'pregunta_id': respuesta.pregunta.id,
                'calificacion_id': respuesta.calificacion.id
            })
        
        # Crear estructura de evaluacion_data
        evaluacion_data = {
            'riesgos_seleccionados': list(riesgos_seleccionados),
            'respuestas': respuestas_por_riesgo
        }
        
        self.stdout.write(f'\n📋 Datos de evaluación:')
        self.stdout.write(f'   Riesgos evaluados: {len(riesgos_seleccionados)}')
        self.stdout.write(f'   Total respuestas: {respuestas.count()}')
        
        # Probar metodología correcta
        try:
            self.stdout.write(f'\n🔄 Aplicando metodología correcta...')
            
            resultados = calcular_promedios_por_metodologia_correcta(evaluacion_data)
            
            self.stdout.write(f'\n✅ RESULTADOS CON METODOLOGÍA CORRECTA:')
            self.stdout.write(f'   Promedio general: {resultados["promedio_general"]:.4f}')
            self.stdout.write(f'   Riesgos evaluados: {resultados["total_riesgos_evaluados"]}')
            
            self.stdout.write(f'\n📊 DETALLE POR RIESGO:')
            
            for riesgo_id, datos_riesgo in resultados['resultados_por_riesgo'].items():
                tipo_riesgo = datos_riesgo['tipo_riesgo']
                promedio_riesgo = datos_riesgo['promedio_riesgo']
                
                self.stdout.write(f'\n🔸 {tipo_riesgo.nombre}:')
                self.stdout.write(f'   Promedio del riesgo: {promedio_riesgo:.4f}')
                self.stdout.write(f'   Número de escenarios: {datos_riesgo["numero_escenarios"]}')
                
                # Mostrar detalle por escenario
                for escenario_id, datos_escenario in datos_riesgo['escenarios'].items():
                    escenario = datos_escenario['escenario']
                    promedio_escenario = datos_escenario['promedio']
                    num_preguntas = datos_escenario['numero_preguntas']
                    
                    self.stdout.write(f'     📋 Escenario: {escenario.nombre}')
                    self.stdout.write(f'        Promedio: {promedio_escenario:.4f}')
                    self.stdout.write(f'        Preguntas: {num_preguntas}')
                    
                    # Mostrar detalle por pregunta
                    for respuesta in datos_escenario['respuestas']:
                        pregunta = respuesta['pregunta']
                        calificacion = respuesta['calificacion']
                        resultado = respuesta['resultado']
                        
                        self.stdout.write(f'          • {pregunta.texto_pregunta[:50]}...')
                        self.stdout.write(f'            Calificación: {calificacion.nombre} ({calificacion.valor})')
                        self.stdout.write(f'            Resultado (1-valor): {resultado:.4f}')
            
            # Guardar resultados
            self.stdout.write(f'\n💾 Guardando resultados en la base de datos...')
            guardar_resultados_con_metodologia_correcta(evaluacion, evaluacion_data)
            
            # Recargar evaluación para ver cambios
            evaluacion.refresh_from_db()
            self.stdout.write(f'✅ Promedio general actualizado: {evaluacion.promedio_general}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error aplicando metodología: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
            
        self.stdout.write(f'\n🎉 Prueba completada!')
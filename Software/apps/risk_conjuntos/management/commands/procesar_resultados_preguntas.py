"""
Comando para procesar y generar resultados automáticos de preguntas existentes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.risk_conjuntos.models import RespuestaPregunta, ResultadoPregunta
import time


class Command(BaseCommand):
    help = 'Procesa automáticamente las respuestas existentes para generar sus resultados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--evaluacion-id',
            type=str,
            help='Procesar solo las respuestas de una evaluación específica'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza el reprocesamiento de resultados existentes'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando procesamiento de resultados...'))
        
        # Filtrar respuestas según los parámetros
        respuestas_query = RespuestaPregunta.objects.all()
        
        if options['evaluacion_id']:
            respuestas_query = respuestas_query.filter(evaluacion_id=options['evaluacion_id'])
            
        if not options['force']:
            # Solo procesar respuestas que no tienen resultado procesado
            respuestas_query = respuestas_query.filter(resultado_procesado__isnull=True)
        
        respuestas = respuestas_query.select_related('pregunta', 'calificacion', 'evaluacion')
        total_respuestas = respuestas.count()
        
        if total_respuestas == 0:
            self.stdout.write(
                self.style.WARNING('No se encontraron respuestas para procesar.')
            )
            return
        
        self.stdout.write(f'Procesando {total_respuestas} respuestas...')
        
        procesadas = 0
        errores = 0
        
        try:
            with transaction.atomic():
                for respuesta in respuestas:
                    try:
                        inicio_tiempo = time.time()
                        
                        # Crear o actualizar el resultado
                        resultado, created = ResultadoPregunta.objects.get_or_create(
                            respuesta=respuesta,
                            defaults={
                                'valor_riesgo': respuesta.resultado_calculado,
                                'peso_pregunta': self.calcular_peso_pregunta(respuesta),
                            }
                        )
                        
                        if not created and options['force']:
                            # Actualizar resultado existente
                            resultado.valor_riesgo = respuesta.resultado_calculado
                            resultado.peso_pregunta = self.calcular_peso_pregunta(respuesta)
                            resultado.save()
                        
                        # Calcular tiempo de procesamiento
                        tiempo_ms = int((time.time() - inicio_tiempo) * 1000)
                        resultado.tiempo_procesamiento_ms = tiempo_ms
                        resultado.save(update_fields=['tiempo_procesamiento_ms'])
                        
                        procesadas += 1
                        
                        if procesadas % 50 == 0:
                            self.stdout.write(f'  Procesadas: {procesadas}/{total_respuestas}')
                            
                    except Exception as e:
                        errores += 1
                        self.stdout.write(
                            self.style.ERROR(f'Error procesando respuesta {respuesta.id}: {str(e)}')
                        )
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error en la transacción: {str(e)}')
            )
            return
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Procesamiento completado!'))
        self.stdout.write(f'  • Respuestas procesadas: {procesadas}')
        self.stdout.write(f'  • Errores: {errores}')
        
        if errores == 0:
            self.stdout.write(self.style.SUCCESS('  • Proceso exitoso sin errores'))
        else:
            self.stdout.write(self.style.WARNING(f'  • Proceso completado con {errores} errores'))
        
        # Mostrar estadísticas de niveles de riesgo
        self.mostrar_estadisticas()

    def calcular_peso_pregunta(self, respuesta):
        """
        Calcula el peso específico de una pregunta basado en su tipo de riesgo
        """
        from decimal import Decimal
        
        tipo_riesgo = respuesta.pregunta.escenario.tipo_riesgo.codigo
        
        # Pesos específicos por tipo de riesgo
        pesos = {
            'intrusion_general': Decimal('1.2'),
            'conspiracion_intrusion': Decimal('1.5'),
            'intrusion_unidad': Decimal('1.3'),
            'robo_vehiculos': Decimal('1.1'),
            'robo_bicicletas': Decimal('0.8'),
            'dano_areas_comunes': Decimal('0.9'),
            'conflictos_parqueos': Decimal('0.7'),
            'sustraccion_bienes': Decimal('1.0'),
            'secuestro': Decimal('2.0'),  # Máxima prioridad
        }
        
        return pesos.get(tipo_riesgo, Decimal('1.0'))

    def mostrar_estadisticas(self):
        """Muestra estadísticas de los resultados procesados"""
        from django.db.models import Count
        
        self.stdout.write('\n' + '-'*30)
        self.stdout.write(self.style.SUCCESS('📊 ESTADÍSTICAS DE RESULTADOS:'))
        
        # Estadísticas por nivel de riesgo
        niveles = ResultadoPregunta.objects.values('nivel_riesgo').annotate(
            cantidad=Count('id')
        ).order_by('nivel_riesgo')
        
        for nivel in niveles:
            nombre_nivel = dict(ResultadoPregunta.NIVEL_RIESGO_CHOICES)[nivel['nivel_riesgo']]
            self.stdout.write(f'  • {nombre_nivel}: {nivel["cantidad"]} resultados')
        
        # Resultados que requieren atención
        requieren_atencion = ResultadoPregunta.objects.filter(requiere_atencion=True).count()
        if requieren_atencion > 0:
            self.stdout.write(
                self.style.WARNING(f'  ⚠️  Requieren atención: {requieren_atencion} resultados')
            )
        
        # Promedio de confiabilidad
        from django.db.models import Avg
        promedio_confiabilidad = ResultadoPregunta.objects.aggregate(
            promedio=Avg('confiabilidad')
        )['promedio']
        
        if promedio_confiabilidad:
            self.stdout.write(f'  📈 Confiabilidad promedio: {promedio_confiabilidad:.1f}%')
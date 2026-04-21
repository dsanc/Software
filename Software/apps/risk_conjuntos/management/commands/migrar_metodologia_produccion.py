"""
Comando para migrar evaluaciones existentes a la nueva metodología
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.risk_conjuntos.models import EvaluacionRiesgo, RespuestaPregunta, ResultadoEscenario, ResultadoRiesgo
from apps.risk_conjuntos.views_evaluacion import guardar_resultados_con_metodologia_correcta
import logging


class Command(BaseCommand):
    help = 'Migra evaluaciones existentes a la nueva metodología de cálculo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta simulación sin hacer cambios reales'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Número de evaluaciones a procesar por lote (default: 10)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la migración incluso si ya tiene resultados'
        )

    def handle(self, *args, **options):
        # Configurar logging
        logger = logging.getLogger('risk_conjuntos.migration')
        
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando migración a nueva metodología...'))
        
        # Obtener evaluaciones a migrar
        evaluaciones_query = EvaluacionRiesgo.objects.filter(estado='completada')
        
        if not options['force']:
            # Solo migrar evaluaciones que no tienen resultados calculados
            evaluaciones_query = evaluaciones_query.filter(
                resultados_riesgo__isnull=True
            ).distinct()
        
        total_evaluaciones = evaluaciones_query.count()
        
        if total_evaluaciones == 0:
            self.stdout.write(
                self.style.WARNING('No se encontraron evaluaciones para migrar.')
            )
            return
        
        self.stdout.write(f'📊 Evaluaciones a migrar: {total_evaluaciones}')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🧪 MODO DRY-RUN: No se harán cambios reales'))
        
        # Procesar en lotes
        batch_size = options['batch_size']
        migradas = 0
        errores = 0
        
        for i in range(0, total_evaluaciones, batch_size):
            lote = list(evaluaciones_query[i:i + batch_size])
            
            self.stdout.write(f'\n📦 Procesando lote {i//batch_size + 1} ({len(lote)} evaluaciones)...')
            
            for evaluacion in lote:
                try:
                    self.stdout.write(f'  🔄 Migrando: {evaluacion}')
                    
                    # Construir evaluacion_data desde respuestas existentes
                    evaluacion_data = self.construir_evaluacion_data(evaluacion)
                    
                    if not evaluacion_data['respuestas']:
                        self.stdout.write(f'    ⚠️  Sin respuestas válidas, saltando...')
                        continue
                    
                    if not options['dry_run']:
                        with transaction.atomic():
                            # Eliminar resultados existentes si es forzado
                            if options['force']:
                                ResultadoRiesgo.objects.filter(evaluacion=evaluacion).delete()
                                ResultadoEscenario.objects.filter(evaluacion=evaluacion).delete()
                            
                            # Aplicar nueva metodología
                            resultados = guardar_resultados_con_metodologia_correcta(evaluacion, evaluacion_data)
                            
                            self.stdout.write(
                                f'    ✅ Migrada. Promedio: {resultados["promedio_general"]:.4f}'
                            )
                            
                            logger.info(f'Evaluación {evaluacion.id} migrada exitosamente')
                    else:
                        self.stdout.write(f'    🧪 Sería migrada (dry-run)')
                    
                    migradas += 1
                    
                except Exception as e:
                    errores += 1
                    error_msg = f'Error migrando evaluación {evaluacion.id}: {str(e)}'
                    self.stdout.write(self.style.ERROR(f'    ❌ {error_msg}'))
                    logger.error(error_msg)
                    
                    if options['verbosity'] >= 2:
                        import traceback
                        self.stdout.write(traceback.format_exc())
        
        # Resumen final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📈 MIGRACIÓN COMPLETADA'))
        self.stdout.write(f'  • Total evaluaciones: {total_evaluaciones}')
        self.stdout.write(f'  • Migradas exitosamente: {migradas}')
        self.stdout.write(f'  • Errores: {errores}')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('  • Modo dry-run: No se realizaron cambios reales'))
        
        if errores > 0:
            self.stdout.write(
                self.style.WARNING(f'  ⚠️  {errores} evaluaciones tuvieron errores. Revisar logs.')
            )
        
        logger.info(f'Migración completada: {migradas} exitosas, {errores} errores')

    def construir_evaluacion_data(self, evaluacion):
        """
        Construye evaluacion_data a partir de respuestas existentes
        """
        respuestas = RespuestaPregunta.objects.filter(evaluacion=evaluacion).select_related(
            'pregunta', 'pregunta__escenario', 'pregunta__escenario__tipo_riesgo', 'calificacion'
        )
        
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
        
        return {
            'riesgos_seleccionados': list(riesgos_seleccionados),
            'respuestas': respuestas_por_riesgo
        }
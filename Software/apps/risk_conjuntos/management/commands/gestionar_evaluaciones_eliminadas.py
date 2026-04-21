from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.risk_conjuntos.models import EvaluacionRiesgo


class Command(BaseCommand):
    help = 'Gestiona las evaluaciones eliminadas (soft delete)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Lista las evaluaciones eliminadas'
        )
        parser.add_argument(
            '--restaurar',
            type=str,
            help='Restaura una evaluación por su ID'
        )
        parser.add_argument(
            '--eliminar-definitivamente',
            type=str,
            help='Elimina definitivamente una evaluación por su ID'
        )
        parser.add_argument(
            '--limpiar-antiguos',
            type=int,
            help='Elimina definitivamente evaluaciones eliminadas hace más de X días'
        )
    
    def handle(self, *args, **options):
        if options['listar']:
            self.listar_eliminadas()
        elif options['restaurar']:
            self.restaurar_evaluacion(options['restaurar'])
        elif options['eliminar_definitivamente']:
            self.eliminar_definitivamente(options['eliminar_definitivamente'])
        elif options['limpiar_antiguos']:
            self.limpiar_antiguos(options['limpiar_antiguos'])
        else:
            self.print_help('manage.py', 'gestionar_evaluaciones_eliminadas')
    
    def listar_eliminadas(self):
        """Lista todas las evaluaciones eliminadas"""
        evaluaciones_eliminadas = EvaluacionRiesgo.all_objects.filter(deleted_at__isnull=False).order_by('-deleted_at')
        
        if not evaluaciones_eliminadas.exists():
            self.stdout.write(self.style.SUCCESS('No hay evaluaciones eliminadas.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Encontradas {evaluaciones_eliminadas.count()} evaluaciones eliminadas:'))
        self.stdout.write('')
        
        for eval in evaluaciones_eliminadas:
            dias_eliminada = (timezone.now() - eval.deleted_at).days
            self.stdout.write(
                f'ID: {eval.id}\n'
                f'  Conjunto: {eval.conjunto.nombre}\n'
                f'  Fecha Evaluación: {eval.fecha_evaluacion.strftime("%d/%m/%Y")}\n'
                f'  Estado: {eval.get_estado_display()}\n'
                f'  Eliminada: {eval.deleted_at.strftime("%d/%m/%Y %H:%M")} ({dias_eliminada} días atrás)\n'
                f'  Creador: {eval.creado_por.get_full_name() if eval.creado_por else "N/A"}\n'
            )
    
    def restaurar_evaluacion(self, evaluacion_id):
        """Restaura una evaluación eliminada"""
        try:
            evaluacion = EvaluacionRiesgo.all_objects.get(id=evaluacion_id, deleted_at__isnull=False)
            evaluacion.restore()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Evaluación {evaluacion_id} restaurada exitosamente.\n'
                    f'Conjunto: {evaluacion.conjunto.nombre}\n'
                    f'Fecha: {evaluacion.fecha_evaluacion.strftime("%d/%m/%Y")}'
                )
            )
        except EvaluacionRiesgo.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'No se encontró una evaluación eliminada con ID: {evaluacion_id}')
            )
    
    def eliminar_definitivamente(self, evaluacion_id):
        """Elimina definitivamente una evaluación"""
        try:
            evaluacion = EvaluacionRiesgo.all_objects.get(id=evaluacion_id, deleted_at__isnull=False)
            conjunto_nombre = evaluacion.conjunto.nombre
            fecha_eval = evaluacion.fecha_evaluacion.strftime("%d/%m/%Y")
            
            # Confirmar la eliminación
            respuesta = input(f'¿Estás seguro de eliminar definitivamente la evaluación del conjunto "{conjunto_nombre}" del {fecha_eval}? [y/N]: ')
            
            if respuesta.lower() in ['y', 'yes', 's', 'si']:
                evaluacion.hard_delete()
                self.stdout.write(
                    self.style.WARNING(f'Evaluación eliminada definitivamente: {conjunto_nombre} - {fecha_eval}')
                )
            else:
                self.stdout.write(self.style.SUCCESS('Operación cancelada.'))
                
        except EvaluacionRiesgo.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'No se encontró una evaluación eliminada con ID: {evaluacion_id}')
            )
    
    def limpiar_antiguos(self, dias):
        """Elimina definitivamente evaluaciones eliminadas hace más de X días"""
        fecha_limite = timezone.now() - timezone.timedelta(days=dias)
        evaluaciones_antiguas = EvaluacionRiesgo.all_objects.filter(
            deleted_at__isnull=False,
            deleted_at__lt=fecha_limite
        )
        
        count = evaluaciones_antiguas.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f'No hay evaluaciones eliminadas hace más de {dias} días.'))
            return
        
        # Mostrar qué se va a eliminar
        self.stdout.write(self.style.WARNING(f'Se eliminarán definitivamente {count} evaluaciones:'))
        for eval in evaluaciones_antiguas:
            self.stdout.write(f'  - {eval.conjunto.nombre} ({eval.fecha_evaluacion.strftime("%d/%m/%Y")})')
        
        # Confirmar
        respuesta = input(f'¿Proceder con la eliminación definitiva? [y/N]: ')
        
        if respuesta.lower() in ['y', 'yes', 's', 'si']:
            for eval in evaluaciones_antiguas:
                eval.hard_delete()
            self.stdout.write(self.style.WARNING(f'{count} evaluaciones eliminadas definitivamente.'))
        else:
            self.stdout.write(self.style.SUCCESS('Operación cancelada.'))
"""
Comando de Django para limpiar evaluaciones obsoletas y huérfanas.

Este comando identifica y elimina:
1. Evaluaciones en estado 'draft' sin respuestas después de 24 horas
2. Evaluaciones en estado 'in_progress' sin actividad después de 7 días
3. Evaluaciones con respuestas incompletas después de 30 días

Uso:
    python manage.py cleanup_stale_assessments
    python manage.py cleanup_stale_assessments --dry-run
    python manage.py cleanup_stale_assessments --force
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging

from apps.risk_hoteles.models import SecurityAssessment, SecurityResponse

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpia evaluaciones de seguridad obsoletas y huérfanas del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué evaluaciones se eliminarían sin eliminarlas realmente',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ejecuta la limpieza sin confirmación interactiva',
        )
        parser.add_argument(
            '--days-draft',
            type=int,
            default=1,
            help='Días después de los cuales eliminar drafts sin respuestas (default: 1)',
        )
        parser.add_argument(
            '--days-progress',
            type=int,
            default=7,
            help='Días después de los cuales eliminar evaluaciones in_progress sin actividad (default: 7)',
        )
        parser.add_argument(
            '--days-incomplete',
            type=int,
            default=30,
            help='Días después de los cuales eliminar evaluaciones incompletas (default: 30)',
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.dry_run = options['dry_run']
        self.force = options['force']
        
        # Configurar tiempos de limpieza
        days_draft = options['days_draft']
        days_progress = options['days_progress']
        days_incomplete = options['days_incomplete']
        
        cutoff_draft = timezone.now() - timedelta(days=days_draft)
        cutoff_progress = timezone.now() - timedelta(days=days_progress)
        cutoff_incomplete = timezone.now() - timedelta(days=days_incomplete)
        
        if self.verbosity >= 1:
            self.stdout.write(
                self.style.SUCCESS('🧹 Iniciando limpieza de evaluaciones obsoletas...')
            )
            if self.dry_run:
                self.stdout.write(
                    self.style.WARNING('🔍 Modo DRY-RUN: No se eliminarán evaluaciones')
                )

        # Estadísticas iniciales
        total_assessments = SecurityAssessment.objects.count()
        if self.verbosity >= 1:
            self.stdout.write(f'📊 Total de evaluaciones en sistema: {total_assessments}')

        # 1. Limpiar drafts sin respuestas
        draft_count = self._cleanup_empty_drafts(cutoff_draft)
        
        # 2. Limpiar evaluaciones in_progress sin actividad
        progress_count = self._cleanup_inactive_progress(cutoff_progress)
        
        # 3. Limpiar evaluaciones incompletas muy antiguas
        incomplete_count = self._cleanup_incomplete_assessments(cutoff_incomplete)
        
        # Resumen final
        total_cleaned = draft_count + progress_count + incomplete_count
        
        if self.verbosity >= 1:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Limpieza completada')
            )
            self.stdout.write(f'📝 Drafts vacíos eliminados: {draft_count}')
            self.stdout.write(f'⏳ In-progress inactivos eliminados: {progress_count}')
            self.stdout.write(f'🗂️ Incompletos antiguos eliminados: {incomplete_count}')
            self.stdout.write(f'🧹 Total eliminados: {total_cleaned}')
            
            final_count = SecurityAssessment.objects.count()
            self.stdout.write(f'📊 Evaluaciones restantes: {final_count}')
            
            if total_cleaned > 0:
                percentage_cleaned = (total_cleaned / total_assessments) * 100
                self.stdout.write(
                    f'📈 Espacio liberado: {percentage_cleaned:.1f}% de la base de datos'
                )

        return f'Limpieza completada: {total_cleaned} evaluaciones eliminadas'

    def _cleanup_empty_drafts(self, cutoff_date):
        """Elimina drafts sin respuestas después del tiempo especificado"""
        
        # Buscar drafts sin respuestas
        empty_drafts = SecurityAssessment.objects.filter(
            status='draft',
            created_at__lt=cutoff_date
        ).annotate(
            response_count=Count('responses')
        ).filter(
            response_count=0
        )
        
        count = empty_drafts.count()
        
        if self.verbosity >= 2:
            self.stdout.write(f'\n🔍 Analizando drafts sin respuestas...')
            self.stdout.write(f'📅 Cutoff: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
            self.stdout.write(f'📊 Encontrados: {count} drafts vacíos')
        
        if count > 0:
            if self.verbosity >= 2:
                for assessment in empty_drafts[:5]:  # Mostrar primeros 5
                    self.stdout.write(
                        f'   • {assessment.hotel.name} - {assessment.created_at.strftime("%Y-%m-%d %H:%M")}'
                    )
                if count > 5:
                    self.stdout.write(f'   • ... y {count - 5} más')
            
            if not self.dry_run:
                if not self.force:
                    confirm = input(f'\n¿Eliminar {count} drafts vacíos? [y/N]: ')
                    if confirm.lower() not in ['y', 'yes', 'sí', 's']:
                        self.stdout.write('❌ Eliminación de drafts cancelada')
                        return 0
                
                deleted_count = empty_drafts.delete()[0]
                if self.verbosity >= 1:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Eliminados {deleted_count} drafts vacíos')
                    )
                return deleted_count
        
        if self.verbosity >= 1:
            self.stdout.write('✅ No se encontraron drafts vacíos para eliminar')
        return 0

    def _cleanup_inactive_progress(self, cutoff_date):
        """Elimina evaluaciones in_progress sin actividad reciente"""
        
        # Buscar evaluaciones in_progress sin actividad
        inactive_progress = SecurityAssessment.objects.filter(
            status='in_progress',
            updated_at__lt=cutoff_date
        )
        
        count = inactive_progress.count()
        
        if self.verbosity >= 2:
            self.stdout.write(f'\n🔍 Analizando evaluaciones in_progress inactivas...')
            self.stdout.write(f'📅 Cutoff: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
            self.stdout.write(f'📊 Encontradas: {count} evaluaciones inactivas')
        
        if count > 0:
            if self.verbosity >= 2:
                for assessment in inactive_progress[:5]:  # Mostrar primeros 5
                    response_count = assessment.responses.count()
                    self.stdout.write(
                        f'   • {assessment.hotel.name} - {response_count} respuestas - '
                        f'Actualizada: {assessment.updated_at.strftime("%Y-%m-%d %H:%M")}'
                    )
                if count > 5:
                    self.stdout.write(f'   • ... y {count - 5} más')
            
            if not self.dry_run:
                if not self.force:
                    confirm = input(f'\n¿Eliminar {count} evaluaciones in_progress inactivas? [y/N]: ')
                    if confirm.lower() not in ['y', 'yes', 'sí', 's']:
                        self.stdout.write('❌ Eliminación de in_progress cancelada')
                        return 0
                
                deleted_count = inactive_progress.delete()[0]
                if self.verbosity >= 1:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Eliminadas {deleted_count} evaluaciones in_progress inactivas')
                    )
                return deleted_count
        
        if self.verbosity >= 1:
            self.stdout.write('✅ No se encontraron evaluaciones in_progress inactivas para eliminar')
        return 0

    def _cleanup_incomplete_assessments(self, cutoff_date):
        """Elimina evaluaciones incompletas muy antiguas"""
        
        # Buscar evaluaciones muy antiguas con pocas respuestas
        incomplete_assessments = SecurityAssessment.objects.filter(
            Q(status='draft') | Q(status='in_progress'),
            created_at__lt=cutoff_date
        ).annotate(
            response_count=Count('responses')
        ).filter(
            response_count__lt=5  # Menos de 5 respuestas se considera incompleto
        )
        
        count = incomplete_assessments.count()
        
        if self.verbosity >= 2:
            self.stdout.write(f'\n🔍 Analizando evaluaciones incompletas antiguas...')
            self.stdout.write(f'📅 Cutoff: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
            self.stdout.write(f'📊 Encontradas: {count} evaluaciones incompletas antiguas')
        
        if count > 0:
            if self.verbosity >= 2:
                for assessment in incomplete_assessments[:5]:  # Mostrar primeros 5
                    response_count = assessment.responses.count()
                    self.stdout.write(
                        f'   • {assessment.hotel.name} - {response_count} respuestas - '
                        f'{assessment.status} - {assessment.created_at.strftime("%Y-%m-%d")}'
                    )
                if count > 5:
                    self.stdout.write(f'   • ... y {count - 5} más')
            
            if not self.dry_run:
                if not self.force:
                    confirm = input(f'\n¿Eliminar {count} evaluaciones incompletas antiguas? [y/N]: ')
                    if confirm.lower() not in ['y', 'yes', 'sí', 's']:
                        self.stdout.write('❌ Eliminación de incompletas cancelada')
                        return 0
                
                deleted_count = incomplete_assessments.delete()[0]
                if self.verbosity >= 1:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Eliminadas {deleted_count} evaluaciones incompletas antiguas')
                    )
                return deleted_count
        
        if self.verbosity >= 1:
            self.stdout.write('✅ No se encontraron evaluaciones incompletas antiguas para eliminar')
        return 0
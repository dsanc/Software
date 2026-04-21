"""
Comando de Django para generar métricas y analytics de evaluaciones.

Este comando analiza patrones de uso y genera reportes sobre:
1. Tasa de abandono por categoría
2. Tiempo promedio de completitud 
3. Puntos de salida más frecuentes
4. Estadísticas de guardado/descarte
5. Análisis de productividad por usuario

Uso:
    python manage.py assessment_analytics
    python manage.py assessment_analytics --export-csv
    python manage.py assessment_analytics --days 30
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField
from django.contrib.auth import get_user_model
from datetime import timedelta
import csv
import json
from io import StringIO

from apps.risk_hoteles.models import SecurityAssessment, SecurityResponse, SecurityCategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Genera métricas y analytics detallados del sistema de evaluaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Número de días hacia atrás para el análisis (default: 30)',
        )
        parser.add_argument(
            '--export-csv',
            action='store_true',
            help='Exporta los resultados a archivos CSV',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Muestra análisis detallado adicional',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Analizar solo un usuario específico',
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.days = options['days']
        self.export_csv = options['export_csv']
        self.detailed = options['detailed']
        self.user_id = options.get('user_id')
        
        # Calcular rango de fechas
        end_date = timezone.now()
        start_date = end_date - timedelta(days=self.days)
        
        if self.verbosity >= 1:
            self.stdout.write(
                self.style.SUCCESS(f'📊 Generando Analytics de Evaluaciones')
            )
            self.stdout.write(f'📅 Período: {start_date.strftime("%Y-%m-%d")} a {end_date.strftime("%Y-%m-%d")}')
            if self.user_id:
                self.stdout.write(f'👤 Usuario específico: ID {self.user_id}')

        # Filtro base de evaluaciones
        assessments_filter = Q(created_at__gte=start_date, created_at__lte=end_date)
        if self.user_id:
            assessments_filter &= Q(created_by_id=self.user_id)

        # Generar diferentes análisis
        results = {}
        results['overview'] = self._generate_overview(assessments_filter)
        results['completion_analysis'] = self._analyze_completion_patterns(assessments_filter)
        results['abandonment_analysis'] = self._analyze_abandonment_patterns(assessments_filter)
        results['time_analysis'] = self._analyze_time_patterns(assessments_filter)
        results['category_analysis'] = self._analyze_category_patterns(assessments_filter)
        
        if self.detailed:
            results['user_productivity'] = self._analyze_user_productivity(assessments_filter)
            results['response_patterns'] = self._analyze_response_patterns(assessments_filter)

        # Mostrar resultados
        self._display_results(results)
        
        # Exportar si se solicita
        if self.export_csv:
            self._export_to_csv(results)

    def _generate_overview(self, assessments_filter):
        """Genera estadísticas generales"""
        assessments = SecurityAssessment.objects.filter(assessments_filter)
        
        total = assessments.count()
        completed = assessments.filter(status='completed').count()
        in_progress = assessments.filter(status='in_progress').count()
        draft = assessments.filter(status='draft').count()
        reviewed = assessments.filter(status='reviewed').count()
        
        # Calcular tasas
        completion_rate = (completed / total * 100) if total > 0 else 0
        abandonment_rate = ((draft + in_progress) / total * 100) if total > 0 else 0
        
        return {
            'total_assessments': total,
            'completed': completed,
            'in_progress': in_progress,
            'draft': draft,
            'reviewed': reviewed,
            'completion_rate': round(completion_rate, 2),
            'abandonment_rate': round(abandonment_rate, 2)
        }

    def _analyze_completion_patterns(self, assessments_filter):
        """Analiza patrones de completitud"""
        completed_assessments = SecurityAssessment.objects.filter(
            assessments_filter,
            status='completed',
            completed_at__isnull=False
        ).annotate(
            duration=ExpressionWrapper(
                F('completed_at') - F('created_at'),
                output_field=DurationField()
            )
        )
        
        if not completed_assessments.exists():
            return {'message': 'No hay evaluaciones completadas en el período'}
        
        durations = [a.duration.total_seconds() / 3600 for a in completed_assessments]  # En horas
        
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # Distribución por rangos de tiempo
        quick_completions = len([d for d in durations if d < 1])  # < 1 hora
        normal_completions = len([d for d in durations if 1 <= d < 4])  # 1-4 horas
        slow_completions = len([d for d in durations if d >= 4])  # > 4 horas
        
        return {
            'total_completed': len(durations),
            'avg_completion_time_hours': round(avg_duration, 2),
            'min_completion_time_hours': round(min_duration, 2),
            'max_completion_time_hours': round(max_duration, 2),
            'quick_completions': quick_completions,
            'normal_completions': normal_completions,
            'slow_completions': slow_completions
        }

    def _analyze_abandonment_patterns(self, assessments_filter):
        """Analiza patrones de abandono"""
        abandoned = SecurityAssessment.objects.filter(
            assessments_filter,
            status__in=['draft', 'in_progress']
        )
        
        total_abandoned = abandoned.count()
        
        if total_abandoned == 0:
            return {'message': 'No hay evaluaciones abandonadas en el período'}
        
        # Abandono por estado
        draft_abandoned = abandoned.filter(status='draft').count()
        progress_abandoned = abandoned.filter(status='in_progress').count()
        
        # Abandono por número de respuestas
        abandoned_with_responses = abandoned.annotate(
            response_count=Count('responses')
        )
        
        no_responses = abandoned_with_responses.filter(response_count=0).count()
        few_responses = abandoned_with_responses.filter(response_count__range=(1, 5)).count()
        many_responses = abandoned_with_responses.filter(response_count__gt=5).count()
        
        return {
            'total_abandoned': total_abandoned,
            'draft_abandoned': draft_abandoned,
            'progress_abandoned': progress_abandoned,
            'abandoned_no_responses': no_responses,
            'abandoned_few_responses': few_responses,
            'abandoned_many_responses': many_responses
        }

    def _analyze_time_patterns(self, assessments_filter):
        """Analiza patrones temporales"""
        assessments = SecurityAssessment.objects.filter(assessments_filter)
        
        # Análisis por día de la semana
        by_weekday = {}
        for i in range(7):
            count = assessments.filter(created_at__week_day=i+1).count()
            weekday_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            by_weekday[weekday_names[i]] = count
        
        # Análisis por hora del día
        by_hour = {}
        for hour in range(24):
            count = assessments.filter(created_at__hour=hour).count()
            by_hour[f'{hour:02d}:00'] = count
        
        return {
            'by_weekday': by_weekday,
            'by_hour': by_hour,
            'peak_weekday': max(by_weekday, key=by_weekday.get),
            'peak_hour': max(by_hour, key=by_hour.get)
        }

    def _analyze_category_patterns(self, assessments_filter):
        """Analiza patrones por categoría"""
        
        # Obtener todas las respuestas del período
        responses = SecurityResponse.objects.filter(
            assessment__in=SecurityAssessment.objects.filter(assessments_filter),
            rating__isnull=False
        )
        
        if not responses.exists():
            return {'message': 'No hay respuestas en el período'}
        
        # Análisis por categoría
        category_stats = responses.values(
            'question__category__name'
        ).annotate(
            total_responses=Count('id'),
            avg_rating=Avg('rating'),
            completion_rate=Count('rating') * 100.0 / Count('id')
        ).order_by('-total_responses')
        
        return {
            'total_responses': responses.count(),
            'category_stats': list(category_stats)
        }

    def _analyze_user_productivity(self, assessments_filter):
        """Analiza productividad por usuario"""
        
        user_stats = SecurityAssessment.objects.filter(
            assessments_filter
        ).values(
            'created_by__username',
            'created_by__first_name',
            'created_by__last_name'
        ).annotate(
            total_assessments=Count('id'),
            completed_assessments=Count('id', filter=Q(status='completed')),
            avg_responses=Avg('responses__rating', filter=Q(responses__rating__isnull=False))
        ).order_by('-total_assessments')
        
        return list(user_stats)

    def _analyze_response_patterns(self, assessments_filter):
        """Analiza patrones de respuestas"""
        
        responses = SecurityResponse.objects.filter(
            assessment__in=SecurityAssessment.objects.filter(assessments_filter),
            rating__isnull=False
        )
        
        if not responses.exists():
            return {'message': 'No hay respuestas en el período'}
        
        # Distribución de calificaciones
        rating_distribution = responses.values('rating').annotate(
            count=Count('id')
        ).order_by('rating')
        
        # Preguntas más problemáticas (calificación baja)
        problematic_questions = responses.filter(
            rating__lte=2
        ).values(
            'question__question_text',
            'question__category__name'
        ).annotate(
            count=Count('id'),
            avg_rating=Avg('rating')
        ).order_by('avg_rating')[:10]
        
        return {
            'rating_distribution': list(rating_distribution),
            'problematic_questions': list(problematic_questions)
        }

    def _display_results(self, results):
        """Muestra los resultados en consola"""
        
        if self.verbosity >= 1:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('📊 RESUMEN EJECUTIVO'))
            self.stdout.write('='*60)
            
            overview = results['overview']
            self.stdout.write(f'📝 Total evaluaciones: {overview["total_assessments"]}')
            self.stdout.write(f'✅ Completadas: {overview["completed"]} ({overview["completion_rate"]}%)')
            self.stdout.write(f'⏳ En progreso: {overview["in_progress"]}')
            self.stdout.write(f'📋 Borradores: {overview["draft"]}')
            self.stdout.write(f'👁️ Revisadas: {overview["reviewed"]}')
            self.stdout.write(f'❌ Tasa de abandono: {overview["abandonment_rate"]}%')
            
            # Análisis de completitud
            completion = results['completion_analysis']
            if 'avg_completion_time_hours' in completion:
                self.stdout.write('\n' + '-'*40)
                self.stdout.write(self.style.SUCCESS('⏱️ ANÁLISIS DE TIEMPO'))
                self.stdout.write('-'*40)
                self.stdout.write(f'📊 Completadas analizadas: {completion["total_completed"]}')
                self.stdout.write(f'⏱️ Tiempo promedio: {completion["avg_completion_time_hours"]:.2f} horas')
                self.stdout.write(f'🏃 Completadas rápidas (<1h): {completion["quick_completions"]}')
                self.stdout.write(f'🚶 Completadas normales (1-4h): {completion["normal_completions"]}')
                self.stdout.write(f'🐌 Completadas lentas (>4h): {completion["slow_completions"]}')
            
            # Análisis de abandono
            abandonment = results['abandonment_analysis']
            if 'total_abandoned' in abandonment:
                self.stdout.write('\n' + '-'*40)
                self.stdout.write(self.style.WARNING('🚪 ANÁLISIS DE ABANDONO'))
                self.stdout.write('-'*40)
                self.stdout.write(f'📊 Total abandonadas: {abandonment["total_abandoned"]}')
                self.stdout.write(f'📋 Abandonadas en draft: {abandonment["draft_abandoned"]}')
                self.stdout.write(f'⏳ Abandonadas en progreso: {abandonment["progress_abandoned"]}')
                self.stdout.write(f'🔴 Sin respuestas: {abandonment["abandoned_no_responses"]}')
                self.stdout.write(f'🟡 Pocas respuestas (1-5): {abandonment["abandoned_few_responses"]}')
                self.stdout.write(f'🟢 Muchas respuestas (>5): {abandonment["abandoned_many_responses"]}')
            
            # Patrones temporales
            time_patterns = results['time_analysis']
            self.stdout.write('\n' + '-'*40)
            self.stdout.write(self.style.SUCCESS('📅 PATRONES TEMPORALES'))
            self.stdout.write('-'*40)
            self.stdout.write(f'📈 Día pico: {time_patterns["peak_weekday"]}')
            self.stdout.write(f'🕐 Hora pico: {time_patterns["peak_hour"]}')

    def _export_to_csv(self, results):
        """Exporta resultados a archivos CSV"""
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        # Exportar resumen ejecutivo
        overview_filename = f'assessment_overview_{timestamp}.csv'
        with open(overview_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Métrica', 'Valor'])
            overview = results['overview']
            for key, value in overview.items():
                writer.writerow([key.replace('_', ' ').title(), value])
        
        if self.verbosity >= 1:
            self.stdout.write(f'\n📁 Resumen exportado a: {overview_filename}')
        
        # Exportar análisis de categorías si existe
        if 'category_stats' in results['category_analysis']:
            category_filename = f'category_analysis_{timestamp}.csv'
            with open(category_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Categoría', 'Total Respuestas', 'Calificación Promedio', 'Tasa Completitud'])
                for stat in results['category_analysis']['category_stats']:
                    writer.writerow([
                        stat['question__category__name'],
                        stat['total_responses'],
                        round(stat['avg_rating'], 2),
                        round(stat['completion_rate'], 2)
                    ])
            
            if self.verbosity >= 1:
                self.stdout.write(f'📁 Análisis de categorías exportado a: {category_filename}')
        
        return f'Analytics exportados con timestamp: {timestamp}'
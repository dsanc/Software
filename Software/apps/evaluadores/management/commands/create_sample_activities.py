from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from apps.evaluadores.models import Evaluador, EvaluatorActivity


class Command(BaseCommand):
    help = 'Crea actividades de prueba para los evaluadores'
    
    def handle(self, *args, **options):
        # Obtener evaluadores existentes
        evaluadores = Evaluador.objects.filter(estado='active')
        
        if not evaluadores.exists():
            self.stdout.write(
                self.style.WARNING(
                    'No hay evaluadores activos. Primero crea algunos evaluadores.'
                )
            )
            return
        
        # Tipos de actividades para crear
        sample_activities = [
            {
                'action': 'evaluation_started',
                'description': 'Inició evaluación de riesgo hotelero',
                'module': 'risk_hoteles',
                'status': 'completed'
            },
            {
                'action': 'evaluation_completed',
                'description': 'Completó evaluación de conjunto residencial',
                'module': 'risk_conjuntos',
                'status': 'completed'
            },
            {
                'action': 'report_generated',
                'description': 'Generó reporte de análisis probabilístico',
                'module': 'security_probabilistic',
                'status': 'completed'
            },
            {
                'action': 'evaluation_updated',
                'description': 'Actualizó evaluación en progreso',
                'module': 'risk_hoteles',
                'status': 'in_progress'
            },
            {
                'action': 'comment_added',
                'description': 'Agregó comentario a evaluación',
                'module': 'risk_conjuntos',
                'status': 'completed'
            },
            {
                'action': 'login',
                'description': 'Inició sesión en el sistema',
                'module': 'dashboard',
                'status': 'completed'
            },
        ]
        
        created_count = 0
        
        # Crear actividades para los últimos 7 días
        for i in range(20):
            evaluador = random.choice(evaluadores)
            activity_data = random.choice(sample_activities)
            
            # Crear fecha aleatoria en los últimos 7 días
            days_ago = random.randint(0, 6)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            created_at = timezone.now() - timedelta(
                days=days_ago, 
                hours=hours_ago, 
                minutes=minutes_ago
            )
            
            # Crear la actividad
            activity = EvaluatorActivity.objects.create(
                evaluador=evaluador,
                action=activity_data['action'],
                description=activity_data['description'],
                module=activity_data['module'],
                status=activity_data['status'],
                metadata={
                    'ip_address': f'192.168.1.{random.randint(1, 255)}',
                    'user_agent': 'Sample User Agent',
                    'session_id': f'sess_{random.randint(1000, 9999)}'
                }
            )
            
            # Establecer la fecha manualmente
            activity.created_at = created_at
            activity.save(update_fields=['created_at'])
            
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Se crearon exitosamente {created_count} actividades de prueba.'
            )
        )
        
        # Mostrar estadísticas
        today_activities = EvaluatorActivity.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        self.stdout.write(f'Actividades de hoy: {today_activities}')
        
        total_activities = EvaluatorActivity.objects.count()
        self.stdout.write(f'Total de actividades: {total_activities}')
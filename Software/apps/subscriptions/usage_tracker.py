from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta


def get_subscription_usage_stats(user, subscription):
    """
    Calcula las estadísticas de uso para una suscripción específica
    """
    module_name = subscription.plan.module.name
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Inicializar estadísticas base
    usage_stats = {
        'reports_used': 0,
        'reports_limit': subscription.plan.max_reports,
        'hotels_count': 0,
        'hotels_limit': getattr(subscription.plan, 'max_hotels', -1),
        'evaluations_count': 0,
        'evaluations_limit': subscription.plan.limits.get('evaluaciones', -1) if subscription.plan.limits else -1,
        'storage_used_gb': 0,
        'storage_limit_gb': subscription.plan.max_storage_gb,
        'users_count': 1,  # El usuario actual
        'users_limit': subscription.plan.max_users,
        'period_start': current_month_start,
        'period_end': current_month_start + timedelta(days=32),  # Aproximadamente un mes
    }
    
    # Obtener estadísticas específicas por módulo
    if module_name == 'risk_hoteles':
        usage_stats.update(_get_risk_hoteles_usage(user, current_month_start))
    elif module_name == 'risk_conjuntos':
        usage_stats.update(_get_risk_conjuntos_usage(user, current_month_start))
    elif module_name == 'security_probabilistic':
        usage_stats.update(_get_security_probabilistic_usage(user, current_month_start))
    
    # Calcular porcentajes de uso
    usage_stats['reports_percentage'] = _calculate_percentage(usage_stats['reports_used'], usage_stats['reports_limit'])
    usage_stats['evaluations_percentage'] = _calculate_percentage(usage_stats['evaluations_count'], usage_stats['evaluations_limit'])
    usage_stats['storage_percentage'] = _calculate_percentage(usage_stats['storage_used_gb'], usage_stats['storage_limit_gb'])
    usage_stats['users_percentage'] = _calculate_percentage(usage_stats['users_count'], usage_stats['users_limit'])
    
    return usage_stats


def _get_risk_hoteles_usage(user, period_start):
    """Obtener estadísticas de uso específicas del módulo risk_hoteles"""
    try:
        from apps.risk_hoteles.models import Hotel, SecurityAssessment
        
        # Hoteles registrados
        hotels_count = Hotel.objects.filter(owner=user, is_active=True).count()
        
        # Evaluaciones creadas este mes
        evaluations_count = SecurityAssessment.objects.filter(
            hotel__owner=user,
            created_at__gte=period_start
        ).count()
        
        # Reportes generados este mes (contamos evaluaciones completadas como reportes)
        reports_used = SecurityAssessment.objects.filter(
            hotel__owner=user,
            status='completed',
            created_at__gte=period_start
        ).count()
        
        return {
            'hotels_count': hotels_count,
            'evaluations_count': evaluations_count,
            'reports_used': reports_used,
            'module_specific': {
                'assessments_completed': SecurityAssessment.objects.filter(
                    hotel__owner=user, 
                    status='completed'
                ).count(),
                'assessments_pending': SecurityAssessment.objects.filter(
                    hotel__owner=user, 
                    status__in=['pending', 'in_progress']
                ).count(),
            }
        }
    except ImportError:
        return {
            'hotels_count': 0,
            'evaluations_count': 0,
            'reports_used': 0,
            'module_specific': {}
        }


def _get_risk_conjuntos_usage(user, period_start):
    """Obtener estadísticas de uso específicas del módulo risk_conjuntos"""
    try:
        from apps.risk_conjuntos.models import Conjunto, EvaluacionSeguridad
        
        # Conjuntos registrados
        conjuntos_count = Conjunto.objects.filter(propietario=user, activo=True).count()
        
        # Evaluaciones creadas este mes
        evaluations_count = EvaluacionSeguridad.objects.filter(
            conjunto__propietario=user,
            fecha_evaluacion__gte=period_start
        ).count()
        
        # Reportes generados este mes
        reports_used = EvaluacionSeguridad.objects.filter(
            conjunto__propietario=user,
            estado='completada',
            fecha_evaluacion__gte=period_start
        ).count()
        
        return {
            'conjuntos_count': conjuntos_count,
            'evaluations_count': evaluations_count,
            'reports_used': reports_used,
            'module_specific': {
                'evaluations_completed': EvaluacionSeguridad.objects.filter(
                    conjunto__propietario=user, 
                    estado='completada'
                ).count(),
                'evaluations_pending': EvaluacionSeguridad.objects.filter(
                    conjunto__propietario=user, 
                    estado__in=['pendiente', 'en_proceso']
                ).count(),
            }
        }
    except ImportError:
        return {
            'conjuntos_count': 0,
            'evaluations_count': 0,
            'reports_used': 0,
            'module_specific': {}
        }


def _get_security_probabilistic_usage(user, period_start):
    """Obtener estadísticas de uso específicas del módulo security_probabilistic"""
    try:
        from apps.security_probabilistic.models import SecurityProject, RiskAssessment
        
        # Proyectos de seguridad registrados
        projects_count = SecurityProject.objects.filter(owner=user, is_active=True).count()
        
        # Análisis creados este mes
        evaluations_count = RiskAssessment.objects.filter(
            project__owner=user,
            created_at__gte=period_start
        ).count()
        
        # Reportes generados este mes
        reports_used = RiskAssessment.objects.filter(
            project__owner=user,
            status='completed',
            created_at__gte=period_start
        ).count()
        
        return {
            'projects_count': projects_count,
            'evaluations_count': evaluations_count,
            'reports_used': reports_used,
            'module_specific': {
                'assessments_completed': RiskAssessment.objects.filter(
                    project__owner=user, 
                    status='completed'
                ).count(),
                'assessments_pending': RiskAssessment.objects.filter(
                    project__owner=user, 
                    status__in=['pending', 'in_progress']
                ).count(),
            }
        }
    except (ImportError, AttributeError):
        # El módulo security_probabilistic podría no existir aún o tener diferentes modelos
        return {
            'projects_count': 0,
            'evaluations_count': 0,
            'reports_used': 0,
            'module_specific': {}
        }


def _calculate_percentage(used, limit):
    """Calcula el porcentaje de uso"""
    if limit == -1:  # Ilimitado
        return 0
    elif limit == 0:
        return 100 if used > 0 else 0
    else:
        return min((used / limit) * 100, 100)


def get_usage_status_color(percentage):
    """Determina el color del indicador según el porcentaje de uso"""
    if percentage >= 90:
        return 'danger'
    elif percentage >= 75:
        return 'warning'
    elif percentage >= 50:
        return 'info'
    else:
        return 'success'


def get_usage_status_text(percentage, limit):
    """Obtiene el texto descriptivo del estado de uso"""
    if limit == -1:
        return 'Ilimitado'
    elif percentage >= 90:
        return 'Límite casi alcanzado'
    elif percentage >= 75:
        return 'Uso alto'
    elif percentage >= 50:
        return 'Uso moderado'
    else:
        return 'Uso bajo'
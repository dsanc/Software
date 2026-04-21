from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def days_until(date):
    """Devuelve los días restantes hasta una fecha"""
    if not date:
        return 0
    
    now = timezone.now().date()
    if isinstance(date, str):
        return 0
    
    target_date = date.date() if hasattr(date, 'date') else date
    
    if target_date <= now:
        return 0
    
    delta = target_date - now
    return delta.days

@register.filter
def subscription_progress(subscription):
    """Calcula el porcentaje de progreso de una suscripción"""
    if not subscription or not subscription.start_date or not subscription.end_date:
        return 0
    
    now = timezone.now().date()
    start_date = subscription.start_date.date() if hasattr(subscription.start_date, 'date') else subscription.start_date
    end_date = subscription.end_date.date() if hasattr(subscription.end_date, 'date') else subscription.end_date
    
    if now < start_date:
        return 0
    elif now > end_date:
        return 100
    
    total_days = (end_date - start_date).days
    elapsed_days = (now - start_date).days
    
    if total_days == 0:
        return 100
    
    progress = (elapsed_days / total_days) * 100
    return min(max(progress, 0), 100)

@register.filter
def subscription_status_color(subscription):
    """Devuelve el color del badge según el estado de la suscripción"""
    if not subscription:
        return 'secondary'
    
    days_left = days_until(subscription.end_date)
    
    if subscription.status == 'active':
        if days_left > 30:
            return 'success'
        elif days_left > 7:
            return 'warning'
        else:
            return 'danger'
    elif subscription.status == 'trial':
        return 'info'
    else:
        return 'secondary'

@register.filter
def subscription_time_remaining(subscription):
    """Devuelve un texto descriptivo del tiempo restante"""
    if not subscription:
        return 'Sin información'
    
    days_left = days_until(subscription.end_date)
    
    if days_left <= 0:
        return 'Expirado'
    elif days_left == 1:
        return '1 día restante'
    elif days_left < 30:
        return f'{days_left} días restantes'
    elif days_left < 365:
        months = days_left // 30
        if months == 1:
            return '1 mes restante'
        else:
            return f'{months} meses restantes'
    else:
        years = days_left // 365
        if years == 1:
            return '1 año restante'
        else:
            return f'{years} años restantes'

@register.inclusion_tag('dashboard/usage_indicator.html')
def usage_indicator(used, limit, label="Uso"):
    """Muestra un indicador de uso con barra de progreso"""
    if limit == -1:
        percentage = 0
        is_unlimited = True
        status_color = 'success'
        status_text = 'Ilimitado'
    else:
        percentage = min((used / limit) * 100, 100) if limit > 0 else (100 if used > 0 else 0)
        is_unlimited = False
        
        if percentage >= 90:
            status_color = 'danger'
            status_text = 'Crítico'
        elif percentage >= 75:
            status_color = 'warning' 
            status_text = 'Alto'
        elif percentage >= 50:
            status_color = 'info'
            status_text = 'Moderado'
        else:
            status_color = 'success'
            status_text = 'Bajo'
    
    return {
        'used': used,
        'limit': limit,
        'percentage': percentage,
        'is_unlimited': is_unlimited,
        'status_color': status_color,
        'status_text': status_text,
        'label': label,
    }

@register.filter
def format_limit(value):
    """Formatea los límites para mostrar"""
    if value == -1:
        return "Ilimitado"
    elif value == 0:
        return "No disponible"
    else:
        return str(value)

@register.filter
def currency_co(value):
    """Formatea números como moneda colombiana con puntos como separadores de miles"""
    if not value:
        return "0"
    try:
        # Convertir a entero y formatear con puntos
        amount = int(float(value))
        return f"{amount:,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(value)


# ====== Nuevas Template Tags para Métricas Detalladas ======

@register.simple_tag
def get_evaluadores_stats(subscription):
    """
    Obtiene estadísticas detalladas de evaluadores para un módulo específico
    """
    try:
        from apps.evaluadores.models import Evaluador
        from django.db.models import Q
        
        # Validación de seguridad: verificar que la suscripción tenga usuario
        if not hasattr(subscription, 'user') and not hasattr(subscription, 'usuario'):
            return {
                'total_evaluadores': 0,
                'evaluadores_activos': 0,
                'evaluadores_inactivos': 0,
                'evaluadores_pendientes': 0,
            }
        
        user = subscription.user if hasattr(subscription, 'user') else subscription.usuario
        
        # Validación adicional: el usuario debe existir
        if not user or not user.is_authenticated:
            return {
                'total_evaluadores': 0,
                'evaluadores_activos': 0,
                'evaluadores_inactivos': 0,
                'evaluadores_pendientes': 0,
            }
            
        module_name = subscription.plan.module.name
        
        # Base queryset para evaluadores del usuario autenticado únicamente
        evaluadores_qs = Evaluador.objects.filter(usuario_principal=user)
        
        # Para SQLite, necesitamos una aproximación diferente
        # Filtrar todos los evaluadores del usuario y luego filtrar en Python
        evaluadores_modulo = evaluadores_qs.all()
        
        # Filtrar en Python por compatibilidad con SQLite
        filtered_evaluadores = []
        for evaluador in evaluadores_modulo:
            # Verificar que el evaluador pertenece al usuario correcto (doble validación)
            if evaluador.usuario_principal_id != user.id:
                continue
                
            modulos = evaluador.modulos_permitidos or []
            
            # Lógica corregida: 
            # - Si modulos está vacío (sin restricciones), tiene acceso a todos
            # - Si no está vacío, debe estar específicamente en la lista
            if len(modulos) == 0 or module_name in modulos:
                filtered_evaluadores.append(evaluador)
        
        # Calcular estadísticas
        total = len(filtered_evaluadores)
        activos = len([e for e in filtered_evaluadores if e.estado == 'active'])
        inactivos = len([e for e in filtered_evaluadores if e.estado == 'inactive'])
        pendientes = len([e for e in filtered_evaluadores if e.estado == 'pending'])
        
        stats = {
            'total_evaluadores': total,
            'evaluadores_activos': activos,
            'evaluadores_inactivos': inactivos,
            'evaluadores_pendientes': pendientes,
        }
        
        return stats
        
    except (ImportError, Exception) as e:
        return {
            'total_evaluadores': 0,
            'evaluadores_activos': 0,
            'evaluadores_inactivos': 0,
            'evaluadores_pendientes': 0,
        }


@register.simple_tag
def get_detailed_module_stats(subscription):
    """
    Obtiene estadísticas detalladas específicas por módulo
    """
    try:
        # Validación de seguridad: verificar que la suscripción tenga usuario
        if not hasattr(subscription, 'user') and not hasattr(subscription, 'usuario'):
            return {
                'module_name': 'unknown',
                'module_display_name': 'Módulo',
                'hoteles_total': 0,
                'hoteles_activos': 0,
                'conjuntos_total': 0,
                'conjuntos_con_evaluaciones': 0,
                'proyectos_total': 0,
                'proyectos_activos': 0,
                'evaluaciones_total': 0,
                'evaluaciones_mes': 0,
                'evaluaciones_completadas': 0,
                'evaluaciones_pendientes': 0,
            }
            
        user = subscription.user if hasattr(subscription, 'user') else subscription.usuario
        
        # Validación adicional: el usuario debe existir y estar autenticado
        if not user or not user.is_authenticated:
            return {
                'module_name': 'unknown',
                'module_display_name': 'Módulo',
                'hoteles_total': 0,
                'hoteles_activos': 0,
                'conjuntos_total': 0,
                'conjuntos_con_evaluaciones': 0,
                'proyectos_total': 0,
                'proyectos_activos': 0,
                'evaluaciones_total': 0,
                'evaluaciones_mes': 0,
                'evaluaciones_completadas': 0,
                'evaluaciones_pendientes': 0,
            }
            
        module_name = subscription.plan.module.name
        
        stats = {
            'module_name': module_name,
            'module_display_name': _get_module_display_name(module_name)
        }
        
        if module_name == 'risk_hoteles':
            stats.update(_get_hoteles_detailed_stats(user))
        elif module_name == 'risk_conjuntos':
            stats.update(_get_conjuntos_detailed_stats(user))
        elif module_name == 'security_probabilistic':
            stats.update(_get_security_detailed_stats(user))
            
        return stats
        
    except Exception as e:
        return {
            'module_name': module_name if 'module_name' in locals() else 'unknown',
            'module_display_name': 'Módulo',
            'hoteles_total': 0,
            'hoteles_activos': 0,
            'conjuntos_total': 0,
            'conjuntos_con_evaluaciones': 0,
            'proyectos_total': 0,
            'proyectos_activos': 0,
            'evaluaciones_total': 0,
            'evaluaciones_mes': 0,
            'evaluaciones_completadas': 0,
            'evaluaciones_pendientes': 0,
        }


def _get_module_display_name(module_name):
    """Retorna el nombre legible del módulo"""
    names = {
        'risk_hoteles': 'Risk Hoteles',
        'risk_conjuntos': 'Risk Conjuntos',
        'security_probabilistic': 'Security Probabilistic'
    }
    return names.get(module_name, module_name.replace('_', ' ').title())


def _get_hoteles_detailed_stats(user):
    """Estadísticas detalladas para Risk Hoteles"""
    try:
        from apps.risk_hoteles.models import Hotel, SecurityAssessment
        from django.utils import timezone
        
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        hoteles = Hotel.objects.filter(owner=user)
        evaluaciones = SecurityAssessment.objects.filter(hotel__owner=user)
        
        return {
            'hoteles_total': hoteles.count(),
            'hoteles_activos': hoteles.filter(is_active=True).count(),
            'evaluaciones_total': evaluaciones.count(),
            'evaluaciones_mes': evaluaciones.filter(created_at__gte=current_month).count(),
            'evaluaciones_completadas': evaluaciones.filter(status='completed').count(),
            'evaluaciones_pendientes': evaluaciones.filter(status__in=['pending', 'in_progress']).count(),
        }
    except ImportError:
        return {
            'hoteles_total': 0,
            'hoteles_activos': 0,
            'evaluaciones_total': 0,
            'evaluaciones_mes': 0,
            'evaluaciones_completadas': 0,
            'evaluaciones_pendientes': 0,
        }


def _get_conjuntos_detailed_stats(user):
    """Estadísticas detalladas para Risk Conjuntos"""
    try:
        from apps.risk_conjuntos.models import Conjunto, EvaluacionSeguridad, EvaluacionRiesgo
        from django.utils import timezone
        from django.db.models import Count, Q
        
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Conjuntos del usuario
        conjuntos = Conjunto.objects.filter(propietario=user, activo=True)
        
        # Evaluaciones del sistema legacy (EvaluacionSeguridad)
        evaluaciones_legacy = EvaluacionSeguridad.objects.filter(conjunto__propietario=user)
        
        # Evaluaciones del sistema principal (EvaluacionRiesgo)
        evaluaciones_principales = EvaluacionRiesgo.objects.filter(
            conjunto__propietario=user,
            deleted_at__isnull=True  # Solo las no borradas
        )
        
        # Totales combinados
        total_evaluaciones_legacy = evaluaciones_legacy.count()
        total_evaluaciones_principales = evaluaciones_principales.count()
        total_evaluaciones = total_evaluaciones_legacy + total_evaluaciones_principales
        
        # Evaluaciones del mes actual
        evaluaciones_mes_legacy = evaluaciones_legacy.filter(fecha_evaluacion__gte=current_month).count()
        evaluaciones_mes_principales = evaluaciones_principales.filter(fecha_evaluacion__gte=current_month).count()
        evaluaciones_mes = evaluaciones_mes_legacy + evaluaciones_mes_principales
        
        # Evaluaciones completadas
        evaluaciones_completadas_legacy = evaluaciones_legacy.filter(estado='completada').count()
        evaluaciones_completadas_principales = evaluaciones_principales.filter(estado='completada').count()
        evaluaciones_completadas = evaluaciones_completadas_legacy + evaluaciones_completadas_principales
        
        # Evaluaciones pendientes
        evaluaciones_pendientes_legacy = evaluaciones_legacy.filter(estado__in=['borrador', 'en_progreso']).count()
        evaluaciones_pendientes_principales = evaluaciones_principales.filter(estado__in=['borrador', 'en_progreso']).count()
        evaluaciones_pendientes = evaluaciones_pendientes_legacy + evaluaciones_pendientes_principales
        
        # Conjuntos con evaluaciones
        conjuntos_con_eval_legacy = conjuntos.annotate(
            eval_count_legacy=Count('evaluaciones_seguridad')
        ).filter(eval_count_legacy__gt=0).count()
        
        conjuntos_con_eval_principales = conjuntos.annotate(
            eval_count_principales=Count('evaluaciones_riesgo', filter=Q(evaluaciones_riesgo__deleted_at__isnull=True))
        ).filter(eval_count_principales__gt=0).count()
        
        # Total de conjuntos con al menos una evaluación (sin duplicados)
        conjuntos_con_evaluaciones = conjuntos.annotate(
            total_evaluaciones=Count('evaluaciones_seguridad') + Count('evaluaciones_riesgo', filter=Q(evaluaciones_riesgo__deleted_at__isnull=True))
        ).filter(total_evaluaciones__gt=0).count()
        
        return {
            'conjuntos_total': conjuntos.count(),
            'conjuntos_activos': conjuntos.count(),  # Alias para compatibilidad
            'conjuntos_con_evaluaciones': conjuntos_con_evaluaciones,
            'evaluaciones_total': total_evaluaciones,
            'evaluaciones_mes': evaluaciones_mes,
            'evaluaciones_completadas': evaluaciones_completadas,
            'evaluaciones_pendientes': evaluaciones_pendientes,
            # Estadísticas adicionales por sistema
            'evaluaciones_legacy': total_evaluaciones_legacy,
            'evaluaciones_principales': total_evaluaciones_principales,
        }
    except ImportError:
        return {
            'conjuntos_total': 0,
            'conjuntos_activos': 0,
            'conjuntos_con_evaluaciones': 0,
            'evaluaciones_total': 0,
            'evaluaciones_mes': 0,
            'evaluaciones_completadas': 0,
            'evaluaciones_pendientes': 0,
            'evaluaciones_legacy': 0,
            'evaluaciones_principales': 0,
        }


def _get_security_detailed_stats(user):
    """Estadísticas detalladas para Security Probabilistic"""
    try:
        from apps.security_probabilistic.models import SecurityProject, RiskAssessment
        from django.utils import timezone
        
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        projects = SecurityProject.objects.filter(owner=user, is_active=True)
        assessments = RiskAssessment.objects.filter(project__owner=user)
        
        return {
            'proyectos_total': projects.count(),
            'proyectos_activos': projects.filter(status='active').count(),
            'evaluaciones_total': assessments.count(),
            'evaluaciones_mes': assessments.filter(created_at__gte=current_month).count(),
            'evaluaciones_completadas': assessments.filter(status='completed').count(),
            'evaluaciones_pendientes': assessments.filter(status__in=['pending', 'in_progress']).count(),
        }
    except ImportError:
        return {
            'proyectos_total': 0,
            'proyectos_activos': 0,
            'evaluaciones_total': 0,
            'evaluaciones_mes': 0,
            'evaluaciones_completadas': 0,
            'evaluaciones_pendientes': 0,
        }


@register.inclusion_tag('dashboard/components/metrics_detail_card.html')
def metrics_detail_card(title, value, icon, color='primary', description='', trend=None):
    """
    Render a detailed metrics card component
    """
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'color': color,
        'description': description,
        'trend': trend,
    }


@register.filter
def percentage(value, total):
    """Calculate percentage between two values"""
    try:
        if total == 0:
            return 0
        return round((value / total) * 100, 1)
    except (TypeError, ZeroDivisionError):
        return 0


@register.filter  
def format_trend(current, previous=None):
    """Format trend indicator"""
    if previous is None or previous == 0:
        return None
        
    try:
        change = ((current - previous) / previous) * 100
        if change > 0:
            return {'value': f'+{change:.1f}%', 'class': 'positive'}
        elif change < 0:
            return {'value': f'{change:.1f}%', 'class': 'negative'}
        else:
            return {'value': '0%', 'class': 'neutral'}
    except:
        return None
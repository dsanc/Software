"""
Views para el sistema de analytics del módulo risk_hoteles
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
import json

from .models_analytics import (
    AnalyticsEvent, UserSession, PageView, ClickEvent,
    ConversionGoal, Conversion, AnalyticsReport
)


@staff_member_required
def analytics_dashboard(request):
    """Dashboard principal de analytics"""
    # Obtener métricas básicas
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Sesiones activas
    active_sessions = UserSession.objects.filter(
        end_time__isnull=True,
        start_time__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    # Métricas del día
    daily_sessions = UserSession.objects.filter(
        start_time__date=today
    ).count()
    
    daily_page_views = PageView.objects.filter(
        timestamp__date=today
    ).count()
    
    # Métricas de la semana
    weekly_sessions = UserSession.objects.filter(
        start_time__date__gte=week_ago
    ).count()
    
    weekly_page_views = PageView.objects.filter(
        timestamp__date__gte=week_ago
    ).count()
    
    # Páginas más visitadas
    top_pages = PageView.objects.filter(
        timestamp__date__gte=week_ago
    ).values('page_url').annotate(
        views=Count('id')
    ).order_by('-views')[:10]
    
    # Eventos más frecuentes
    top_events = AnalyticsEvent.objects.filter(
        timestamp__date__gte=week_ago
    ).values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'title': 'Analytics Dashboard',
        'active_sessions': active_sessions,
        'daily_sessions': daily_sessions,
        'daily_page_views': daily_page_views,
        'weekly_sessions': weekly_sessions,
        'weekly_page_views': weekly_page_views,
        'top_pages': top_pages,
        'top_events': top_events,
    }
    
    return render(request, 'risk_hoteles/admin/analytics_dashboard.html', context)


@staff_member_required
def analytics_events(request):
    """Vista de eventos de analytics"""
    events = AnalyticsEvent.objects.all().order_by('-timestamp')
    
    # Filtros
    event_type = request.GET.get('event_type')
    if event_type:
        events = events.filter(event_type=event_type)
    
    user_id = request.GET.get('user_id')
    if user_id:
        events = events.filter(user_id=user_id)
    
    date_from = request.GET.get('date_from')
    if date_from:
        events = events.filter(timestamp__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        events = events.filter(timestamp__date__lte=date_to)
    
    # Paginación
    paginator = Paginator(events, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Tipos de eventos únicos para el filtro
    event_types = AnalyticsEvent.objects.values_list(
        'event_type', flat=True
    ).distinct()
    
    context = {
        'title': 'Eventos de Analytics',
        'page_obj': page_obj,
        'event_types': event_types,
        'current_filters': {
            'event_type': event_type,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'risk_hoteles/admin/analytics_events.html', context)


@staff_member_required
def analytics_sessions(request):
    """Vista de sesiones de usuario"""
    sessions = UserSession.objects.all().order_by('-start_time')
    
    # Filtros
    user_id = request.GET.get('user_id')
    if user_id:
        sessions = sessions.filter(user_id=user_id)
    
    date_from = request.GET.get('date_from')
    if date_from:
        sessions = sessions.filter(start_time__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        sessions = sessions.filter(start_time__date__lte=date_to)
    
    # Paginación
    paginator = Paginator(sessions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Sesiones de Usuario',
        'page_obj': page_obj,
        'current_filters': {
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'risk_hoteles/admin/analytics_sessions.html', context)


@staff_member_required
def analytics_api(request):
    """API para obtener datos de analytics"""
    action = request.GET.get('action', 'overview')
    
    try:
        if action == 'overview':
            data = get_analytics_overview()
        elif action == 'events':
            data = get_recent_events()
        elif action == 'sessions':
            data = get_session_stats()
        elif action == 'conversions':
            data = get_conversion_stats()
        else:
            return JsonResponse({
                'success': False,
                'error': 'Acción no válida'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'data': data,
            'timestamp': timezone.now().isoformat()
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def track_event(request):
    """Endpoint para registrar eventos de analytics"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Crear evento
        event = AnalyticsEvent.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=data.get('session_id', ''),
            event_type=data.get('event_type', ''),
            event_data=data.get('event_data', {}),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'event_id': str(event.id)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def track_page_view(request):
    """Endpoint para registrar vistas de página"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=405)
    
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        # Obtener o crear sesión
        session, created = UserSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': request.user if request.user.is_authenticated else None,
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'pages_visited': 0
            }
        )
        
        # Crear vista de página
        page_view = PageView.objects.create(
            session=session,
            page_url=data.get('page_url', ''),
            page_title=data.get('page_title', ''),
            time_on_page=data.get('time_on_page')
        )
        
        # Actualizar contador de páginas visitadas
        session.pages_visited += 1
        session.save()
        
        return JsonResponse({
            'success': True,
            'page_view_id': str(page_view.id)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_analytics_overview():
    """Obtener resumen de analytics"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    return {
        'total_events': AnalyticsEvent.objects.count(),
        'total_sessions': UserSession.objects.count(),
        'total_page_views': PageView.objects.count(),
        'events_today': AnalyticsEvent.objects.filter(timestamp__date=today).count(),
        'sessions_today': UserSession.objects.filter(start_time__date=today).count(),
        'page_views_today': PageView.objects.filter(timestamp__date=today).count(),
        'events_week': AnalyticsEvent.objects.filter(timestamp__date__gte=week_ago).count(),
        'sessions_week': UserSession.objects.filter(start_time__date__gte=week_ago).count(),
        'page_views_week': PageView.objects.filter(timestamp__date__gte=week_ago).count(),
    }


def get_recent_events():
    """Obtener eventos recientes"""
    events = AnalyticsEvent.objects.order_by('-timestamp')[:100]
    
    return [{
        'id': str(event.id),
        'event_type': event.event_type,
        'timestamp': event.timestamp.isoformat(),
        'user': event.user.username if event.user else 'Anonymous',
        'session_id': event.session_id,
        'event_data': event.event_data
    } for event in events]


def get_session_stats():
    """Obtener estadísticas de sesiones"""
    today = timezone.now().date()
    
    return {
        'active_sessions': UserSession.objects.filter(
            end_time__isnull=True,
            start_time__gte=timezone.now() - timedelta(hours=1)
        ).count(),
        'total_sessions_today': UserSession.objects.filter(
            start_time__date=today
        ).count(),
        'avg_session_duration': get_avg_session_duration(),
        'avg_pages_per_session': UserSession.objects.aggregate(
            avg_pages=Avg('pages_visited')
        )['avg_pages'] or 0
    }


def get_conversion_stats():
    """Obtener estadísticas de conversiones"""
    active_goals = ConversionGoal.objects.filter(is_active=True)
    
    stats = []
    for goal in active_goals:
        conversions = Conversion.objects.filter(goal=goal)
        stats.append({
            'goal_name': goal.name,
            'total_conversions': conversions.count(),
            'conversions_today': conversions.filter(
                timestamp__date=timezone.now().date()
            ).count(),
            'conversion_rate': calculate_conversion_rate(goal)
        })
    
    return stats


def get_avg_session_duration():
    """Calcular duración promedio de sesiones"""
    finished_sessions = UserSession.objects.filter(
        end_time__isnull=False
    )
    
    if not finished_sessions.exists():
        return 0
    
    total_duration = 0
    count = 0
    
    for session in finished_sessions:
        duration = (session.end_time - session.start_time).total_seconds()
        total_duration += duration
        count += 1
    
    return total_duration / count if count > 0 else 0


def calculate_conversion_rate(goal):
    """Calcular tasa de conversión para un objetivo"""
    total_sessions = UserSession.objects.count()
    conversions = Conversion.objects.filter(goal=goal).count()
    
    if total_sessions == 0:
        return 0
    
    return (conversions / total_sessions) * 100


def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@staff_member_required
def analytics_users(request):
    """Vista de usuarios de analytics"""
    sessions = UserSession.objects.filter(
        user__isnull=False
    ).select_related('user').order_by('-start_time')
    
    # Paginación
    paginator = Paginator(sessions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Usuarios de Analytics',
        'page_obj': page_obj,
    }
    
    return render(request, 'risk_hoteles/admin/analytics_users.html', context)


@staff_member_required
def analytics_performance(request):
    """Vista de performance de analytics"""
    context = {
        'title': 'Performance Analytics',
        'metrics': get_performance_analytics(),
    }
    
    return render(request, 'risk_hoteles/admin/analytics_performance.html', context)


@staff_member_required
def analytics_conversions(request):
    """Vista de conversiones de analytics"""
    goals = ConversionGoal.objects.filter(is_active=True)
    
    context = {
        'title': 'Conversiones Analytics',
        'goals': goals,
        'conversion_stats': get_conversion_stats(),
    }
    
    return render(request, 'risk_hoteles/admin/analytics_conversions.html', context)


@staff_member_required
def user_journey(request, user_id):
    """Vista del journey de un usuario específico"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = get_object_or_404(User, id=user_id)
    sessions = UserSession.objects.filter(user=user).order_by('-start_time')
    
    context = {
        'title': f'Journey de {user.username}',
        'user': user,
        'sessions': sessions,
    }
    
    return render(request, 'risk_hoteles/admin/user_journey.html', context)


@csrf_exempt
def track_event_api(request):
    """API para rastrear eventos"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            event = AnalyticsEvent.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=data.get('session_id', ''),
                event_type=data.get('event_type', ''),
                event_data=data.get('event_data', {}),
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return JsonResponse({
                'success': True,
                'event_id': str(event.id)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)


@csrf_exempt
def track_click_api(request):
    """API para rastrear clicks"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            
            session, created = UserSession.objects.get_or_create(
                session_id=session_id,
                defaults={
                    'user': request.user if request.user.is_authenticated else None,
                    'ip_address': get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )
            
            click_event = ClickEvent.objects.create(
                session=session,
                element_id=data.get('element_id'),
                element_class=data.get('element_class'),
                element_text=data.get('element_text'),
                page_url=data.get('page_url', ''),
                coordinates_x=data.get('x'),
                coordinates_y=data.get('y')
            )
            
            return JsonResponse({
                'success': True,
                'click_id': str(click_event.id)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)


@csrf_exempt
def track_performance_api(request):
    """API para rastrear performance"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Crear evento de performance
            AnalyticsEvent.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=data.get('session_id', ''),
                event_type='performance',
                event_data=data,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Performance data tracked'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)


@csrf_exempt
def track_batch_api(request):
    """API para rastrear eventos en lote"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            events = data.get('events', [])
            
            created_events = []
            for event_data in events:
                event = AnalyticsEvent.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_id=event_data.get('session_id', ''),
                    event_type=event_data.get('event_type', ''),
                    event_data=event_data.get('event_data', {}),
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                created_events.append(str(event.id))
            
            return JsonResponse({
                'success': True,
                'events_created': len(created_events),
                'event_ids': created_events
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)


@staff_member_required
def analytics_api_data(request):
    """API para obtener datos de analytics para dashboard"""
    try:
        data_type = request.GET.get('type', 'overview')
        
        if data_type == 'overview':
            data = get_analytics_overview()
        elif data_type == 'events':
            data = get_recent_events()
        elif data_type == 'sessions':
            data = get_session_stats()
        elif data_type == 'conversions':
            data = get_conversion_stats()
        elif data_type == 'performance':
            data = get_performance_analytics()
        else:
            return JsonResponse({
                'success': False,
                'error': 'Tipo de datos no válido'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'data': data,
            'timestamp': timezone.now().isoformat()
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_performance_analytics():
    """Obtener métricas de performance para analytics"""
    today = timezone.now().date()
    
    return {
        'avg_load_time': 1.2,  # En un entorno real esto vendría de métricas reales
        'bounce_rate': 25.5,
        'pages_per_session': 3.2,
        'conversion_rate': 12.8,
        'active_users': UserSession.objects.filter(
            end_time__isnull=True,
            start_time__gte=timezone.now() - timedelta(hours=1)
        ).count(),
        'page_views_today': PageView.objects.filter(
            timestamp__date=today
        ).count(),
    }
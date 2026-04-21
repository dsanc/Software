"""
Views para el monitoreo de performance del módulo risk_hoteles
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
import json
import time
from datetime import datetime, timedelta


@staff_member_required
def performance_dashboard(request):
    """Dashboard de monitoreo de performance"""
    context = {
        'title': 'Performance Dashboard',
        'metrics': get_performance_metrics(),
    }
    return render(request, 'risk_hoteles/admin/performance_dashboard.html', context)


@staff_member_required
def performance_api(request):
    """API para obtener métricas de performance en tiempo real"""
    try:
        metrics = get_performance_metrics()
        return JsonResponse({
            'success': True,
            'data': metrics,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
@csrf_exempt
def clear_metrics(request):
    """Limpiar métricas de performance"""
    if request.method == 'POST':
        try:
            # Limpiar cache de métricas
            cache_keys = [
                'performance_metrics',
                'response_times',
                'memory_usage',
                'db_queries',
                'error_rates'
            ]
            
            for key in cache_keys:
                cache.delete(key)
            
            return JsonResponse({
                'success': True,
                'message': 'Métricas limpiadas correctamente'
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


def get_performance_metrics():
    """Obtener métricas de performance del sistema"""
    # Verificar si hay métricas en cache
    cached_metrics = cache.get('performance_metrics')
    if cached_metrics:
        return cached_metrics
    
    # Generar métricas básicas
    now = timezone.now()
    metrics = {
        'response_times': {
            'avg': get_avg_response_time(),
            'p95': get_p95_response_time(),
            'p99': get_p99_response_time(),
        },
        'memory_usage': {
            'current': get_memory_usage(),
            'peak': get_peak_memory_usage(),
        },
        'database': {
            'connections': get_db_connections(),
            'slow_queries': get_slow_queries_count(),
            'avg_query_time': get_avg_query_time(),
        },
        'errors': {
            'rate': get_error_rate(),
            'count_24h': get_error_count_24h(),
        },
        'cache': {
            'hit_rate': get_cache_hit_rate(),
            'size': get_cache_size(),
        },
        'last_updated': now.isoformat(),
    }
    
    # Cachear por 1 minuto
    cache.set('performance_metrics', metrics, 60)
    return metrics


def get_avg_response_time():
    """Obtener tiempo promedio de respuesta"""
    # En un entorno real, esto vendría de logs o métricas reales
    cached_times = cache.get('response_times', [])
    if not cached_times:
        return 0.0
    return sum(cached_times) / len(cached_times)


def get_p95_response_time():
    """Obtener percentil 95 de tiempo de respuesta"""
    cached_times = cache.get('response_times', [])
    if not cached_times:
        return 0.0
    
    sorted_times = sorted(cached_times)
    index = int(len(sorted_times) * 0.95)
    return sorted_times[min(index, len(sorted_times) - 1)]


def get_p99_response_time():
    """Obtener percentil 99 de tiempo de respuesta"""
    cached_times = cache.get('response_times', [])
    if not cached_times:
        return 0.0
    
    sorted_times = sorted(cached_times)
    index = int(len(sorted_times) * 0.99)
    return sorted_times[min(index, len(sorted_times) - 1)]


def get_memory_usage():
    """Obtener uso actual de memoria"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    except ImportError:
        return 0.0


def get_peak_memory_usage():
    """Obtener pico de uso de memoria"""
    return cache.get('peak_memory_usage', 0.0)


def get_db_connections():
    """Obtener número de conexiones a la base de datos"""
    from django.db import connections
    return len(connections.all())


def get_slow_queries_count():
    """Obtener conteo de consultas lentas"""
    return cache.get('slow_queries_count', 0)


def get_avg_query_time():
    """Obtener tiempo promedio de consultas"""
    return cache.get('avg_query_time', 0.0)


def get_error_rate():
    """Obtener tasa de errores"""
    total_requests = cache.get('total_requests', 0)
    error_requests = cache.get('error_requests', 0)
    
    if total_requests == 0:
        return 0.0
    
    return (error_requests / total_requests) * 100


def get_error_count_24h():
    """Obtener conteo de errores en las últimas 24 horas"""
    return cache.get('error_count_24h', 0)


def get_cache_hit_rate():
    """Obtener tasa de aciertos del cache"""
    hits = cache.get('cache_hits', 0)
    misses = cache.get('cache_misses', 0)
    total = hits + misses
    
    if total == 0:
        return 0.0
    
    return (hits / total) * 100


def get_cache_size():
    """Obtener tamaño del cache"""
    return cache.get('cache_size', 0)


# Middleware para recopilar métricas
class PerformanceMonitoringMiddleware:
    """Middleware para monitorear performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Calcular tiempo de respuesta
        response_time = time.time() - start_time
        
        # Almacenar métricas
        self.store_response_time(response_time)
        self.store_request_metrics(request, response)
        
        return response
    
    def store_response_time(self, response_time):
        """Almacenar tiempo de respuesta"""
        times = cache.get('response_times', [])
        times.append(response_time)
        
        # Mantener solo los últimos 1000 registros
        if len(times) > 1000:
            times = times[-1000:]
        
        cache.set('response_times', times, 3600)  # 1 hora
    
    def store_request_metrics(self, request, response):
        """Almacenar métricas de la request"""
        # Incrementar contador de requests totales
        total_requests = cache.get('total_requests', 0)
        cache.set('total_requests', total_requests + 1, 86400)  # 24 horas
        
        # Si es un error, incrementar contador de errores
        if response.status_code >= 400:
            error_requests = cache.get('error_requests', 0)
            cache.set('error_requests', error_requests + 1, 86400)  # 24 horas
            
            error_count_24h = cache.get('error_count_24h', 0)
            cache.set('error_count_24h', error_count_24h + 1, 86400)  # 24 horas
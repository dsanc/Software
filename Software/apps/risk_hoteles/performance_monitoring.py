"""
Sistema de monitoreo de performance para risk_hoteles
"""
import time
import threading
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import json

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Clase para recopilar y gestionar métricas de performance"""
    
    def __init__(self):
        self.start_time = time.time()
        self._lock = threading.Lock()
        self.metrics = {
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'db_queries': [],
            'cache_hits': 0,
            'cache_misses': 0,
        }
    
    def record_response_time(self, response_time):
        """Registrar tiempo de respuesta"""
        with self._lock:
            self.metrics['response_times'].append({
                'time': response_time,
                'timestamp': timezone.now().isoformat()
            })
            
            # Mantener solo los últimos 100 registros
            if len(self.metrics['response_times']) > 100:
                self.metrics['response_times'] = self.metrics['response_times'][-100:]
    
    def record_memory_usage(self):
        """Registrar uso de memoria"""
        try:
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
            else:
                # Fallback: usar estimación básica
                memory_mb = 100.0  # Valor estimado
            
            with self._lock:
                self.metrics['memory_usage'].append({
                    'memory_mb': memory_mb,
                    'timestamp': timezone.now().isoformat()
                })
                
                # Mantener solo los últimos 50 registros
                if len(self.metrics['memory_usage']) > 50:
                    self.metrics['memory_usage'] = self.metrics['memory_usage'][-50:]
                
        except Exception as e:
            logger.warning(f"Error recording memory usage: {e}")
    
    def record_cpu_usage(self):
        """Registrar uso de CPU"""
        try:
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=1)
            else:
                # Fallback: usar estimación básica
                cpu_percent = 10.0  # Valor estimado
            
            with self._lock:
                self.metrics['cpu_usage'].append({
                    'cpu_percent': cpu_percent,
                    'timestamp': timezone.now().isoformat()
                })
                
                # Mantener solo los últimos 50 registros
                if len(self.metrics['cpu_usage']) > 50:
                    self.metrics['cpu_usage'] = self.metrics['cpu_usage'][-50:]
                
        except Exception as e:
            logger.warning(f"Error recording CPU usage: {e}")
    
    def record_db_query(self, query_time, query_sql):
        """Registrar consulta de base de datos"""
        with self._lock:
            self.metrics['db_queries'].append({
                'time': query_time,
                'sql': query_sql[:100] + '...' if len(query_sql) > 100 else query_sql,
                'timestamp': timezone.now().isoformat()
            })
            
            # Mantener solo las últimas 20 consultas
            if len(self.metrics['db_queries']) > 20:
                self.metrics['db_queries'] = self.metrics['db_queries'][-20:]
    
    def record_cache_hit(self):
        """Registrar acierto de cache"""
        with self._lock:
            self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """Registrar fallo de cache"""
        with self._lock:
            self.metrics['cache_misses'] += 1
    
    def get_summary(self):
        """Obtener resumen de métricas"""
        with self._lock:
            response_times = [m['time'] for m in self.metrics['response_times']]
            total_db_queries = len(self.metrics['db_queries'])
            cache_hits = self.metrics['cache_hits']
            cache_misses = self.metrics['cache_misses']
            current_memory = self.metrics['memory_usage'][-1]['memory_mb'] if self.metrics['memory_usage'] else 0
            current_cpu = self.metrics['cpu_usage'][-1]['cpu_percent'] if self.metrics['cpu_usage'] else 0
        
        total_cache = cache_hits + cache_misses
        summary = {
            'uptime': time.time() - self.start_time,
            'total_requests': len(response_times),
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'total_db_queries': total_db_queries,
            'cache_hit_rate': (cache_hits / total_cache * 100) if total_cache else 0,
            'current_memory': current_memory,
            'current_cpu': current_cpu,
        }
        
        return summary


# Instancia global de métricas
performance_metrics = PerformanceMetrics()


class AlertsPerformanceMiddleware:
    """Middleware para monitorear performance de alertas"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Registrar memoria y CPU periódicamente
        if hasattr(self, '_last_system_check'):
            if time.time() - self._last_system_check > 60:  # Cada minuto
                performance_metrics.record_memory_usage()
                performance_metrics.record_cpu_usage()
                self._last_system_check = time.time()
        else:
            self._last_system_check = time.time()
        
        response = self.get_response(request)
        
        # Calcular tiempo de respuesta
        response_time = time.time() - start_time
        performance_metrics.record_response_time(response_time)
        
        # Registrar consultas de base de datos
        if hasattr(connection, 'queries'):
            for query in connection.queries:
                if 'time' in query:
                    performance_metrics.record_db_query(
                        float(query['time']),
                        query['sql']
                    )
        
        return response


def get_performance_dashboard_data():
    """Obtener datos para el dashboard de performance"""
    try:
        summary = performance_metrics.get_summary()
        
        dashboard_data = {
            'status': 'healthy' if summary['avg_response_time'] < 1.0 else 'warning',
            'uptime_hours': summary['uptime'] / 3600,
            'total_requests': summary['total_requests'],
            'avg_response_time': round(summary['avg_response_time'], 3),
            'max_response_time': round(summary['max_response_time'], 3),
            'min_response_time': round(summary['min_response_time'], 3),
            'db_queries_count': summary['total_db_queries'],
            'cache_hit_rate': round(summary['cache_hit_rate'], 1),
            'memory_usage_mb': round(summary['current_memory'], 1),
            'cpu_usage_percent': round(summary['current_cpu'], 1),
            'alerts_active': get_active_alerts_count(),
            'system_health': get_system_health_status(),
            'last_updated': timezone.now().isoformat(),
        }
        
        # Cachear los datos por 30 segundos
        cache.set('performance_dashboard_data', dashboard_data, 30)
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting performance dashboard data: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'last_updated': timezone.now().isoformat(),
        }


def get_active_alerts_count():
    """Obtener número de alertas activas"""
    try:
        from .models import AlertaRiesgo
        return AlertaRiesgo.objects.filter(estado='ACTIVA').count()
    except Exception as e:
        logger.warning(f"Error getting active alerts count: {e}")
        return 0


def get_system_health_status():
    """Determinar estado de salud del sistema"""
    try:
        summary = performance_metrics.get_summary()
        
        # Criterios de salud
        health_score = 100
        
        # Penalizar por tiempo de respuesta alto
        if summary['avg_response_time'] > 2.0:
            health_score -= 30
        elif summary['avg_response_time'] > 1.0:
            health_score -= 15
        
        # Penalizar por uso alto de memoria
        if summary['current_memory'] > 500:  # 500 MB
            health_score -= 20
        elif summary['current_memory'] > 300:  # 300 MB
            health_score -= 10
        
        # Penalizar por uso alto de CPU
        if summary['current_cpu'] > 80:
            health_score -= 25
        elif summary['current_cpu'] > 60:
            health_score -= 15
        
        # Penalizar por baja tasa de cache hits
        if summary['cache_hit_rate'] < 50:
            health_score -= 15
        
        # Determinar estado
        if health_score >= 80:
            return 'excellent'
        elif health_score >= 60:
            return 'good'
        elif health_score >= 40:
            return 'warning'
        else:
            return 'critical'
            
    except Exception as e:
        logger.error(f"Error determining system health: {e}")
        return 'unknown'


def reset_performance_metrics():
    """Reiniciar métricas de performance"""
    global performance_metrics
    performance_metrics = PerformanceMetrics()
    cache.delete('performance_dashboard_data')
    logger.info("Performance metrics reset")


def export_performance_data():
    """Exportar datos de performance"""
    try:
        with performance_metrics._lock:
            metrics_snapshot = {
                'response_times': list(performance_metrics.metrics['response_times']),
                'memory_usage': list(performance_metrics.metrics['memory_usage']),
                'cpu_usage': list(performance_metrics.metrics['cpu_usage']),
                'db_queries': list(performance_metrics.metrics['db_queries']),
                'cache_hits': performance_metrics.metrics['cache_hits'],
                'cache_misses': performance_metrics.metrics['cache_misses'],
            }
        data = {
            'metrics': metrics_snapshot,
            'summary': performance_metrics.get_summary(),
            'export_time': timezone.now().isoformat(),
        }
        return json.dumps(data, indent=2)
    except Exception as e:
        logger.error(f"Error exporting performance data: {e}")
        return None


# Función para inicializar el monitoreo en un hilo separado
def start_background_monitoring():
    """Iniciar monitoreo en background"""
    def monitor_loop():
        while True:
            try:
                performance_metrics.record_memory_usage()
                performance_metrics.record_cpu_usage()
                time.sleep(60)  # Cada minuto
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                time.sleep(60)
    
    # Ejecutar en hilo separado
    monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitoring_thread.start()
    logger.info("Background performance monitoring started")


# Inicializar monitoreo al importar el módulo
if getattr(settings, 'ENABLE_PERFORMANCE_MONITORING', True):
    start_background_monitoring()
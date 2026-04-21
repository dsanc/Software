"""
Optimizaciones de performance para el módulo risk_conjuntos
"""
from django.db import models
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import hashlib


class OptimizedQueryMixin:
    """
    Mixin para optimizar consultas frecuentes
    """
    
    @classmethod
    def get_conjuntos_usuario_optimized(cls, user):
        """
        Consulta optimizada para obtener conjuntos de un usuario
        """
        cache_key = f'conjuntos_user_{user.id}'
        conjuntos = cache.get(cache_key)
        
        if conjuntos is None:
            conjuntos = cls.objects.filter(
                propietario=user, 
                activo=True
            ).select_related(
                'tipo_conjunto'
            ).prefetch_related(
                'evaluaciones_riesgo'
            ).order_by('-fecha_creacion')
            
            # Cache por 15 minutos
            cache.set(cache_key, conjuntos, 60 * 15)
        
        return conjuntos
    
    @classmethod
    def get_evaluaciones_usuario_optimized(cls, user):
        """
        Consulta optimizada para evaluaciones de un usuario
        """
        cache_key = f'evaluaciones_user_{user.id}'
        evaluaciones = cache.get(cache_key)
        
        if evaluaciones is None:
            evaluaciones = cls.objects.filter(
                conjunto__propietario=user
            ).select_related(
                'conjunto',
                'conjunto__tipo_conjunto',
                'creado_por'
            ).prefetch_related(
                'respuestas__pregunta__escenario__tipo_riesgo',
                'resultados_riesgo__tipo_riesgo'
            ).order_by('-fecha_evaluacion')
            
            # Cache por 10 minutos
            cache.set(cache_key, evaluaciones, 60 * 10)
        
        return evaluaciones


class CacheManager:
    """
    Manager para operaciones de cache específicas del módulo
    """
    
    @staticmethod
    def get_dashboard_stats(user_id):
        """
        Obtiene estadísticas del dashboard con cache
        """
        cache_key = f'dashboard_stats_{user_id}'
        stats = cache.get(cache_key)
        
        if stats is None:
            from .models import Conjunto, EvaluacionRiesgo
            
            # Calcular estadísticas
            conjuntos = Conjunto.objects.filter(propietario_id=user_id, activo=True)
            evaluaciones = EvaluacionRiesgo.objects.filter(
                conjunto__propietario_id=user_id
            ).select_related('conjunto')
            
            stats = {
                'total_conjuntos': conjuntos.count(),
                'total_evaluaciones': evaluaciones.filter(estado='completada').count(),
                'evaluaciones_mes': evaluaciones.filter(
                    fecha_evaluacion__month=timezone.now().month
                ).count(),
                'promedio_general': evaluaciones.filter(
                    estado='completada',
                    promedio_general__isnull=False
                ).aggregate(
                    promedio=models.Avg('promedio_general')
                )['promedio'] or 0
            }
            
            # Cache por 5 minutos
            cache.set(cache_key, stats, 60 * 5)
        
        return stats
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """
        Invalida todo el cache relacionado con un usuario
        """
        cache_keys = [
            f'conjuntos_user_{user_id}',
            f'evaluaciones_user_{user_id}',
            f'dashboard_stats_{user_id}',
        ]
        
        cache.delete_many(cache_keys)
    
    @staticmethod
    def generate_cache_key(prefix, *args):
        """
        Genera una clave de cache única
        """
        key_data = f"{prefix}_{'_'.join(map(str, args))}"
        return hashlib.md5(key_data.encode()).hexdigest()[:20]


def optimize_query_with_cache(queryset, cache_key, timeout=300):
    """
    Decorator para agregar cache a querysets
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


# Índices adicionales para optimización
ADDITIONAL_INDEXES = [
    # Índices para Conjunto
    ('risk_conjuntos_conjunto', 'propietario_id'),
    ('risk_conjuntos_conjunto', 'activo'),
    ('risk_conjuntos_conjunto', ['propietario_id', 'activo']),
    
    # Índices para EvaluacionRiesgo
    ('risk_conjuntos_evaluacionriesgo', 'estado'),
    ('risk_conjuntos_evaluacionriesgo', 'fecha_evaluacion'),
    ('risk_conjuntos_evaluacionriesgo', ['conjunto_id', 'estado']),
    
    # Índices para RespuestaPregunta
    ('risk_conjuntos_respuestapregunta', 'evaluacion_id'),
    ('risk_conjuntos_respuestapregunta', 'pregunta_id'),
    
    # Índices para modelos optimizados
    ('risk_conjuntos_analisisriesgo', 'nivel_riesgo'),
    ('risk_conjuntos_metricacalidad', 'requiere_atencion'),
    ('risk_conjuntos_recomendacionsistema', 'es_critica'),
]
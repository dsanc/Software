# Documentación del Módulo Risk Conjuntos

## Descripción General

El módulo `risk_conjuntos` es un sistema integral para la gestión y evaluación de riesgos de seguridad en conjuntos residenciales. Proporciona herramientas para:

- Gestión de conjuntos residenciales
- Evaluación paso a paso de riesgos de seguridad
- Análisis automatizado de resultados
- Generación de reportes y recomendaciones
- Dashboard con métricas y estadísticas

## Arquitectura

### Modelos Principales

#### Core Models
- **`Conjunto`**: Representa un conjunto residencial con toda su información
- **`TipoConjunto`**: Tipos de conjuntos (cerrado, urbanización, etc.)

#### Sistema de Evaluación de Riesgos (Principal)
- **`TipoRiesgo`**: Tipos específicos de riesgos de seguridad
- **`EscenarioRiesgo`**: Escenarios específicos para cada tipo de riesgo
- **`PreguntaEvaluacion`**: Preguntas específicas por escenario
- **`CalificacionOpcion`**: Opciones de calificación (ausente, deficiente, vulnerable, adecuado, eficaz)
- **`EvaluacionRiesgo`**: Evaluación principal de riesgos
- **`RespuestaPregunta`**: Respuestas a preguntas específicas

#### Modelos Optimizados (Nuevos)
- **`AnalisisRiesgo`**: Análisis específico de riesgo
- **`PonderacionRiesgo`**: Ponderación y cálculos
- **`MetricaCalidad`**: Métricas de calidad y confiabilidad
- **`RecomendacionSistema`**: Recomendaciones automáticas

#### Sistema Legacy (Deprecated)
- **`CategoriaSeguridad`**: Categorías de seguridad (legacy)
- **`PreguntaSeguridad`**: Preguntas de seguridad (legacy)
- **`EvaluacionSeguridad`**: Evaluaciones de seguridad (legacy)

### Optimizaciones Implementadas

#### 1. Eliminación de Campos Deprecated
- Migración de `RespuestaPregunta.comentarios` a `ComentarioRiesgo`
- Comando de migración: `migrar_comentarios_deprecated`

#### 2. Refactorización de Modelos Complejos
- Separación de `ResultadoPregunta` en modelos especializados
- Mejora en mantenibilidad y responsabilidades únicas

#### 3. URLs Consolidadas
- Sistema principal de evaluación de riesgos
- URLs legacy marcadas como deprecated
- Estructura más limpia y organizada

#### 4. Optimizaciones de Performance
- Cache para estadísticas del dashboard
- Consultas optimizadas con `select_related` y `prefetch_related`
- Índices agregados a campos frecuentemente consultados

#### 5. Sistema de Cache
```python
# Ejemplo de uso
from apps.risk_conjuntos.performance_optimizations import CacheManager

stats = CacheManager.get_dashboard_stats(user.id)
CacheManager.invalidate_user_cache(user.id)
```

## API Endpoints

### Principales
- `GET /conjuntos/` - Lista de conjuntos
- `GET /conjuntos/{id}/` - Detalle de conjunto
- `POST /conjuntos/{id}/evaluacion/iniciar/` - Iniciar evaluación
- `GET /reportes/` - Lista de reportes

### APIs REST
- `GET /api/dashboard-stats/` - Estadísticas del dashboard
- `GET /api/tipos-conjunto/` - Tipos de conjunto disponibles
- `POST /api/conjunto/crear/` - Crear nuevo conjunto

## Proceso de Evaluación

### Flujo Principal (4 Pasos)

#### Paso 1: Selección de Riesgos
- URL: `/conjuntos/{id}/evaluacion/paso-1/`
- Selección de tipos de riesgos a evaluar
- Información de la evaluación

#### Paso 2: Respuesta a Preguntas
- URL: `/conjuntos/{id}/evaluacion/paso-2/{riesgo_index}/`
- Preguntas específicas por escenario
- Calificación de 1-5 por pregunta

#### Paso 3: Observaciones y Recomendaciones
- URL: `/conjuntos/{id}/evaluacion/paso-3/`
- Comentarios generales por tipo de riesgo
- Observaciones y limitaciones

#### Paso 4: Resumen y Finalización
- URL: `/conjuntos/{id}/evaluacion/paso-4/`
- Resumen de resultados
- Confirmación y guardado final

### Cálculo de Resultados

```python
# Metodología de cálculo
resultado_calculado = 1 - valor_calificacion
promedio_escenario = suma(resultados_preguntas) / cantidad_preguntas
promedio_riesgo = suma(promedios_escenarios) / cantidad_escenarios
promedio_general = suma(promedios_riesgos) / cantidad_riesgos
```

## Configuración

### Settings Requeridos
```python
# Cache (recomendado Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Apps
INSTALLED_APPS = [
    'apps.risk_conjuntos',
    'apps.subscriptions',  # Required for access control
    # ...
]
```

### URLs
```python
# urls.py principal
urlpatterns = [
    path('risk-conjuntos/', include('apps.risk_conjuntos.urls')),
]
```

## Comandos de Gestión

### Inicialización
```bash
# Inicializar datos básicos
python manage.py init_risk_conjuntos

# Cargar datos de evaluación
python manage.py load_risk_evaluation_data

# Migrar comentarios deprecated
python manage.py migrar_comentarios_deprecated
```

### Testing
```bash
# Ejecutar todos los tests
python manage.py test apps.risk_conjuntos

# Tests específicos
python manage.py test apps.risk_conjuntos.tests.test_optimizations
python manage.py test apps.risk_conjuntos.tests.test_metodologia_calculo
```

## Permisos y Control de Acceso

### Decoradores
```python
from apps.risk_conjuntos.decorators import requires_risk_conjuntos

@login_required
@requires_risk_conjuntos()
def mi_vista(request):
    # Solo usuarios con plan que incluya risk_conjuntos
    pass
```

### Sistema Legacy
```python
from apps.risk_conjuntos.legacy_decorators import legacy_evaluation_system

@legacy_evaluation_system("Mensaje personalizado")
def vista_legacy(request):
    # Vista marcada como legacy
    pass
```

## Estructura de Archivos

```
apps/risk_conjuntos/
├── models.py                    # Modelos principales
├── models_optimized.py          # Modelos refactorizados
├── views.py                     # Vistas principales
├── views_evaluacion.py          # Vistas del proceso de evaluación
├── views_backup.py              # Vistas legacy (backup)
├── urls.py                      # URLs consolidadas
├── forms.py                     # Formularios principales
├── forms_evaluacion.py          # Formularios de evaluación
├── modal_forms.py               # Formularios para modales
├── admin.py                     # Configuración del admin
├── legacy_decorators.py         # Decoradores para sistema legacy
├── performance_optimizations.py # Optimizaciones de performance
├── management/commands/         # Comandos de gestión
├── migrations/                  # Migraciones de Django
├── tests/                       # Tests automatizados
├── templatetags/               # Tags personalizados
└── templates/risk_conjuntos/   # Plantillas HTML
```

## Migraciones y Compatibilidad

### Historia de Migraciones Importantes
- `0009_deprecar_comentarios_individuales` - Marca campos como deprecated
- `0014_remove_comentarios_deprecated` - Remueve campos deprecated
- `0015_add_optimized_models` - Agrega modelos optimizados

### Compatibilidad hacia atrás
- URLs legacy mantenidas por compatibilidad
- Decoradores de advertencia para vistas legacy
- Sistema de migración gradual

## Performance y Monitoreo

### Métricas Recomendadas
- Tiempo de carga del dashboard
- Número de consultas por vista
- Uso de cache
- Tiempo de evaluación completa

### Optimizaciones Activas
- Cache de estadísticas (5 minutos)
- Cache de datos de usuario (15 minutos)
- Índices en campos frecuentes
- Consultas optimizadas con prefetch

## Troubleshooting

### Problemas Comunes

#### 1. Performance lenta en dashboard
```python
# Verificar cache
from django.core.cache import cache
print(cache.get('dashboard_stats_{user_id}'))

# Invalidar cache si es necesario
CacheManager.invalidate_user_cache(user_id)
```

#### 2. Errores de migración
```bash
# Verificar estado de migraciones
python manage.py showmigrations risk_conjuntos

# Aplicar migraciones faltantes
python manage.py migrate risk_conjuntos
```

#### 3. URLs legacy no funcionan
- Verificar que las URLs están incluidas correctamente
- Revisar que los decoradores están aplicados
- Verificar permisos de usuario

### Logs Importantes
```python
import logging
logger = logging.getLogger('apps.risk_conjuntos')
logger.info('Mensaje de debug')
```

## Desarrollo y Contribución

### Estándares de Código
- Seguir PEP 8
- Documentar funciones complejas
- Tests para nuevas funcionalidades
- Usar type hints cuando sea posible

### Testing
- Cobertura mínima: 80%
- Tests unitarios para modelos
- Tests de integración para vistas
- Tests de performance para optimizaciones

### Versionado
- Usar semantic versioning
- Documentar cambios en CHANGELOG
- Mantener compatibilidad hacia atrás cuando sea posible

## Próximas Mejoras

### Fase 1 (Corto plazo)
- [ ] Completar migración del sistema legacy
- [ ] Mejorar cobertura de tests
- [ ] Optimizar más consultas

### Fase 2 (Mediano plazo)
- [ ] API REST completa
- [ ] Sistema de notificaciones
- [ ] Exportación avanzada de reportes

### Fase 3 (Largo plazo)
- [ ] Machine Learning para recomendaciones
- [ ] Integración con sistemas externos
- [ ] Análisis predictivo de riesgos
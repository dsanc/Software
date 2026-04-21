# Módulo de Evaluadores

## Descripción General

El módulo de evaluadores permite a los usuarios principales (suscritos) gestionar un equipo de evaluadores que pueden acceder a las funcionalidades del sistema heredando los planes y suscripciones del usuario principal.

## Características Principales

### 1. **Gestión de Evaluadores**
- **Crear evaluadores**: Los usuarios principales pueden agregar evaluadores directamente si ya están registrados
- **Tipos de evaluador**: Diferentes niveles de acceso (Evaluador, Revisor, Analista, Administrador)
- **Control granular**: Permisos específicos por evaluador y módulo

### 2. **Herencia de Suscripciones**
- Los evaluadores heredan automáticamente las suscripciones activas del usuario principal
- Acceso solo a los módulos específicamente autorizados
- Limitaciones personalizadas por evaluador
- Sistema de verificación de permisos en tiempo real

### 3. **Control de Acceso**
- Middleware integrado para verificación automática de permisos
- Decoradores especializados para vistas sensibles
- Sistema de herencia de características del plan
- Limitaciones específicas por evaluador

## Estructura del Módulo

```
apps/evaluadores/
├── __init__.py
├── admin.py              # Configuración del admin
├── apps.py               # Configuración de la aplicación
├── decorators.py         # Decoradores de permisos
├── forms.py              # Formularios de gestión
├── middleware.py         # Middleware de control de acceso
├── models.py             # Modelos principales
├── services.py           # Servicios de negocio
├── signals.py            # Señales y notificaciones
├── tests.py              # Tests unitarios
├── urls.py               # Configuración de URLs
└── views.py              # Vistas principales
```

## Modelos Principales

### Evaluador
Representa la relación entre un usuario principal y un evaluador.

**Campos principales:**
- `usuario_principal`: Usuario que administra al evaluador
- `usuario_evaluador`: Usuario que actúa como evaluador
- `tipo_evaluador`: Nivel de acceso (evaluator, reviewer, analyst, administrator)
- `estado`: Estado actual (pending, active, suspended, inactive)
- `modulos_permitidos`: Lista de módulos autorizados
- `permisos_especiales`: Configuración específica de permisos
- `max_evaluaciones_mes`: Límite mensual de evaluaciones
- `fecha_expiracion`: Fecha límite de acceso (opcional)

**Métodos principales:**
- `tiene_acceso_a_modulo()`: Verifica acceso a módulo específico
- `puede_realizar_accion()`: Verifica permisos para acciones específicas
- `obtener_suscripciones_heredadas()`: Obtiene suscripciones disponibles
- `actualizar_ultimo_acceso()`: Registra actividad

## Servicios Principales

### EvaluadorService
Servicio principal para gestión de evaluadores.

**Métodos principales:**
- `es_evaluador_activo()`: Verifica si un usuario es evaluador
- `obtener_perfiles_evaluador()`: Obtiene perfiles de evaluador de un usuario
- `tiene_acceso_como_evaluador()`: Verifica acceso específico
- `actualizar_ultimo_acceso()`: Registra actividad

### EvaluadorSubscriptionService
Extiende el servicio de suscripciones para incluir herencia.

**Métodos principales:**
- `get_user_subscriptions_with_inheritance()`: Suscripciones propias + heredadas
- `has_module_access_with_inheritance()`: Verificación de acceso con herencia
- `get_usage_limits_with_inheritance()`: Límites considerando herencia
- `can_user_perform_action_with_inheritance()`: Verificación de acciones

## Middleware

### EvaluadorMiddleware
Añade contexto de evaluador a todas las requests.

### EvaluadorAccessMiddleware
Controla automáticamente el acceso a rutas protegidas.

### EvaluadorSessionMiddleware
Gestiona sesiones específicas de evaluadores (invitaciones post-login, selección de usuario principal).

## Decoradores de Permisos

### @evaluador_required
Requiere que el usuario sea evaluador activo.

### @subscription_required_with_inheritance
Verifica acceso a módulo con herencia de suscripciones.

### @evaluador_permission_required
Verifica permisos específicos de evaluador.

### @main_user_access_required
Requiere acceso de usuario principal específico.

## URLs Principales

```python
# Gestión de evaluadores
/evaluadores/                          # Lista de evaluadores
/evaluadores/crear/                    # Crear nuevo evaluador
/evaluadores/<id>/                     # Detalle de evaluador
/evaluadores/<id>/editar/              # Editar evaluador
/evaluadores/<id>/eliminar/            # Eliminar evaluador

/evaluadores/<id>/                     # Detalle del evaluador
/evaluadores/<id>/editar/              # Editar evaluador
/evaluadores/<id>/eliminar/            # Eliminar evaluador

# Evaluadores (perspectiva del evaluador)
/evaluadores/mi-perfil/                # Perfil del evaluador
/evaluadores/dashboard/<user_id>/      # Dashboard específico
```

## Uso del Sistema

### Como Usuario Principal

1. **Crear un evaluador directo:**
   ```python
   # El usuario debe existir en el sistema
   evaluador = Evaluador.objects.create(
       usuario_principal=request.user,
       usuario_evaluador=usuario_existente,
       tipo_evaluador='evaluator',
       modulos_permitidos=['risk_hoteles', 'risk_conjuntos']
   )
   ```
   )
   ```

### Como Evaluador

1. **Verificar acceso a módulo:**
   ```python
   from apps.evaluadores.services import EvaluadorSubscriptionService
   
   tiene_acceso = EvaluadorSubscriptionService.has_module_access_with_inheritance(
       request.user, 
       'risk_hoteles'
   )
   ```

2. **Obtener suscripciones heredadas:**
   ```python
   suscripciones = EvaluadorSubscriptionService.get_user_subscriptions_with_inheritance(
       request.user,
       'risk_hoteles'
   )
   ```

## Integración con Otros Módulos

### Sistema de Suscripciones
- Herencia automática de planes activos
- Verificación de límites y características
- Aplicación de restricciones específicas del evaluador

### Sistema de Usuarios
- Integración con modelo User personalizado
- Aprovechamiento del sistema de autenticación existente
- Compatibilidad con perfiles y configuraciones

### Módulos de Evaluación
- Los módulos `risk_hoteles`, `risk_conjuntos`, y `security_probabilistic` pueden usar los decoradores para verificar permisos automáticamente
- Herencia transparente de funcionalidades

## Configuración

### Settings
```python
INSTALLED_APPS = [
    # ...
    'apps.evaluadores',
]

MIDDLEWARE = [
    # ...
    'apps.evaluadores.middleware.EvaluadorMiddleware',
    'apps.evaluadores.middleware.EvaluadorAccessMiddleware', 
    'apps.evaluadores.middleware.EvaluadorSessionMiddleware',
]

TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ...
                'apps.evaluadores.middleware.evaluator_context_processor',
            ],
        },
    },
]
```

### URLs
```python
urlpatterns = [
    # ...
    path('evaluadores/', include('apps.evaluadores.urls')),
]
```

## Seguridad

### Control de Acceso
- Verificación automática de permisos en cada request
- Tokens únicos para invitaciones con expiración
- Aislamiento entre usuarios principales

### Validaciones
- Los evaluadores no pueden modificar sus propios permisos
- Verificación de suscripciones activas del usuario principal
- Limitaciones específicas por evaluador aplicadas automáticamente

### Auditoría
- Registro de último acceso por evaluador
- Seguimiento de creación/modificación de evaluadores
- Logs de cambios de estado y permisos

## Notificaciones

### Emails Automáticos
- Bienvenida al crear evaluador
- Activación de cuenta
- Notificaciones al usuario principal

### Configuración de Templates
Los emails utilizan templates HTML personalizables en `templates/evaluadores/emails/`:
- `bienvenida.html`
- `activacion.html`
- `eliminacion.html`
- `notificacion_principal.html`

## Extensibilidad

### Nuevos Tipos de Evaluador
Fácilmente extensible agregando opciones a `Evaluador.TIPOS_EVALUADOR`.

### Permisos Personalizados
El campo `permisos_especiales` (JSONField) permite configuraciones específicas por módulo.

### Integración con Nuevos Módulos
Los nuevos módulos pueden usar los servicios y decoradores existentes para verificar permisos automáticamente.

## Testing

El módulo incluye tests para:
- Creación y gestión de evaluadores
- Herencia de suscripciones
- Control de acceso y permisos
- Middleware y decoradores

```bash
# Ejecutar tests específicos del módulo
python manage.py test apps.evaluadores
```

## Dependencias

- Django >= 4.2
- apps.users (modelo User personalizado)
- apps.subscriptions (sistema de suscripciones)
- django.contrib.auth (sistema de autenticación)

## Consideraciones de Rendimiento

- Uso de `select_related` y `prefetch_related` en consultas
- Índices optimizados en campos de búsqueda frecuente
- Cache de información de evaluador en middleware
- Consultas optimizadas para verificación de permisos

---

**Desarrollado como parte del proyecto Django Modular**
**Versión: 1.0.0**
**Fecha: Noviembre 2024**
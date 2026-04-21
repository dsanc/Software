# Módulo Security Probabilistic 🛡️

Sistema **independiente** de **Evaluación de Seguridad Probabilística** basado en árboles de decisión para analizar el riesgo de seguridad de figuras políticas según patrones de desplazamiento y actividades laborales.

## ✨ Características Principales

### 🔓 **Sistema Completamente Independiente**
- **Sin relación con usuarios Django**: Funciona como sistema autónomo
- **Perfiles independientes**: Figuras políticas no requieren cuentas de usuario
- **Evaluaciones libres**: Cualquiera puede evaluar cualquier perfil
- **Máxima flexibilidad**: Sin restricciones de ownership o permisos complejos

### 🌳 Árbol de Decisiones Dinámico
- **Preguntas encadenadas**: Cada respuesta determina la siguiente pregunta
- **Pesos probabilísticos**: Cada opción tiene un valor específico que contribuye al riesgo total
- **Respuestas finales**: Algunas opciones pueden terminar la evaluación inmediatamente

### 📊 Cálculo Probabilístico
- **Acumulación de riesgo**: Los valores se suman para obtener una probabilidad total
- **Niveles de riesgo**: Clasificación automática en 5 niveles (Muy Bajo a Muy Alto)
- **Recomendaciones**: Sugerencias personalizadas basadas en el nivel de riesgo

### 🗺️ Gestión de Zonas
- **Catálogo de zonas de riesgo**: Base de datos de ubicaciones con niveles predefinidos
- **Coordenadas geográficas**: Soporte para delimitación de áreas
- **Integración con evaluaciones**: Las zonas pueden influir en las evaluaciones

## 🏗️ Estructura del Módulo

```
apps/security_probabilistic/
├── models.py              # Modelos de datos
├── views.py               # Vistas y lógica de presentación
├── forms.py               # Formularios
├── admin.py               # Configuración del panel administrativo
├── services.py            # Motor de evaluación y reportes
├── urls.py                # Configuración de URLs
└── migrations/            # Migraciones de base de datos
```

## 📋 Modelos de Datos (Sistema Independiente)

### PerfilSeguridad
**Figuras políticas independientes** - No requieren cuentas de usuario Django.
Contiene información completa de personas públicas para evaluación de riesgo.

### EvaluacionSeguridad
**Evaluaciones autónomas** - Sin vinculación a usuarios específicos.
Registro de análisis de riesgo con información opcional del evaluador en texto libre.

### ArbolDecision
Estructura principal que contiene las preguntas y define el flujo de evaluación.

### Pregunta
Cada pregunta del árbol con su orden y relaciones padre-hijo.

### OpcionRespuesta
Opciones de respuesta con sus valores ponderados y siguiente pregunta.

### RespuestaEvaluacion
Respuestas individuales de cada evaluación.

### ZonaRiesgo
Catálogo de zonas geográficas con niveles de riesgo predefinidos.

## 🚀 Ejemplo de Uso

### 1. Crear Árbol de Decisión
```python
arbol = ArbolDecision.objects.create(
    nombre="Evaluación de Seguridad Laboral",
    descripcion="Evaluación probabilística de riesgo laboral",
    activo=True
)
```

### 2. Crear Preguntas
```python
pregunta1 = Pregunta.objects.create(
    arbol=arbol,
    texto="¿Con qué frecuencia se desplaza a estos lugares?",
    orden=1,
    es_pregunta_inicial=True
)
```

### 3. Crear Opciones con Pesos
```python
OpcionRespuesta.objects.create(
    pregunta=pregunta1,
    texto="Menos de 3 meses",
    valor_ponderado=Decimal('0.005'),
    orden=1,
    pregunta_siguiente=pregunta2
)
```

## 🔄 Flujo de Evaluación

1. **Inicio**: Usuario selecciona tipo de evaluación
2. **Navegación**: Sistema presenta preguntas según las respuestas anteriores
3. **Cálculo**: Se acumulan los valores ponderados de cada respuesta
4. **Resultado**: Se determina el nivel de riesgo y se generan recomendaciones

## 📊 Ejemplo de Ponderaciones

| Frecuencia de Desplazamiento | Valor Ponderado |
|------------------------------|-----------------|
| < 3 Meses                    | 0.005          |
| 4 a 10 Meses                 | 0.01           |
| > 10 Meses                   | 0.02           |
| No me desplazo               | 0.0            |

## 🎯 Niveles de Riesgo

| Probabilidad Total | Nivel de Riesgo | Color      |
|-------------------|-----------------|------------|
| 0.0 - 0.2         | Muy Bajo        | Verde      |
| 0.2 - 0.4         | Bajo            | Azul       |
| 0.4 - 0.6         | Medio           | Amarillo   |
| 0.6 - 0.8         | Alto            | Naranja    |
| 0.8 - 1.0         | Muy Alto        | Rojo       |

## 🔧 Configuración

### 1. Agregar a INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ... otras apps
    'apps.security_probabilistic',
]
```

### 2. Incluir URLs
```python
urlpatterns = [
    # ... otras URLs
    path('security-probabilistic/', include('apps.security_probabilistic.urls')),
]
```

### 3. Ejecutar Migraciones
```bash
python manage.py makemigrations security_probabilistic
python manage.py migrate
```

## 📁 URLs Disponibles

- `/security-probabilistic/` - Dashboard principal
- `/security-probabilistic/evaluacion/nueva/` - Iniciar nueva evaluación
- `/security-probabilistic/evaluacion/<id>/` - Continuar evaluación
- `/security-probabilistic/admin/` - Gestión administrativa (solo staff)

## 🎨 Templates

### Estructura de Templates
```
templates/security_probabilistic/
├── dashboard.html                 # Dashboard principal
├── iniciar_evaluacion.html       # Formulario de inicio
├── responder_pregunta.html        # Interfaz de preguntas
├── resultado_evaluacion.html      # Resultados finales
└── admin/                         # Templates administrativos
```

## 📋 Scripts de Ejemplo

### Crear Datos de Prueba
```bash
python crear_datos_security_probabilistic.py
```

Este script crea:
- ✅ 1 Árbol de decisión de ejemplo
- ✅ 4 Preguntas encadenadas
- ✅ 16 Opciones de respuesta con pesos
- ✅ 4 Zonas de riesgo de ejemplo

## 🔐 Permisos y Seguridad

- **Usuarios autenticados**: Pueden crear y realizar evaluaciones
- **Staff**: Acceso a gestión de árboles y estadísticas
- **Superusuarios**: Acceso completo al panel administrativo

## 🚀 Motor de Evaluación

### MotorEvaluacionSeguridad
```python
motor = MotorEvaluacionSeguridad(evaluacion)
siguiente_pregunta, es_completa = motor.procesar_respuesta(pregunta_id, opcion_id)
```

### GeneradorReportes
```python
generador = GeneradorReportes(evaluacion)
reporte = generador.generar_reporte_completo()
```

## 📈 Funcionalidades Avanzadas

### API Endpoints
- Obtener siguiente pregunta
- Guardar respuesta
- Consultar zonas de riesgo

### Filtros y Búsqueda
- Filtrar por estado de evaluación
- Filtrar por nivel de riesgo
- Rango de fechas

### Reportes
- Resumen de respuestas
- Distribución del riesgo
- Recomendaciones personalizadas
- Estadísticas agregadas

## 🔄 Extensibilidad

El sistema está diseñado para ser fácilmente extensible:

1. **Nuevos tipos de preguntas**: Solo agregar nuevos modelos de ArbolDecision
2. **Algoritmos de cálculo**: Modificar métodos en MotorEvaluacionSeguridad
3. **Nuevos reportes**: Extender GeneradorReportes
4. **Integración geográfica**: Usar coordenadas en ZonaRiesgo

## 🎯 Casos de Uso

- ✅ Evaluación de riesgo laboral
- ✅ Análisis de seguridad de desplazamientos
- ✅ Gestión de riesgos empresariales
- ✅ Auditorías de seguridad
- ✅ Capacitación en prevención de riesgos

---

**🎉 ¡El módulo está listo para usar!**

Accede a `http://localhost:8000/security-probabilistic/` para comenzar a usar el sistema.
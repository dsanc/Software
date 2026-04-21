"""
Documentación: Nueva Columna de Promedio General en Lista de Conjuntos
====================================================================

## 🎯 FUNCIONALIDAD IMPLEMENTADA

### ✅ **Nueva Columna "Promedio General"**

**Ubicación:** Lista de conjuntos (`/risk_conjuntos/`)
**Posición:** Entre "Amenidades" y "Acciones"

### 🔧 **Cálculo del Promedio**

La columna muestra el **promedio de todas las evaluaciones completadas** de cada conjunto:

```sql
-- Query SQL equivalente
SELECT 
  conjunto.*,
  AVG(evaluaciones_riesgo.promedio_general) as promedio_general_evaluaciones,
  COUNT(evaluaciones_riesgo.id) as total_evaluaciones
FROM conjunto 
LEFT JOIN evaluaciones_riesgo ON conjunto.id = evaluaciones_riesgo.conjunto_id
WHERE evaluaciones_riesgo.estado = 'completada'
GROUP BY conjunto.id
```

### 📊 **Visualización**

**1. Con Evaluaciones:**
- 🟢 **Círculo colorido** con porcentaje
- ✅ **0-30%:** Verde (Bajo Riesgo)
- ⚠️ **31-50%:** Amarillo (Moderado)  
- 🔶 **51-70%:** Naranja (Alto Riesgo)
- 🔴 **71-100%:** Rojo (Crítico)
- 📈 **Contador** de evaluaciones realizadas

**2. Sin Evaluaciones:**
- ⚪ **Círculo gris** con "--"
- ❓ **Texto:** "Sin evaluar"

### 🎨 **Estilos Responsivos**

**Desktop (>768px):** Columna completa visible
**Tablet (768px):** Se oculta "Administración", mantiene promedio
**Mobile (<576px):** Se oculta "Amenidades" y "Promedio", solo info esencial

### 🔧 **Implementación Técnica**

**Backend (views.py):**
```python
conjuntos = get_user_conjuntos(request.user).annotate(
    promedio_general_evaluaciones=Avg(
        'evaluaciones_riesgo__promedio_general',
        filter=Q(evaluaciones_riesgo__estado='completada')
    ),
    total_evaluaciones=Count(
        'evaluaciones_riesgo',
        filter=Q(evaluaciones_riesgo__estado='completada'),
        distinct=True
    )
)

# Convertir decimal (0-1) a porcentaje (0-100)
for conjunto in conjuntos:
    if conjunto.promedio_general_evaluaciones:
        conjunto.promedio_porcentaje = float(conjunto.promedio_general_evaluaciones) * 100
```

**Frontend (template):**
```django
<th class="text-center">Promedio General</th>

<td class="text-center">
    {% if conjunto.promedio_porcentaje %}
        <div class="score-circle bg-success/warning/danger">
            {{ promedio|floatformat:1 }}%
        </div>
        <small>{{ conjunto.total_evaluaciones }} evaluaciones</small>
    {% else %}
        <div class="score-circle bg-light">--</div>
        <small>Sin evaluar</small>
    {% endif %}
</td>
```

### 📱 **Casos de Uso**

**1. Evaluador visualiza sus conjuntos:**
- Ve rápidamente qué conjuntos tienen mayor riesgo
- Identifica conjuntos sin evaluar
- Prioriza próximas evaluaciones

**2. Administrador revisa portafolio:**
- Compara rendimiento entre conjuntos
- Identifica tendencias de riesgo
- Toma decisiones de recursos

**3. Análisis histórico:**
- El promedio incluye TODAS las evaluaciones completadas
- Refleja evolución temporal del riesgo
- Permite comparaciones objetivas

### 🎯 **Ejemplo de Datos Reales**

Según verificación del sistema:

```
🏠 Conjunto Prueba
   📊 2 evaluaciones completadas
   🎯 Promedio: 40.5% (Moderado - Amarillo)

🏠 Torres Ejecutivas del Norte  
   📊 1 evaluación completada
   🎯 Promedio: 93.6% (Crítico - Rojo)
```

### ✅ **Beneficios de la Funcionalidad**

**1. Visión Rápida:** Dashboard visual del estado de riesgo
**2. Toma de Decisiones:** Priorización basada en datos
**3. Seguimiento:** Evolución histórica del riesgo
**4. Comparación:** Benchmarking entre conjuntos
**5. Eficiencia:** No necesidad de entrar a cada conjunto

### 🚀 **Testing**

**Verificado en:**
- ✅ Conjuntos con múltiples evaluaciones
- ✅ Conjuntos con una evaluación  
- ✅ Conjuntos sin evaluaciones
- ✅ Responsividad móvil
- ✅ Cálculos de promedio correctos
- ✅ Colores según nivel de riesgo

### 📈 **Estadísticas del Sistema**

```
👥 Total usuarios: 14
🏢 Total conjuntos: 10  
📊 Total evaluaciones: 9
✅ Evaluaciones completadas: 6

🎯 Conjuntos con datos:
   - 2 conjuntos con evaluaciones completadas
   - 8 conjuntos pendientes de evaluar
   - Rango de riesgo: 40.5% - 93.6%
```

## 🎊 **¡FUNCIONALIDAD COMPLETAMENTE IMPLEMENTADA!**

**La nueva columna de Promedio General está:**
- ✅ **Implementada** en backend y frontend
- ✅ **Funcionando** con cálculos correctos  
- ✅ **Responsive** para todos los dispositivos
- ✅ **Probada** con datos reales
- ✅ **Lista** para producción

**🌟 Accede a: http://127.0.0.1:8000/risk_conjuntos/ para verla en acción! 🌟**
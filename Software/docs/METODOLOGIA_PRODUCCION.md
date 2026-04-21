# 🚀 METODOLOGÍA DE CÁLCULO CORRECTA - GUÍA DE PRODUCCIÓN

## 📋 RESUMEN DE CAMBIOS

Se implementó la metodología de cálculo correcta para evaluaciones de riesgo en conjuntos residenciales, aplicando la fórmula específica requerida:

1. **Para cada pregunta:** `resultado = 1 - valor_calificacion`
2. **Para cada escenario:** `promedio = suma(resultados_preguntas) / número_preguntas`
3. **Para cada riesgo:** `promedio = promedio(resultados_escenarios)`
4. **Promedio general:** `promedio(resultados_riesgos)`

## 🛠️ ARCHIVOS MODIFICADOS

### `apps/risk_conjuntos/views_evaluacion.py`
- ✅ **Función agregada:** `calcular_promedios_por_metodologia_correcta()`
- ✅ **Función agregada:** `guardar_resultados_con_metodologia_correcta()`
- ✅ **Función modificada:** `crear_evaluacion_completa()` - Ahora aplica metodología automáticamente
- ✅ **Función modificada:** `preparar_resumen_completo()` - Usa nueva metodología con fallback

### Comandos de Gestión
- ✅ **Nuevo:** `migrar_metodologia_produccion.py` - Migra evaluaciones existentes
- ✅ **Nuevo:** `test_metodologia_correcta.py` - Prueba implementación

### Tests
- ✅ **Nuevo:** `test_metodologia_calculo.py` - Tests unitarios completos

## 🔄 PROCESO DE MIGRACIÓN A PRODUCCIÓN

### 1. **Pre-Despliegue**
```bash
# 1. Hacer backup de la base de datos
mysqldump -u usuario -p base_datos > backup_pre_metodologia.sql

# 2. Verificar espacio en disco (para logs adicionales)
df -h

# 3. Verificar que no hay evaluaciones en progreso
python manage.py shell -c "
from apps.risk_conjuntos.models import EvaluacionRiesgo
en_progreso = EvaluacionRiesgo.objects.filter(estado='en_progreso').count()
print(f'Evaluaciones en progreso: {en_progreso}')
"
```

### 2. **Despliegue**
```bash
# 1. Desplegar código nuevo
git pull origin main

# 2. Instalar dependencias (si hay nuevas)
pip install -r requirements/production.txt

# 3. Ejecutar migraciones de base de datos (si las hay)
python manage.py migrate

# 4. Recopilar archivos estáticos
python manage.py collectstatic --noinput

# 5. Reiniciar servicios
systemctl restart gunicorn
systemctl restart nginx
```

### 3. **Post-Despliegue**
```bash
# 1. Verificar que el servicio está funcionando
curl -I https://tu-dominio.com/

# 2. Migrar evaluaciones existentes (DRY-RUN primero)
python manage.py migrar_metodologia_produccion --dry-run

# 3. Si está bien, ejecutar migración real
python manage.py migrar_metodologia_produccion --batch-size=50

# 4. Verificar resultados
python manage.py shell -c "
from apps.risk_conjuntos.models import EvaluacionRiesgo, ResultadoRiesgo
total_evaluaciones = EvaluacionRiesgo.objects.filter(estado='completada').count()
con_resultados = EvaluacionRiesgo.objects.filter(resultados_riesgo__isnull=False).distinct().count()
print(f'Evaluaciones totales: {total_evaluaciones}')
print(f'Con nueva metodología: {con_resultados}')
"
```

## 📊 VALIDACIÓN DE FUNCIONAMIENTO

### Verificar Nueva Evaluación
```bash
# Crear una evaluación de prueba y verificar que aplica metodología correcta
# Revisar logs para confirmar:
tail -f /var/log/django/risk_conjuntos.log | grep "Metodología aplicada correctamente"
```

### Verificar Evaluaciones Migradas
```bash
python manage.py shell -c "
from apps.risk_conjuntos.models import EvaluacionRiesgo, ResultadoRiesgo, ResultadoEscenario
import random

# Tomar evaluación aleatoria migrada
evaluacion = EvaluacionRiesgo.objects.filter(resultados_riesgo__isnull=False).first()
if evaluacion:
    print(f'Evaluación: {evaluacion}')
    print(f'Promedio general: {evaluacion.promedio_general}')
    
    print('Resultados por riesgo:')
    for resultado in evaluacion.resultados_riesgo.all():
        print(f'  - {resultado.tipo_riesgo.nombre}: {resultado.promedio_riesgo}')
    
    print('Resultados por escenario:')
    for resultado in evaluacion.resultados_escenario.all():
        print(f'  - {resultado.escenario.nombre}: {resultado.promedio_escenario}')
else:
    print('No hay evaluaciones migradas')
"
```

## ⚠️ CONSIDERACIONES IMPORTANTES

### **Compatibilidad Hacia Atrás**
- ✅ Las evaluaciones antiguas siguen funcionando
- ✅ Hay fallback automático en caso de error
- ✅ No se modifican datos existentes sin migración explícita

### **Monitoreo**
- 📊 **Logs:** Se agregan logs automáticos en `risk_conjuntos.evaluacion`
- 🔔 **Alertas:** Monitorear errores en aplicación de metodología
- 📈 **Métricas:** Verificar que promedio general esté en rango 0-1

### **Rendimiento**
- ⚡ **Optimización:** Cálculos se hacen en memoria, luego se guardan en lote
- 🔄 **Transacciones:** Uso de transacciones atómicas para consistencia
- 📦 **Batch Processing:** Migración en lotes configurables

## 🎯 CALIFICACIONES Y CONVERSIONES

### Calificaciones Base
```python
CALIFICACIONES = {
    'ausente': 0.005,      # → 1 - 0.005 = 0.995
    'deficiente': 0.100,   # → 1 - 0.100 = 0.900
    'vulnerable': 0.250,   # → 1 - 0.250 = 0.750
    'adecuado': 0.600,     # → 1 - 0.600 = 0.400
    'eficaz': 0.900,       # → 1 - 0.900 = 0.100
}
```

### Interpretación de Resultados
- **0.8 - 1.0:** Excelente (puntajes altos después de 1-valor)
- **0.6 - 0.8:** Bueno
- **0.4 - 0.6:** Regular
- **0.2 - 0.4:** Deficiente
- **0.0 - 0.2:** Crítico

## 🔧 COMANDOS ÚTILES

### Migración Manual de Evaluación Específica
```bash
python manage.py migrar_metodologia_produccion --evaluacion-id=<UUID> --force
```

### Verificar Estado de Migración
```bash
python manage.py shell -c "
from apps.risk_conjuntos.models import EvaluacionRiesgo
total = EvaluacionRiesgo.objects.filter(estado='completada').count()
migradas = EvaluacionRiesgo.objects.filter(resultados_riesgo__isnull=False).distinct().count()
porcentaje = (migradas / total * 100) if total > 0 else 0
print(f'Progreso migración: {migradas}/{total} ({porcentaje:.1f}%)')
"
```

### Rollback de Evaluación (Si es necesario)
```bash
python manage.py shell -c "
from apps.risk_conjuntos.models import EvaluacionRiesgo, ResultadoRiesgo, ResultadoEscenario
evaluacion_id = '<UUID>'
evaluacion = EvaluacionRiesgo.objects.get(id=evaluacion_id)
ResultadoRiesgo.objects.filter(evaluacion=evaluacion).delete()
ResultadoEscenario.objects.filter(evaluacion=evaluacion).delete()
evaluacion.promedio_general = None
evaluacion.save()
print('Rollback completado')
"
```

## 📞 CONTACTO Y SOPORTE

En caso de problemas durante el despliegue:

1. **Revisar logs:** `/var/log/django/risk_conjuntos.log`
2. **Verificar base de datos:** Conexiones y espacio disponible
3. **Rollback:** Usar backup pre-despliegue si es necesario
4. **Contactar:** Equipo de desarrollo con logs específicos

---
**Fecha de implementación:** November 3, 2025
**Versión:** 2.0.0 - Metodología Correcta
**Estado:** ✅ Listo para producción
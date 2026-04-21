# ✅ Tablas de Departamentos y Municipios - Colombia

## 🎯 **Objetivo Completado**

Se han creado exitosamente las tablas de **Departamentos** y **Municipios** de Colombia con gestión de **niveles de riesgo de zona** para el módulo `security_probabilistic`.

## 🏗️ **Estructura Implementada**

### **Modelo Departamento**
```python
class Departamento(models.Model):
    codigo_dane = models.CharField(max_length=2, unique=True)
    nombre = models.CharField(max_length=100)
    region = models.CharField(max_length=50, choices=[...])
    nivel_riesgo = models.CharField(max_length=20, choices=[...])
    factor_riesgo = models.DecimalField(max_digits=5, decimal_places=3)
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    # Timestamps automáticos
```

#### **Características:**
- ✅ **Código DANE** único por departamento
- ✅ **Regiones geográficas** (Andina, Caribe, Pacífica, etc.)
- ✅ **Niveles de riesgo**: Muy Bajo, Bajo, Medio, Alto, Muy Alto, Crítico
- ✅ **Factor numérico** (0.000 - 1.000) para cálculos de evaluación
- ✅ **Observaciones** sobre el nivel de riesgo

### **Modelo Municipio**
```python
class Municipio(models.Model):
    departamento = models.ForeignKey(Departamento, ...)
    codigo_dane = models.CharField(max_length=5, unique=True)
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=[...])
    nivel_riesgo = models.CharField(max_length=20, choices=[...])
    factor_riesgo = models.DecimalField(max_digits=5, decimal_places=3)
    usa_riesgo_departamento = models.BooleanField(default=True)
    poblacion = models.PositiveIntegerField(blank=True, null=True)
    # Más campos...
```

#### **Características:**
- ✅ **Relación con Departamento** (ForeignKey)
- ✅ **Categoría municipal** (Especial, Primera, Segunda, etc.)
- ✅ **Riesgo propio o heredado** del departamento
- ✅ **Factor de riesgo efectivo** calculado automáticamente
- ✅ **Población estimada** para contexto

## 🎨 **Admin Mejorado**

### **DepartamentoAdmin**
- **Vista de lista**: Nombre, código DANE, región, nivel de riesgo con colores, factor de riesgo
- **Filtros**: Por región, nivel de riesgo, estado activo
- **Inlines**: Gestión directa de municipios
- **Acciones**: Activar/desactivar, establecer riesgo medio/alto

### **MunicipioAdmin**
- **Vista de lista**: Nombre, departamento, categoría, riesgo efectivo, población
- **Filtros**: Por departamento, categoría, uso de riesgo
- **Acciones**: Usar riesgo del departamento o propio

## 📊 **Datos Creados**

### **8 Departamentos**
| Departamento | Región | Nivel de Riesgo | Factor |
|--------------|--------|-----------------|--------|
| Bogotá D.C. | Andina | Medio | 0.500 |
| Antioquia | Andina | Alto | 0.750 |
| Valle del Cauca | Pacífica | Alto | 0.700 |
| Atlántico | Caribe | Medio | 0.450 |
| Bolívar | Caribe | Alto | 0.800 |
| Cundinamarca | Andina | Medio | 0.400 |
| Nariño | Pacífica | Muy Alto | 0.900 |
| César | Caribe | Alto | 0.750 |

### **11 Municipios Principales**
- **Bogotá** (Usa riesgo departamental)
- **Medellín** (Riesgo propio: Muy Alto - 0.850)
- **Cali** (Riesgo propio: Muy Alto - 0.800)
- **Barranquilla** (Usa riesgo departamental)
- **Cartagena** (Riesgo propio: Alto - 0.750)
- **Chía** (Riesgo propio: Bajo - 0.200)
- Y más...

## 🔧 **Funcionalidades Clave**

### **Gestión de Riesgo Inteligente**
```python
@property
def nivel_riesgo_efectivo(self):
    """Retorna el nivel de riesgo efectivo (propio o del departamento)"""
    if self.usa_riesgo_departamento:
        return self.departamento.nivel_riesgo
    return self.nivel_riesgo

@property  
def factor_riesgo_efectivo(self):
    """Retorna el factor de riesgo efectivo para cálculos"""
    if self.usa_riesgo_departamento:
        return self.departamento.factor_riesgo
    return self.factor_riesgo
```

### **Indicadores Visuales en Admin**
- **Colores por nivel**: Verde (Bajo) → Naranja (Medio) → Rojo (Alto) → Morado (Crítico)
- **Fuente de riesgo**: "(Dep.)" o "(Mun.)" para indicar si usa riesgo departamental o propio
- **Enlaces contextuales**: Navegación directa entre departamentos y municipios

## 🚀 **Estado Actual**

- ✅ **Migraciones aplicadas**: Tablas creadas correctamente
- ✅ **Admin funcional**: Gestión completa desde interfaz web
- ✅ **Datos de ejemplo**: 8 departamentos, 11 municipios principales
- ✅ **Sin errores**: `python manage.py check` pasa sin problemas
- ✅ **Niveles de riesgo**: Listos para ser usados en evaluaciones

## 🌐 **Acceso**

- **Admin Departamentos**: http://127.0.0.1:8000/admin/security_probabilistic/departamento/
- **Admin Municipios**: http://127.0.0.1:8000/admin/security_probabilistic/municipio/

## 🎯 **Preparado para Evaluaciones**

Las tablas están **listas para ser integradas** en el sistema de evaluaciones:

1. **Factor de riesgo geográfico** disponible por ubicación
2. **Flexibilidad**: Municipios pueden usar riesgo departamental o propio
3. **Escalabilidad**: Fácil agregar más departamentos/municipios
4. **Datos reales**: Códigos DANE oficiales y poblaciones reales

## 📝 **Próximos Pasos Sugeridos**

1. **Cargar datos completos**: Script para los 32 departamentos y 1,122 municipios
2. **Integración con evaluaciones**: Usar factor de riesgo en cálculos
3. **API endpoints**: Exposer datos geográficos vía REST API
4. **Mapas**: Visualización geográfica de niveles de riesgo

---

**✅ Tablas de departamentos y municipios con gestión de riesgo completamente implementadas y funcionales!**
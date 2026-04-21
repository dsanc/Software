# Sistema de Permisos Granulares para Evaluadores

## Resumen del Sistema Implementado

Se ha implementado un **sistema completo de gestión de permisos granulares** que permite controlar específicamente qué puede hacer cada evaluador en cada módulo del sistema.

## Funcionalidades Implementadas

### 1. **Modelo de Permisos Granulares (EvaluadorPermisoModulo)**
   
**Ubicación:** `apps/evaluadores/models_permisos.py`

**Características:**
- **20+ campos de permisos** específicos por módulo
- **Control temporal** (fechas de inicio y fin)
- **Plantillas predefinidas** de permisos comunes
- **Integración** con el sistema de suscripciones existente

**Permisos disponibles por módulo:**
- ✅ **Lectura:** puede_ver, puede_ver_detalle, puede_buscar, puede_filtrar
- ✅ **Escritura:** puede_crear, puede_editar, puede_eliminar, puede_duplicar
- ✅ **Configuración:** puede_configurar, puede_gestionar_usuarios, puede_ver_reportes_admin
- ✅ **Reportes:** puede_exportar, puede_generar_reportes, puede_ver_graficos, puede_imprimir
- ✅ **Avanzado:** puede_importar, puede_hacer_backup, puede_aprobar, puede_rechazar
- ✅ **Comentarios:** puede_comentar, puede_moderar_comentarios

### 2. **Plantillas de Permisos Predefinidas**

```python
PLANTILLAS_PERMISOS = {
    'sin_acceso': {
        'acceso_habilitado': False,
        # Todos los permisos en False
    },
    'solo_lectura': {
        'acceso_habilitado': True,
        'puede_ver': True,
        'puede_ver_detalle': True,
        'puede_buscar': True,
        'puede_filtrar': True,
        # Solo permisos de lectura
    },
    'basico': {
        'acceso_habilitado': True,
        'puede_ver': True,
        'puede_crear': True,
        'puede_editar': True,
        # Permisos básicos de CRUD
    },
    'completo': {
        'acceso_habilitado': True,
        # Todos los permisos en True
    }
}
```

### 3. **Interface de Gestión de Permisos**

**Ubicación:** `templates/evaluadores/permisos/gestionar_permisos.html`

**Características:**
- **Interface visual moderna** con switches para activar/desactivar permisos
- **Organización por grupos** (Lectura, Escritura, Reportes, etc.)
- **Aplicación rápida de plantillas** predefinidas
- **Feedback visual** del estado actual de cada permiso
- **AJAX** para updates en tiempo real sin recargar página

### 4. **Vistas de Gestión**

**Ubicación:** `apps/evaluadores/views_permisos.py`

**Vistas implementadas:**
- `gestionar_permisos()` - Interface principal de gestión
- `configurar_permiso_modulo()` - Configuración específica por módulo
- `aplicar_plantilla_permisos()` - Aplicación rápida de plantillas
- `toggle_acceso_modulo()` - Habilitar/deshabilitar acceso completo
- `clonar_permisos()` - Copiar permisos entre evaluadores
- `resumen_permisos()` - Vista de resumen y estadísticas

### 5. **APIs REST para Funcionalidad AJAX**

**Ubicación:** `apps/evaluadores/api_permisos.py`

**APIs disponibles:**
- `PATCH /api/permisos/<id>/` - Actualizar permisos específicos
- `POST /api/permisos/<id>/plantilla/` - Aplicar plantilla
- `GET /api/<evaluador_id>/estadisticas-permisos/` - Obtener estadísticas

### 6. **Formularios Avanzados**

**Ubicación:** `apps/evaluadores/forms_permisos.py`

**Características:**
- **Campos agrupados** por funcionalidad
- **Validación avanzada** de dependencias entre permisos
- **Auto-completado** y sugerencias contextuales

## Rutas y URLs Disponibles

```python
# Gestión de permisos
evaluadores/<int:evaluador_pk>/permisos/                    # Interface principal
evaluadores/<int:evaluador_pk>/permisos/<int:modulo_id>/    # Configuración específica
evaluadores/<int:evaluador_pk>/permisos/resumen/           # Resumen de permisos

# APIs AJAX
evaluadores/api/permisos/<int:permiso_id>/                  # Actualizar permisos
evaluadores/api/permisos/<int:permiso_id>/plantilla/       # Aplicar plantilla
```

## Integración con Sistema Existente

### **Con Suscripciones:**
- ✅ Respeta límites de evaluadores por plan
- ✅ Solo permite permisos para módulos incluidos en suscripción
- ✅ Herencia automática de permisos del usuario principal

### **Con Evaluadores:**
- ✅ Integración completa con modelo Evaluador existente
- ✅ Campos `nombres` y `apellidos` agregados
- ✅ Avatar y gestión de perfil mejorados

### **Con Módulos:**
- ✅ Utiliza modelo Module de suscripciones
- ✅ Iconos y colores personalizados por módulo
- ✅ Configuración flexible por tipo de módulo

## Casos de Uso Prácticos

### **Caso 1: Evaluador Junior**
```python
# Solo lectura en todos los módulos
plantilla = 'solo_lectura'
```

### **Caso 2: Evaluador Senior**
```python
# Acceso completo excepto configuraciones administrativas
plantilla = 'basico'
# + permisos específicos personalizados
```

### **Caso 3: Supervisor**
```python
# Acceso completo a todos los módulos
plantilla = 'completo'
```

### **Caso 4: Evaluador Temporal**
```python
# Permisos con fecha de expiración
fecha_inicio = '2024-01-01'
fecha_fin = '2024-12-31'
```

## Migraciones Aplicadas

```bash
# Migración creada y aplicada exitosamente
apps/evaluadores/migrations/0003_evaluadorpermisomodulo.py
```

## Próximos Pasos Recomendados

1. **Decoradores de Permisos**: Crear decoradores para verificar permisos específicos en vistas
2. **Middleware de Permisos**: Implementar middleware automático de verificación
3. **Logs de Auditoría**: Registrar cambios de permisos para auditoría
4. **Notificaciones**: Alertar cuando se modifican permisos importantes
5. **Bulk Operations**: Permitir cambios masivos de permisos

## Estado del Sistema

✅ **Migración:** Completada y aplicada  
✅ **Modelos:** Creados y configurados  
✅ **Vistas:** Implementadas y funcionales  
✅ **Templates:** Diseño moderno y responsivo  
✅ **URLs:** Configuradas y probadas  
✅ **APIs:** RESTful para AJAX  
✅ **Integración:** Con suscripciones y evaluadores  

**El sistema está completamente funcional y listo para usar.**

## Instrucciones de Uso

1. **Acceder a la gestión de permisos:**
   - Ve a la lista de evaluadores
   - Selecciona un evaluador
   - Click en "Gestionar Permisos"

2. **Configurar permisos por módulo:**
   - Activa/desactiva el acceso general al módulo
   - Configura permisos específicos usando los switches
   - Aplica plantillas rápidas según el rol

3. **Clonar permisos:**
   - Útil para nuevos evaluadores con roles similares
   - Copia toda la configuración de permisos existente

4. **Monitorear uso:**
   - Revisa el resumen de permisos
   - Verifica estadísticas de acceso por evaluador
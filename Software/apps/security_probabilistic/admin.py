from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db import transaction
from .models import (
    ArbolDecision, Pregunta, OpcionRespuesta, 
    EvaluacionSeguridad, RespuestaEvaluacion, ZonaRiesgo, PerfilSeguridad,
    Departamento, Municipio
)


# ================================
# INLINES PARA MANEJO DE RELACIONES
# ================================

class OpcionRespuestaInline(admin.TabularInline):
    """Inline para gestionar opciones directamente desde la pregunta"""
    model = OpcionRespuesta
    fk_name = 'pregunta'  # Especificar la FK correcta
    extra = 2
    fields = ('texto', 'valor_ponderado', 'orden', 'es_respuesta_final', 'pregunta_siguiente')
    ordering = ('orden',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "pregunta_siguiente":
            # Solo mostrar preguntas del mismo árbol
            if hasattr(request, '_obj_'):
                kwargs["queryset"] = Pregunta.objects.filter(arbol=request._obj_.arbol)
            else:
                kwargs["queryset"] = Pregunta.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PreguntaInline(admin.TabularInline):
    """Inline para gestionar preguntas directamente desde el árbol"""
    model = Pregunta
    extra = 1
    fields = ('texto_resumido', 'orden', 'es_pregunta_inicial', 'ver_opciones')
    readonly_fields = ('texto_resumido', 'ver_opciones')
    ordering = ('orden',)
    
    def texto_resumido(self, obj):
        if obj.texto:
            return obj.texto[:60] + "..." if len(obj.texto) > 60 else obj.texto
        return "Nueva pregunta"
    texto_resumido.short_description = "Pregunta"
    
    def ver_opciones(self, obj):
        if obj.pk:
            count = obj.opciones.count()
            url = reverse('admin:security_probabilistic_pregunta_change', args=[obj.pk])
            return format_html('<a href="{}">Ver {} opciones</a>', url, count)
        return "Guardar para ver opciones"
    ver_opciones.short_description = "Opciones"


# ================================
# ADMINISTRADORES PRINCIPALES
# ================================

@admin.register(ArbolDecision)
class ArbolDecisionAdmin(admin.ModelAdmin):
    """Administración avanzada para árboles de decisión"""
    list_display = ('nombre', 'descripcion_corta', 'activo', 'total_preguntas', 'pregunta_inicial', 'validar_integridad')
    list_filter = ('activo', 'creado_en')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('creado_en', 'actualizado_en')
    inlines = [PreguntaInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activar_arboles', 'desactivar_arboles', 'duplicar_arbol', 'validar_estructura']
    
    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = "Descripción"
    
    def total_preguntas(self, obj):
        count = obj.preguntas.count()
        url = reverse('admin:security_probabilistic_pregunta_changelist') + f'?arbol__id__exact={obj.pk}'
        return format_html('<a href="{}">{} preguntas</a>', url, count)
    total_preguntas.short_description = "Preguntas"
    
    def pregunta_inicial(self, obj):
        inicial = obj.preguntas.filter(es_pregunta_inicial=True).first()
        if inicial:
            url = reverse('admin:security_probabilistic_pregunta_change', args=[inicial.pk])
            return format_html('<a href="{}">Ver inicial</a>', url)
        return mark_safe('<span style="color: red;">Sin pregunta inicial</span>')
    pregunta_inicial.short_description = "Pregunta Inicial"
    
    def validar_integridad(self, obj):
        # Validaciones básicas
        preguntas = obj.preguntas.count()
        iniciales = obj.preguntas.filter(es_pregunta_inicial=True).count()
        
        issues = []
        if preguntas == 0:
            issues.append("Sin preguntas")
        if iniciales == 0:
            issues.append("Sin pregunta inicial")
        elif iniciales > 1:
            issues.append("Múltiples preguntas iniciales")
            
        if issues:
            return format_html('<span style="color: red;">⚠ {}</span>', ', '.join(issues))
        return mark_safe('<span style="color: green;">✓ Válido</span>')
    validar_integridad.short_description = "Estado"
    
    def activar_arboles(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} árboles activados correctamente.')
    activar_arboles.short_description = "Activar árboles seleccionados"
    
    def desactivar_arboles(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} árboles desactivados correctamente.')
    desactivar_arboles.short_description = "Desactivar árboles seleccionados"
    
    def duplicar_arbol(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Selecciona solo un árbol para duplicar.', messages.ERROR)
            return
            
        arbol = queryset.first()
        try:
            with transaction.atomic():
                # Duplicar árbol
                nuevo_arbol = ArbolDecision.objects.create(
                    nombre=f"{arbol.nombre} (Copia)",
                    descripcion=f"Copia de: {arbol.descripcion}",
                    activo=False
                )
                
                # Mapeo de preguntas originales a nuevas
                pregunta_map = {}
                
                # Duplicar preguntas
                for pregunta in arbol.preguntas.all():
                    nueva_pregunta = Pregunta.objects.create(
                        arbol=nuevo_arbol,
                        texto=pregunta.texto,
                        orden=pregunta.orden,
                        es_pregunta_inicial=pregunta.es_pregunta_inicial
                    )
                    pregunta_map[pregunta.pk] = nueva_pregunta
                
                # Duplicar opciones y reconectar referencias
                for pregunta_original in arbol.preguntas.all():
                    nueva_pregunta = pregunta_map[pregunta_original.pk]
                    for opcion in pregunta_original.opciones.all():
                        OpcionRespuesta.objects.create(
                            pregunta=nueva_pregunta,
                            texto=opcion.texto,
                            valor_ponderado=opcion.valor_ponderado,
                            orden=opcion.orden,
                            es_respuesta_final=opcion.es_respuesta_final,
                            pregunta_siguiente=pregunta_map.get(opcion.pregunta_siguiente_id) if opcion.pregunta_siguiente_id else None
                        )
                
                self.message_user(request, f'Árbol "{nuevo_arbol.nombre}" duplicado correctamente.')
                
        except Exception as e:
            self.message_user(request, f'Error al duplicar: {str(e)}', messages.ERROR)
    
    duplicar_arbol.short_description = "Duplicar árbol seleccionado"
    
    def validar_estructura(self, request, queryset):
        for arbol in queryset:
            issues = []
            preguntas = arbol.preguntas.all()
            
            # Validar pregunta inicial
            iniciales = preguntas.filter(es_pregunta_inicial=True)
            if not iniciales.exists():
                issues.append("Sin pregunta inicial")
            elif iniciales.count() > 1:
                issues.append("Múltiples preguntas iniciales")
            
            # Validar conexiones
            for pregunta in preguntas:
                opciones = pregunta.opciones.all()
                if not opciones.exists():
                    issues.append(f"Pregunta '{pregunta.orden}' sin opciones")
                
                for opcion in opciones:
                    if not opcion.es_respuesta_final and not opcion.pregunta_siguiente:
                        issues.append(f"Opción '{opcion.texto[:20]}...' sin siguiente pregunta")
            
            if issues:
                self.message_user(request, f'Árbol "{arbol.nombre}": {"; ".join(issues)}', messages.WARNING)
            else:
                self.message_user(request, f'Árbol "{arbol.nombre}": estructura válida ✓')
    
    validar_estructura.short_description = "Validar estructura de árboles"


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    """Administración avanzada para preguntas"""
    list_display = ('orden', 'arbol', 'texto_corto', 'es_pregunta_inicial', 'total_opciones', 'estado_conexiones')
    list_filter = ('arbol', 'es_pregunta_inicial')
    search_fields = ('texto', 'arbol__nombre')
    ordering = ('arbol', 'orden')
    inlines = [OpcionRespuestaInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('arbol', 'texto', 'orden', 'es_pregunta_inicial')
        }),
        ('Configuración Avanzada', {
            'fields': ('valor', 'var_amenaza', 'pregunta_padre'),
            'classes': ('collapse',),
            'description': 'Configuración avanzada del árbol de decisiones'
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        # Pasar el objeto actual al request para usar en formfield_for_foreignkey
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)
    
    def texto_corto(self, obj):
        return obj.texto[:50] + "..." if len(obj.texto) > 50 else obj.texto
    texto_corto.short_description = "Pregunta"
    
    def total_opciones(self, obj):
        count = obj.opciones.count()
        if count == 0:
            return mark_safe('<span style="color: red;">Sin opciones</span>')
        return f"{count} opciones"
    total_opciones.short_description = "Opciones"
    
    def estado_conexiones(self, obj):
        opciones = obj.opciones.all()
        if not opciones:
            return mark_safe('<span style="color: red;">Sin opciones</span>')
        
        issues = []
        for opcion in opciones:
            if not opcion.es_respuesta_final and not opcion.pregunta_siguiente:
                issues.append(f"'{opcion.texto[:15]}...' sin conexión")
        
        if issues:
            return format_html('<span style="color: orange;">⚠ {}</span>', ', '.join(issues))
        return mark_safe('<span style="color: green;">✓ Conectada</span>')
    estado_conexiones.short_description = "Conexiones"


@admin.register(OpcionRespuesta)
class OpcionRespuestaAdmin(admin.ModelAdmin):
    """Administración avanzada para opciones de respuesta"""
    list_display = ('pregunta_info', 'texto_corto', 'valor_ponderado', 'orden', 'es_respuesta_final', 'conexion_siguiente')
    list_filter = ('es_respuesta_final', 'pregunta__arbol')
    search_fields = ('texto', 'pregunta__texto')
    ordering = ('pregunta__arbol', 'pregunta__orden', 'orden')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('pregunta', 'texto', 'orden')
        }),
        ('Configuración de Evaluación', {
            'fields': ('valor_ponderado', 'es_respuesta_final', 'pregunta_siguiente'),
            'description': 'Configuración para el flujo de evaluación'
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "pregunta_siguiente":
            # Filtrar por árbol de la pregunta actual si existe
            if 'pregunta' in request.GET:
                try:
                    pregunta_id = request.GET['pregunta']
                    pregunta = Pregunta.objects.get(pk=pregunta_id)
                    kwargs["queryset"] = Pregunta.objects.filter(arbol=pregunta.arbol).exclude(pk=pregunta_id)
                except:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def pregunta_info(self, obj):
        return f"{obj.pregunta.arbol.nombre} - P{obj.pregunta.orden}"
    pregunta_info.short_description = "Árbol - Pregunta"
    
    def texto_corto(self, obj):
        return obj.texto[:40] + "..." if len(obj.texto) > 40 else obj.texto
    texto_corto.short_description = "Opción"
    
    def conexion_siguiente(self, obj):
        if obj.es_respuesta_final:
            return mark_safe('<span style="color: blue;">Final</span>')
        elif obj.pregunta_siguiente:
            return format_html('<span style="color: green;">→ P{}</span>', obj.pregunta_siguiente.orden)
        else:
            return mark_safe('<span style="color: red;">Sin conexión</span>')
    conexion_siguiente.short_description = "Siguiente"


@admin.register(PerfilSeguridad)
class PerfilSeguridadAdmin(admin.ModelAdmin):
    """Configuración mejorada para administración de perfiles"""
    list_display = ('nombres_completos', 'tipo_documento', 'numero_documento', 'telefono_principal', 'cargo_politico', 'total_evaluaciones')
    list_filter = ('tipo_documento', 'cargo_politico', 'nivel_exposicion', 'departamento', 'estado_perfil', 'creado_en')
    search_fields = ('nombres', 'apellidos', 'numero_documento', 'municipio', 'departamento')
    readonly_fields = ('creado_en', 'actualizado_en')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombres', 'apellidos', 'tipo_documento', 'numero_documento', 'fecha_nacimiento', 'genero')
        }),
        ('Información de Contacto', {
            'fields': ('telefono_principal', 'telefono_emergencia')
        }),
        ('Información Política', {
            'fields': ('cargo_politico', 'partido_politico', 'nivel_exposicion')
        }),
        ('Ubicación', {
            'fields': ('departamento', 'municipio', 'direccion_residencia', 'direccion_trabajo')
        }),
        ('Información de Seguridad', {
            'fields': ('tiene_esquema_seguridad', 'nivel_esquema_seguridad', 'amenazas_recibidas', 'fecha_ultima_amenaza'),
            'classes': ('collapse',)
        }),
        ('Contacto de Emergencia', {
            'fields': ('contacto_emergencia_nombre', 'contacto_emergencia_telefono', 'contacto_emergencia_relacion'),
            'classes': ('collapse',)
        }),
        ('Control del Perfil', {
            'fields': ('estado_perfil', 'observaciones')
        }),
        ('Metadatos del Sistema', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )
    
    def nombres_completos(self, obj):
        return f"{obj.nombres} {obj.apellidos}"
    nombres_completos.short_description = "Nombre Completo"
    
    def total_evaluaciones(self, obj):
        count = obj.evaluaciones.count()
        if count > 0:
            url = reverse('admin:security_probabilistic_evaluacionseguridad_changelist') + f'?perfil__id__exact={obj.pk}'
            return format_html('<a href="{}">{} evaluaciones</a>', url, count)
        return "Sin evaluaciones"
    total_evaluaciones.short_description = "Evaluaciones"


@admin.register(EvaluacionSeguridad)
class EvaluacionSeguridadAdmin(admin.ModelAdmin):
    """Configuración mejorada para evaluaciones"""
    list_display = ('perfil_info', 'arbol', 'estado', 'probabilidad_total', 'nivel_riesgo_display', 'creada_en')
    list_filter = ('estado', 'arbol', 'nivel_riesgo', 'creada_en')
    search_fields = ('perfil__nombres', 'perfil__apellidos', 'perfil__numero_documento')
    readonly_fields = ('creada_en', 'completada_en', 'probabilidad_total', 'nivel_riesgo')
    date_hierarchy = 'creada_en'
    
    fieldsets = (
        ('Información de la Evaluación', {
            'fields': ('perfil', 'arbol', 'estado')
        }),
        ('Resultados', {
            'fields': ('probabilidad_total', 'nivel_riesgo', 'observaciones'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('creada_en', 'completada_en'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_completadas', 'generar_reporte']
    
    def perfil_info(self, obj):
        return f"{obj.perfil.nombres} {obj.perfil.apellidos}"
    perfil_info.short_description = "Perfil"
    
    def nivel_riesgo_display(self, obj):
        colors = {
            'bajo': 'green',
            'medio': 'orange', 
            'alto': 'red',
            'critico': 'darkred'
        }
        color = colors.get(obj.nivel_riesgo, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                         color, obj.get_nivel_riesgo_display())
    nivel_riesgo_display.short_description = "Nivel de Riesgo"
    
    def marcar_completadas(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(estado='en_progreso').update(
            estado='completada', 
            completada_en=timezone.now()
        )
        self.message_user(request, f'{updated} evaluaciones marcadas como completadas.')
    marcar_completadas.short_description = "Marcar como completadas"
    
    def generar_reporte(self, request, queryset):
        # Aquí podrías implementar la lógica para generar reportes
        self.message_user(request, f'Generando reporte para {queryset.count()} evaluaciones...')
    generar_reporte.short_description = "Generar reporte"


@admin.register(ZonaRiesgo)
class ZonaRiesgoAdmin(admin.ModelAdmin):
    """Configuración mejorada para zonas de riesgo"""
    list_display = ('nombre', 'nivel_riesgo_base', 'activa', 'total_evaluaciones')
    list_filter = ('activa', 'nivel_riesgo_base')
    search_fields = ('nombre', 'descripcion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'nivel_riesgo_base', 'activa')
        }),
        ('Configuración Avanzada', {
            'fields': ('coordenadas_geograficas', 'radio_influencia'),
            'classes': ('collapse',)
        }),
    )
    
    def total_evaluaciones(self, obj):
        # Aquí podrías contar evaluaciones relacionadas con esta zona
        return "N/A"  # Implementar según la lógica de negocio
    total_evaluaciones.short_description = "Evaluaciones"


# ================================
# ADMINISTRADORES GEOGRÁFICOS
# ================================

class MunicipioInline(admin.TabularInline):
    """Inline para gestionar municipios desde departamento"""
    model = Municipio
    extra = 1
    fields = ('nombre', 'codigo_dane', 'categoria', 'nivel_riesgo', 'factor_riesgo', 'usa_riesgo_departamento', 'activo')
    ordering = ('nombre',)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    """Administración de departamentos de Colombia con gestión de riesgo"""
    list_display = ('nombre', 'codigo_dane', 'region', 'nivel_riesgo_display', 'factor_riesgo', 'total_municipios_display', 'activo')
    list_filter = ('region', 'nivel_riesgo', 'activo')
    search_fields = ('nombre', 'codigo_dane')
    ordering = ('nombre',)
    inlines = [MunicipioInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_dane', 'nombre', 'region')
        }),
        ('Gestión de Riesgo', {
            'fields': ('nivel_riesgo', 'factor_riesgo', 'observaciones'),
            'description': 'Configuración del nivel de riesgo para evaluaciones de seguridad'
        }),
        ('Control', {
            'fields': ('activo',)
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('creado_en', 'actualizado_en')
    actions = ['activar_departamentos', 'desactivar_departamentos', 'establecer_riesgo_medio', 'establecer_riesgo_alto']
    
    def nivel_riesgo_display(self, obj):
        colors = {
            'muy_bajo': 'green',
            'bajo': 'lightgreen',
            'medio': 'orange', 
            'alto': 'red',
            'muy_alto': 'darkred',
            'critico': 'purple'
        }
        color = colors.get(obj.nivel_riesgo, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                         color, obj.get_nivel_riesgo_display())
    nivel_riesgo_display.short_description = "Nivel de Riesgo"
    
    def total_municipios_display(self, obj):
        count = obj.total_municipios
        if count > 0:
            url = reverse('admin:security_probabilistic_municipio_changelist') + f'?departamento__id__exact={obj.pk}'
            return format_html('<a href="{}">{} municipios</a>', url, count)
        return "Sin municipios"
    total_municipios_display.short_description = "Municipios"
    
    def activar_departamentos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} departamentos activados.')
    activar_departamentos.short_description = "Activar departamentos seleccionados"
    
    def desactivar_departamentos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} departamentos desactivados.')
    desactivar_departamentos.short_description = "Desactivar departamentos seleccionados"
    
    def establecer_riesgo_medio(self, request, queryset):
        updated = queryset.update(nivel_riesgo='medio', factor_riesgo=0.500)
        self.message_user(request, f'{updated} departamentos configurados con riesgo medio.')
    establecer_riesgo_medio.short_description = "Establecer riesgo medio"
    
    def establecer_riesgo_alto(self, request, queryset):
        updated = queryset.update(nivel_riesgo='alto', factor_riesgo=0.750)
        self.message_user(request, f'{updated} departamentos configurados con riesgo alto.')
    establecer_riesgo_alto.short_description = "Establecer riesgo alto"


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    """Administración de municipios de Colombia con gestión de riesgo"""
    list_display = ('nombre', 'departamento', 'codigo_dane', 'categoria', 'nivel_riesgo_efectivo_display', 'factor_riesgo_efectivo', 'usa_riesgo_departamento', 'poblacion_display', 'activo')
    list_filter = ('departamento', 'categoria', 'nivel_riesgo', 'usa_riesgo_departamento', 'activo')
    search_fields = ('nombre', 'codigo_dane', 'departamento__nombre')
    ordering = ('departamento__nombre', 'nombre')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('departamento', 'codigo_dane', 'nombre', 'categoria', 'poblacion')
        }),
        ('Gestión de Riesgo', {
            'fields': ('usa_riesgo_departamento', 'nivel_riesgo', 'factor_riesgo', 'observaciones'),
            'description': 'Configuración del nivel de riesgo para evaluaciones. Si "Usar Riesgo del Departamento" está marcado, se usará el riesgo del departamento.'
        }),
        ('Control', {
            'fields': ('activo',)
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('creado_en', 'actualizado_en')
    actions = ['activar_municipios', 'desactivar_municipios', 'usar_riesgo_departamento', 'usar_riesgo_propio']
    
    def nivel_riesgo_efectivo_display(self, obj):
        nivel = obj.nivel_riesgo_efectivo
        colors = {
            'muy_bajo': 'green',
            'bajo': 'lightgreen',
            'medio': 'orange', 
            'alto': 'red',
            'muy_alto': 'darkred',
            'critico': 'purple'
        }
        color = colors.get(nivel, 'gray')
        source = "Dep." if obj.usa_riesgo_departamento else "Mun."
        return format_html('<span style="color: {}; font-weight: bold;">{}</span> <small>({})</small>', 
                         color, obj.get_nivel_riesgo_display() if not obj.usa_riesgo_departamento else obj.departamento.get_nivel_riesgo_display(), source)
    nivel_riesgo_efectivo_display.short_description = "Nivel de Riesgo Efectivo"
    
    def poblacion_display(self, obj):
        if obj.poblacion:
            return f"{obj.poblacion:,}"
        return "No especificada"
    poblacion_display.short_description = "Población"
    
    def activar_municipios(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} municipios activados.')
    activar_municipios.short_description = "Activar municipios seleccionados"
    
    def desactivar_municipios(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} municipios desactivados.')
    desactivar_municipios.short_description = "Desactivar municipios seleccionados"
    
    def usar_riesgo_departamento(self, request, queryset):
        updated = queryset.update(usa_riesgo_departamento=True)
        self.message_user(request, f'{updated} municipios configurados para usar el riesgo del departamento.')
    usar_riesgo_departamento.short_description = "Usar riesgo del departamento"
    
    def usar_riesgo_propio(self, request, queryset):
        updated = queryset.update(usa_riesgo_departamento=False)
        self.message_user(request, f'{updated} municipios configurados para usar su propio riesgo.')
    usar_riesgo_propio.short_description = "Usar riesgo propio"


# ================================
# CONFIGURACIÓN GLOBAL DEL ADMIN
# ================================

admin.site.site_header = "Administración - Security Probabilistic"
admin.site.site_title = "Security Probabilistic Admin"
admin.site.index_title = "Panel de Administración"
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg, Q
from django.contrib.admin.views.main import ChangeList
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
import csv

from .models import (
    TipoConjunto, Conjunto,
    TipoRiesgo, EscenarioRiesgo, PreguntaEvaluacion, CalificacionOpcion,
    EvaluacionRiesgo, ResultadoRiesgo, ResultadoEscenario, RespuestaPregunta,
    ResultadoPregunta, CategoriaSeguridad, PreguntaSeguridad, 
    EvaluacionSeguridad, RespuestaEvaluacion, ScoreCategoria
)
from .models_optimized import AnalisisRiesgo, PonderacionRiesgo, MetricaCalidad, RecomendacionSistema


class BaseModelAdmin(admin.ModelAdmin):
    """Clase base para todos los admins con configuraciones comunes"""
    
    def get_readonly_fields(self, request, obj=None):
        """Hacer campos de fecha/tiempo readonly automáticamente"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        common_readonly = [
            'id', 'created_at', 'updated_at', 'fecha_creacion', 
            'fecha_actualizacion', 'deleted_at'
        ]
        for field in common_readonly:
            if hasattr(self.model, field) and field not in readonly_fields:
                readonly_fields.append(field)
        return readonly_fields


# ============================================================================
# ADMIN PARA CONFIGURACIÓN BÁSICA
# ============================================================================

@admin.register(TipoConjunto)
class TipoConjuntoAdmin(BaseModelAdmin):
    list_display = ('get_nombre_display', 'descripcion', 'icono_preview', 'color_preview')
    list_editable = ('descripcion',)
    search_fields = ('nombre', 'descripcion')
    list_per_page = 20
    
    def icono_preview(self, obj):
        return format_html(
            '<i class="{}" style="font-size: 16px; color: {};"></i>',
            obj.icono,
            obj.color
        )
    icono_preview.short_description = "Vista previa"
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.color
        )
    color_preview.short_description = "Color"


@admin.register(CategoriaSeguridad)
class CategoriaSeguridad(BaseModelAdmin):
    list_display = ('nombre', 'codigo', 'icono_preview', 'peso', 'orden', 'preguntas_count', 'activa')
    list_editable = ('peso', 'orden', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre', 'codigo', 'descripcion')
    ordering = ('orden',)
    
    def icono_preview(self, obj):
        return format_html('<i class="{}"></i>', obj.icono)
    icono_preview.short_description = "Icono"
    
    def preguntas_count(self, obj):
        return obj.preguntas.count()
    preguntas_count.short_description = "# Preguntas"
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('preguntas')


@admin.register(CalificacionOpcion)
class CalificacionOpcionAdmin(BaseModelAdmin):
    list_display = ('nombre', 'codigo', 'valor', 'orden', 'color_badge', 'activa')
    list_editable = ('valor', 'orden', 'activa')
    list_filter = ('activa',)
    ordering = ('orden',)
    
    def color_badge(self, obj):
        colors = {
            'ausente': '#dc3545',
            'deficiente': '#fd7e14', 
            'vulnerable': '#ffc107',
            'adecuado': '#20c997',
            'eficaz': '#198754'
        }
        color = colors.get(obj.codigo, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.nombre
        )
    color_badge.short_description = "Vista"


# ============================================================================
# ADMIN PARA CONJUNTOS
# ============================================================================

def export_conjuntos_csv(modeladmin, request, queryset):
    """Exportar conjuntos seleccionados a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="conjuntos.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'NIT', 'Nombre', 'Tipo', 'Ciudad', 'Departamento', 
        'Unidades', 'Torres', 'Administrador', 'Teléfono', 'Estado'
    ])
    
    for conjunto in queryset:
        writer.writerow([
            conjunto.nit, conjunto.nombre, conjunto.tipo_conjunto.get_nombre_display(),
            conjunto.ciudad, conjunto.departamento, conjunto.numero_unidades,
            conjunto.numero_torres, conjunto.administrador_nombre,
            conjunto.administrador_telefono, 'Activo' if conjunto.activo else 'Inactivo'
        ])
    
    return response
export_conjuntos_csv.short_description = "Exportar conjuntos a CSV"


def export_evaluaciones_csv(modeladmin, request, queryset):
    """Exportar evaluaciones de conjuntos seleccionados a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="evaluaciones_conjuntos_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Conjunto', 'NIT', 'Fecha Evaluación', 'Estado', 
        'Evaluador', 'Promedio General', 'Observaciones'
    ])
    
    for conjunto in queryset:
        evaluaciones = EvaluacionRiesgo.objects.filter(conjunto=conjunto).order_by('-fecha_evaluacion')
        if evaluaciones.exists():
            for eval in evaluaciones[:5]:  # Últimas 5 evaluaciones
                writer.writerow([
                    conjunto.nombre,
                    conjunto.nit,
                    eval.fecha_evaluacion.strftime('%Y-%m-%d'),
                    eval.get_estado_display(),
                    eval.creado_por.get_full_name() if eval.creado_por else 'N/A',
                    f"{eval.promedio_general:.2f}" if eval.promedio_general else 'N/A',
                    eval.observaciones[:100] if eval.observaciones else 'Sin observaciones'
                ])
        else:
            writer.writerow([
                conjunto.nombre,
                conjunto.nit,
                'Sin evaluaciones',
                '-',
                '-',
                '-',
                'No hay evaluaciones registradas'
            ])
    
    return response
export_evaluaciones_csv.short_description = "Exportar evaluaciones de conjuntos a CSV"


@admin.register(Conjunto)
class ConjuntoAdmin(BaseModelAdmin):
    list_display = (
        'nombre', 'nit', 'tipo_conjunto', 'ciudad', 'unidades_torres',
        'propietario', 'estado_badge', 'evaluaciones_count', 'ultimo_assessment', 'acciones'
    )
    list_filter = ('tipo_conjunto', 'ciudad', 'departamento', 'activo', 'fecha_creacion')
    search_fields = ('nombre', 'nit', 'direccion', 'administrador_nombre', 'propietario__username', 'propietario__first_name', 'propietario__last_name')
    readonly_fields = ('id', 'fecha_creacion', 'fecha_actualizacion', 'amenidades_resumen')
    list_per_page = 25
    date_hierarchy = 'fecha_creacion'
    actions = [export_conjuntos_csv, export_evaluaciones_csv]
    
    fieldsets = (
        ('🏢 Información Básica', {
            'fields': ('propietario', 'nombre', 'tipo_conjunto', 'nit', 'activo'),
            'classes': ('wide',)
        }),
        ('📍 Ubicación', {
            'fields': ('direccion', 'ciudad', 'departamento'),
            'classes': ('wide',)
        }),
        ('🏗️ Características', {
            'fields': ('numero_torres', 'numero_unidades', 'amenidades_resumen'),
            'classes': ('wide',)
        }),
        ('🏊‍♂️ Amenidades', {
            'fields': ('tiene_piscina', 'tiene_gimnasio', 'tiene_salon_social', 
                      'tiene_juegos_infantiles', 'tiene_canchas_deportivas'),
            'classes': ('wide',)
        }),
        ('👥 Administración', {
            'fields': ('administrador_nombre', 'administrador_telefono', 'administrador_email'),
            'classes': ('wide',)
        }),
        ('ℹ️ Información del Sistema', {
            'fields': ('id', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def unidades_torres(self, obj):
        return f"{obj.numero_unidades} unidades / {obj.numero_torres} torres"
    unidades_torres.short_description = "Unidades/Torres"
    
    def estado_badge(self, obj):
        color = 'success' if obj.activo else 'danger'
        estado = 'Activo' if obj.activo else 'Inactivo'
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, estado
        )
    estado_badge.short_description = "Estado"
    
    def evaluaciones_count(self, obj):
        count = obj.evaluaciones_riesgo.count()
        if count > 0:
            return format_html(
                '<a href="{}?conjunto__id__exact={}">{} evaluaciones</a>',
                reverse('admin:risk_conjuntos_evaluacionriesgo_changelist'),
                obj.id, count
            )
        return "Sin evaluaciones"
    evaluaciones_count.short_description = "Evaluaciones"
    
    def ultimo_assessment(self, obj):
        ultima = obj.evaluaciones_riesgo.filter(estado='completada').order_by('-fecha_evaluacion').first()
        if ultima:
            days_ago = (timezone.now().date() - ultima.fecha_evaluacion.date()).days
            color = 'success' if days_ago < 30 else 'warning' if days_ago < 90 else 'danger'
            return format_html(
                '<span class="badge badge-{}">{} días</span>',
                color, days_ago
            )
        return mark_safe('<span class="badge badge-secondary">Nunca</span>')
    ultimo_assessment.short_description = "Último Assessment"
    
    def amenidades_resumen(self, obj):
        amenidades = []
        if obj.tiene_piscina: amenidades.append("🏊‍♂️ Piscina")
        if obj.tiene_gimnasio: amenidades.append("🏋️‍♂️ Gimnasio") 
        if obj.tiene_salon_social: amenidades.append("🎉 Salón Social")
        if obj.tiene_juegos_infantiles: amenidades.append("🎪 Juegos Infantiles")
        if obj.tiene_canchas_deportivas: amenidades.append("⚽ Canchas Deportivas")
        
        if amenidades:
            return format_html('<br>'.join(amenidades))
        return "Sin amenidades registradas"
    amenidades_resumen.short_description = "Amenidades"
    
    def acciones(self, obj):
        return format_html(
            '<a href="{}" class="button" target="_blank">Ver Dashboard</a> | '
            '<a href="{}" class="button">Nueva Evaluación</a>',
            reverse('risk_conjuntos:dashboard') + f'?conjunto_id={obj.id}',
            reverse('risk_conjuntos:iniciar_evaluacion', args=[obj.id])
        )
    acciones.short_description = "Acciones"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'propietario', 'tipo_conjunto'
        ).prefetch_related('evaluaciones_riesgo')


# ============================================================================
# ADMIN PARA SISTEMA DE EVALUACIÓN DE RIESGOS
# ============================================================================

@admin.register(TipoRiesgo)
class TipoRiesgoAdmin(BaseModelAdmin):
    list_display = ('nombre', 'codigo', 'escenarios_count', 'preguntas_count', 'orden', 'estado_badge')
    list_editable = ('orden',)
    list_filter = ('activo',)
    search_fields = ('nombre', 'codigo', 'descripcion')
    ordering = ('orden',)
    
    def escenarios_count(self, obj):
        return obj.escenarios.count()
    escenarios_count.short_description = "# Escenarios"
    
    def preguntas_count(self, obj):
        return PreguntaEvaluacion.objects.filter(escenario__tipo_riesgo=obj).count()
    preguntas_count.short_description = "# Preguntas"
    
    def estado_badge(self, obj):
        color = 'success' if obj.activo else 'secondary'
        estado = 'Activo' if obj.activo else 'Inactivo'
        return format_html('<span class="badge badge-{}">{}</span>', color, estado)
    estado_badge.short_description = "Estado"
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('escenarios')


class PreguntaEvaluacionInline(admin.TabularInline):
    model = PreguntaEvaluacion
    extra = 0
    fields = ('texto_pregunta', 'orden', 'obligatoria', 'activa')
    readonly_fields = ()


@admin.register(EscenarioRiesgo)
class EscenarioRiesgoAdmin(BaseModelAdmin):
    list_display = ('nombre', 'tipo_riesgo', 'codigo', 'preguntas_count', 'orden', 'estado_badge')
    list_editable = ('orden',)
    list_filter = ('tipo_riesgo', 'activo')
    search_fields = ('nombre', 'codigo', 'descripcion')
    ordering = ('tipo_riesgo', 'orden')
    inlines = [PreguntaEvaluacionInline]
    
    def preguntas_count(self, obj):
        return obj.preguntas.count()
    preguntas_count.short_description = "# Preguntas"
    
    def estado_badge(self, obj):
        color = 'success' if obj.activo else 'secondary'
        estado = 'Activo' if obj.activo else 'Inactivo'
        return format_html('<span class="badge badge-{}">{}</span>', color, estado)
    estado_badge.short_description = "Estado"


@admin.register(PreguntaEvaluacion)
class PreguntaEvaluacionAdmin(BaseModelAdmin):
    list_display = ('texto_pregunta_corto', 'escenario_info', 'orden', 'obligatoria', 'estado_badge', 'respuestas_count')
    list_filter = ('escenario__tipo_riesgo', 'obligatoria', 'activa')
    search_fields = ('texto_pregunta', 'escenario__nombre', 'escenario__tipo_riesgo__nombre')
    ordering = ('escenario__tipo_riesgo', 'escenario', 'orden')
    list_per_page = 30
    
    fieldsets = (
        ('📝 Contenido de la Pregunta', {
            'fields': ('escenario', 'texto_pregunta', 'ayuda'),
            'classes': ('wide',)
        }),
        ('⚙️ Configuración', {
            'fields': ('orden', 'obligatoria', 'activa'),
            'classes': ('wide',)
        }),
        ('ℹ️ Información del Sistema', {
            'fields': (),
            'classes': ('collapse',)
        }),
    )
    
    def texto_pregunta_corto(self, obj):
        return obj.texto_pregunta[:60] + "..." if len(obj.texto_pregunta) > 60 else obj.texto_pregunta
    texto_pregunta_corto.short_description = "Pregunta"
    
    def escenario_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.escenario.nombre,
            obj.escenario.tipo_riesgo.nombre
        )
    escenario_info.short_description = "Escenario / Tipo de Riesgo"
    
    def estado_badge(self, obj):
        if not obj.activa:
            return mark_safe('<span class="badge badge-secondary">Inactiva</span>')
        elif obj.obligatoria:
            return mark_safe('<span class="badge badge-danger">Obligatoria</span>')
        else:
            return mark_safe('<span class="badge badge-success">Opcional</span>')
    estado_badge.short_description = "Estado"
    
    def respuestas_count(self, obj):
        count = RespuestaPregunta.objects.filter(pregunta=obj).count()
        if count > 0:
            return format_html(
                '<a href="{}?pregunta__id__exact={}">{} respuestas</a>',
                reverse('admin:risk_conjuntos_respuestapregunta_changelist'),
                obj.id, count
            )
        return "0 respuestas"
    respuestas_count.short_description = "Respuestas"


# ============================================================================
# ADMIN PARA EVALUACIONES Y RESULTADOS
# ============================================================================

def export_evaluaciones_csv(modeladmin, request, queryset):
    """Exportar evaluaciones seleccionadas a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="evaluaciones_riesgo.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Conjunto', 'NIT', 'Tipo Evaluación', 'Fecha', 'Estado', 
        'Promedio General', 'Evaluador', 'Tiempo (min)'
    ])
    
    for evaluacion in queryset:
        writer.writerow([
            evaluacion.conjunto.nombre, evaluacion.conjunto.nit,
            evaluacion.get_tipo_evaluacion_display(), evaluacion.fecha_evaluacion.strftime('%Y-%m-%d'),
            evaluacion.get_estado_display(), evaluacion.promedio_general or 'N/A',
            evaluacion.creado_por.get_full_name() if evaluacion.creado_por else 'N/A',
            evaluacion.tiempo_evaluacion_minutos or 'N/A'
        ])
    
    return response
export_evaluaciones_csv.short_description = "Exportar evaluaciones a CSV"


@admin.register(EvaluacionRiesgo)
class EvaluacionRiesgoAdmin(BaseModelAdmin):
    list_display = (
        'conjunto_info', 'tipo_evaluacion', 'fecha_evaluacion', 
        'evaluador_info', 'estado_badge', 'promedio_badge', 'tiempo_evaluacion',
        'acciones'
    )
    list_filter = ('tipo_evaluacion', 'estado', 'fecha_evaluacion', 'deleted_at')
    search_fields = ('conjunto__nombre', 'conjunto__nit', 'creado_por__username', 'creado_por__first_name', 'creado_por__last_name')
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'deleted_at',
        'fecha_completado', 'promedio_general', 'ip_evaluacion'
    )
    date_hierarchy = 'fecha_evaluacion'
    list_per_page = 20
    actions = [export_evaluaciones_csv]
    
    fieldsets = (
        ('🏢 Información General', {
            'fields': ('conjunto', 'creado_por', 'tipo_evaluacion', 'fecha_evaluacion'),
            'classes': ('wide',)
        }),
        ('📊 Estado y Resultados', {
            'fields': ('estado', 'promedio_general', 'tiempo_evaluacion_minutos'),
            'classes': ('wide',)
        }),
        ('📝 Observaciones y Recomendaciones', {
            'fields': ('observaciones_generales', 'recomendaciones_generales', 'conclusiones'),
            'classes': ('wide',)
        }),
        ('🔬 Campos Adicionales', {
            'fields': ('metodologia_aplicada', 'limitaciones_evaluacion', 'proximas_acciones'),
            'classes': ('collapse',)
        }),
        ('ℹ️ Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'deleted_at', 'fecha_completado', 'ip_evaluacion'),
            'classes': ('collapse',)
        }),
    )
    
    def conjunto_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>NIT: {} | {}</small>',
            obj.conjunto.nombre,
            obj.conjunto.nit,
            obj.conjunto.ciudad
        )
    conjunto_info.short_description = "Conjunto"
    
    def evaluador_info(self, obj):
        if obj.creado_por:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.creado_por.get_full_name() or obj.creado_por.username,
                obj.creado_por.email
            )
        return "N/A"
    evaluador_info.short_description = "Evaluador"
    
    def estado_badge(self, obj):
        colors = {
            'borrador': 'secondary',
            'en_progreso': 'primary',
            'completada': 'success',
            'revisada': 'info'
        }
        color = colors.get(obj.estado, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    
    def promedio_badge(self, obj):
        if obj.promedio_general is None:
            return mark_safe('<span class="badge badge-secondary">Sin calcular</span>')
        
        promedio = float(obj.promedio_general)
        if promedio >= 4.0:
            color = 'success'
        elif promedio >= 3.0:
            color = 'warning'
        else:
            color = 'danger'
            
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, f"{promedio:.1f}"
        )
    promedio_badge.short_description = "Promedio"
    
    def tiempo_evaluacion(self, obj):
        if obj.tiempo_evaluacion_minutos:
            return f"{obj.tiempo_evaluacion_minutos} min"
        return "N/A"
    tiempo_evaluacion.short_description = "Tiempo"
    
    def acciones(self, obj):
        return format_html(
            '<a href="{}" class="button" target="_blank">Ver Detalle</a> | '
            '<a href="{}" class="button">Ver PDF</a>',
            reverse('risk_conjuntos:detalle_evaluacion', args=[obj.conjunto.id, obj.id]),
            reverse('risk_conjuntos:generar_pdf_evaluacion', args=[obj.id])
        )
    acciones.short_description = "Acciones"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conjunto', 'creado_por'
        )


@admin.register(RespuestaPregunta)
class RespuestaPreguntaAdmin(BaseModelAdmin):
    list_display = (
        'pregunta_corta', 'evaluacion_info', 'calificacion_badge', 
        'resultado_badge', 'fecha_respuesta'
    )
    list_filter = ('calificacion__codigo', 'fecha_respuesta', 'evaluacion__estado')
    search_fields = (
        'evaluacion__conjunto__nombre', 'pregunta__texto_pregunta',
        'evaluacion__creado_por__username'
    )
    readonly_fields = ('resultado_calculado', 'fecha_respuesta')
    list_per_page = 30
    
    def pregunta_corta(self, obj):
        return obj.pregunta.texto_pregunta[:50] + "..." if len(obj.pregunta.texto_pregunta) > 50 else obj.pregunta.texto_pregunta
    pregunta_corta.short_description = "Pregunta"
    
    def evaluacion_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.evaluacion.conjunto.nombre,
            obj.evaluacion.fecha_evaluacion.strftime('%Y-%m-%d')
        )
    evaluacion_info.short_description = "Evaluación"
    
    def calificacion_badge(self, obj):
        if obj.calificacion:
            colors = {
                'ausente': 'danger',
                'deficiente': 'warning', 
                'vulnerable': 'warning',
                'adecuado': 'info',
                'eficaz': 'success'
            }
            color = colors.get(obj.calificacion.codigo, 'secondary')
            return format_html(
                '<span class="badge badge-{}">{}</span>',
                color, obj.calificacion.nombre
            )
        return "Sin calificar"
    calificacion_badge.short_description = "Calificación"
    
    def resultado_badge(self, obj):
        if obj.resultado_calculado is not None:
            resultado = float(obj.resultado_calculado)
            if resultado >= 4.0:
                color = 'success'
            elif resultado >= 3.0:
                color = 'warning'
            else:
                color = 'danger'
            return format_html(
                '<span class="badge badge-{}">{}</span>',
                color, f"{resultado:.1f}"
            )
        return "N/A"
    resultado_badge.short_description = "Resultado"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'evaluacion__conjunto', 'pregunta', 'calificacion'
        )


# ============================================================================
# ADMIN PARA MODELOS OPTIMIZADOS (IA/ML)
# ============================================================================

@admin.register(AnalisisRiesgo)
class AnalisisRiesgoAdmin(BaseModelAdmin):
    list_display = ('nivel_riesgo_badge', 'porcentaje_display', 'valor_riesgo', 'fecha_calculo')
    list_filter = ('nivel_riesgo', 'fecha_calculo')
    readonly_fields = ('porcentaje_riesgo', 'nivel_riesgo', 'fecha_calculo', 'fecha_actualizacion')
    
    fieldsets = (
        ('🎯 Análisis de Riesgo', {
            'fields': ('valor_riesgo', 'porcentaje_riesgo', 'nivel_riesgo'),
            'classes': ('wide',)
        }),
        ('ℹ️ Metadata', {
            'fields': ('fecha_calculo', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def nivel_riesgo_badge(self, obj):
        color_map = {
            'muy_bajo': 'success',
            'bajo': 'info',
            'medio': 'warning', 
            'alto': 'danger',
            'critico': 'dark'
        }
        color = color_map.get(obj.nivel_riesgo, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_nivel_riesgo_display()
        )
    nivel_riesgo_badge.short_description = "Nivel de Riesgo"
    
    def porcentaje_display(self, obj):
        return f"{obj.porcentaje_riesgo:.1f}%"
    porcentaje_display.short_description = "% Riesgo"


@admin.register(PonderacionRiesgo)
class PonderacionRiesgoAdmin(BaseModelAdmin):
    list_display = ('peso_pregunta', 'valor_ponderado_display', 'version_algoritmo', 'fecha_calculo')
    list_filter = ('version_algoritmo', 'fecha_calculo')
    readonly_fields = ('fecha_calculo',)
    
    def valor_ponderado_display(self, obj):
        return f"{obj.valor_ponderado:.3f}"
    valor_ponderado_display.short_description = "Valor Ponderado"


@admin.register(MetricaCalidad)
class MetricaCalidadAdmin(BaseModelAdmin):
    list_display = ('confiabilidad_display', 'requiere_atencion_badge', 'tiempo_procesamiento_display', 'fecha_calculo')
    list_filter = ('requiere_atencion', 'fecha_calculo')
    readonly_fields = ('fecha_calculo',)
    
    def confiabilidad_display(self, obj):
        return f"{obj.confiabilidad:.1f}%"
    confiabilidad_display.short_description = "Confiabilidad"
    
    def requiere_atencion_badge(self, obj):
        color = 'danger' if obj.requiere_atencion else 'success'
        texto = 'Sí' if obj.requiere_atencion else 'No'
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, texto
        )
    requiere_atencion_badge.short_description = "Requiere Atención"
    
    def tiempo_procesamiento_display(self, obj):
        return f"{obj.tiempo_procesamiento_ms} ms"
    tiempo_procesamiento_display.short_description = "Tiempo"


@admin.register(RecomendacionSistema)
class RecomendacionSistemaAdmin(BaseModelAdmin):
    list_display = ('tipo_recomendacion', 'es_critica_badge', 'recomendacion_corta', 'fecha_generacion')
    list_filter = ('tipo_recomendacion', 'es_critica', 'fecha_generacion')
    readonly_fields = ('fecha_generacion',)
    
    def recomendacion_corta(self, obj):
        return f'{obj.recomendacion_automatica[:60]}...'
    recomendacion_corta.short_description = "Recomendación"
    
    def es_critica_badge(self, obj):
        color = 'danger' if obj.es_critica else 'info'
        texto = 'Crítica' if obj.es_critica else 'Normal'
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, texto
        )
    es_critica_badge.short_description = "Criticidad"


# ============================================================================
# ADMIN PARA SISTEMA LEGACY DE EVALUACIÓN DE SEGURIDAD
# ============================================================================

@admin.register(PreguntaSeguridad)
class PreguntaSeguridadAdmin(BaseModelAdmin):
    list_display = ('texto_corto', 'categoria', 'tipo_respuesta', 'peso', 'orden', 'estado_badge', 'respuestas_count')
    list_filter = ('categoria', 'tipo_respuesta', 'obligatoria', 'activa')
    search_fields = ('texto_pregunta', 'categoria__nombre')
    list_editable = ('peso', 'orden')
    ordering = ('categoria', 'orden')
    
    fieldsets = (
        ('📝 Contenido de la Pregunta', {
            'fields': ('categoria', 'texto_pregunta', 'ayuda'),
            'classes': ('wide',)
        }),
        ('⚙️ Configuración', {
            'fields': ('tipo_respuesta', 'opciones_json', 'obligatoria', 'activa', 'orden', 'peso'),
            'classes': ('wide',)
        }),
    )
    
    def texto_corto(self, obj):
        return obj.texto_pregunta[:50] + "..." if len(obj.texto_pregunta) > 50 else obj.texto_pregunta
    texto_corto.short_description = "Pregunta"
    
    def estado_badge(self, obj):
        if not obj.activa:
            return mark_safe('<span class="badge badge-secondary">Inactiva</span>')
        elif obj.obligatoria:
            return mark_safe('<span class="badge badge-danger">Obligatoria</span>')
        else:
            return mark_safe('<span class="badge badge-success">Opcional</span>')
    estado_badge.short_description = "Estado"
    
    def respuestas_count(self, obj):
        count = RespuestaEvaluacion.objects.filter(pregunta=obj).count()
        return f"{count} respuestas"
    respuestas_count.short_description = "# Respuestas"


@admin.register(EvaluacionSeguridad)
class EvaluacionSeguridadAdmin(BaseModelAdmin):
    list_display = ('conjunto_info', 'tipo_evaluacion', 'fecha_evaluacion', 'evaluador_info', 'estado_badge', 'score_badge', 'acciones')
    list_filter = ('tipo_evaluacion', 'estado', 'fecha_evaluacion')
    search_fields = ('conjunto__nombre', 'conjunto__nit', 'creado_por__username', 'creado_por__first_name', 'creado_por__last_name')
    readonly_fields = ('score_total', 'fecha_completado', 'ip_evaluacion', 'tiempo_evaluacion_minutos')
    date_hierarchy = 'fecha_evaluacion'
    
    fieldsets = (
        ('🏢 Información General', {
            'fields': ('conjunto', 'creado_por', 'tipo_evaluacion', 'fecha_evaluacion'),
            'classes': ('wide',)
        }),
        ('📊 Estado y Resultados', {
            'fields': ('estado', 'score_total', 'tiempo_evaluacion_minutos'),
            'classes': ('wide',)
        }),
        ('📝 Observaciones', {
            'fields': ('observaciones', 'recomendaciones'),
            'classes': ('wide',)
        }),
        ('ℹ️ Metadata', {
            'fields': ('fecha_completado', 'ip_evaluacion'),
            'classes': ('collapse',)
        }),
    )
    
    def conjunto_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>NIT: {} | {}</small>',
            obj.conjunto.nombre,
            obj.conjunto.nit,
            obj.conjunto.ciudad
        )
    conjunto_info.short_description = "Conjunto"
    
    def evaluador_info(self, obj):
        if obj.creado_por:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.creado_por.get_full_name() or obj.creado_por.username,
                obj.creado_por.email
            )
        return "N/A"
    evaluador_info.short_description = "Evaluador"
    
    def estado_badge(self, obj):
        colors = {
            'borrador': 'secondary',
            'en_progreso': 'primary', 
            'completada': 'success',
            'revisada': 'info'
        }
        color = colors.get(obj.estado, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    
    def score_badge(self, obj):
        if obj.score_total is not None:
            score = float(obj.score_total)
            if score >= 80:
                color = 'success'
            elif score >= 60:
                color = 'warning'
            else:
                color = 'danger'
            return format_html(
                '<span class="badge badge-{}">{}</span>',
                color, f"{score:.1f}%"
            )
        return "Sin calcular"
    score_badge.short_description = "Score"
    
    def acciones(self, obj):
        return format_html(
            '<a href="{}" class="button" target="_blank">Ver Evaluación</a>',
            reverse('risk_conjuntos:detalle_evaluacion_legacy', args=[obj.id])
        )
    acciones.short_description = "Acciones"


@admin.register(RespuestaEvaluacion)
class RespuestaEvaluacionAdmin(BaseModelAdmin):
    list_display = ('evaluacion_info', 'pregunta_corta', 'rating', 'fecha_respuesta')
    list_filter = ('evaluacion__estado', 'fecha_respuesta', 'pregunta__categoria')
    search_fields = ('evaluacion__conjunto__nombre', 'pregunta__texto_pregunta')
    readonly_fields = ('fecha_respuesta',)
    
    def evaluacion_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.evaluacion.conjunto.nombre,
            obj.evaluacion.fecha_evaluacion.strftime('%Y-%m-%d')
        )
    evaluacion_info.short_description = "Evaluación"
    
    def pregunta_corta(self, obj):
        return obj.pregunta.texto_pregunta[:50] + "..." if len(obj.pregunta.texto_pregunta) > 50 else obj.pregunta.texto_pregunta
    pregunta_corta.short_description = "Pregunta"


@admin.register(ScoreCategoria)
class ScoreCategoriaAdmin(BaseModelAdmin):
    list_display = ('evaluacion_info', 'categoria', 'score', 'porcentaje')
    list_filter = ('categoria',)
    search_fields = ('evaluacion__conjunto__nombre', 'categoria__nombre')
    
    def evaluacion_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.evaluacion.conjunto.nombre,
            obj.evaluacion.fecha_evaluacion.strftime('%Y-%m-%d')
        )
    evaluacion_info.short_description = "Evaluación"


# ============================================================================
# ADMIN PARA RESULTADOS ADICIONALES
# ============================================================================

@admin.register(ResultadoRiesgo)
class ResultadoRiesgoAdmin(BaseModelAdmin):
    list_display = ('evaluacion_info', 'tipo_riesgo', 'promedio_badge', 'escenarios_evaluados')
    list_filter = ('tipo_riesgo',)
    search_fields = ('evaluacion__conjunto__nombre', 'tipo_riesgo__nombre')
    
    def evaluacion_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.evaluacion.conjunto.nombre,
            obj.evaluacion.fecha_evaluacion.strftime('%Y-%m-%d')
        )
    evaluacion_info.short_description = "Evaluación"
    
    def promedio_badge(self, obj):
        if obj.promedio_riesgo is not None:
            promedio = float(obj.promedio_riesgo)
            if promedio >= 4.0:
                color = 'success'
            elif promedio >= 3.0:
                color = 'warning'
            else:
                color = 'danger'
            return format_html(
                '<span class="badge badge-{}">{}</span>',
                color, f"{promedio:.2f}"
            )
        return "N/A"
    promedio_badge.short_description = "Promedio"
    
    def escenarios_evaluados(self, obj):
        count = ResultadoEscenario.objects.filter(evaluacion=obj.evaluacion, escenario__tipo_riesgo=obj.tipo_riesgo).count()
        return f"{count} escenarios"
    escenarios_evaluados.short_description = "Escenarios"


@admin.register(ResultadoEscenario)
class ResultadoEscenarioAdmin(BaseModelAdmin):
    list_display = ('evaluacion_info', 'escenario', 'promedio_badge', 'preguntas_respondidas')
    list_filter = ('escenario__tipo_riesgo',)
    search_fields = ('evaluacion__conjunto__nombre', 'escenario__nombre')
    
    def evaluacion_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.evaluacion.conjunto.nombre,
            obj.evaluacion.fecha_evaluacion.strftime('%Y-%m-%d')
        )
    evaluacion_info.short_description = "Evaluación"
    
    def promedio_badge(self, obj):
        if obj.promedio_escenario is not None:
            promedio = float(obj.promedio_escenario)
            if promedio >= 4.0:
                color = 'success'
            elif promedio >= 3.0:
                color = 'warning'
            else:
                color = 'danger'
            return format_html(
                '<span class="badge badge-{}">{}</span>',
                color, f"{promedio:.2f}"
            )
        return "N/A"
    promedio_badge.short_description = "Promedio"
    
    def preguntas_respondidas(self, obj):
        count = RespuestaPregunta.objects.filter(evaluacion=obj.evaluacion, pregunta__escenario=obj.escenario).count()
        return f"{count} preguntas"
    preguntas_respondidas.short_description = "Preguntas"


@admin.register(ResultadoPregunta)
class ResultadoPreguntaAdmin(BaseModelAdmin):
    list_display = ('respuesta_corta', 'estado_badge', 'nivel_riesgo_display', 'requiere_atencion_display', 'fecha_calculo')
    list_filter = ('estado', 'fecha_calculo')
    search_fields = ('respuesta__pregunta__texto_pregunta', 'notas_evaluador')
    readonly_fields = (
        'id', 'fecha_calculo', 'fecha_actualizacion'
    )
    
    fieldsets = (
        ('📝 Información de la Respuesta', {
            'fields': ('respuesta',),
            'classes': ('wide',)
        }),
        ('🔬 Análisis Especializado', {
            'fields': ('analisis_riesgo', 'ponderacion', 'metrica_calidad', 'recomendacion'),
            'classes': ('collapse',)
        }),
        ('📊 Estado y Notas', {
            'fields': ('estado', 'notas_evaluador'),
            'classes': ('wide',)
        }),
        ('ℹ️ Metadata', {
            'fields': ('id', 'fecha_calculo', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def respuesta_corta(self, obj):
        return f'{obj.respuesta.pregunta.texto_pregunta[:40]}...'
    respuesta_corta.short_description = "Pregunta"
    
    def estado_badge(self, obj):
        colors = {'pendiente': 'warning', 'procesado': 'success', 'error': 'danger'}
        color = colors.get(obj.estado, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    
    def nivel_riesgo_display(self, obj):
        if obj.analisis_riesgo:
            color_map = {
                'muy_bajo': 'success',
                'bajo': 'info', 
                'medio': 'warning',
                'alto': 'danger',
                'critico': 'dark'
            }
            color = color_map.get(obj.analisis_riesgo.nivel_riesgo, 'secondary')
            return format_html(
                '<span class="badge badge-{}">{}</span>',
                color, obj.analisis_riesgo.get_nivel_riesgo_display()
            )
        return 'Sin análisis'
    nivel_riesgo_display.short_description = "Nivel de Riesgo"
    
    def requiere_atencion_display(self, obj):
        if obj.metrica_calidad:
            return "⚠️ Sí" if obj.metrica_calidad.requiere_atencion else "✅ No"
        return "❓ N/D"
    requiere_atencion_display.short_description = "Requiere Atención"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'respuesta__pregunta', 'respuesta__evaluacion__conjunto',
            'analisis_riesgo', 'metrica_calidad'
        )


# ============================================================================
# CONFIGURACIÓN ADICIONAL DEL ADMIN
# ============================================================================

# Personalizar el admin site
admin.site.site_header = "Risk Conjuntos - Administración"
admin.site.site_title = "Risk Conjuntos Admin"
admin.site.index_title = "Panel de Administración - Risk Conjuntos"
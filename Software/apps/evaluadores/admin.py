"""
Configuración del admin para el módulo de evaluadores
"""
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from .models import Evaluador


@admin.register(Evaluador)
class EvaluadorAdmin(admin.ModelAdmin):
    """Configuración del admin para Evaluador"""
    
    list_display = [
        'usuario_evaluador_info',
        'usuario_principal_info', 
        'tipo_evaluador',
        'estado_badge',
        'modulos_display',
        'fecha_activacion',
        'ultimo_acceso_display',
        'acciones_admin'
    ]
    
    list_filter = [
        'tipo_evaluador',
        'estado',
        'is_active',
        'puede_crear_reportes',
        'puede_editar_evaluaciones',
        'acceso_completo_dashboard',
        'fecha_activacion',
        'created_at'
    ]
    
    search_fields = [
        'usuario_evaluador__email',
        'usuario_evaluador__first_name',
        'usuario_evaluador__last_name',
        'usuario_principal__email',
        'usuario_principal__first_name',
        'usuario_principal__last_name',
        'notas'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'fecha_invitacion',
        'suscripciones_heredadas_display',
        'estadisticas_uso_display'
    ]
    
    fieldsets = [
        ('Información Principal', {
            'fields': [
                'usuario_principal',
                'usuario_evaluador',
                'tipo_evaluador',
                'estado'
            ]
        }),
        ('Limitaciones', {
            'fields': [
                'max_evaluaciones_mes',
                'fecha_expiracion'
            ]
        }),
        ('Fechas de Control', {
            'fields': [
                'fecha_invitacion',
                'fecha_activacion', 
                'fecha_ultimo_acceso',
                'created_at',
                'updated_at'
            ]
        }),
        ('Información Adicional', {
            'fields': [
                'notas',
                'is_active'
            ]
        }),
        ('Datos Heredados', {
            'fields': [
                'suscripciones_heredadas_display',
                'estadisticas_uso_display'
            ]
        })
    ]
    
    raw_id_fields = ['usuario_principal', 'usuario_evaluador']
    
    ordering = ['-created_at']
    
    actions = [
        'activar_evaluadores',
        'suspender_evaluadores',
        'desactivar_evaluadores'
    ]
    
    def usuario_evaluador_info(self, obj):
        """Información del usuario evaluador"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.usuario_evaluador.get_full_name(),
            obj.usuario_evaluador.email
        )
    usuario_evaluador_info.short_description = 'Evaluador'
    
    def usuario_principal_info(self, obj):
        """Información del usuario principal"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.usuario_principal.get_full_name(),
            obj.usuario_principal.email
        )
    usuario_principal_info.short_description = 'Usuario Principal'
    
    def estado_badge(self, obj):
        """Badge del estado"""
        colors = {
            'pending': '#ffc107',    # amarillo
            'active': '#28a745',     # verde
            'suspended': '#dc3545',  # rojo
            'inactive': '#6c757d'    # gris
        }
        
        color = colors.get(obj.estado, '#6c757d')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def modulos_display(self, obj):
        """Muestra los módulos permitidos"""
        if not obj.modulos_permitidos:
            return mark_safe('<em>Ninguno</em>')
        
        modulos = obj.modulos_permitidos[:3]  # Mostrar solo los primeros 3
        
        display = ', '.join(modulos)
        if len(obj.modulos_permitidos) > 3:
            display += f' (+{len(obj.modulos_permitidos) - 3} más)'
            
        return display
    modulos_display.short_description = 'Módulos'
    
    def ultimo_acceso_display(self, obj):
        """Muestra el último acceso"""
        if not obj.fecha_ultimo_acceso:
            return mark_safe('<em>Nunca</em>')
        
        now = timezone.now()
        delta = now - obj.fecha_ultimo_acceso
        
        if delta.days == 0:
            return mark_safe('<span style="color: #28a745;">Hoy</span>')
        elif delta.days == 1:
            return mark_safe('<span style="color: #ffc107;">Ayer</span>')
        elif delta.days <= 7:
            return format_html(
                '<span style="color: #fd7e14;">{} días</span>',
                delta.days
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">{} días</span>',
                delta.days
            )
    ultimo_acceso_display.short_description = 'Último Acceso'
    
    def acciones_admin(self, obj):
        """Acciones rápidas"""
        acciones = []
        
        if obj.estado == 'pending':
            acciones.append(
                mark_safe(
                    '<a href="#" onclick="django.jQuery(\'#id_estado\').val(\'active\'); return false;" style="color: #28a745;">✓ Activar</a>'
                )
            )
        elif obj.estado == 'active':
            acciones.append(
                mark_safe(
                    '<a href="#" onclick="django.jQuery(\'#id_estado\').val(\'suspended\'); return false;" style="color: #dc3545;">⏸ Suspender</a>'
                )
            )
        
        return mark_safe(' | '.join(acciones))
    acciones_admin.short_description = 'Acciones'
    
    def suscripciones_heredadas_display(self, obj):
        """Muestra las suscripciones heredadas"""
        suscripciones = obj.obtener_suscripciones_heredadas()
        
        if not suscripciones:
            return mark_safe('<em>No hay suscripciones activas</em>')
        
        html = '<ul>'
        for sub in suscripciones:
            html += f'<li><strong>{sub.plan.module.display_name}</strong> - {sub.plan.name}</li>'
        html += '</ul>'
        
        return mark_safe(html)
    suscripciones_heredadas_display.short_description = 'Suscripciones Heredadas'
    
    def estadisticas_uso_display(self, obj):
        """Muestra estadísticas de uso"""
        stats = obj.obtener_estadisticas_uso()
        
        html = f'''
        <div>
            <p><strong>Evaluaciones:</strong> {stats.get('evaluaciones_realizadas', 0)}</p>
            <p><strong>Reportes:</strong> {stats.get('reportes_generados', 0)}</p>
            <p><strong>Días desde último acceso:</strong> {stats.get('dias_desde_ultimo_acceso', 'N/A')}</p>
        </div>
        '''
        
        return mark_safe(html)
    estadisticas_uso_display.short_description = 'Estadísticas'
    
    # Acciones personalizadas
    def activar_evaluadores(self, request, queryset):
        """Activar evaluadores seleccionados"""
        updated = 0
        for evaluador in queryset:
            if evaluador.estado != 'active':
                evaluador.activar()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} evaluadores han sido activados.'
        )
    activar_evaluadores.short_description = "Activar evaluadores seleccionados"
    
    def suspender_evaluadores(self, request, queryset):
        """Suspender evaluadores seleccionados"""
        updated = queryset.update(estado='suspended')
        self.message_user(
            request,
            f'{updated} evaluadores han sido suspendidos.'
        )
    suspender_evaluadores.short_description = "Suspender evaluadores seleccionados"
    
    def desactivar_evaluadores(self, request, queryset):
        """Desactivar evaluadores seleccionados"""
        updated = 0
        for evaluador in queryset:
            evaluador.desactivar()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} evaluadores han sido desactivados.'
        )
    desactivar_evaluadores.short_description = "Desactivar evaluadores seleccionados"
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related(
            'usuario_principal',
            'usuario_evaluador'
        ).prefetch_related(
            'usuario_principal__subscriptions',
            'usuario_principal__subscriptions__plan',
            'usuario_principal__subscriptions__plan__module'
        )


# Configuración adicional para el admin
admin.site.site_header = "Administración de Evaluadores"
admin.site.site_title = "Evaluadores Admin"
admin.site.index_title = "Panel de Control - Evaluadores"
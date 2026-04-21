"""
Configuración del admin para el sistema de suscripciones
"""
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Sum
from .models import (
    Module, PlanType, Plan, Cart, CartItem, Order, OrderItem,
    WompiTransaction, Subscription, WebhookEvent
)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'is_active', 'order', 'plans_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'display_name', 'description')
    prepopulated_fields = {'name': ('display_name',)}
    ordering = ('order', 'display_name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Configuración', {
            'fields': ('icon', 'color', 'is_active', 'order')
        }),
    )
    
    def plans_count(self, obj):
        return obj.plans.count()
    plans_count.short_description = 'Planes'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('plans')


@admin.register(PlanType)
class PlanTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active', 'plans_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    
    def plans_count(self, obj):
        return obj.plans.count()
    plans_count.short_description = 'Planes'


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'module', 'plan_type', 'monthly_price', 'yearly_price', 
        'is_active', 'is_featured', 'subscriptions_count'
    )
    list_filter = ('module', 'plan_type', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'module__display_name')
    ordering = ('module', 'order', 'monthly_price')
    
    fieldsets = (
        (None, {
            'fields': ('module', 'plan_type', 'name', 'description')
        }),
        ('Precios', {
            'fields': ('monthly_price', 'quarterly_price', 'yearly_price')
        }),
        ('Límites', {
            'fields': ('trial_days', 'max_users', 'max_reports', 'max_storage_gb')
        }),
        ('Configuración Avanzada', {
            'fields': ('features', 'limits'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
    )
    
    def subscriptions_count(self, obj):
        return obj.subscriptions.filter(status='active').count()
    subscriptions_count.short_description = 'Suscripciones Activas'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('module', 'plan_type')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_info', 'total_items', 'total_amount', 'created_at', 'is_expired_status')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('user__email', 'session_key')
    readonly_fields = ('id', 'total_amount', 'total_items', 'created_at', 'updated_at')
    inlines = [CartItemInline]
    
    def user_info(self, obj):
        if obj.user:
            return obj.user.email
        return f"Sesión: {obj.session_key[:10]}..."
    user_info.short_description = 'Usuario/Sesión'
    
    def is_expired_status(self, obj):
        if obj.is_expired():
            return mark_safe('<span style="color: red;">Expirado</span>')
        return mark_safe('<span style="color: green;">Activo</span>')
    is_expired_status.short_description = 'Estado'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user', 'status', 'total_amount', 'currency', 
        'created_at', 'completed_at'
    )
    list_filter = ('status', 'currency', 'created_at', 'completed_at')
    search_fields = ('order_number', 'user__email', 'billing_email')
    readonly_fields = ('id', 'order_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        (None, {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Información de Facturación', {
            'fields': ('billing_name', 'billing_email', 'billing_phone', 'billing_address', 'billing_city', 'billing_country')
        }),
        ('Totales', {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'currency')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
        ('Información Adicional', {
            'fields': ('notes', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_cancelled']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid', completed_at=timezone.now())
        self.message_user(request, f'{updated} órdenes marcadas como pagadas.')
    mark_as_paid.short_description = 'Marcar como pagado'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} órdenes canceladas.')
    mark_as_cancelled.short_description = 'Cancelar órdenes'


@admin.register(WompiTransaction)
class WompiTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'wompi_transaction_id', 'order', 'wompi_status', 'amount', 
        'currency', 'payment_method', 'created_at'
    )
    list_filter = ('wompi_status', 'currency', 'payment_method', 'created_at')
    search_fields = ('wompi_transaction_id', 'wompi_reference', 'order__order_number')
    readonly_fields = ('id', 'amount', 'created_at', 'updated_at', 'processed_at')
    
    fieldsets = (
        (None, {
            'fields': ('order', 'wompi_transaction_id', 'wompi_reference', 'wompi_status')
        }),
        ('Detalles del Pago', {
            'fields': ('amount_in_cents', 'currency', 'payment_method', 'payment_source_id')
        }),
        ('URLs', {
            'fields': ('redirect_url',)
        }),
        ('Respuesta de Wompi', {
            'fields': ('wompi_response',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'processed_at')
        }),
    )
    
    def order_link(self, obj):
        url = reverse('admin:subscriptions_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Orden'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'plan', 'status', 'billing_cycle', 'start_date', 
        'end_date', 'days_remaining_display', 'is_trial'
    )
    list_filter = ('status', 'billing_cycle', 'is_trial', 'plan__module', 'start_date')
    search_fields = ('user__email', 'plan__name', 'plan__module__display_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'plan', 'order', 'status')
        }),
        ('Configuración', {
            'fields': ('billing_cycle', 'start_date', 'end_date', 'next_billing_date')
        }),
        ('Período de Prueba', {
            'fields': ('is_trial', 'trial_end_date')
        }),
        ('Uso Actual', {
            'fields': ('current_users', 'current_reports', 'current_storage_gb')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def days_remaining_display(self, obj):
        days = obj.days_remaining()
        if days <= 0:
            return mark_safe('<span style="color: red;">Expirado</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} días</span>', days)
        else:
            return format_html('<span style="color: green;">{} días</span>', days)
    days_remaining_display.short_description = 'Días Restantes'
    
    actions = ['renew_subscription', 'cancel_subscription']
    
    def renew_subscription(self, request, queryset):
        # Lógica para renovar suscripciones
        count = 0
        for subscription in queryset:
            if subscription.status == 'expired':
                subscription.status = 'active'
                subscription.save()
                count += 1
        self.message_user(request, f'{count} suscripciones renovadas.')
    renew_subscription.short_description = 'Renovar suscripciones'
    
    def cancel_subscription(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} suscripciones canceladas.')
    cancel_subscription.short_description = 'Cancelar suscripciones'


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('wompi_event_id', 'event_type', 'processed', 'created_at', 'processed_at')
    list_filter = ('event_type', 'processed', 'created_at')
    search_fields = ('wompi_event_id', 'event_type')
    readonly_fields = ('id', 'created_at', 'processed_at')
    
    fieldsets = (
        (None, {
            'fields': ('wompi_event_id', 'event_type', 'transaction')
        }),
        ('Estado', {
            'fields': ('processed', 'processing_error')
        }),
        ('Datos', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'processed_at')
        }),
    )
    
    actions = ['reprocess_events']
    
    def reprocess_events(self, request, queryset):
        # Lógica para reprocesar eventos
        from .services import WompiService
        wompi_service = WompiService()
        
        count = 0
        for event in queryset.filter(processed=False):
            if wompi_service.process_webhook_event(event.payload):
                event.processed = True
                event.processing_error = ''
                event.processed_at = timezone.now()
                event.save()
                count += 1
        
        self.message_user(request, f'{count} eventos reprocesados exitosamente.')
    reprocess_events.short_description = 'Reprocesar eventos'


# Configuración del admin site
admin.site.site_header = 'Administración de Suscripciones'
admin.site.site_title = 'Suscripciones Admin'
admin.site.index_title = 'Panel de Administración'
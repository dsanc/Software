"""
Modelos para sistema de suscripciones, carrito de compras y pagos con Wompi
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
import json

User = get_user_model()


class Module(models.Model):
    """Módulos disponibles del sistema"""
    
    name = models.CharField('Nombre interno', max_length=100, unique=True)
    display_name = models.CharField('Nombre a mostrar', max_length=200)
    description = models.TextField('Descripción')
    icon = models.CharField('Icono', max_length=50, blank=True, help_text='Clase CSS del icono')
    color = models.CharField('Color', max_length=7, default='#007bff', help_text='Color hexadecimal')
    is_active = models.BooleanField('Activo', default=True)
    order = models.PositiveIntegerField('Orden', default=0)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'
        ordering = ['order', 'display_name']
    
    def __str__(self):
        return self.display_name


class PlanType(models.Model):
    """Tipos de planes (Básico, Pro, Enterprise, etc.)"""
    
    name = models.CharField('Nombre', max_length=100)
    description = models.TextField('Descripción', blank=True)
    order = models.PositiveIntegerField('Orden', default=0)
    is_active = models.BooleanField('Activo', default=True)
    
    class Meta:
        verbose_name = 'Tipo de Plan'
        verbose_name_plural = 'Tipos de Planes'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Plan(models.Model):
    """Planes de suscripción por módulo"""
    
    BILLING_CYCLES = [
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='plans')
    plan_type = models.ForeignKey(PlanType, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField('Nombre', max_length=200)
    description = models.TextField('Descripción')
    
    # Precios
    monthly_price = models.DecimalField('Precio mensual', max_digits=10, decimal_places=2, default=0)
    quarterly_price = models.DecimalField('Precio trimestral', max_digits=10, decimal_places=2, default=0)
    yearly_price = models.DecimalField('Precio anual', max_digits=10, decimal_places=2, default=0)
    
    # Configuración
    trial_days = models.PositiveIntegerField('Días de prueba', default=14)
    max_users = models.IntegerField('Máximo usuarios', default=1, validators=[MinValueValidator(1)])
    max_reports = models.IntegerField('Máximo reportes/mes', default=10, help_text='-1 para ilimitado')
    max_storage_gb = models.IntegerField('Almacenamiento GB', default=1)
    
    # Características incluidas (JSON)
    features = models.JSONField('Características', default=dict, blank=True)
    limits = models.JSONField('Límites específicos', default=dict, blank=True)
    
    # Estado
    is_active = models.BooleanField('Activo', default=True)
    is_featured = models.BooleanField('Destacado', default=False)
    order = models.PositiveIntegerField('Orden', default=0)
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'
        ordering = ['module', 'order', 'monthly_price']
        unique_together = ['module', 'plan_type']
    
    def __str__(self):
        return f"{self.module.display_name} - {self.plan_type.name}"
    
    def get_price(self, billing_cycle='monthly'):
        """Obtiene el precio según el ciclo de facturación"""
        prices = {
            'monthly': self.monthly_price,
            'quarterly': self.quarterly_price,
            'yearly': self.yearly_price,
        }
        return prices.get(billing_cycle, self.monthly_price)
    
    def get_discount_percentage(self, billing_cycle='yearly'):
        """Calcula el descuento respecto al precio mensual"""
        if billing_cycle == 'monthly':
            return 0
        
        monthly_total = self.monthly_price * (12 if billing_cycle == 'yearly' else 3)
        cycle_price = self.get_price(billing_cycle)
        
        if monthly_total > 0 and cycle_price < monthly_total:
            return round(((monthly_total - cycle_price) / monthly_total) * 100, 1)
        return 0
    
    @property
    def quarterly_discount_percentage(self):
        """Descuento del plan trimestral"""
        return self.get_discount_percentage('quarterly')
    
    @property
    def yearly_discount_percentage(self):
        """Descuento del plan anual"""
        return self.get_discount_percentage('yearly')
    
    @property
    def features_list(self):
        """Devuelve las características como lista"""
        if isinstance(self.features, list):
            return self.features
        elif isinstance(self.features, dict):
            return list(self.features.values())
        return []
    
    @property
    def limits_dict(self):
        """Devuelve los límites como diccionario"""
        if isinstance(self.limits, dict):
            return self.limits
        return {}


class Cart(models.Model):
    """Carrito de compras"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_key = models.CharField('Clave de sesión', max_length=40, blank=True)
    
    # Estado del carrito
    is_active = models.BooleanField('Activo', default=True, help_text='Si el carrito está activo para modificaciones')
    is_completed = models.BooleanField('Completado', default=False, help_text='Si la compra fue completada')
    
    # Fechas
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    expires_at = models.DateTimeField('Expira', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'
        ordering = ['-updated_at']
    
    def __str__(self):
        user_info = self.user.email if self.user else f"Sesión: {self.session_key[:10]}..."
        return f"Carrito - {user_info}"
    
    @property
    def total_amount(self):
        """Calcula el total del carrito"""
        return sum(item.subtotal for item in self.items.all())
    
    @property 
    def subtotal_amount(self):
        """Calcula el subtotal del carrito (sin descuentos ni impuestos)"""
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def discount_amount(self):
        """Descuentos aplicados (por ahora siempre 0)"""
        return 0
    
    @property
    def tax_amount(self):
        """Impuestos aplicados (por ahora siempre 0)"""
        return 0
    
    @property
    def tax_rate(self):
        """Tasa de impuesto aplicada (por ahora siempre 0)"""
        return 0
    
    @property
    def total_items(self):
        """Cuenta el total de items en el carrito"""
        return self.items.count()
    
    def is_expired(self):
        """Verifica si el carrito ha expirado"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def clear(self):
        """Vacía el carrito"""
        self.items.all().delete()


class CartItem(models.Model):
    """Items del carrito de compras"""
    
    BILLING_CYCLES = Plan.BILLING_CYCLES
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    billing_cycle = models.CharField('Ciclo de facturación', max_length=20, choices=BILLING_CYCLES, default='monthly')
    quantity = models.PositiveIntegerField('Cantidad', default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Item del Carrito'
        verbose_name_plural = 'Items del Carrito'
        unique_together = ['cart', 'plan', 'billing_cycle']
    
    def __str__(self):
        return f"{self.plan} x{self.quantity} ({self.billing_cycle})"
    
    @property
    def subtotal(self):
        """Calcula el subtotal del item"""
        return self.unit_price * self.quantity
    
    def save(self, *args, **kwargs):
        # Actualizar precio al guardar
        if not self.unit_price:
            self.unit_price = self.plan.get_price(self.billing_cycle)
        super().save(*args, **kwargs)


class Order(models.Model):
    """Órdenes de compra"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('paid', 'Pagado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField('Número de orden', max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Información de facturación
    billing_name = models.CharField('Nombre facturación', max_length=200)
    billing_email = models.EmailField('Email facturación')
    billing_phone = models.CharField('Teléfono', max_length=20, blank=True)
    billing_address = models.TextField('Dirección', blank=True)
    billing_city = models.CharField('Ciudad', max_length=100, blank=True)
    billing_country = models.CharField('País', max_length=100, default='Colombia')
    
    # Totales
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField('Impuestos', max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)
    currency = models.CharField('Moneda', max_length=3, default='COP')
    
    # Estado y fechas
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    completed_at = models.DateTimeField('Completado', null=True, blank=True)
    
    # Información adicional
    notes = models.TextField('Notas', blank=True)
    metadata = models.JSONField('Metadatos', default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Orden {self.order_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generar número de orden único
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.order_number = f"ORD-{timestamp}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calcula los totales de la orden"""
        items_total = sum(item.subtotal for item in self.items.all())
        self.subtotal = items_total
        self.tax_amount = items_total * Decimal('0.19')  # IVA Colombia 19%
        self.total_amount = self.subtotal + self.tax_amount
        self.save()


class OrderItem(models.Model):
    """Items de la orden"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    plan_name = models.CharField('Nombre del plan', max_length=200)  # Snapshot
    billing_cycle = models.CharField('Ciclo facturación', max_length=20)
    quantity = models.PositiveIntegerField('Cantidad', default=1)
    unit_price = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2)
    
    # Snapshot de características al momento de la compra
    features_snapshot = models.JSONField('Características', default=dict, blank=True)
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Item de Orden'
        verbose_name_plural = 'Items de Orden'
    
    def __str__(self):
        return f"{self.plan_name} x{self.quantity}"
    
    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class WompiTransaction(models.Model):
    """Transacciones de Wompi"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('APPROVED', 'Aprobado'),
        ('DECLINED', 'Rechazado'),
        ('VOIDED', 'Anulado'),
        ('ERROR', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='wompi_transactions')
    
    # Datos de Wompi
    wompi_transaction_id = models.CharField('ID Transacción Wompi', max_length=100, unique=True, null=True, blank=True)
    wompi_reference = models.CharField('Referencia Wompi', max_length=100, blank=True)
    wompi_status = models.CharField('Estado Wompi', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Información de pago
    amount_in_cents = models.PositiveIntegerField('Monto en centavos')
    currency = models.CharField('Moneda', max_length=3, default='COP')
    payment_method = models.CharField('Método de pago', max_length=50, blank=True)
    payment_source_id = models.CharField('ID Fuente de pago', max_length=100, blank=True)
    
    # URLs de callback
    redirect_url = models.URLField('URL redirección', blank=True)
    
    # Respuesta completa de Wompi
    wompi_response = models.JSONField('Respuesta Wompi', default=dict, blank=True)
    
    # Fechas
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    processed_at = models.DateTimeField('Procesado', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Transacción Wompi'
        verbose_name_plural = 'Transacciones Wompi'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Wompi {self.wompi_transaction_id or self.id} - {self.wompi_status}"
    
    @property
    def amount(self):
        """Convierte centavos a pesos"""
        return self.amount_in_cents / 100
    
    def is_approved(self):
        return self.wompi_status == 'APPROVED'
    
    def is_pending(self):
        return self.wompi_status == 'PENDING'


class Subscription(models.Model):
    """Suscripciones activas generadas desde órdenes pagadas"""
    
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
        ('suspended', 'Suspendida'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='subscriptions')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='subscriptions', null=True, blank=True)
    
    # Configuración de la suscripción
    billing_cycle = models.CharField('Ciclo facturación', max_length=20, choices=Plan.BILLING_CYCLES)
    
    # Fechas
    start_date = models.DateTimeField('Fecha inicio')
    end_date = models.DateTimeField('Fecha fin')
    next_billing_date = models.DateTimeField('Próxima facturación', null=True, blank=True)
    
    # Estado
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='active')
    is_trial = models.BooleanField('Es período de prueba', default=False)
    trial_end_date = models.DateTimeField('Fin período prueba', null=True, blank=True)
    
    # Control de uso
    current_users = models.PositiveIntegerField('Usuarios actuales', default=0)
    current_reports = models.PositiveIntegerField('Reportes este período', default=0)
    current_storage_gb = models.FloatField('Almacenamiento usado GB', default=0.0)
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-created_at']
        unique_together = ['user', 'plan']  # Un usuario no puede tener múltiples suscripciones al mismo plan
    
    def __str__(self):
        return f"{self.user.email} - {self.plan}"
    
    def is_active(self):
        """Verifica si la suscripción está activa"""
        now = timezone.now()
        return (
            self.status == 'active' and 
            self.start_date <= now <= self.end_date
        )
    
    def is_expired(self):
        """Verifica si la suscripción ha expirado"""
        return timezone.now() > self.end_date
    
    def days_remaining(self):
        """Días restantes de la suscripción"""
        if self.is_expired():
            return 0
        delta = self.end_date - timezone.now()
        return delta.days
    
    def usage_percentage(self, resource='reports'):
        """Porcentaje de uso de un recurso"""
        limits = {
            'reports': self.plan.max_reports,
            'users': self.plan.max_users,
            'storage': self.plan.max_storage_gb,
        }
        
        current_usage = {
            'reports': self.current_reports,
            'users': self.current_users,
            'storage': self.current_storage_gb,
        }
        
        limit = limits.get(resource, 0)
        usage = current_usage.get(resource, 0)
        
        if limit <= 0:  # Ilimitado
            return 0
        
        return min(100, (usage / limit) * 100)
    
    def can_use_feature(self, feature_code):
        """Verifica si puede usar una característica específica"""
        if not self.is_active():
            return False
        
        features = self.plan.features or {}
        return features.get(feature_code, False)


class WebhookEvent(models.Model):
    """Log de eventos webhook de Wompi"""
    
    EVENT_TYPES = [
        ('transaction.updated', 'Transacción actualizada'),
        ('transaction.approved', 'Transacción aprobada'),
        ('transaction.declined', 'Transacción rechazada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField('Tipo de evento', max_length=50)
    wompi_event_id = models.CharField('ID Evento Wompi', max_length=100, unique=True)
    
    # Datos del evento
    payload = models.JSONField('Payload completo', default=dict)
    processed = models.BooleanField('Procesado', default=False)
    processing_error = models.TextField('Error procesamiento', blank=True)
    
    # Relaciones
    transaction = models.ForeignKey(WompiTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    processed_at = models.DateTimeField('Procesado', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Evento Webhook'
        verbose_name_plural = 'Eventos Webhook'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.wompi_event_id}"
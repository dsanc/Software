"""
Modelos para gestión de evaluadores
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class EvaluadorManager(models.Manager):
    """Manager personalizado para evaluadores"""
    
    def activos(self):
        """Retorna solo evaluadores activos"""
        return self.filter(is_active=True)
    
    def de_usuario_principal(self, usuario_principal):
        """Retorna evaluadores de un usuario principal específico"""
        return self.filter(usuario_principal=usuario_principal)
    
    def con_acceso_a_modulo(self, modulo_name):
        """Retorna evaluadores con acceso a un módulo específico"""
        return self.filter(
            modulos_permitidos__icontains=modulo_name,
            is_active=True
        )


class Evaluador(models.Model):
    """
    Modelo para gestionar evaluadores bajo un usuario principal suscrito
    """
    
    TIPOS_EVALUADOR = [
        ('evaluator', 'Evaluador'),
        ('reviewer', 'Revisor'),
        ('analyst', 'Analista'),
        ('administrator', 'Administrador'),
    ]
    
    ESTADOS = [
        ('pending', 'Pendiente'),
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('inactive', 'Inactivo'),
    ]
    
    # Relaciones principales
    usuario_principal = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evaluadores_administrados',
        verbose_name='Usuario Principal',
        help_text='Usuario principal que administra este evaluador'
    )
    
    usuario_evaluador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evaluador_profile',
        verbose_name='Usuario Evaluador',
        help_text='Usuario que actuará como evaluador'
    )
    
    # Información del evaluador
    nombres = models.CharField(
        'Nombres',
        max_length=100,
        default='Sin especificar',
        help_text='Nombres del evaluador'
    )
    
    apellidos = models.CharField(
        'Apellidos', 
        max_length=100,
        default='Sin especificar',
        help_text='Apellidos del evaluador'
    )
    
    tipo_evaluador = models.CharField(
        'Tipo de Evaluador',
        max_length=20,
        choices=TIPOS_EVALUADOR,
        default='evaluator'
    )
    
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADOS,
        default='pending'
    )
    
    # Permisos y restricciones
    modulos_permitidos = models.JSONField(
        'Módulos Permitidos',
        default=list,
        blank=True,
        help_text='Lista de módulos a los que tiene acceso este evaluador'
    )
    
    permisos_crud = models.JSONField(
        'Permisos CRUD por Módulo',
        default=dict,
        blank=True,
        help_text='Permisos específicos CRUD para cada módulo. Formato: {"modulo": {"create": bool, "read": bool, "update": bool, "delete": bool, "export": bool, "approve": bool}}'
    )
    
    permisos_especiales = models.JSONField(
        'Permisos Especiales',
        default=dict,
        blank=True,
        help_text='Configuración específica de permisos por módulo (legacy)'
    )
    
    # Limitaciones específicas
    max_evaluaciones_mes = models.PositiveIntegerField(
        'Máximo Evaluaciones por Mes',
        default=10,
        help_text='Número máximo de evaluaciones que puede realizar por mes'
    )
    
    puede_crear_reportes = models.BooleanField(
        'Puede Crear Reportes',
        default=True,
        help_text='Si puede generar reportes de evaluación'
    )
    
    puede_editar_evaluaciones = models.BooleanField(
        'Puede Editar Evaluaciones',
        default=True,
        help_text='Si puede editar evaluaciones existentes'
    )
    
    acceso_completo_dashboard = models.BooleanField(
        'Acceso Completo Dashboard',
        default=False,
        help_text='Si tiene acceso completo al dashboard del usuario principal'
    )
    
    # Información adicional
    notas = models.TextField(
        'Notas',
        blank=True,
        help_text='Notas adicionales sobre este evaluador'
    )
    
    # Fechas de control
    fecha_invitacion = models.DateTimeField(
        'Fecha de Invitación',
        auto_now_add=True
    )
    
    fecha_activacion = models.DateTimeField(
        'Fecha de Activación',
        null=True,
        blank=True
    )
    
    fecha_ultimo_acceso = models.DateTimeField(
        'Último Acceso',
        null=True,
        blank=True
    )
    
    fecha_expiracion = models.DateTimeField(
        'Fecha de Expiración',
        null=True,
        blank=True,
        help_text='Fecha hasta la cual el evaluador tiene acceso'
    )
    
    # Control
    is_active = models.BooleanField(
        'Activo',
        default=True,
        help_text='Si este evaluador está activo en el sistema'
    )
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    objects = EvaluadorManager()
    
    class Meta:
        verbose_name = 'Evaluador'
        verbose_name_plural = 'Evaluadores'
        ordering = ['-created_at']
        unique_together = [
            ('usuario_principal', 'usuario_evaluador'),
        ]
        indexes = [
            models.Index(fields=['usuario_principal', 'estado']),
            models.Index(fields=['usuario_evaluador', 'is_active']),
            models.Index(fields=['estado', 'is_active']),
        ]
    
    def __str__(self):
        try:
            if self.usuario_principal:
                return f"{self.get_full_name()} -> {self.usuario_principal.get_full_name()}"
            else:
                return f"{self.get_full_name()} (Sin usuario principal)"
        except Exception:
            return f"Evaluador #{self.pk if self.pk else 'Nuevo'}"
    
    def get_full_name(self):
        """Retorna el nombre completo del evaluador"""
        if self.nombres and self.apellidos:
            return f"{self.nombres} {self.apellidos}"
        elif self.nombres:
            return self.nombres
        elif self.apellidos:
            return self.apellidos
        else:
            # Fallback al usuario si no hay nombres configurados
            try:
                if hasattr(self, 'usuario_evaluador') and self.usuario_evaluador:
                    return self.usuario_evaluador.get_full_name() or self.usuario_evaluador.username
                else:
                    return "Sin nombre configurado"
            except Exception:
                return "Sin nombre configurado"
    
    def clean(self):
        """Validaciones del modelo"""
        super().clean()
        
        # Solo validar si tanto usuario_principal como usuario_evaluador están asignados
        if hasattr(self, 'usuario_principal') and self.usuario_principal and hasattr(self, 'usuario_evaluador') and self.usuario_evaluador:
            # No puede ser evaluador de sí mismo
            if self.usuario_principal == self.usuario_evaluador:
                raise ValidationError(
                    _('Un usuario no puede ser evaluador de sí mismo.')
                )
            
            # Validar que el usuario principal tenga suscripciones activas
            if not self.usuario_principal.subscriptions.filter(status='active').exists():
                raise ValidationError(
                    _('El usuario principal debe tener al menos una suscripción activa.')
                )
    
    def save(self, *args, **kwargs):
        """Override del save para lógica adicional"""
        # Actualizar fecha de activación si cambia a activo
        if self.estado == 'active' and not self.fecha_activacion:
            self.fecha_activacion = timezone.now()
        
        # Validar antes de guardar
        self.clean()
        
        # Verificar si es un nuevo evaluador
        es_nuevo = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Si es un nuevo evaluador, crear suscripciones heredadas
        if es_nuevo and self.usuario_evaluador and self.usuario_principal:
            self.crear_suscripciones_heredadas()
    
    def activar(self):
        """Activa el evaluador"""
        self.estado = 'active'
        self.is_active = True
        self.fecha_activacion = timezone.now()
        self.save()
    
    def suspender(self):
        """Suspende el evaluador"""
        self.estado = 'suspended'
        self.save()
    
    def desactivar(self):
        """Desactiva el evaluador"""
        self.estado = 'inactive'
        self.is_active = False
        self.save()
    
    def tiene_acceso_a_modulo(self, modulo_name):
        """Verifica si tiene acceso a un módulo específico"""
        return modulo_name in self.modulos_permitidos
    
    def puede_realizar_accion(self, accion):
        """Verifica si puede realizar una acción específica"""
        if not self.is_active or self.estado != 'active':
            return False, "Evaluador no activo"
        
        # Verificar expiración
        if self.fecha_expiracion and timezone.now() > self.fecha_expiracion:
            return False, "Acceso expirado"
        
        # Verificar acciones específicas
        acciones_permisos = {
            'crear_reportes': self.puede_crear_reportes,
            'editar_evaluaciones': self.puede_editar_evaluaciones,
            'acceso_dashboard': self.acceso_completo_dashboard,
        }
        
        if accion in acciones_permisos:
            if not acciones_permisos[accion]:
                return False, f"Sin permisos para {accion}"
        
        return True, "Permitido"
    
    def tiene_permiso_crud(self, modulo_name, accion):
        """
        Verifica si tiene un permiso CRUD específico para un módulo
        
        Args:
            modulo_name (str): Nombre del módulo
            accion (str): Acción CRUD ('create', 'read', 'update', 'delete', 'export', 'approve')
            
        Returns:
            bool: True si tiene el permiso, False en caso contrario
        """
        # Verificar que esté activo y tenga acceso al módulo
        if not self.is_active or self.estado != 'active':
            return False
            
        if not self.tiene_acceso_a_modulo(modulo_name):
            return False
            
        # Si no hay permisos CRUD configurados, dar permisos básicos por defecto
        if not self.permisos_crud:
            return accion in ['create', 'read', 'update']  # Sin delete por defecto
            
        # Verificar permisos específicos del módulo
        permisos_modulo = self.permisos_crud.get(modulo_name, {})
        
        # Si el módulo no tiene permisos específicos, dar permisos básicos
        if not permisos_modulo:
            return accion in ['create', 'read', 'update']
            
        return permisos_modulo.get(accion, False)
    
    def establecer_permiso_crud(self, modulo_name, accion, permitido=True):
        """
        Establece un permiso CRUD específico para un módulo
        
        Args:
            modulo_name (str): Nombre del módulo
            accion (str): Acción CRUD
            permitido (bool): Si se permite o no la acción
        """
        if not self.permisos_crud:
            self.permisos_crud = {}
            
        if modulo_name not in self.permisos_crud:
            self.permisos_crud[modulo_name] = {}
            
        self.permisos_crud[modulo_name][accion] = permitido
    
    def obtener_permisos_modulo(self, modulo_name):
        """
        Obtiene todos los permisos CRUD para un módulo específico
        
        Returns:
            dict: Diccionario con los permisos del módulo
        """
        if not self.permisos_crud:
            return {}
            
        return self.permisos_crud.get(modulo_name, {})
    
    def establecer_permisos_modulo(self, modulo_name, permisos):
        """
        Establece todos los permisos CRUD para un módulo
        
        Args:
            modulo_name (str): Nombre del módulo
            permisos (dict): Diccionario con los permisos {'create': bool, 'read': bool, etc.}
        """
        if not self.permisos_crud:
            self.permisos_crud = {}
            
        self.permisos_crud[modulo_name] = permisos
    
    def obtener_suscripciones_heredadas(self):
        """
        Obtiene las suscripciones del usuario principal que puede usar
        """
        from apps.subscriptions.models import Subscription
        
        suscripciones_principales = Subscription.objects.filter(
            user=self.usuario_principal,
            status='active'
        )
        
        # Filtrar solo las de módulos permitidos si están especificados
        if self.modulos_permitidos:
            suscripciones_principales = suscripciones_principales.filter(
                plan__module__name__in=self.modulos_permitidos
            )
        
        return suscripciones_principales
    
    def crear_suscripciones_heredadas(self):
        """
        Crea suscripciones heredadas del usuario principal para el evaluador
        """
        from apps.subscriptions.models import Subscription
        from datetime import timedelta
        
        # Obtener suscripciones activas del usuario principal
        suscripciones_principales = self.usuario_principal.subscriptions.filter(status='active')
        
        # Filtrar solo las de módulos permitidos
        if self.modulos_permitidos:
            suscripciones_principales = suscripciones_principales.filter(
                plan__module__name__in=self.modulos_permitidos
            )
        
        suscripciones_creadas = []
        
        for suscripcion_principal in suscripciones_principales:
            # Verificar si ya existe una suscripción para este plan
            suscripcion_existente = Subscription.objects.filter(
                user=self.usuario_evaluador,
                plan=suscripcion_principal.plan,
                status='active'
            ).first()
            
            if not suscripcion_existente:
                # Crear nueva suscripción heredada
                suscripcion_heredada = Subscription.objects.create(
                    user=self.usuario_evaluador,
                    plan=suscripcion_principal.plan,
                    billing_cycle=suscripcion_principal.billing_cycle,
                    start_date=timezone.now(),
                    end_date=suscripcion_principal.end_date,  # Misma fecha de fin que el principal
                    status='active'
                )
                suscripciones_creadas.append(suscripcion_heredada)
        
        return suscripciones_creadas
    
    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha del último acceso"""
        self.fecha_ultimo_acceso = timezone.now()
        self.save(update_fields=['fecha_ultimo_acceso'])
    
    def obtener_estadisticas_uso(self):
        """Obtiene estadísticas de uso del evaluador"""
        # TODO: Implementar según los módulos específicos
        return {
            'evaluaciones_realizadas': 0,  # Implementar según módulo
            'reportes_generados': 0,       # Implementar según módulo
            'ultimo_acceso': self.fecha_ultimo_acceso,
            'dias_desde_ultimo_acceso': (
                (timezone.now() - self.fecha_ultimo_acceso).days 
                if self.fecha_ultimo_acceso else None
            ),
        }
    
    def get_initials(self):
        """Retorna las iniciales del evaluador para el avatar"""
        if self.nombres and self.apellidos:
            return f"{self.nombres[0]}{self.apellidos[0]}".upper()
        elif self.usuario_evaluador and self.usuario_evaluador.first_name and self.usuario_evaluador.last_name:
            return f"{self.usuario_evaluador.first_name[0]}{self.usuario_evaluador.last_name[0]}".upper()
        elif self.usuario_evaluador:
            return self.usuario_evaluador.username[:2].upper()
        return "EV"
    
    def get_avatar_color(self):
        """Retorna un color para el avatar basado en el ID"""
        colors = ['primary', 'success', 'info', 'warning', 'secondary']
        return colors[self.pk % len(colors)]
    
    def get_full_name(self):
        """Retorna el nombre completo del evaluador"""
        if self.nombres and self.apellidos:
            return f"{self.nombres} {self.apellidos}"
        elif self.usuario_evaluador:
            return self.usuario_evaluador.get_full_name() or self.usuario_evaluador.username
        return "Evaluador"
    
    def get_tipo_evaluador_display(self):
        """Retorna el display del tipo de evaluador"""
        return dict(self.TIPOS_EVALUADOR).get(self.tipo_evaluador, 'Evaluador')


class EvaluatorActivity(models.Model):
    """
    Modelo para registrar actividades de los evaluadores
    """
    
    ACTION_CHOICES = [
        ('evaluation_started', 'Evaluación Iniciada'),
        ('evaluation_completed', 'Evaluación Completada'),
        ('evaluation_updated', 'Evaluación Actualizada'),
        ('comment_added', 'Comentario Agregado'),
        ('report_generated', 'Reporte Generado'),
        ('login', 'Inicio de Sesión'),
        ('logout', 'Cierre de Sesión'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Completado'),
        ('in_progress', 'En Progreso'),
        ('pending', 'Pendiente'),
        ('cancelled', 'Cancelado'),
        ('error', 'Error'),
    ]
    
    evaluador = models.ForeignKey(
        Evaluador,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    
    action = models.CharField(
        'Acción',
        max_length=50,
        choices=ACTION_CHOICES
    )
    
    description = models.CharField(
        'Descripción',
        max_length=255,
        help_text='Descripción detallada de la actividad'
    )
    
    module = models.CharField(
        'Módulo',
        max_length=50,
        help_text='Módulo donde se realizó la actividad'
    )
    
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed'
    )
    
    created_at = models.DateTimeField(
        'Fecha de Creación',
        auto_now_add=True
    )
    
    metadata = models.JSONField(
        'Metadatos',
        default=dict,
        blank=True,
        help_text='Información adicional sobre la actividad'
    )
    
    class Meta:
        verbose_name = 'Actividad de Evaluador'
        verbose_name_plural = 'Actividades de Evaluadores'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.evaluador.get_full_name()} - {self.get_action_display()}"
    
    def get_icon_class(self):
        """Retorna la clase del ícono basada en la acción"""
        icon_map = {
            'evaluation_started': 'fa-play',
            'evaluation_completed': 'fa-check-circle',
            'evaluation_updated': 'fa-edit',
            'comment_added': 'fa-comment-alt',
            'report_generated': 'fa-file-alt',
            'login': 'fa-sign-in-alt',
            'logout': 'fa-sign-out-alt',
        }
        return icon_map.get(self.action, 'fa-circle')
    
    def get_icon_color(self):
        """Retorna el color del ícono basado en la acción"""
        color_map = {
            'evaluation_started': 'text-warning',
            'evaluation_completed': 'text-success',
            'evaluation_updated': 'text-info',
            'comment_added': 'text-info',
            'report_generated': 'text-primary',
            'login': 'text-success',
            'logout': 'text-secondary',
        }
        return color_map.get(self.action, 'text-muted')
    
    def get_module_color(self):
        """Retorna el color del badge del módulo"""
        module_colors = {
            'risk_hoteles': 'primary',
            'risk_conjuntos': 'success',
            'security_probabilistic': 'danger',
        }
        return module_colors.get(self.module, 'secondary')
    
    def get_module_icon(self):
        """Retorna el ícono del módulo"""
        module_icons = {
            'risk_hoteles': 'fa-hotel',
            'risk_conjuntos': 'fa-building',
            'security_probabilistic': 'fa-shield-alt',
        }
        return module_icons.get(self.module, 'fa-cube')
    
    def get_module_display(self):
        """Retorna el nombre de display del módulo"""
        module_names = {
            'risk_hoteles': 'Risk Hoteles',
            'risk_conjuntos': 'Risk Conjuntos',
            'security_probabilistic': 'Security Probabilistic',
        }
        return module_names.get(self.module, self.module.title())
    
    def get_status_color(self):
        """Retorna el color del badge del estado"""
        status_colors = {
            'completed': 'success',
            'in_progress': 'warning',
            'pending': 'info',
            'cancelled': 'secondary',
            'error': 'danger',
        }
        return status_colors.get(self.status, 'secondary')
    
    def get_status_icon(self):
        """Retorna el ícono del estado"""
        status_icons = {
            'completed': 'fa-check-circle',
            'in_progress': 'fa-clock',
            'pending': 'fa-hourglass-half',
            'cancelled': 'fa-times-circle',
            'error': 'fa-exclamation-circle',
        }
        return status_icons.get(self.status, 'fa-circle')
    
    @property
    def detail_url(self):
        """URL para ver detalles de la actividad"""
        # Implementar según necesidades
        return None
    
    @property
    def download_url(self):
        """URL para descargar contenido relacionado"""
        # Implementar según necesidades
        return None
    
    @property
    def action_url(self):
        """URL para realizar acciones adicionales"""
        # Implementar según necesidades
        return None
    
    @property
    def action_title(self):
        """Título para la acción adicional"""
        # Implementar según necesidades
        return "Acción"
    
    @property
    def action_icon(self):
        """Ícono para la acción adicional"""
        # Implementar según necesidades
        return "fa-cog"



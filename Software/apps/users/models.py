from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from PIL import Image
import os
import logging

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser
    """
    # Campos básicos
    email = models.EmailField('Correo electrónico', unique=True)
    first_name = models.CharField('Nombre', max_length=30)
    last_name = models.CharField('Apellido', max_length=30)
    
    # Avatar y personalización
    avatar = models.ImageField(
        'Avatar', 
        upload_to='avatars/%Y/%m/', 
        blank=True, 
        null=True,
        help_text='Sube una imagen de perfil. Se redimensionará automáticamente.'
    )
    
    # Información de contacto
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="El número de teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos permitidos."
    )
    phone = models.CharField(
        'Teléfono',
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text='Formato: +52123456789'
    )
    
    # Información profesional
    job_title = models.CharField('Cargo/Puesto', max_length=100, blank=True)
    company = models.CharField('Empresa', max_length=100, blank=True)
    department = models.CharField('Departamento', max_length=100, blank=True)
    
    # Información de ubicación
    country = models.CharField('País', max_length=50, blank=True)
    city = models.CharField('Ciudad', max_length=50, blank=True)
    
    # Configuración de notificaciones
    email_notifications = models.BooleanField(
        'Notificaciones por email',
        default=True,
        help_text='Recibir notificaciones importantes por correo electrónico'
    )
    sms_notifications = models.BooleanField(
        'Notificaciones por SMS',
        default=False,
        help_text='Recibir notificaciones por mensaje de texto'
    )
    
    # Campos de control
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    is_active = models.BooleanField('Activo', default=True)
    
    # Campos adicionales de seguridad
    email_verified = models.BooleanField('Email verificado', default=False)
    phone_verified = models.BooleanField('Teléfono verificado', default=False)
    two_factor_enabled = models.BooleanField('2FA habilitado', default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retorna el nombre corto del usuario"""
        return self.first_name
    
    def get_avatar_url(self):
        """Retorna la URL del avatar o una imagen por defecto"""
        try:
            if self.avatar and hasattr(self.avatar, 'url'):
                # Verificar que el archivo existe
                from django.core.files.storage import default_storage
                if default_storage.exists(self.avatar.name):
                    return self.avatar.url
        except Exception as e:
            logger.warning(f"Error accediendo al avatar del usuario {self.id}: {e}")
        
        # Retornar imagen por defecto
        return '/static/images/default-avatar.svg'
    
    def get_initials(self):
        """Retorna las iniciales del usuario"""
        initials = ""
        if self.first_name:
            initials += self.first_name[0].upper()
        if self.last_name:
            initials += self.last_name[0].upper()
        return initials or self.username[0].upper()
    
    def save(self, *args, **kwargs):
        """Override save para procesar imagen de avatar"""
        super().save(*args, **kwargs)
        
        # Procesar avatar si existe
        if self.avatar:
            self._resize_avatar()
    
    def _resize_avatar(self):
        """Redimensiona el avatar a un tamaño apropiado"""
        try:
            img = Image.open(self.avatar.path)
            
            # Redimensionar a 300x300 máximo manteniendo aspect ratio
            max_size = (300, 300)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convertir a RGB si es necesario (para JPEG)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Guardar imagen optimizada
            img.save(self.avatar.path, 'JPEG', quality=85, optimize=True)
            
        except Exception as e:
            # Log error but don't fail the save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error redimensionando avatar para usuario {self.id}: {e}")
    
    def delete_avatar(self):
        """Elimina el archivo de avatar del sistema de archivos"""
        if self.avatar:
            try:
                if os.path.isfile(self.avatar.path):
                    os.remove(self.avatar.path)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error eliminando avatar para usuario {self.id}: {e}")
            finally:
                self.avatar = None
                self.save()
    
    @property
    def profile_completion(self):
        """Calcula el porcentaje de completitud del perfil"""
        fields_to_check = [
            'first_name', 'last_name', 'email', 'phone',
            'avatar', 'job_title', 'company', 'city', 'country'
        ]
        
        completed_fields = 0
        total_fields = len(fields_to_check)
        
        for field in fields_to_check:
            value = getattr(self, field, None)
            if value:
                if hasattr(value, 'name'):  # Para archivos
                    if value.name:
                        completed_fields += 1
                else:
                    completed_fields += 1
        
        return int((completed_fields / total_fields) * 100)


class LoginAttempt(models.Model):
    """
    Modelo para rastrear intentos de login (exitosos y fallidos)
    """
    username = models.CharField('Username/Email', max_length=254)
    ip_address = models.GenericIPAddressField('Dirección IP')
    user_agent = models.TextField('User Agent', blank=True)
    success = models.BooleanField('Exitoso', default=False)
    failure_reason = models.CharField('Razón del fallo', max_length=200, blank=True)
    timestamp = models.DateTimeField('Fecha y hora', auto_now_add=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='login_attempts'
    )
    
    class Meta:
        verbose_name = 'Intento de Login'
        verbose_name_plural = 'Intentos de Login'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]
    
    def __str__(self):
        status = "Exitoso" if self.success else "Fallido"
        return f"{self.username} - {status} - {self.timestamp}"


class AccountLockout(models.Model):
    """
    Modelo para gestionar bloqueos de cuenta por intentos fallidos
    """
    LOCKOUT_REASONS = [
        ('failed_attempts', 'Intentos fallidos consecutivos'),
        ('suspicious_activity', 'Actividad sospechosa'),
        ('admin_manual', 'Bloqueo manual por administrador'),
        ('security_breach', 'Posible violación de seguridad'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='lockouts'
    )
    ip_address = models.GenericIPAddressField('Dirección IP', null=True, blank=True)
    reason = models.CharField(
        'Razón del bloqueo', 
        max_length=50, 
        choices=LOCKOUT_REASONS,
        default='failed_attempts'
    )
    locked_at = models.DateTimeField('Bloqueado en', auto_now_add=True)
    unlock_at = models.DateTimeField('Desbloquear en')
    unlocked_at = models.DateTimeField('Desbloqueado en', null=True, blank=True)
    is_active = models.BooleanField('Activo', default=True)
    failed_attempts_count = models.PositiveIntegerField('Número de intentos fallidos', default=0)
    unlocked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unlocked_accounts'
    )
    notes = models.TextField('Notas', blank=True)
    
    class Meta:
        verbose_name = 'Bloqueo de Cuenta'
        verbose_name_plural = 'Bloqueos de Cuenta'
        ordering = ['-locked_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['unlock_at', 'is_active']),
            models.Index(fields=['ip_address', 'locked_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_reason_display()} - {self.locked_at}"
    
    @property
    def is_expired(self):
        """Verifica si el bloqueo ha expirado"""
        from django.utils import timezone
        return timezone.now() >= self.unlock_at
    
    @property
    def time_remaining(self):
        """Retorna el tiempo restante para el desbloqueo"""
        from django.utils import timezone
        if self.is_expired:
            return None
        return self.unlock_at - timezone.now()
    
    def unlock(self, unlocked_by=None):
        """Desbloquea la cuenta manualmente"""
        from django.utils import timezone
        self.is_active = False
        self.unlocked_at = timezone.now()
        self.unlocked_by = unlocked_by
        self.save()


class SecurityEvent(models.Model):
    """
    Modelo para registrar eventos de seguridad importantes
    """
    EVENT_TYPES = [
        ('login_success', 'Login exitoso'),
        ('login_failure', 'Login fallido'),
        ('password_change', 'Cambio de contraseña'),
        ('password_reset', 'Reset de contraseña'),
        ('account_lockout', 'Bloqueo de cuenta'),
        ('account_unlock', 'Desbloqueo de cuenta'),
        ('2fa_enabled', '2FA habilitado'),
        ('2fa_disabled', '2FA deshabilitado'),
        ('2fa_backup_used', 'Código de backup 2FA usado'),
        ('suspicious_activity', 'Actividad sospechosa'),
        ('data_export', 'Exportación de datos'),
        ('profile_update', 'Actualización de perfil'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='security_events'
    )
    event_type = models.CharField('Tipo de evento', max_length=50, choices=EVENT_TYPES)
    description = models.TextField('Descripción')
    ip_address = models.GenericIPAddressField('Dirección IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    timestamp = models.DateTimeField('Fecha y hora', auto_now_add=True)
    metadata = models.JSONField('Metadatos adicionales', default=dict, blank=True)
    severity = models.CharField(
        'Severidad',
        max_length=20,
        choices=[
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('critical', 'Crítica'),
        ],
        default='medium'
    )
    
    class Meta:
        verbose_name = 'Evento de Seguridad'
        verbose_name_plural = 'Eventos de Seguridad'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_event_type_display()} - {self.timestamp}"
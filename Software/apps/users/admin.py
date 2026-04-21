from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.utils import timezone
from .models import User, LoginAttempt, AccountLockout, SecurityEvent
from .services import AccountSecurityService


class CustomUserCreationForm(UserCreationForm):
    """Formulario personalizado para crear usuarios"""
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name')


class CustomUserChangeForm(UserChangeForm):
    """Formulario personalizado para editar usuarios"""
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuración del admin para el modelo User personalizado
    """
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff', 'two_factor_status', 'account_status', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'two_factor_enabled', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Información Profesional', {'fields': ('job_title', 'company', 'department', 'city', 'country')}),
        ('Configuración', {'fields': ('email_notifications', 'sms_notifications')}),
        ('Seguridad', {'fields': ('two_factor_enabled', 'email_verified', 'phone_verified')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')
    
    actions = ['unlock_accounts', 'disable_2fa', 'enable_2fa']
    
    def two_factor_status(self, obj):
        """Mostrar estado del 2FA"""
        if obj.two_factor_enabled:
            return mark_safe('<span style="color: green;">✓ Habilitado</span>')
        return mark_safe('<span style="color: orange;">✗ Deshabilitado</span>')
    two_factor_status.short_description = '2FA'
    
    def account_status(self, obj):
        """Mostrar estado de bloqueo de la cuenta"""
        if AccountSecurityService.is_account_locked(obj):
            lockout = AccountSecurityService.get_active_lockout(obj)
            remaining = lockout.time_remaining
            if remaining:
                minutes = int(remaining.total_seconds() // 60)
                return format_html('<span style="color: red;">🔒 Bloqueado ({} min)</span>', minutes)
            return mark_safe('<span style="color: red;">🔒 Bloqueado</span>')
        return mark_safe('<span style="color: green;">🔓 Activo</span>')
    account_status.short_description = 'Estado'
    
    def unlock_accounts(self, request, queryset):
        """Acción para desbloquear cuentas"""
        count = 0
        for user in queryset:
            if AccountSecurityService.is_account_locked(user):
                AccountSecurityService.unlock_account(user, request.user, "Desbloqueado por administrador")
                count += 1
        
        self.message_user(request, f'{count} cuenta(s) desbloqueada(s).')
    unlock_accounts.short_description = "Desbloquear cuentas seleccionadas"
    
    def disable_2fa(self, request, queryset):
        """Acción para deshabilitar 2FA"""
        count = queryset.filter(two_factor_enabled=True).update(two_factor_enabled=False)
        self.message_user(request, f'2FA deshabilitado para {count} usuario(s).')
    disable_2fa.short_description = "Deshabilitar 2FA en usuarios seleccionados"
    
    def enable_2fa(self, request, queryset):
        """Acción para habilitar 2FA"""
        count = queryset.filter(two_factor_enabled=False).update(two_factor_enabled=True)
        self.message_user(request, f'2FA habilitado para {count} usuario(s).')
    enable_2fa.short_description = "Habilitar 2FA en usuarios seleccionados"


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """
    Admin para los intentos de login
    """
    list_display = ('username', 'user', 'ip_address', 'success', 'timestamp', 'failure_reason')
    list_filter = ('success', 'timestamp', 'failure_reason')
    search_fields = ('username', 'ip_address', 'user__email')
    readonly_fields = ('username', 'ip_address', 'user_agent', 'success', 'failure_reason', 'timestamp', 'user')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AccountLockout)
class AccountLockoutAdmin(admin.ModelAdmin):
    """
    Admin para los bloqueos de cuenta
    """
    list_display = ('user', 'reason', 'locked_at', 'unlock_at', 'is_active', 'failed_attempts_count', 'unlocked_by')
    list_filter = ('reason', 'is_active', 'locked_at', 'unlock_at')
    search_fields = ('user__email', 'ip_address', 'notes')
    readonly_fields = ('user', 'ip_address', 'reason', 'locked_at', 'unlock_at', 'failed_attempts_count')
    date_hierarchy = 'locked_at'
    ordering = ('-locked_at',)
    
    fieldsets = (
        ('Información del Bloqueo', {
            'fields': ('user', 'reason', 'ip_address', 'failed_attempts_count')
        }),
        ('Tiempos', {
            'fields': ('locked_at', 'unlock_at', 'unlocked_at')
        }),
        ('Estado', {
            'fields': ('is_active', 'unlocked_by', 'notes')
        }),
    )
    
    actions = ['unlock_selected']
    
    def unlock_selected(self, request, queryset):
        """Acción para desbloquear cuentas"""
        count = 0
        for lockout in queryset.filter(is_active=True):
            lockout.unlock(request.user)
            count += 1
        
        self.message_user(request, f'{count} bloqueo(s) removido(s).')
    unlock_selected.short_description = "Desbloquear cuentas seleccionadas"


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """
    Admin para eventos de seguridad
    """
    list_display = ('user', 'event_type', 'severity', 'ip_address', 'timestamp', 'description_short')
    list_filter = ('event_type', 'severity', 'timestamp')
    search_fields = ('user__email', 'description', 'ip_address')
    readonly_fields = ('user', 'event_type', 'description', 'ip_address', 'user_agent', 'timestamp', 'metadata', 'severity')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Información del Evento', {
            'fields': ('user', 'event_type', 'severity', 'description')
        }),
        ('Contexto Técnico', {
            'fields': ('ip_address', 'user_agent', 'metadata')
        }),
        ('Tiempo', {
            'fields': ('timestamp',)
        }),
    )
    
    def description_short(self, obj):
        """Descripción corta para la lista"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Descripción'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Personalizar el admin site
admin.site.site_header = 'Panel de Administración - Django Modular'
admin.site.site_title = 'Admin Django Modular'
admin.site.index_title = 'Gestión del Sistema'
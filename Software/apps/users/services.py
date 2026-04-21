"""
Servicios para gestión de seguridad de usuarios
"""
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import LoginAttempt, AccountLockout, SecurityEvent
from .security_logging import security_logger

User = get_user_model()


class AccountSecurityService:
    """
    Servicio para gestionar la seguridad de cuentas de usuario
    """
    
    # Configuraciones por defecto
    MAX_LOGIN_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
    LOCKOUT_DURATION_MINUTES = getattr(settings, 'LOCKOUT_DURATION_MINUTES', 30)
    ATTEMPT_WINDOW_MINUTES = getattr(settings, 'ATTEMPT_WINDOW_MINUTES', 15)
    
    @classmethod
    def record_login_attempt(cls, username, ip_address, user_agent='', success=True, 
                           failure_reason='', user=None, request=None):
        """
        Registra un intento de login
        """
        # Crear registro del intento
        attempt = LoginAttempt.objects.create(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
            user=user
        )
        
        # Logging
        if success:
            security_logger.log_login_success(user, request)
            cls._record_security_event(
                user, 'login_success', 
                f'Login exitoso desde {ip_address}', 
                ip_address, user_agent
            )
        else:
            security_logger.log_login_failure(username, request, failure_reason)
            if user:
                cls._record_security_event(
                    user, 'login_failure', 
                    f'Login fallido: {failure_reason}', 
                    ip_address, user_agent
                )
        
        # Si fue fallido, verificar si necesita bloqueo
        if not success and user:
            cls._check_and_apply_lockout(user, ip_address, request)
        
        return attempt
    
    @classmethod
    def _check_and_apply_lockout(cls, user, ip_address, request=None):
        """
        Verifica si el usuario debe ser bloqueado por intentos fallidos
        """
        # Verificar si ya está bloqueado
        if cls.is_account_locked(user):
            return
        
        # Obtener intentos fallidos recientes
        time_window = timezone.now() - timedelta(minutes=cls.ATTEMPT_WINDOW_MINUTES)
        recent_failures = LoginAttempt.objects.filter(
            user=user,
            success=False,
            timestamp__gte=time_window
        ).count()
        
        # Si excede el límite, bloquear cuenta
        if recent_failures >= cls.MAX_LOGIN_ATTEMPTS:
            unlock_time = timezone.now() + timedelta(minutes=cls.LOCKOUT_DURATION_MINUTES)
            
            lockout = AccountLockout.objects.create(
                user=user,
                ip_address=ip_address,
                reason='failed_attempts',
                unlock_at=unlock_time,
                failed_attempts_count=recent_failures
            )
            
            # Logging
            security_logger.log_account_lockout(user.email, request, 
                                              f'{recent_failures} intentos fallidos')
            
            cls._record_security_event(
                user, 'account_lockout',
                f'Cuenta bloqueada por {recent_failures} intentos fallidos',
                ip_address, severity='high'
            )
            
            return lockout
        
        return None
    
    @classmethod
    def is_account_locked(cls, user):
        """
        Verifica si una cuenta está bloqueada
        """
        if not user:
            return False
        
        # Buscar bloqueos activos no expirados
        active_lockouts = AccountLockout.objects.filter(
            user=user,
            is_active=True,
            unlock_at__gt=timezone.now()
        )
        
        return active_lockouts.exists()
    
    @classmethod
    def get_active_lockout(cls, user):
        """
        Obtiene el bloqueo activo de un usuario si existe
        """
        if not user:
            return None
        
        return AccountLockout.objects.filter(
            user=user,
            is_active=True,
            unlock_at__gt=timezone.now()
        ).first()
    
    @classmethod
    def unlock_account(cls, user, unlocked_by=None, reason=''):
        """
        Desbloquea una cuenta manualmente
        """
        active_lockouts = AccountLockout.objects.filter(
            user=user,
            is_active=True
        )
        
        for lockout in active_lockouts:
            lockout.unlock(unlocked_by)
            lockout.notes = reason
            lockout.save()
        
        # Logging
        security_logger.logger.info(
            f"ACCOUNT_UNLOCK | User: {user.email} | "
            f"UnlockedBy: {unlocked_by.email if unlocked_by else 'System'} | "
            f"Reason: {reason}"
        )
        
        cls._record_security_event(
            user, 'account_unlock',
            f'Cuenta desbloqueada por {unlocked_by.email if unlocked_by else "sistema"}',
            severity='medium'
        )
        
        return True
    
    @classmethod
    def cleanup_expired_lockouts(cls):
        """
        Limpia bloqueos expirados (para ejecutar periódicamente)
        """
        expired_lockouts = AccountLockout.objects.filter(
            is_active=True,
            unlock_at__lte=timezone.now()
        )
        
        count = expired_lockouts.count()
        expired_lockouts.update(is_active=False, unlocked_at=timezone.now())
        
        return count
    
    @classmethod
    def get_recent_failed_attempts(cls, user, minutes=None):
        """
        Obtiene intentos fallidos recientes para un usuario
        """
        minutes = minutes or cls.ATTEMPT_WINDOW_MINUTES
        time_window = timezone.now() - timedelta(minutes=minutes)
        
        return LoginAttempt.objects.filter(
            user=user,
            success=False,
            timestamp__gte=time_window
        ).order_by('-timestamp')
    
    @classmethod
    def _record_security_event(cls, user, event_type, description, 
                             ip_address=None, user_agent='', severity='medium', 
                             metadata=None):
        """
        Registra un evento de seguridad
        """
        if not user:
            return None
        
        return SecurityEvent.objects.create(
            user=user,
            event_type=event_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            metadata=metadata or {}
        )
    
    @classmethod
    def get_security_summary(cls, user, days=30):
        """
        Obtiene un resumen de seguridad para un usuario
        """
        time_window = timezone.now() - timedelta(days=days)
        
        events = SecurityEvent.objects.filter(
            user=user,
            timestamp__gte=time_window
        )
        
        summary = {
            'total_events': events.count(),
            'login_attempts': events.filter(event_type='login_success').count(),
            'failed_logins': events.filter(event_type='login_failure').count(),
            'lockouts': events.filter(event_type='account_lockout').count(),
            'password_changes': events.filter(event_type='password_change').count(),
            'high_severity_events': events.filter(severity__in=['high', 'critical']).count(),
            'recent_ips': list(events.exclude(ip_address__isnull=True)
                             .values_list('ip_address', flat=True)
                             .distinct()[:10])
        }
        
        return summary


class TwoFactorService:
    """
    Servicio para gestión de autenticación de dos factores
    """
    
    @classmethod
    def enable_2fa(cls, user, request=None):
        """
        Habilita 2FA para un usuario
        """
        user.two_factor_enabled = True
        user.save()
        
        # Logging
        security_logger.logger.info(
            f"2FA_ENABLED | User: {user.email} | "
            f"IP: {security_logger._get_client_ip(request)}"
        )
        
        AccountSecurityService._record_security_event(
            user, '2fa_enabled', 
            'Autenticación de dos factores habilitada',
            security_logger._get_client_ip(request),
            security_logger._get_user_agent(request),
            severity='medium'
        )
    
    @classmethod
    def disable_2fa(cls, user, request=None):
        """
        Deshabilita 2FA para un usuario
        """
        user.two_factor_enabled = False
        user.save()
        
        # Logging
        security_logger.logger.warning(
            f"2FA_DISABLED | User: {user.email} | "
            f"IP: {security_logger._get_client_ip(request)}"
        )
        
        AccountSecurityService._record_security_event(
            user, '2fa_disabled', 
            'Autenticación de dos factores deshabilitada',
            security_logger._get_client_ip(request),
            security_logger._get_user_agent(request),
            severity='high'
        )
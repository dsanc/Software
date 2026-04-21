"""
Configuración de logging para seguridad y auditoría
"""
import os
from pathlib import Path

def get_security_logging_config(base_dir):
    """
    Configuración de logging especializada para eventos de seguridad
    """
    
    # Crear directorio de logs si no existe
    logs_dir = base_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'security_formatter': {
                'format': '[SECURITY] {asctime} | {levelname} | {name} | {funcName}:{lineno} | {message}',
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed_formatter': {
                'format': '{asctime} | {levelname} | {name} | {module}.{funcName}:{lineno} | PID:{process} | TID:{thread} | {message}',
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple_formatter': {
                'format': '{levelname} | {name} | {message}',
                'style': '{',
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            # Console handler para desarrollo
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple_formatter',
                'level': 'INFO',
            },
            
            # Handler principal para logs generales
            'file_general': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'django.log',
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'formatter': 'detailed_formatter',
                'level': 'INFO',
            },
            
            # Handler específico para eventos de seguridad
            'file_security': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'security.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 10,
                'formatter': 'security_formatter',
                'level': 'INFO',
            },
            
            # Handler para errores de autenticación
            'file_auth_errors': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'auth_errors.log',
                'maxBytes': 20 * 1024 * 1024,  # 20MB
                'backupCount': 7,
                'formatter': 'security_formatter',
                'level': 'WARNING',
            },
            
            # Handler para cambios de contraseña
            'file_password_changes': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'password_changes.log',
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 12,
                'formatter': 'security_formatter',
                'level': 'INFO',
            },
            
            # Handler para emails críticos (errores)
            'mail_admins': {
                'class': 'django.utils.log.AdminEmailHandler',
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'formatter': 'detailed_formatter',
                'include_html': True,
            },
        },
        'loggers': {
            # Logger principal de Django
            'django': {
                'handlers': ['console', 'file_general'],
                'level': 'INFO',
                'propagate': False,
            },
            
            # Logger para el módulo de usuarios
            'apps.users': {
                'handlers': ['console', 'file_general', 'file_security'],
                'level': 'DEBUG',
                'propagate': False,
            },
            
            # Logger específico para eventos de autenticación
            'apps.users.auth': {
                'handlers': ['file_security', 'file_auth_errors'],
                'level': 'INFO',
                'propagate': False,
            },
            
            # Logger específico para cambios de contraseña
            'apps.users.password': {
                'handlers': ['file_security', 'file_password_changes'],
                'level': 'INFO',
                'propagate': False,
            },
            
            # Logger para errores críticos de seguridad
            'security.critical': {
                'handlers': ['file_security', 'mail_admins', 'console'],
                'level': 'ERROR',
                'propagate': False,
            },
            
            # Logger para Django auth
            'django.contrib.auth': {
                'handlers': ['file_security', 'file_auth_errors'],
                'level': 'WARNING',
                'propagate': False,
            },
            
            # Logger para requests
            'django.request': {
                'handlers': ['file_general', 'mail_admins'],
                'level': 'ERROR',
                'propagate': False,
            },
            
            # Logger para la base de datos (solo errores)
            'django.db.backends': {
                'handlers': ['file_general'],
                'level': 'ERROR',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file_general'],
            'level': 'WARNING',
        },
    }


class SecurityLogger:
    """
    Clase utilitaria para logging de eventos de seguridad
    """
    
    def __init__(self, logger_name='apps.users'):
        import logging
        self.logger = logging.getLogger(logger_name)
        self.auth_logger = logging.getLogger('apps.users.auth')
        self.password_logger = logging.getLogger('apps.users.password')
        self.critical_logger = logging.getLogger('security.critical')
    
    def log_login_success(self, user, request, **extra_info):
        """Log login exitoso"""
        self.auth_logger.info(
            f"LOGIN_SUCCESS | User: {user.email} | "
            f"IP: {self._get_client_ip(request)} | "
            f"UserAgent: {self._get_user_agent(request)[:100]} | "
            f"Extra: {extra_info}"
        )
    
    def log_login_failure(self, username, request, reason="", **extra_info):
        """Log intento de login fallido"""
        self.auth_logger.warning(
            f"LOGIN_FAILURE | Username: {username} | "
            f"IP: {self._get_client_ip(request)} | "
            f"UserAgent: {self._get_user_agent(request)[:100]} | "
            f"Reason: {reason} | Extra: {extra_info}"
        )
    
    def log_password_change_success(self, user, request, method="form"):
        """Log cambio de contraseña exitoso"""
        self.password_logger.info(
            f"PASSWORD_CHANGE_SUCCESS | User: {user.email} | "
            f"IP: {self._get_client_ip(request)} | "
            f"Method: {method} | "
            f"UserAgent: {self._get_user_agent(request)[:100]}"
        )
    
    def log_password_change_failure(self, user, request, reason="", method="form"):
        """Log intento fallido de cambio de contraseña"""
        self.password_logger.warning(
            f"PASSWORD_CHANGE_FAILURE | User: {user.email} | "
            f"IP: {self._get_client_ip(request)} | "
            f"Method: {method} | Reason: {reason} | "
            f"UserAgent: {self._get_user_agent(request)[:100]}"
        )
    
    def log_password_reset_request(self, email, request):
        """Log solicitud de reset de contraseña"""
        self.password_logger.info(
            f"PASSWORD_RESET_REQUEST | Email: {email} | "
            f"IP: {self._get_client_ip(request)} | "
            f"UserAgent: {self._get_user_agent(request)[:100]}"
        )
    
    def log_password_reset_complete(self, user, request):
        """Log reset de contraseña completado"""
        self.password_logger.info(
            f"PASSWORD_RESET_COMPLETE | User: {user.email} | "
            f"IP: {self._get_client_ip(request)} | "
            f"UserAgent: {self._get_user_agent(request)[:100]}"
        )
    
    def log_suspicious_activity(self, user_or_ip, activity, request=None, **details):
        """Log actividad sospechosa"""
        ip = self._get_client_ip(request) if request else user_or_ip
        user_agent = self._get_user_agent(request) if request else "Unknown"
        
        self.critical_logger.error(
            f"SUSPICIOUS_ACTIVITY | Subject: {user_or_ip} | "
            f"Activity: {activity} | IP: {ip} | "
            f"UserAgent: {user_agent[:100]} | Details: {details}"
        )
    
    def log_account_lockout(self, user_or_email, request, reason=""):
        """Log bloqueo de cuenta"""
        self.critical_logger.warning(
            f"ACCOUNT_LOCKOUT | Account: {user_or_email} | "
            f"IP: {self._get_client_ip(request)} | "
            f"Reason: {reason} | "
            f"UserAgent: {self._get_user_agent(request)[:100]}"
        )
    
    def _get_client_ip(self, request):
        """Obtener IP real del cliente"""
        if not request:
            return "Unknown"
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip
    
    def _get_user_agent(self, request):
        """Obtener User Agent del request"""
        if not request:
            return "Unknown"
        return request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    def log_user_registration(self, user, request, method="form"):
        """Log de registro de usuario exitoso"""
        self.logger.info(
            f"Registro de usuario exitoso | "
            f"Email: {user.email} | "
            f"ID: {user.id} | "
            f"Método: {method} | "
            f"IP: {self._get_client_ip(request)} | "
            f"UserAgent: {self._get_user_agent(request)}"
        )
    
    def log_user_registration_failure(self, request, reason="Unknown", form_errors=None):
        """Log de intento de registro fallido"""
        error_details = ""
        if form_errors:
            error_details = f" | Errores: {dict(form_errors)}"
        
        self.logger.warning(
            f"Intento de registro fallido | "
            f"Razón: {reason} | "
            f"IP: {self._get_client_ip(request)} | "
            f"UserAgent: {self._get_user_agent(request)}"
            f"{error_details}"
        )


# Instancia global del logger de seguridad
security_logger = SecurityLogger()
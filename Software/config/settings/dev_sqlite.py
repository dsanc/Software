"""
Configuraciones para desarrollo local con SQLite
Útil para desarrollo rápido sin necesidad de configurar MySQL
"""
from .base import *

# Base de datos SQLite para desarrollo rápido
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Solo browser reload para auto-refresh
INSTALLED_APPS += [
    'django_browser_reload',
]

# Channel Layers para desarrollo (usar memoria en lugar de Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Solo browser reload middleware
MIDDLEWARE = MIDDLEWARE + [
    'django_browser_reload.middleware.BrowserReloadMiddleware',
]

# Configuración de Email para desarrollo
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Configuraciones adicionales de email
DEFAULT_FROM_EMAIL = 'Sistema <noreply@localhost>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_SUBJECT_PREFIX = '[Django Local] '

# Configuraciones para reset de contraseña
PASSWORD_RESET_TIMEOUT = 86400  # 24 horas en segundos

# Cache para desarrollo
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Configuración mejorada de logging para debugging y seguridad
# from apps.users.security_logging import get_security_logging_config

# LOGGING = get_security_logging_config(BASE_DIR)

# Logging temporal solo a consola para debug
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}
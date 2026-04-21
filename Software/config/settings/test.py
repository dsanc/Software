"""
Settings específicos para tests PWA
"""
from .dev_sqlite import *

# Deshabilitar middleware de subscriptions para tests
if 'apps.subscriptions.middleware.SubscriptionMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('apps.subscriptions.middleware.SubscriptionMiddleware')

# Asegurar que el middleware de mensajes esté presente
if 'django.contrib.messages.middleware.MessageMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.append('django.contrib.messages.middleware.MessageMiddleware')

# Configuración específica para PWA tests
PWA_APP_NAME = "Risk Hoteles Test"
PWA_APP_SHORT_NAME = "Risk Hotels Test"
PWA_APP_DESCRIPTION = "Sistema de gestión de riesgos hoteleros - Tests"
PWA_THEME_COLOR = "#007cba"
PWA_BACKGROUND_COLOR = "#ffffff"

# Configuración para tests de notificaciones push
VAPID_PUBLIC_KEY = "test-vapid-public-key"
VAPID_PRIVATE_KEY = "test-vapid-private-key"
VAPID_ADMIN_EMAIL = "test@example.com"

# Deshabilitar el cache para tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Configurar logging para tests
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
        'level': 'INFO',
    },
}

# Configuración para tests de WebSockets (si se usa Channels)
if 'channels' in INSTALLED_APPS:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        }
    }

# Password hashers más rápidos para tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Media files para tests
MEDIA_ROOT = os.path.join(BASE_DIR, 'test_media')

# Email backend para tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
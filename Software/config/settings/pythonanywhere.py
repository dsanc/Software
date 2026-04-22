"""
Configuraciones específicas para PythonAnywhere
Hereda de production.py con ajustes para la plataforma
"""
from .base import *

# Seguridad
DEBUG = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# NOTA: PythonAnywhere maneja HTTPS internamente.
# No activar SECURE_SSL_REDIRECT ni SECURE_HSTS en plan gratuito.
# En plan de pago con dominio propio, descomentar las siguientes líneas:
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Base de datos MySQL (PythonAnywhere provee MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),  # formato: tuusuario.mysql.pythonanywhere-services.com
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
            'charset': 'utf8mb4',
            'use_unicode': True,
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# PythonAnywhere NO soporta Redis en plan gratuito.
# Se usa InMemoryChannelLayer como reemplazo.
# En plan de pago con Redis, cambiar a channels_redis.core.RedisChannelLayer
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Archivos estáticos — whitenoise ya está configurado en base.py
# PythonAnywhere también permite servir /static/ y /media/ desde el panel web.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

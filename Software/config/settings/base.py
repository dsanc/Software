"""
Configuraciones base de Django
"""
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# No default provided for security - must be set in environment variables
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=lambda v: [s.strip() for s in v.split(',')])

CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'django_extensions',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'channels',
    'django_summernote',
    'widget_tweaks',
]

LOCAL_APPS = [
    'apps.users',
    'apps.dashboard',
    'apps.subscriptions',
    'apps.evaluadores',
    'apps.risk_hoteles',
    'apps.risk_conjuntos',
    'apps.security_probabilistic',
    'apps.core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'apps.subscriptions.middleware.SubscriptionRequiredMiddleware',  # Verificación de suscripción
    'apps.evaluadores.middleware.EvaluadorMiddleware',  # Contexto de evaluadores
    'apps.evaluadores.middleware.EvaluadorAccessMiddleware',  # Control de acceso de evaluadores
    'apps.evaluadores.middleware.EvaluadorSessionMiddleware',  # Gestión de sesiones de evaluadores
    'apps.risk_hoteles.performance_monitoring.AlertsPerformanceMiddleware',  # Performance monitoring
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ASGI Configuration for WebSockets
ASGI_APPLICATION = 'config.asgi.application'

# Channel Layers Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'apps.evaluadores.middleware.evaluator_context_processor',
                'apps.evaluadores.context_processors.evaluador_permissions',
                'core.context_processors.branding_context',
                'core.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='django_modular'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
            'charset': 'utf8mb4',
            'use_unicode': True,
        },
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'apps.users.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'first_name', 'last_name', 'email'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    # Validadores personalizados
    {
        'NAME': 'apps.users.validators.CustomPasswordValidator',
        'OPTIONS': {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special': True,
            'max_personal_similarity': 0.7,
        }
    },
    {
        'NAME': 'apps.users.validators.NoPersonalInfoValidator',
    },
    {
        'NAME': 'apps.users.validators.NoRepeatingCharactersValidator',
        'OPTIONS': {
            'max_repeats': 2,
        }
    },
    {
        'NAME': 'apps.users.validators.NoSequentialCharactersValidator',
        'OPTIONS': {
            'max_sequence_length': 3,
        }
    },
]

# Internationalization
LANGUAGE_CODE = 'es-es'
# Zona horaria configurada para Colombia
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# URLs de autenticación
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/users/login/'

# ===================================
# CONFIGURACIONES DE SEGURIDAD
# ===================================

# Configuraciones para bloqueo de cuentas
MAX_LOGIN_ATTEMPTS = config('MAX_LOGIN_ATTEMPTS', default=5, cast=int)
LOCKOUT_DURATION_MINUTES = config('LOCKOUT_DURATION_MINUTES', default=30, cast=int)
ATTEMPT_WINDOW_MINUTES = config('ATTEMPT_WINDOW_MINUTES', default=15, cast=int)

# Configuraciones para 2FA
OTP_TOTP_ISSUER = config('OTP_TOTP_ISSUER', default='Django Modular')
OTP_LOGIN_URL = '/users/2fa/login/'

# Configuraciones de sesión para seguridad
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = not DEBUG  # Solo HTTPS en producción
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Configuraciones CSRF
CSRF_COOKIE_SECURE = not DEBUG  # Solo HTTPS en producción
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Configuraciones de seguridad adicionales
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de logging de seguridad
from apps.users.security_logging import get_security_logging_config
if not DEBUG:
    LOGGING = get_security_logging_config(BASE_DIR)
else:
    # Configuración simple para desarrollo
    LOGGING.update({
        'loggers': {
            **LOGGING.get('loggers', {}),
            'apps.users': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'apps.users.auth': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'alerts.performance': {
                'handlers': ['file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
        }
    })
LOGIN_REDIRECT_URL = '/dashboard/'

# =============================================================================
# CONFIGURACIÓN DE PAGOS Y SUSCRIPCIONES
# =============================================================================

# Wompi Configuration
WOMPI_BASE_URL = config('WOMPI_BASE_URL', default='https://sandbox.wompi.co/v1')
WOMPI_PUBLIC_KEY = config('WOMPI_PUBLIC_KEY', default='')
WOMPI_PRIVATE_KEY = config('WOMPI_PRIVATE_KEY', default='')
WOMPI_EVENT_SECRET = config('WOMPI_EVENT_SECRET', default='')
WOMPI_SANDBOX = config('WOMPI_SANDBOX', default=True, cast=bool)

# Site URL for payment redirects
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Subscription Settings
SUBSCRIPTION_SETTINGS = {
    'TRIAL_PERIOD_DAYS': 14,
    'GRACE_PERIOD_DAYS': 3,
    'MAX_FAILED_PAYMENTS': 3,
    'PAYMENT_PROCESSORS': ['wompi'],
    'DEFAULT_CURRENCY': 'COP',
    'AUTO_RENEW_SUBSCRIPTIONS': True,
    'SEND_EXPIRATION_NOTIFICATIONS': True,
    'EXPIRATION_NOTIFICATION_DAYS': [30, 7, 1],
}

# Plan Limits Configuration
DEFAULT_PLAN_LIMITS = {
    'risk_hoteles': {
        'basic': {
            'reports': 10,
            'users': 2,
            'storage_gb': 1,
            'api_calls': 1000,
        },
        'pro': {
            'reports': 100,
            'users': 10,
            'storage_gb': 10,
            'api_calls': 10000,
        },
        'enterprise': {
            'reports': -1,  # -1 = unlimited
            'users': -1,
            'storage_gb': 100,
            'api_calls': -1,
        }
    },
    'risk_conjuntos': {
        'starter': {
            'reports': 5,
            'users': 1,
            'storage_gb': 1,
            'api_calls': 500,
        },
        'advanced': {
            'reports': 50,
            'users': 5,
            'storage_gb': 5,
            'api_calls': 5000,
        },
        'premium': {
            'reports': -1,
            'users': -1,
            'storage_gb': 50,
            'api_calls': -1,
        }
    },
    'security_probabilistic': {
        'essential': {
            'reports': 20,
            'users': 3,
            'storage_gb': 2,
            'api_calls': 2000,
        },
        'professional': {
            'reports': 200,
            'users': 15,
            'storage_gb': 20,
            'api_calls': 20000,
        },
        'enterprise': {
            'reports': -1,
            'users': -1,
            'storage_gb': 200,
            'api_calls': -1,
        }
    }
}

# Django Summernote Configuration
SUMMERNOTE_CONFIG = {
    'iframe': False,
    'summernote': {
        'airMode': False,
        'width': '100%',
        'height': '200',
        'toolbar': [
            ['style', ['style']],
            ['font', ['bold', 'italic', 'underline', 'clear']],
            ['fontname', ['fontname']],
            ['color', ['color']],
            ['para', ['ul', 'ol', 'paragraph']],
            ['table', ['table']],
        ],
        'fontNames': ['Arial', 'Arial Black', 'Comic Sans MS', 'Courier New', 'Helvetica', 'Impact', 'Tahoma', 'Times New Roman', 'Verdana'],
        'fontSizes': ['8', '9', '10', '11', '12', '14', '16', '18', '24', '36', '48'],
    },
    'css': (
        '//cdnjs.cloudflare.com/ajax/libs/summernote/0.8.20/summernote-bs5.min.css',
    ),
    'js': (
        '//cdnjs.cloudflare.com/ajax/libs/summernote/0.8.20/summernote-bs5.min.js',
    ),
    'css_for_inplace': (
        '//cdnjs.cloudflare.com/ajax/libs/summernote/0.8.20/summernote-bs5.min.css',
    ),
    'js_for_inplace': (
        '//cdnjs.cloudflare.com/ajax/libs/summernote/0.8.20/summernote-bs5.min.js',
    ),
    'codemirror': {
        'mode': 'htmlmixed',
        'lineNumbers': 'true',
        'theme': 'monokai',
    },
    'lazy': True,
}

# ============================================================
# CONFIGURACIÓN DE LOGO Y BRANDING
# ============================================================

# URL del logo principal (puede ser local o externa)
SITE_LOGO_URL = config('SITE_LOGO_URL', default='images/logo-sidebar.svg')

# Configuración de logos para diferentes contextos
LOGO_CONFIG = {
    'sidebar': {
        'standard': config('LOGO_SIDEBAR_STANDARD', default='images/logo-sidebar.svg'),
        'hidpi': config('LOGO_SIDEBAR_HIDPI', default='images/logo-sidebar-@2x.svg'),
        'fallback_icon': config('LOGO_SIDEBAR_FALLBACK', default='fas fa-cube'),
        'alt_text': config('LOGO_ALT_TEXT', default='ModernApp'),
    },
    'navbar': {
        'standard': config('LOGO_NAVBAR_STANDARD', default='images/logo-navbar.svg'),
        'hidpi': config('LOGO_NAVBAR_HIDPI', default='images/logo-navbar-@2x.svg'),
    },
    'favicon': {
        'ico': config('FAVICON_ICO', default='favicon.ico'),
        'png': config('FAVICON_PNG', default='favicon.png'),
    }
}

# Nombre de la aplicación (usado como fallback cuando no hay logo)
SITE_NAME = config('SITE_NAME', default='Risk')

# Configuración de branding adicional
BRANDING_CONFIG = {
    'company_name': config('COMPANY_NAME', default='Mi Empresa'),
    'company_tagline': config('COMPANY_TAGLINE', default='Soluciones tecnológicas innovadoras'),
    'primary_color': config('PRIMARY_COLOR', default='#3b82f6'),
    'secondary_color': config('SECONDARY_COLOR', default='#8b5cf6'),
}

LOGOUT_REDIRECT_URL = '/'
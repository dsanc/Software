"""
Context processors para configuraciones globales del proyecto
"""
from django.conf import settings


def branding_context(request):
    """
    Context processor que añade configuraciones de branding y logos a todos los templates.
    
    Hace que estas variables estén disponibles en todos los templates:
    - logo_config: Configuración de logos
    - site_name: Nombre del sitio
    - branding_config: Configuración de branding
    """
    return {
        'logo_config': getattr(settings, 'LOGO_CONFIG', {}),
        'site_name': getattr(settings, 'SITE_NAME', 'ModernApp'),
        'site_logo_url': getattr(settings, 'SITE_LOGO_URL', 'images/logo-sidebar.svg'),
        'branding_config': getattr(settings, 'BRANDING_CONFIG', {}),
    }


def site_context(request):
    """
    Context processor para información general del sitio.
    """
    return {
        'DEBUG': settings.DEBUG,
        'ENVIRONMENT': getattr(settings, 'ENVIRONMENT', 'development'),
    }
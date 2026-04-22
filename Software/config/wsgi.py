"""
WSGI config for django_modular project.

It exposes the WSGI callable as a module-level variable named ``application``.

Para desarrollo local:
    DJANGO_SETTINGS_MODULE=config.settings.development

Para PythonAnywhere:
    DJANGO_SETTINGS_MODULE=config.settings.pythonanywhere

La variable de entorno tiene prioridad sobre el valor por defecto aquí.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.pythonanywhere')

application = get_wsgi_application()
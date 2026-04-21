"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import debug view
import sys
import os
sys.path.append(os.path.dirname(__file__))
from debug_view import debug_form_view

# Import CSS test view - COMMENTED OUT: file not found
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# from test_css_view import css_test_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('debug-form/', debug_form_view, name='debug_form'),  # URL temporal para debug
    # path('css-test/', css_test_view, name='css_test'),  # URL para probar CSS - COMMENTED OUT: view not found
    path('', include('apps.dashboard.urls')),
    path('users/', include('apps.users.urls')),
    path('subscriptions/', include('apps.subscriptions.urls')),
    path('evaluadores/', include('apps.evaluadores.urls')),
    path('risk-hoteles/', include('apps.risk_hoteles.urls')),
    path('risk-conjuntos/', include('apps.risk_conjuntos.urls')),
    path('security-probabilistic/', include('apps.security_probabilistic.urls')),
    path('summernote/', include('django_summernote.urls')),
]

# Servir archivos media y estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # STATIC files son servidos automáticamente por django.contrib.staticfiles en DEBUG=True
    # No añadir static(STATIC_URL, STATIC_ROOT) ya que apunta a staticfiles/ (collectstatic)
    # y omite los archivos nuevos en static/ que aún no se han colectado.
        
    # Browser reload
    if 'django_browser_reload' in settings.INSTALLED_APPS:
        urlpatterns = [
            path("__reload__/", include("django_browser_reload.urls")),
        ] + urlpatterns
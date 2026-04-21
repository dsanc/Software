"""
Decoradores y utilidades para el proceso de consolidación de sistemas de evaluación
"""
import functools
import warnings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse


def legacy_evaluation_system(message=None):
    """
    Decorador para marcar vistas del sistema legacy como deprecated
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Mostrar warning en desarrollo
            warnings.warn(
                f"Vista {view_func.__name__} está usando el sistema legacy de evaluaciones. "
                "Migrar al sistema de riesgos.",
                DeprecationWarning,
                stacklevel=2
            )
            
            # Mostrar mensaje al usuario
            default_message = (
                "Esta funcionalidad está siendo migrada al nuevo sistema de evaluación de riesgos. "
                "Algunas características pueden cambiar próximamente."
            )
            user_message = message or default_message
            
            if request.user.is_staff:
                messages.warning(request, f"SISTEMA LEGACY: {user_message}")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def redirect_to_risk_evaluation(conjunto_id):
    """
    Utility para redirigir del sistema legacy al nuevo sistema de riesgos
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Redirigir automáticamente al nuevo sistema
            messages.info(
                request, 
                "Redirigido al nuevo sistema de evaluación de riesgos."
            )
            return HttpResponseRedirect(
                reverse('risk_conjuntos:iniciar_evaluacion', 
                       kwargs={'conjunto_id': conjunto_id})
            )
        return wrapper
    return decorator


class LegacySystemMixin:
    """
    Mixin para views basadas en clases del sistema legacy
    """
    def dispatch(self, request, *args, **kwargs):
        warnings.warn(
            f"Vista {self.__class__.__name__} está usando el sistema legacy de evaluaciones.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if request.user.is_staff:
            messages.warning(
                request, 
                f"SISTEMA LEGACY: Vista {self.__class__.__name__} será migrada."
            )
        
        return super().dispatch(request, *args, **kwargs)
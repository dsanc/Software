from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from functools import wraps


class StaffRequiredMixin(LoginRequiredMixin):
    """
    Mixin que requiere que el usuario sea staff
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Acceso denegado. Se requieren permisos de staff.")
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin(LoginRequiredMixin):
    """
    Mixin que requiere que el usuario sea superuser
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Acceso denegado. Se requieren permisos de administrador.")
        return super().dispatch(request, *args, **kwargs)


def staff_required(view_func):
    """
    Decorador que requiere que el usuario sea staff
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Acceso denegado. Se requieren permisos de staff.")
        return view_func(request, *args, **kwargs)
    return wrapper


def superuser_required(view_func):
    """
    Decorador que requiere que el usuario sea superuser
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Acceso denegado. Se requieren permisos de administrador.")
        return view_func(request, *args, **kwargs)
    return wrapper
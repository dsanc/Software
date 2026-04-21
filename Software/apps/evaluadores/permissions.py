"""
Sistema de validación de permisos para evaluadores
"""
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps
from .models import Evaluador


class EvaluadorPermissionMixin:
    """
    Mixin para validar permisos de evaluadores en vistas
    """
    # Propiedades que deben ser definidas en las vistas que usen este mixin
    required_module = None
    evaluador_module = None
    required_permission = 'read'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override de dispatch para verificar permisos de evaluadores automáticamente
        """
        # Verificar autenticación
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('users:login')
        
        # Verificar acceso al módulo si está configurado
        if self.required_module or self.evaluador_module:
            modulo_name = self.required_module or self.evaluador_module
            
            if not self.verificar_permiso_modulo(request.user, modulo_name):
                # Para peticiones AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': False,
                        'error': 'module_access',
                        'module': modulo_name,
                        'message': f'No tienes acceso al módulo {modulo_name}'
                    }, status=403)
                
                # Para peticiones normales, redirigir a página de error personalizada
                from django.shortcuts import redirect
                from urllib.parse import urlencode
                
                params = urlencode({
                    'error_type': 'module_access',
                    'module': modulo_name,
                    'action': 'access'
                })
                
                return redirect(f'/evaluadores/permission-denied/?{params}')
        
        # Verificar permiso específico si está configurado
        if self.required_permission and (self.required_module or self.evaluador_module):
            modulo_name = self.required_module or self.evaluador_module
            
            if not self.verificar_permiso_crud(request.user, modulo_name, self.required_permission):
                # Para peticiones AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': False,
                        'error': 'permission_denied',
                        'module': modulo_name,
                        'action': self.required_permission,
                        'message': f'No tienes permisos para {self.required_permission} en el módulo {modulo_name}'
                    }, status=403)
                
                # Para peticiones normales, redirigir a página de error personalizada
                from django.shortcuts import redirect
                from urllib.parse import urlencode
                
                params = urlencode({
                    'error_type': 'permission_denied',
                    'module': modulo_name,
                    'action': self.required_permission
                })
                
                return redirect(f'/evaluadores/permission-denied/?{params}')
        
        # Si todo está bien, continuar con el dispatch normal
        return super().dispatch(request, *args, **kwargs)
    
    def get_evaluador_permisos(self, user, modulo_name):
        """
        Obtiene los permisos CRUD del evaluador para un módulo específico
        """
        if not user.is_authenticated:
            return {}

        # PRIMERO: Verificar si el usuario ES un evaluador
        try:
            evaluador = Evaluador.objects.get(
                usuario_evaluador=user,
                estado__in=['active', 'pending'],  # Incluir pending también
                is_active=True
            )
            
            # Verificar acceso al módulo
            # Si modulos_permitidos está vacío, verificar por suscripciones heredadas
            if evaluador.modulos_permitidos and modulo_name not in evaluador.modulos_permitidos:
                return {}
            
            # Si modulos_permitidos está vacío, verificar por suscripciones
            if not evaluador.modulos_permitidos:
                from apps.subscriptions.models import Subscription
                if not Subscription.objects.filter(
                    user=user,
                    plan__module__name=modulo_name,
                    status='active'
                ).exists():
                    return {}
            
            # Obtener permisos CRUD específicos del evaluador
            permisos_crud = evaluador.permisos_crud.get(modulo_name, {})
            
            # Permisos por defecto para evaluadores (restrictivos)
            permisos_default = {
                'create': False,
                'read': True,  # Por defecto puede leer
                'update': False,
                'delete': False,
                'export': False,
                'approve': False
            }
            
            # Combinar con permisos específicos del evaluador
            permisos_default.update(permisos_crud)
            return permisos_default
            
        except Evaluador.DoesNotExist:
            # SEGUNDO: Si NO es evaluador, verificar si es usuario principal
            
            # Si es superusuario o staff, tiene todos los permisos
            if user.is_superuser or user.is_staff:
                return {
                    'create': True,
                    'read': True,
                    'update': True,
                    'delete': True,
                    'export': True,
                    'approve': True
                }
            
            # Verificar si es usuario principal con suscripciones activas
            from apps.subscriptions.models import Subscription
            if Subscription.objects.filter(
                user=user,
                plan__module__name=modulo_name,
                status='active'
            ).exists():
                return {
                    'create': True,
                    'read': True,
                    'update': True,
                    'delete': True,
                    'export': True,
                    'approve': True
                }
        
        return {}
    
    def verificar_permiso_modulo(self, user, modulo_name):
        """
        Verifica si el usuario tiene acceso al módulo
        """
        permisos = self.get_evaluador_permisos(user, modulo_name)
        return len(permisos) > 0 and permisos.get('read', False)
    
    def verificar_permiso_crud(self, user, modulo_name, accion):
        """
        Verifica si el usuario puede realizar una acción específica
        """
        permisos = self.get_evaluador_permisos(user, modulo_name)
        return permisos.get(accion, False)


def evaluador_permission_required(modulo_name, accion='read'):
    """
    Decorador para validar permisos de evaluadores en vistas
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            mixin = EvaluadorPermissionMixin()
            
            if not mixin.verificar_permiso_crud(request.user, modulo_name, accion):
                # Si es una petición AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': False,
                        'error': 'permission_denied',
                        'module': modulo_name,
                        'action': accion,
                        'message': f'No tienes permisos para {accion} en el módulo {modulo_name}'
                    }, status=403)
                
                # Para peticiones normales, redirigir a página de error personalizada
                from django.shortcuts import redirect
                from urllib.parse import urlencode
                
                params = urlencode({
                    'error_type': 'permission_denied',
                    'module': modulo_name,
                    'action': accion
                })
                
                return redirect(f'/evaluadores/permission-denied/?{params}')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def evaluador_module_required(modulo_name):
    """
    Decorador para validar acceso al módulo
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            mixin = EvaluadorPermissionMixin()
            
            if not mixin.verificar_permiso_modulo(request.user, modulo_name):
                # Si es una petición AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': False,
                        'error': 'module_access',
                        'module': modulo_name,
                        'message': f'No tienes acceso al módulo {modulo_name}'
                    }, status=403)
                
                # Para peticiones normales, redirigir a página de error personalizada
                from django.shortcuts import redirect
                from urllib.parse import urlencode
                
                params = urlencode({
                    'error_type': 'module_access',
                    'module': modulo_name,
                    'action': 'access'
                })
                
                return redirect(f'/evaluadores/permission-denied/?{params}')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def get_user_module_permissions(user, modulo_name, spanish_keys=False):
    """
    Función helper para obtener permisos de un usuario en un módulo
    """
    mixin = EvaluadorPermissionMixin()
    permisos = mixin.get_evaluador_permisos(user, modulo_name)
    
    # Opción de mapear a claves en español
    if spanish_keys:
        mapeo = {
            'create': 'crear',
            'read': 'ver', 
            'update': 'editar',
            'delete': 'eliminar',
            'export': 'exportar',
            'approve': 'aprobar'
        }
        return {mapeo.get(k, k): v for k, v in permisos.items()}
    
    return permisos
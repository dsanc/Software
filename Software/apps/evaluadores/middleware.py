"""
Middleware para gestión de evaluadores
"""
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .services import EvaluadorService, EvaluadorSubscriptionService


class EvaluadorMiddleware(MiddlewareMixin):
    """
    Middleware que añade contexto de evaluador a las requests
    """
    
    def process_request(self, request):
        """
        Procesa la request para añadir contexto de evaluador
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Verificar si es evaluador - solo para el usuario autenticado
            es_evaluador = EvaluadorService.es_evaluador_activo(request.user)
            
            # Añadir información de evaluador al request
            request.evaluator_context = {
                'is_evaluator': es_evaluador,
                'profiles': [],
                'inherited_subscriptions': [],
                'main_users': []
            }
            
            if es_evaluador:
                # Obtener contexto completo de evaluador solo para el usuario autenticado
                context = EvaluadorSubscriptionService.get_inherited_subscription_context(
                    request.user
                )
                
                # Validación adicional: verificar que todos los datos pertenecen al usuario
                filtered_context = {}
                for key, value in context.items():
                    if key == 'evaluator_profiles' and isinstance(value, list):
                        # Filtrar perfiles que pertenezcan al usuario autenticado como evaluador
                        # Los perfiles son dicts con clave 'perfil', no objetos con atributo 'perfil'
                        filtered_profiles = []
                        for profile in value:
                            if (isinstance(profile, dict) and 'perfil' in profile and
                                    profile['perfil'].usuario_evaluador_id == request.user.id):
                                filtered_profiles.append(profile)
                        filtered_context[key] = filtered_profiles
                    elif key == 'main_users' and isinstance(value, list):
                        # Filtrar usuarios principales para los que el usuario autenticado es evaluador
                        filtered_users = []
                        for user in value:
                            # Verificar que el usuario autenticado es evaluador de este usuario principal
                            if EvaluadorService.es_evaluador_activo(request.user):
                                perfiles = EvaluadorService.obtener_perfiles_evaluador(request.user)
                                if any(p.usuario_principal_id == user.id for p in perfiles):
                                    filtered_users.append(user)
                        filtered_context[key] = filtered_users
                    else:
                        filtered_context[key] = value
                
                request.evaluator_context.update(filtered_context)
        
        return None


class EvaluadorAccessMiddleware(MiddlewareMixin):
    """
    Middleware para controlar el acceso de evaluadores a rutas específicas
    """
    
    # Rutas que requieren verificación de evaluador
    EVALUATOR_PROTECTED_PATHS = [
        '/risk_conjuntos/',
        '/risk_hoteles/', 
        '/security_probabilistic/',
        # Agregar más rutas según sea necesario
    ]
    
    # Rutas que están excluidas de la verificación
    EXCLUDED_PATHS = [
        '/admin/',
        '/users/',
        '/evaluadores/',
        '/dashboard/',
        '/subscriptions/',
    ]
    
    def process_request(self, request):
        """
        Verifica el acceso de evaluadores a rutas protegidas
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        path = request.path_info
        
        # Verificar si la ruta necesita verificación de evaluador
        needs_evaluation = any(
            path.startswith(protected_path) 
            for protected_path in self.EVALUATOR_PROTECTED_PATHS
        )
        
        # Verificar si está en rutas excluidas
        is_excluded = any(
            path.startswith(excluded_path) 
            for excluded_path in self.EXCLUDED_PATHS
        )
        
        if needs_evaluation and not is_excluded:
            # Determinar el módulo basado en la ruta
            module_name = self._get_module_from_path(path)
            
            if module_name:
                # Verificar acceso (propio o heredado)
                has_access = EvaluadorSubscriptionService.has_module_access_with_inheritance(
                    request.user, 
                    module_name
                )
                
                if not has_access:
                    messages.error(
                        request,
                        f'No tienes acceso al módulo {module_name}. '
                        'Contacta a tu administrador si crees que es un error.'
                    )
                    return redirect('dashboard:home')
                
                # Si es evaluador, actualizar último acceso
                if hasattr(request, 'evaluator_context') and request.evaluator_context['is_evaluator']:
                    self._update_evaluator_access(request, module_name)
        
        return None
    
    def _get_module_from_path(self, path):
        """
        Determina el nombre del módulo basado en la ruta
        """
        module_mapping = {
            '/risk_conjuntos/': 'risk_conjuntos',
            '/risk_hoteles/': 'risk_hoteles',
            '/security_probabilistic/': 'security_probabilistic',
        }
        
        for path_prefix, module_name in module_mapping.items():
            if path.startswith(path_prefix):
                return module_name
        
        return None
    
    def _update_evaluator_access(self, request, module_name):
        """
        Actualiza el último acceso de los evaluadores
        """
        if not hasattr(request, 'evaluator_context'):
            return
        
        for profile_data in request.evaluator_context.get('evaluator_profiles', []):
            perfil = profile_data['perfil']
            if perfil.tiene_acceso_a_modulo(module_name):
                EvaluadorService.actualizar_ultimo_acceso(
                    request.user,
                    perfil.usuario_principal
                )


class EvaluadorSessionMiddleware(MiddlewareMixin):
    """
    Middleware para manejar sesiones específicas de evaluadores
    """
    
    def process_request(self, request):
        """
        Procesa información de sesión para evaluadores
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Verificar si hay un token de invitación en la sesión (post-login)
            if 'invitacion_token' in request.session:
                token = request.session.pop('invitacion_token')
                # Redirigir a la página de aceptación de invitación
                from django.shortcuts import redirect
                return redirect('evaluadores:aceptar_invitacion', token=token)
            
            # Manejar selección de usuario principal si es evaluador múltiple
            if hasattr(request, 'evaluator_context') and request.evaluator_context['is_evaluator']:
                profiles = request.evaluator_context.get('evaluator_profiles', [])
                
                if len(profiles) > 1 and 'selected_main_user' not in request.session:
                    # Si tiene múltiples perfiles y no ha seleccionado uno
                    # Se podría implementar una lógica de selección automática
                    # o redirigir a una página de selección
                    pass
        
        return None


def evaluator_context_processor(request):
    """
    Context processor para añadir información de evaluador y límites de suscripción a todas las plantillas
    """
    context = {
        'is_evaluator': False,
        'evaluator_profiles': [],
        'inherited_modules': [],
        'main_users': [],
        'evaluator_limits': None
    }
    
    # Variables globales para el template sidebar
    user_subscriptions = []
    has_subscriptions = False
    
    # Validación de seguridad: solo usuarios autenticados
    if hasattr(request, 'user') and request.user.is_authenticated:
        # Añadir información de evaluador
        if hasattr(request, 'evaluator_context'):
            context.update(request.evaluator_context)
        
        # Obtener suscripciones del usuario autenticado para el sidebar
        try:
            from apps.subscriptions.services import SubscriptionService
            # Validar que solo se obtengan suscripciones del usuario autenticado
            user_subscriptions = list(SubscriptionService.get_user_subscriptions(request.user))
            has_subscriptions = len(user_subscriptions) > 0
            
            # Validación adicional: verificar que todas las suscripciones pertenecen al usuario
            filtered_subscriptions = []
            for subscription in user_subscriptions:
                if hasattr(subscription, 'user') and subscription.user == request.user:
                    filtered_subscriptions.append(subscription)
                elif hasattr(subscription, 'usuario') and subscription.usuario == request.user:
                    filtered_subscriptions.append(subscription)
            
            user_subscriptions = filtered_subscriptions
            has_subscriptions = len(user_subscriptions) > 0
            
        except ImportError:
            # Si el módulo de subscriptions no está disponible
            pass
        
        # Agregar límites de evaluadores - solo para el usuario autenticado
        try:
            from .decorators import get_user_evaluator_limits
            context['evaluator_limits'] = get_user_evaluator_limits(request.user)
        except Exception:
            # Si hay algún error, no romper la página
            context['evaluator_limits'] = None
    
    return {
        'evaluator': context,
        'user_subscriptions': user_subscriptions,
        'has_subscriptions': has_subscriptions,
    }
"""
Servicios para gestión de evaluadores y herencia de planes
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from apps.subscriptions.models import Subscription
from apps.subscriptions.services import SubscriptionService
from .models import Evaluador

User = get_user_model()


class EvaluadorService:
    """
    Servicio principal para gestionar la lógica de evaluadores
    """
    
    @staticmethod
    def es_evaluador_activo(usuario):
        """
        Verifica si un usuario es evaluador activo de algún usuario principal
        """
        return Evaluador.objects.filter(
            usuario_evaluador=usuario,
            is_active=True,
            estado='active'
        ).exists()
    
    @staticmethod
    def obtener_perfiles_evaluador(usuario):
        """
        Obtiene todos los perfiles de evaluador activos de un usuario
        """
        return Evaluador.objects.filter(
            usuario_evaluador=usuario,
            is_active=True,
            estado='active'
        ).select_related('usuario_principal')
    
    @staticmethod
    def obtener_usuarios_principales(usuario_evaluador):
        """
        Obtiene la lista de usuarios principales para los que trabaja el evaluador
        """
        perfiles = EvaluadorService.obtener_perfiles_evaluador(usuario_evaluador)
        return [perfil.usuario_principal for perfil in perfiles]
    
    @staticmethod
    def tiene_acceso_como_evaluador(usuario_evaluador, usuario_principal, modulo_name=None):
        """
        Verifica si un evaluador tiene acceso a trabajar para un usuario principal específico
        """
        try:
            perfil = Evaluador.objects.get(
                usuario_evaluador=usuario_evaluador,
                usuario_principal=usuario_principal,
                is_active=True,
                estado='active'
            )
            
            # Verificar expiración
            if perfil.fecha_expiracion and timezone.now() > perfil.fecha_expiracion:
                return False, "Acceso expirado"
            
            # Verificar acceso al módulo específico si se especifica
            if modulo_name and not perfil.tiene_acceso_a_modulo(modulo_name):
                return False, f"Sin acceso al módulo {modulo_name}"
            
            return True, "Acceso permitido"
            
        except Evaluador.DoesNotExist:
            return False, "No es evaluador de este usuario"
    
    @staticmethod
    def actualizar_ultimo_acceso(usuario_evaluador, usuario_principal):
        """
        Actualiza la fecha de último acceso de un evaluador
        """
        try:
            perfil = Evaluador.objects.get(
                usuario_evaluador=usuario_evaluador,
                usuario_principal=usuario_principal,
                is_active=True
            )
            perfil.actualizar_ultimo_acceso()
            return True
        except Evaluador.DoesNotExist:
            return False


class EvaluadorSubscriptionService(SubscriptionService):
    """
    Servicio extendido que maneja la herencia de suscripciones para evaluadores
    """
    
    @staticmethod
    def get_user_subscriptions_with_inheritance(user, module_name=None):
        """
        Obtiene suscripciones del usuario, incluyendo las heredadas como evaluador
        """
        # Validación de seguridad: verificar que el usuario esté autenticado
        if not user or not user.is_authenticated:
            return Subscription.objects.none()
        
        # Primero obtener suscripciones propias del usuario autenticado
        suscripciones_propias = SubscriptionService.get_user_subscriptions(user, module_name)
        
        # Si ya tiene suscripciones propias, retornarlas
        if suscripciones_propias.exists():
            return suscripciones_propias
        
        # Si no tiene suscripciones propias, buscar como evaluador
        perfiles_evaluador = EvaluadorService.obtener_perfiles_evaluador(user)
        
        suscripciones_heredadas = Subscription.objects.none()
        
        for perfil in perfiles_evaluador:
            # Validación adicional: verificar que el perfil pertenece al usuario autenticado
            if perfil.usuario_evaluador_id != user.id:
                continue
            
            # Obtener suscripciones del usuario principal
            suscripciones_principal = SubscriptionService.get_user_subscriptions(
                perfil.usuario_principal, 
                module_name
            )
            
            # Filtrar por módulos permitidos para este evaluador
            if perfil.modulos_permitidos:
                suscripciones_principal = suscripciones_principal.filter(
                    plan__module__name__in=perfil.modulos_permitidos
                )
            
            # Combinar con las suscripciones heredadas
            suscripciones_heredadas = suscripciones_heredadas.union(suscripciones_principal)
        
        return suscripciones_heredadas
    
    @staticmethod
    def has_module_access_with_inheritance(user, module_name):
        """
        Verifica si el usuario tiene acceso a un módulo, incluyendo herencia
        """
        # Validación de seguridad: verificar que el usuario esté autenticado
        if not user or not user.is_authenticated:
            return False
        
        # Primero verificar acceso propio
        if SubscriptionService.has_module_access(user, module_name):
            return True
        
        # Verificar como evaluador - solo para el usuario autenticado
        perfiles_evaluador = EvaluadorService.obtener_perfiles_evaluador(user)
        
        for perfil in perfiles_evaluador:
            # Validación adicional: verificar que el perfil pertenece al usuario autenticado
            if perfil.usuario_evaluador_id != user.id:
                continue
            
            # Verificar si tiene acceso al módulo
            if perfil.tiene_acceso_a_modulo(module_name):
                # Verificar si el usuario principal tiene suscripción activa para este módulo
                if SubscriptionService.has_module_access(perfil.usuario_principal, module_name):
                    return True
        
        return False
    
    @staticmethod
    def has_feature_access_with_inheritance(user, module_name, feature_code):
        """
        Verifica si el usuario puede usar una característica, incluyendo herencia
        """
        # Primero verificar acceso propio
        if SubscriptionService.has_feature_access(user, module_name, feature_code):
            return True
        
        # Verificar como evaluador
        perfiles_evaluador = EvaluadorService.obtener_perfiles_evaluador(user)
        
        for perfil in perfiles_evaluador:
            if perfil.tiene_acceso_a_modulo(module_name):
                # Verificar si el usuario principal tiene acceso a la característica
                if SubscriptionService.has_feature_access(
                    perfil.usuario_principal, 
                    module_name, 
                    feature_code
                ):
                    return True
        
        return False
    
    @staticmethod
    def get_usage_limits_with_inheritance(user, module_name):
        """
        Obtiene límites de uso incluyendo herencia de evaluadores
        """
        # Primero verificar si tiene suscripción propia
        suscripciones_propias = SubscriptionService.get_user_subscriptions(user, module_name)
        
        if suscripciones_propias.exists():
            return SubscriptionService.get_usage_limits(user, module_name)
        
        # Buscar como evaluador
        perfiles_evaluador = EvaluadorService.obtener_perfiles_evaluador(user)
        
        for perfil in perfiles_evaluador:
            if perfil.tiene_acceso_a_modulo(module_name):
                # Obtener límites del usuario principal
                limits = SubscriptionService.get_usage_limits(
                    perfil.usuario_principal, 
                    module_name
                )
                
                # Aplicar limitaciones específicas del evaluador
                limits = EvaluadorSubscriptionService._apply_evaluator_limits(
                    limits, 
                    perfil
                )
                
                return limits
        
        # Si no encontró acceso como evaluador, retornar límites vacíos
        return {
            'has_access': False,
            'subscription': None,
            'limits': {},
            'usage': {},
            'warnings': ['Sin acceso al módulo']
        }
    
    @staticmethod
    def _apply_evaluator_limits(limits, perfil_evaluador):
        """
        Aplica las limitaciones específicas del evaluador a los límites heredados
        """
        # Aplicar limitaciones específicas del evaluador
        if 'limits' in limits:
            # Limitación de evaluaciones por mes
            if 'evaluaciones' in limits['limits']:
                limits['limits']['evaluaciones'] = min(
                    limits['limits']['evaluaciones'],
                    perfil_evaluador.max_evaluaciones_mes
                )
            else:
                limits['limits']['evaluaciones'] = perfil_evaluador.max_evaluaciones_mes
        
        # Agregar información sobre el perfil de evaluador
        limits['evaluator_profile'] = {
            'is_evaluator': True,
            'usuario_principal': perfil_evaluador.usuario_principal.get_full_name(),
            'tipo_evaluador': perfil_evaluador.get_tipo_evaluador_display(),
            'puede_crear_reportes': perfil_evaluador.puede_crear_reportes,
            'puede_editar_evaluaciones': perfil_evaluador.puede_editar_evaluaciones,
            'acceso_completo_dashboard': perfil_evaluador.acceso_completo_dashboard
        }
        
        return limits
    
    @staticmethod
    def can_user_perform_action_with_inheritance(user, module_name, action):
        """
        Verifica si el usuario puede realizar una acción, considerando herencia
        """
        # Primero verificar acceso propio
        suscripciones_propias = SubscriptionService.get_user_subscriptions(user, module_name)
        
        if suscripciones_propias.exists():
            # Tiene suscripciones propias, usar lógica estándar
            # (aquí se implementarían las verificaciones estándar según la acción)
            return True, "Acceso propio"
        
        # Verificar como evaluador
        perfiles_evaluador = EvaluadorService.obtener_perfiles_evaluador(user)
        
        for perfil in perfiles_evaluador:
            if perfil.tiene_acceso_a_modulo(module_name):
                # Verificar si puede realizar la acción específica
                puede_realizar, mensaje = perfil.puede_realizar_accion(action)
                
                if puede_realizar:
                    # Verificar también que el usuario principal pueda realizar la acción
                    if EvaluadorSubscriptionService._user_principal_can_perform_action(
                        perfil.usuario_principal, 
                        module_name, 
                        action
                    ):
                        return True, f"Acceso heredado de {perfil.usuario_principal.get_full_name()}"
                    else:
                        return False, "Usuario principal sin acceso a la acción"
                else:
                    return False, mensaje
        
        return False, "Sin acceso al módulo"
    
    @staticmethod
    def _user_principal_can_perform_action(usuario_principal, module_name, action):
        """
        Verifica si el usuario principal puede realizar una acción
        """
        # Implementar lógica específica según la acción
        # Por ahora, verificar solo que tenga suscripción activa
        return SubscriptionService.has_module_access(usuario_principal, module_name)
    
    @staticmethod
    def get_inherited_subscription_context(user):
        """
        Obtiene el contexto completo de suscripciones heredadas
        """
        # Validación de seguridad: verificar que el usuario esté autenticado
        if not user or not user.is_authenticated:
            return {
                'is_evaluator': False,
                'own_subscriptions': [],
                'evaluator_profiles': [],
                'inherited_modules': set(),
                'main_users': []
            }
        
        context = {
            'is_evaluator': EvaluadorService.es_evaluador_activo(user),
            'own_subscriptions': list(SubscriptionService.get_user_subscriptions(user)),
            'evaluator_profiles': [],
            'inherited_modules': set(),
            'main_users': []
        }
        
        if context['is_evaluator']:
            perfiles = EvaluadorService.obtener_perfiles_evaluador(user)
            
            for perfil in perfiles:
                # Validación adicional: verificar que el perfil pertenece al usuario autenticado
                if perfil.usuario_evaluador_id != user.id:
                    continue
                
                perfil_data = {
                    'perfil': perfil,
                    'usuario_principal': perfil.usuario_principal,
                    'modulos_permitidos': perfil.modulos_permitidos,
                    'suscripciones_heredadas': list(perfil.obtener_suscripciones_heredadas()),
                    'permisos': {
                        'puede_crear_reportes': perfil.puede_crear_reportes,
                        'puede_editar_evaluaciones': perfil.puede_editar_evaluaciones,
                        'acceso_completo_dashboard': perfil.acceso_completo_dashboard
                    }
                }
                
                context['evaluator_profiles'].append(perfil_data)
                context['inherited_modules'].update(perfil.modulos_permitidos or [])
                
                # Solo agregar usuarios principales donde este usuario es evaluador autorizado
                if perfil.usuario_principal not in context['main_users']:
                    context['main_users'].append(perfil.usuario_principal)
        
        return context
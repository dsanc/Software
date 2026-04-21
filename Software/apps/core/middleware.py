"""
Middleware para limpiar avatares inválidos
"""
import os
import logging

logger = logging.getLogger(__name__)


class AvatarCleanupMiddleware:
    """
    Middleware que limpia automáticamente avatares inválidos cuando se detectan
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar antes de la vista
        if hasattr(request, 'user') and request.user.is_authenticated:
            self.clean_user_avatar(request.user)
        
        response = self.get_response(request)
        return response

    def clean_user_avatar(self, user):
        """Limpia el avatar si el archivo no existe"""
        try:
            if user.avatar and user.avatar.name:
                # Verificar si el archivo existe
                if hasattr(user.avatar, 'path'):
                    if not os.path.exists(user.avatar.path):
                        logger.warning(f"Avatar inválido detectado para usuario {user.email}: {user.avatar.name}")
                        user.avatar.delete(save=False)
                        user.avatar = None
                        user.save(update_fields=['avatar'])
        except Exception as e:
            logger.error(f"Error al verificar avatar de {user.email}: {e}")
            # En caso de cualquier error, limpiar el avatar
            try:
                user.avatar = None
                user.save(update_fields=['avatar'])
            except:
                pass
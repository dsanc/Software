"""
Utilidades para manejo de avatares
"""
import os
from django.conf import settings
from django.templatetags.static import static


def get_avatar_url(user):
    """
    Obtiene la URL del avatar del usuario o devuelve la imagen por defecto
    """
    if user.avatar and hasattr(user.avatar, 'url'):
        try:
            # Verificar si el archivo existe físicamente
            if hasattr(user.avatar, 'path') and os.path.exists(user.avatar.path):
                return user.avatar.url
            else:
                # Si no existe, limpiar el campo avatar
                user.avatar = None
                user.save(update_fields=['avatar'])
                return static('images/default-avatar.svg')
        except Exception:
            return static('images/default-avatar.svg')
    else:
        return static('images/default-avatar.svg')


def cleanup_invalid_avatar(user):
    """
    Limpia avatares inválidos de un usuario específico
    """
    if user.avatar:
        try:
            if hasattr(user.avatar, 'path') and not os.path.exists(user.avatar.path):
                user.avatar.delete(save=False)
                user.avatar = None
                user.save(update_fields=['avatar'])
                return True
        except Exception:
            user.avatar = None
            user.save(update_fields=['avatar'])
            return True
    return False
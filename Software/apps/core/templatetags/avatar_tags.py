"""
Template tags para avatares
"""
from django import template
from django.templatetags.static import static
from ..avatar_utils import get_avatar_url

register = template.Library()


@register.simple_tag
def avatar_url(user):
    """
    Template tag para obtener la URL del avatar de forma segura
    """
    return get_avatar_url(user)


@register.filter
def safe_avatar(user):
    """
    Filtro para obtener avatar seguro
    """
    return get_avatar_url(user)
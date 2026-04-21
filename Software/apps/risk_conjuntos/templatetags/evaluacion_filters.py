"""
Filtros personalizados para templates de evaluación
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Obtiene un item de un diccionario o formulario usando una clave
    """
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    elif hasattr(dictionary, '__getitem__'):
        try:
            return dictionary[key]
        except (KeyError, TypeError):
            return None
    return None


@register.filter
def get_field(form, field_name):
    """
    Obtiene un campo específico de un formulario
    """
    try:
        return form[field_name]
    except KeyError:
        return None


@register.filter
def multiply(value, arg):
    """
    Multiplica un valor por un argumento
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """
    Calcula el porcentaje de un valor respecto al total
    """
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def range_list(value):
    """
    Convierte un número en una lista de rango
    """
    try:
        return list(range(int(value)))
    except (ValueError, TypeError):
        return []


@register.filter
def get_id(field):
    """
    Obtiene el ID de un campo de formulario
    """
    try:
        if hasattr(field, 'id_for_label'):
            return field.id_for_label
        elif hasattr(field, 'auto_id'):
            return field.auto_id
        return None
    except (AttributeError, TypeError):
        return None
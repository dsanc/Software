from django import template
import unicodedata

register = template.Library()

@register.filter
def normalize_var_amenaza(value):
    """
    Normaliza variables de amenaza eliminando acentos y convirtiendo a minúsculas.
    Ejemplo: "Exposición" -> "exposicion"
    """
    if not value:
        return ""
    
    # Normalizar caracteres Unicode (eliminar acentos)
    normalized = unicodedata.normalize('NFD', str(value))
    # Filtrar solo caracteres no diacríticos
    ascii_chars = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    # Convertir a minúsculas
    return ascii_chars.lower()

@register.filter
def normalize_response(value):
    """
    Normaliza respuestas para usar como clases CSS.
    Ejemplo: "Mas de 10 meses" -> "mas-de-10-meses"
    """
    if not value:
        return ""
    
    # Normalizar caracteres Unicode (eliminar acentos)
    normalized = unicodedata.normalize('NFD', str(value))
    # Filtrar solo caracteres no diacríticos
    ascii_chars = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    # Convertir a minúsculas y reemplazar espacios por guiones
    return ascii_chars.lower().replace(' ', '-')

@register.filter
def initials(name):
    """
    Extrae las iniciales de un nombre completo.
    Ejemplo: "Juan Carlos Pérez" -> "JC"
    """
    if not name:
        return ""
    
    words = name.strip().split()
    if len(words) == 0:
        return ""
    elif len(words) == 1:
        return words[0][0].upper() if words[0] else ""
    else:
        # Tomar la primera letra de las dos primeras palabras
        return (words[0][0] + words[1][0]).upper() if len(words[0]) > 0 and len(words[1]) > 0 else words[0][0].upper()

@register.filter
def promedio_completo(evaluacion):
    """
    Calcula el promedio completo de una evaluación incluyendo factor geográfico.
    """
    if not evaluacion or evaluacion.estado != 'completada':
        return None
    
    try:
        resultado = evaluacion.calcular_promedio_completo()
        return resultado['promedio_completo']
    except:
        return evaluacion.probabilidad_total

@register.filter
def promedio_completo_porcentaje(evaluacion):
    """
    Calcula el promedio completo como porcentaje incluyendo factor geográfico.
    """
    if not evaluacion or evaluacion.estado != 'completada':
        return None
    
    try:
        resultado = evaluacion.calcular_promedio_completo()
        return resultado['porcentaje']
    except:
        return float(evaluacion.probabilidad_total) * 100 if evaluacion.probabilidad_total else 0

@register.filter
def user_initials(user):
    """
    Extrae las iniciales del nombre de un usuario.
    Primero intenta con first_name y last_name, luego con username.
    """
    if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
        if user.first_name and user.last_name:
            return (user.first_name[0] + user.last_name[0]).upper()
        elif user.first_name:
            return user.first_name[0].upper()
        elif user.last_name:
            return user.last_name[0].upper()
    
    # Fallback al username
    if hasattr(user, 'username') and user.username:
        return user.username[0].upper()
    
    return "U"  # Fallback por defecto
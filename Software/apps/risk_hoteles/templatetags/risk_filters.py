from django import template
import re

register = template.Library()

@register.filter(name='split_recommendations')
def split_recommendations(value):
    """
    Divide el texto de recomendaciones en una lista de recomendaciones individuales.
    Las recomendaciones pueden estar separadas por puntos, números o guiones.
    
    Uso: {{ recommendations|split_recommendations }}
    """
    if not value:
        return []
        
    # Eliminar espacios extras y saltos de línea
    value = value.strip()
    
    # Dividir por diferentes patrones comunes de separación
    patterns = [
        r'\d+\.\s+',  # números seguidos de punto (1., 2., etc.)
        r'[-•]\s+',   # guiones o bullets
        r'\n\s*\n',   # doble salto de línea
        r'(?<=[.!?])\s+'  # puntos, exclamaciones o interrogaciones seguidos de espacio
    ]
    
    # Unir todos los patrones
    split_pattern = '|'.join(patterns)
    
    # Dividir el texto y limpiar los resultados
    recommendations = [
        rec.strip() for rec in re.split(split_pattern, value)
        if rec.strip()
    ]
    
    return recommendations

@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a elementos de un diccionario usando una clave dinámica en templates
    Uso: {{ my_dict|get_item:key_variable }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def css_percentage(value):
    """
    Convierte un valor numérico a formato de porcentaje válido para CSS.
    Reemplaza comas decimales con puntos y asegura el formato correcto.
    
    Uso: {{ percentage|css_percentage }}
    """
    if value is None:
        return '0%'
    
    try:
        # Convertir a string y reemplazar coma por punto
        str_value = str(value).replace(',', '.')
        
        # Si ya tiene %, mantenerlo, si no agregarlo
        if '%' in str_value:
            return str_value
        else:
            return f"{str_value}%"
    except (ValueError, TypeError):
        return '0%'

@register.filter
def multiply(value, arg):
    """
    Multiplica dos valores
    Uso: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter        
def subtract(value, arg):
    """
    Resta dos valores
    Uso: {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """
    Alias para multiply - Multiplica dos valores
    Uso: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
        
@register.filter
def percentage(value, total):
    """
    Calcula el porcentaje
    Uso: {{ value|percentage:total }}
    """
    try:
        if total == 0:
            return 0
        return round((float(value) / float(total)) * 100, 2)
    except (ValueError, TypeError):
        return 0

@register.filter
def replace_underscore(value):
    """
    Reemplaza guiones bajos con espacios
    Uso: {{ value|replace_underscore }}
    """
    if value:
        return str(value).replace('_', ' ')
    return value

@register.filter
def lookup(dictionary, key):
    """
    Búsqueda en diccionario
    Uso: {{ my_dict|lookup:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def split(value, separator):
    """
    Divide una cadena por un separador
    Uso: {{ value|split:" " }}
    """
    if value:
        return str(value).split(separator)
    return []

@register.filter
def subtract(value, arg):
    """
    Resta dos números
    Uso: {{ value|subtract:other_value }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sub(value, arg):
    """
    Resta dos números (versión corta)
    Uso: {{ value|sub:other_value }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='js_number')
def js_number(value, decimals=1):
    """
    Convierte un número a formato JavaScript (con puntos decimales)
    
    Uso: {{ value|js_number:1 }}
    """
    if value is None:
        return "0"
    
    try:
        # Convertir a float y formatear con los decimales especificados
        num = float(value)
        formatted = f"{num:.{decimals}f}"
        # Asegurar que use punto decimal (no coma)
        formatted = formatted.replace(',', '.')
        return formatted
    except (ValueError, TypeError):
        return "0"

@register.filter(name='score_to_percentage')
def score_to_percentage(value):
    """
    Convierte una puntuación de escala 0-5 a porcentaje (0-100%)
    
    Uso: {{ score|score_to_percentage }}
    """
    if value is None:
        return 0
    
    try:
        # Convertir la puntuación de 0-5 a porcentaje 0-100
        score = float(value)
        percentage = (score / 5.0) * 100
        return round(percentage, 1)
    except (ValueError, TypeError):
        return 0
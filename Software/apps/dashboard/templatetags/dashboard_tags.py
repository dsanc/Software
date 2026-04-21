"""
Template tags personalizados para el dashboard
"""
from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """Permite hacer lookup en diccionarios desde templates"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def percentage_of(value, total):
    """Calcula el porcentaje de un valor respecto al total"""
    try:
        if total == 0:
            return 0
        return int((value / total) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def format_currency(value):
    """Formatea un número como moneda colombiana"""
    try:
        return "${:,.0f}".format(float(value)).replace(',', '.')
    except (ValueError, TypeError):
        return "$0"


@register.filter
def days_to_color(days):
    """Convierte días restantes en una clase de color CSS"""
    try:
        days = int(days)
        if days < 7:
            return 'danger'
        elif days < 30:
            return 'warning'
        else:
            return 'success'
    except (ValueError, TypeError):
        return 'secondary'


@register.simple_tag
def subscription_status_badge(subscription):
    """Genera un badge HTML para el estado de la suscripción"""
    if not subscription:
        return ''
    
    status_map = {
        'active': ('success', 'Activa'),
        'cancelled': ('danger', 'Cancelada'),
        'expired': ('warning', 'Expirada'),
        'suspended': ('secondary', 'Suspendida'),
    }
    
    color, text = status_map.get(subscription.status, ('secondary', subscription.status.title()))
    
    return f'<span class="badge bg-{color}">{text}</span>'


@register.inclusion_tag('dashboard/components/usage_bar.html')
def usage_bar(current, maximum, label="Uso"):
    """Renderiza una barra de progreso para mostrar el uso de recursos"""
    if maximum <= 0:  # Ilimitado
        percentage = 0
        color = 'success'
    else:
        percentage = min(100, (current / maximum) * 100)
        if percentage >= 90:
            color = 'danger'
        elif percentage >= 70:
            color = 'warning'
        else:
            color = 'success'
    
    return {
        'current': current,
        'maximum': maximum,
        'percentage': percentage,
        'color': color,
        'label': label,
        'is_unlimited': maximum <= 0
    }
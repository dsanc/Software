from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def semaforo_riesgo(promedio):
    """
    Filtro para obtener la clase CSS del semáforo de riesgo.
    A mayor porcentaje = mayor riesgo de materialización
    """
    if not promedio:
        return 'semaforo-sin-evaluar'
    
    try:
        if isinstance(promedio, str):
            promedio = Decimal(promedio)
        elif isinstance(promedio, float):
            promedio = Decimal(str(promedio))
        
        porcentaje = float(promedio * 100)
        
        if porcentaje <= 30:
            return 'semaforo-bajo'
        elif porcentaje <= 60:
            return 'semaforo-medio'
        else:
            return 'semaforo-alto'
    except (ValueError, TypeError, AttributeError):
        return 'semaforo-sin-evaluar'

@register.filter
def color_riesgo(promedio):
    """
    Filtro para obtener el color hexadecimal del riesgo
    """
    if not promedio:
        return '#6c757d'
    
    try:
        if isinstance(promedio, str):
            promedio = Decimal(promedio)
        elif isinstance(promedio, float):
            promedio = Decimal(str(promedio))
        
        porcentaje = float(promedio * 100)
        
        if porcentaje <= 30:
            return '#28a745'    # Verde
        elif porcentaje <= 60:
            return '#ffc107'    # Amarillo
        else:
            return '#dc3545'    # Rojo
    except (ValueError, TypeError, AttributeError):
        return '#6c757d'       # Gris

@register.filter
def texto_riesgo(promedio):
    """
    Filtro para obtener el texto descriptivo del nivel de riesgo
    """
    if not promedio:
        return 'Sin Evaluar'
    
    try:
        if isinstance(promedio, str):
            promedio = Decimal(promedio)
        elif isinstance(promedio, float):
            promedio = Decimal(str(promedio))
        
        porcentaje = float(promedio * 100)
        
        if porcentaje <= 30:
            return 'Riesgo Bajo'
        elif porcentaje <= 60:
            return 'Riesgo Moderado'
        else:
            return 'Riesgo Alto'
    except (ValueError, TypeError, AttributeError):
        return 'Sin Evaluar'

@register.filter  
def descripcion_riesgo(promedio):
    """
    Filtro para obtener una descripción detallada del riesgo
    """
    if not promedio:
        return 'Evaluación no completada'
    
    try:
        if isinstance(promedio, str):
            promedio = Decimal(promedio)
        elif isinstance(promedio, float):
            promedio = Decimal(str(promedio))
        
        porcentaje = float(promedio * 100)
        
        if porcentaje <= 30:
            return f'Probabilidad de materialización baja ({porcentaje:.1f}%). Las medidas de seguridad son efectivas.'
        elif porcentaje <= 60:
            return f'Probabilidad de materialización moderada ({porcentaje:.1f}%). Se requieren mejoras en seguridad.'
        else:
            return f'Probabilidad de materialización alta ({porcentaje:.1f}%). Requiere atención inmediata.'
    except (ValueError, TypeError, AttributeError):
        return 'Error al calcular el riesgo'

@register.inclusion_tag('risk_conjuntos/components/semaforo_riesgo.html')
def mostrar_semaforo(promedio, tamaño='normal', mostrar_texto=True, mostrar_porcentaje=True):
    """
    Template tag para mostrar el semáforo de riesgo completo
    """
    context = {
        'promedio': promedio,
        'clase_semaforo': semaforo_riesgo(promedio),
        'color': color_riesgo(promedio),
        'texto': texto_riesgo(promedio),
        'descripcion': descripcion_riesgo(promedio),
        'tamaño': tamaño,
        'mostrar_texto': mostrar_texto,
        'mostrar_porcentaje': mostrar_porcentaje,
    }
    
    if promedio:
        try:
            if isinstance(promedio, str):
                promedio = Decimal(promedio)
            elif isinstance(promedio, float):
                promedio = Decimal(str(promedio))
            context['porcentaje'] = float(promedio * 100)
        except (ValueError, TypeError, AttributeError):
            context['porcentaje'] = 0
    else:
        context['porcentaje'] = 0
    
    return context
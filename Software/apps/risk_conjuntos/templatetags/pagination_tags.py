"""
Template tags para paginación avanzada
"""

from django import template
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag
def url_replace(request, **kwargs):
    """
    Reemplaza parámetros en la URL actual manteniendo los filtros existentes
    """
    query = request.GET.dict()
    query.update(kwargs)
    
    # Remover parámetros vacíos
    query = {k: v for k, v in query.items() if v}
    
    return '?' + urlencode(query) if query else '?'


@register.simple_tag
def pagination_range(page_obj, on_each_side=3, on_ends=2):
    """
    Genera un rango inteligente de páginas para mostrar
    Similar al paginator de Django admin
    """
    paginator = page_obj.paginator
    page_number = page_obj.number
    
    # Si hay pocas páginas, mostrar todas
    if paginator.num_pages <= 2 * on_each_side + 2 * on_ends + 1:
        return list(range(1, paginator.num_pages + 1))
    
    # Calcular rangos
    if page_number <= on_each_side + on_ends + 1:
        # Página cerca del inicio
        result = list(range(1, on_each_side + on_ends + 2))
        result.append('...')
        result.extend(range(paginator.num_pages - on_ends + 1, paginator.num_pages + 1))
    elif page_number >= paginator.num_pages - on_each_side - on_ends:
        # Página cerca del final
        result = list(range(1, on_ends + 1))
        result.append('...')
        result.extend(range(paginator.num_pages - on_each_side - on_ends, paginator.num_pages + 1))
    else:
        # Página en el medio
        result = list(range(1, on_ends + 1))
        result.append('...')
        result.extend(range(page_number - on_each_side, page_number + on_each_side + 1))
        result.append('...')
        result.extend(range(paginator.num_pages - on_ends + 1, paginator.num_pages + 1))
    
    return result


@register.inclusion_tag('risk_conjuntos/components/pagination_info.html')
def pagination_info(page_obj, start_index, end_index, total_items):
    """
    Muestra información detallada de la paginación
    """
    return {
        'page_obj': page_obj,
        'start_index': start_index,
        'end_index': end_index,
        'total_items': total_items,
        'current_page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
    }


@register.inclusion_tag('risk_conjuntos/components/per_page_selector.html')
def per_page_selector(request, items_per_page, per_page_options):
    """
    Selector de elementos por página
    """
    return {
        'request': request,
        'items_per_page': items_per_page,
        'per_page_options': per_page_options,
    }
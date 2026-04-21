from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import json


def paginate_queryset(queryset, page_number, per_page=10):
    """
    Utilidad para paginación de querysets
    """
    paginator = Paginator(queryset, per_page)
    try:
        page_obj = paginator.page(page_number)
    except:
        page_obj = paginator.page(1)
    
    return page_obj


def json_response(data=None, status=200, message=None, errors=None):
    """
    Utilidad para respuestas JSON consistentes
    """
    response_data = {}
    
    if message:
        response_data['message'] = message
    
    if data is not None:
        response_data['data'] = data
    
    if errors:
        response_data['errors'] = errors
        
    response_data['status'] = status
    
    return JsonResponse(response_data, status=status)


def validate_json(request):
    """
    Valida y parsea JSON de una request
    """
    try:
        if request.content_type == 'application/json':
            return json.loads(request.body)
        return None
    except json.JSONDecodeError:
        raise ValidationError("JSON inválido")


class APIResponseMixin:
    """
    Mixin para vistas que necesitan respuestas API consistentes
    """
    
    def success_response(self, data=None, message="Operación exitosa"):
        return json_response(data=data, message=message, status=200)
    
    def error_response(self, errors, message="Error en la operación", status=400):
        return json_response(errors=errors, message=message, status=status)
    
    def not_found_response(self, message="Recurso no encontrado"):
        return json_response(message=message, status=404)
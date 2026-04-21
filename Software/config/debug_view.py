from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["GET", "POST"])
def debug_form_view(request):
    """Vista simple para debug del formulario"""
    
    if request.method == 'GET':
        print(f"🔍 DEBUG GET - Usuario: {request.user}, Autenticado: {request.user.is_authenticated}")
        return render(request, 'security_probabilistic/debug_form.html')
    
    elif request.method == 'POST':
        print(f"🚀 DEBUG POST recibido!")
        print(f"👤 Usuario: {request.user}")
        print(f"📋 POST data:")
        for key, value in request.POST.items():
            print(f"   {key}: {value}")
        
        print(f"📁 FILES data:")
        for key, value in request.FILES.items():
            print(f"   {key}: {value}")
        
        print(f"🌐 Headers:")
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                print(f"   {key}: {value}")
        
        # Responder con los datos recibidos
        response_data = {
            'status': 'success',
            'message': 'Datos recibidos correctamente',
            'data': dict(request.POST),
            'user': str(request.user),
            'authenticated': request.user.is_authenticated
        }
        
        return JsonResponse(response_data)
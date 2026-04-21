from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.subscriptions.access_control import requires_security_probabilistic
from .models import PerfilSeguridad

@login_required
@requires_security_probabilistic()
def test_perfiles_view(request):
    """Vista de prueba simple para verificar perfiles"""
    perfiles = PerfilSeguridad.objects.all()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Perfiles</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .perfil { border: 1px solid #ccc; margin: 10px 0; padding: 10px; }
        </style>
    </head>
    <body>
        <h1>Lista de Perfiles - Prueba</h1>
        <p>Total de perfiles: {}</p>
        
        {}
        
        <hr>
        <a href="/security-probabilistic/">← Volver al Dashboard</a>
    </body>
    </html>
    """.format(
        perfiles.count(),
        ''.join([
            f'<div class="perfil"><strong>{p.nombre_completo}</strong> - {p.get_cargo_politico_display()} ({p.get_estado_perfil_display()})</div>'
            for p in perfiles
        ])
    )
    
    return HttpResponse(html)
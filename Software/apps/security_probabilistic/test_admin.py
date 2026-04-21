#!/usr/bin/env python3
"""
Script para probar las funcionalidades mejoradas del admin
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev_sqlite')
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

django.setup()

from django.contrib.admin.sites import site
from apps.security_probabilistic.models import ArbolDecision, Pregunta, OpcionRespuesta
from apps.security_probabilistic.admin import ArbolDecisionAdmin, PreguntaAdmin, OpcionRespuestaAdmin

def test_admin_functionality():
    """Prueba las funcionalidades básicas del admin"""
    print("🔍 Probando funcionalidades del admin mejorado...")
    
    # Verificar que los modelos están registrados
    registered_models = [model._meta.model for model in site._registry.values()]
    
    models_to_check = [ArbolDecision, Pregunta, OpcionRespuesta]
    
    print("\n📋 Modelos registrados en el admin:")
    for model in models_to_check:
        if model in registered_models:
            print(f"✅ {model.__name__} - Registrado")
        else:
            print(f"❌ {model.__name__} - NO registrado")
    
    # Verificar configuraciones específicas
    print("\n🔧 Verificando configuraciones del ArbolDecisionAdmin:")
    arbol_admin = site._registry[ArbolDecision]
    
    print(f"  - List display: {arbol_admin.list_display}")
    print(f"  - List filter: {arbol_admin.list_filter}")
    print(f"  - Search fields: {arbol_admin.search_fields}")
    print(f"  - Inlines: {[inline.__name__ for inline in arbol_admin.inlines]}")
    print(f"  - Actions: {[action for action in arbol_admin.actions if not action.startswith('delete')]}")
    
    print("\n🔧 Verificando configuraciones del PreguntaAdmin:")
    pregunta_admin = site._registry[Pregunta]
    
    print(f"  - List display: {pregunta_admin.list_display}")
    print(f"  - Inlines: {[inline.__name__ for inline in pregunta_admin.inlines]}")
    
    print("\n🔧 Verificando configuraciones del OpcionRespuestaAdmin:")
    opcion_admin = site._registry[OpcionRespuesta]
    
    print(f"  - List display: {opcion_admin.list_display}")
    print(f"  - List filter: {opcion_admin.list_filter}")
    
    # Verificar que existen datos para probar
    print("\n📊 Estado de los datos:")
    arboles = ArbolDecision.objects.count()
    preguntas = Pregunta.objects.count()
    opciones = OpcionRespuesta.objects.count()
    
    print(f"  - Árboles de decisión: {arboles}")
    print(f"  - Preguntas: {preguntas}")
    print(f"  - Opciones de respuesta: {opciones}")
    
    if arboles > 0:
        arbol = ArbolDecision.objects.first()
        print(f"\n🌳 Probando métodos del ArbolDecisionAdmin con '{arbol.nombre}':")
        
        # Probar métodos display
        admin_instance = ArbolDecisionAdmin(ArbolDecision, site)
        
        try:
            desc_corta = admin_instance.descripcion_corta(arbol)
            print(f"  - descripcion_corta: {desc_corta}")
        except Exception as e:
            print(f"  - descripcion_corta: ERROR - {e}")
        
        try:
            total_preguntas = admin_instance.total_preguntas(arbol)
            print(f"  - total_preguntas: {total_preguntas}")
        except Exception as e:
            print(f"  - total_preguntas: ERROR - {e}")
        
        try:
            pregunta_inicial = admin_instance.pregunta_inicial(arbol)
            print(f"  - pregunta_inicial: {pregunta_inicial}")
        except Exception as e:
            print(f"  - pregunta_inicial: ERROR - {e}")
        
        try:
            validar_integridad = admin_instance.validar_integridad(arbol)
            print(f"  - validar_integridad: {validar_integridad}")
        except Exception as e:
            print(f"  - validar_integridad: ERROR - {e}")
    
    print("\n✅ Prueba del admin completada!")

if __name__ == "__main__":
    test_admin_functionality()
#!/usr/bin/env python3
"""
Script para crear algunos datos de ejemplo y probar el admin mejorado
"""

print("🔄 Probando funcionalidades del admin mejorado...")

# Crear algunos datos de ejemplo para probar
try:
    from apps.security_probabilistic.models import ArbolDecision, Pregunta, OpcionRespuesta, PerfilSeguridad
    
    # Crear un perfil de ejemplo si no existe
    perfil, created = PerfilSeguridad.objects.get_or_create(
        numero_documento='12345678',
        defaults={
            'nombres': 'Juan Carlos',
            'apellidos': 'Pérez García',
            'tipo_documento': 'CC',
            'fecha_nacimiento': '1980-01-01',
            'genero': 'M',
            'telefono_principal': '3001234567',
            'cargo_politico': 'alcalde',
            'departamento': 'Bogotá',
            'municipio': 'Bogotá',
            'direccion_residencia': 'Calle 123 # 45-67',
            'contacto_emergencia_nombre': 'María Pérez',
            'contacto_emergencia_telefono': '3009876543',
            'contacto_emergencia_relacion': 'Esposa'
        }
    )
    
    if created:
        print(f"✅ Perfil creado: {perfil.nombre_completo}")
    else:
        print(f"ℹ️ Perfil existente: {perfil.nombre_completo}")
    
    # Verificar árboles existentes
    arboles = ArbolDecision.objects.count()
    preguntas = Pregunta.objects.count()
    opciones = OpcionRespuesta.objects.count()
    
    print(f"\n📊 Estado actual de los datos:")
    print(f"  - Árboles de decisión: {arboles}")
    print(f"  - Preguntas: {preguntas}")
    print(f"  - Opciones de respuesta: {opciones}")
    print(f"  - Perfiles de seguridad: {PerfilSeguridad.objects.count()}")
    
    print(f"\n🌐 Servidor corriendo en: http://127.0.0.1:8000/admin/")
    print(f"📋 Accede al admin para ver las mejoras implementadas:")
    print(f"  - Gestión avanzada de árboles de decisión")
    print(f"  - Validaciones automáticas de integridad")
    print(f"  - Inlines para opciones y preguntas")
    print(f"  - Acciones personalizadas (duplicar, validar)")
    print(f"  - Indicadores visuales de estado")
    
    if arboles > 0:
        arbol = ArbolDecision.objects.first()
        print(f"\n🌳 Árbol de ejemplo disponible: '{arbol.nombre}'")
        print(f"  - Preguntas: {arbol.preguntas.count()}")
        print(f"  - Pregunta inicial: {'Sí' if arbol.preguntas.filter(es_pregunta_inicial=True).exists() else 'No configurada'}")
    
    print(f"\n✅ ¡Admin mejorado listo para usar!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Asegúrate de que Django esté configurado correctamente.")

print(f"\n📚 Documentación completa en: apps/security_probabilistic/ADMIN_MEJORAS.md")
"""
Comando para crear datos de ejemplo del sistema de evaluación de riesgos
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.risk_conjuntos.models import (
    TipoConjunto, Conjunto, TipoRiesgo, EscenarioRiesgo, 
    PreguntaEvaluacion, CalificacionOpcion, EvaluacionRiesgo, 
    RespuestaPregunta, ResultadoPregunta
)
import random
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos de ejemplo para demostrar el sistema de evaluación'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de ejemplo...'))
        
        try:
            with transaction.atomic():
                # 1. Crear usuario de ejemplo si no existe
                user, created = User.objects.get_or_create(
                    username='admin_ejemplo',
                    defaults={
                        'email': 'admin_ejemplo@ejemplo.com',
                        'first_name': 'Admin',
                        'last_name': 'Ejemplo'
                    }
                )
                if created:
                    user.set_password('123456')
                    user.save()
                    self.stdout.write('  ✓ Usuario admin_ejemplo creado')
                
                # 2. Crear tipo de conjunto si no existe
                tipo_conjunto, created = TipoConjunto.objects.get_or_create(
                    nombre='conjunto_cerrado',
                    defaults={
                        'descripcion': 'Conjunto residencial cerrado con seguridad',
                        'icono': 'fas fa-building',
                        'color': '#3498db'
                    }
                )
                if created:
                    self.stdout.write('  ✓ Tipo de conjunto creado')
                
                # 3. Crear conjunto de ejemplo si no existe
                conjunto, created = Conjunto.objects.get_or_create(
                    nombre='Conjunto Villa Segura',
                    defaults={
                        'propietario': user,
                        'nit': '800123456-7',
                        'tipo_conjunto': tipo_conjunto,
                        'direccion': 'Calle 123 #45-67',
                        'ciudad': 'Bogotá',
                        'departamento': 'Cundinamarca',
                        'numero_unidades': 150,
                        'numero_torres': 3,
                        'tiene_piscina': True,
                        'tiene_gimnasio': True,
                        'tiene_salon_social': True,
                        'administrador_nombre': 'María González',
                        'administrador_telefono': '+57 311 123 4567',
                        'administrador_email': 'admin@villasegura.com'
                    }
                )
                if created:
                    self.stdout.write('  ✓ Conjunto Villa Segura creado')
                
                # 4. Crear evaluación de ejemplo
                evaluacion, created = EvaluacionRiesgo.objects.get_or_create(
                    conjunto=conjunto,
                    creado_por=user,
                    defaults={
                        'creado_por': user,
                        'tipo_evaluacion': 'inicial',
                        'observaciones': 'Evaluación inicial del conjunto residencial',
                        'estado': 'en_progreso'
                    }
                )
                if created:
                    self.stdout.write('  ✓ Evaluación de ejemplo creada')
                
                # 5. Crear respuestas de ejemplo para algunas preguntas
                respuestas_creadas = 0
                preguntas = PreguntaEvaluacion.objects.filter(activa=True)[:10]  # Solo las primeras 10
                opciones = list(CalificacionOpcion.objects.all())
                
                for pregunta in preguntas:
                    # Crear respuesta aleatoria
                    opcion_aleatoria = random.choice(opciones)
                    respuesta, created = RespuestaPregunta.objects.get_or_create(
                        evaluacion=evaluacion,
                        pregunta=pregunta,
                        defaults={
                            'calificacion': opcion_aleatoria,
                            'comentarios': f'Respuesta de ejemplo para {pregunta.texto_pregunta[:30]}...'
                        }
                    )
                    if created:
                        respuestas_creadas += 1
                
                self.stdout.write(f'  ✓ {respuestas_creadas} respuestas de ejemplo creadas')
                
                # 6. Procesar resultados automáticamente
                self.stdout.write('  📊 Procesando resultados automáticamente...')
                
                # Importar y ejecutar el comando de procesamiento
                from django.core.management import call_command
                call_command('procesar_resultados_preguntas', '--force')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando datos de ejemplo: {str(e)}')
            )
            return
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✓ ¡Datos de ejemplo creados exitosamente!'))
        self.stdout.write('\nPuedes ver los datos en:')
        self.stdout.write('• Admin: http://127.0.0.1:8000/admin/')
        self.stdout.write('• Usuario: admin_ejemplo')
        self.stdout.write('• Contraseña: 123456')
        self.stdout.write('\nModelos disponibles:')
        self.stdout.write('• Conjuntos → Conjunto Villa Segura')
        self.stdout.write('• Evaluaciones de Riesgo → Evaluación inicial')
        self.stdout.write('• Respuestas de Preguntas → 10 respuestas de ejemplo')
        self.stdout.write('• Resultados de Preguntas → Resultados procesados automáticamente')
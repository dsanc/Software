from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.evaluadores.models import Evaluador

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea evaluadores de prueba para testing'
    
    def handle(self, *args, **options):
        # Crear o obtener usuario principal
        main_user, created = User.objects.get_or_create(
            username='admin_principal',
            defaults={
                'email': 'admin@test.com',
                'first_name': 'Admin',
                'last_name': 'Principal',
                'is_staff': True,
            }
        )
        
        if created:
            main_user.set_password('admin123')
            main_user.save()
            self.stdout.write(f'Usuario principal creado: {main_user.username}')
        
        # Datos de evaluadores de prueba
        evaluadores_data = [
            {
                'username': 'evaluador1',
                'email': 'evaluador1@test.com',
                'first_name': 'María',
                'last_name': 'García',
                'nombres': 'María Elena',
                'apellidos': 'García López',
                'tipo_evaluador': 'senior',
                'telefono': '+57 300 123 4567',
                'cargo': 'Evaluadora Senior de Riesgos',
                'especialidad': 'Análisis de Riesgos Hoteleros',
            },
            {
                'username': 'evaluador2',
                'email': 'evaluador2@test.com',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'nombres': 'Carlos Alberto',
                'apellidos': 'Rodríguez Pérez',
                'tipo_evaluador': 'junior',
                'telefono': '+57 301 234 5678',
                'cargo': 'Evaluador Junior',
                'especialidad': 'Seguridad Probabilística',
            },
            {
                'username': 'evaluador3',
                'email': 'evaluador3@test.com',
                'first_name': 'Ana',
                'last_name': 'Martínez',
                'nombres': 'Ana Sofía',
                'apellidos': 'Martínez Torres',
                'tipo_evaluador': 'especialista',
                'telefono': '+57 302 345 6789',
                'cargo': 'Especialista en Conjuntos',
                'especialidad': 'Evaluación de Conjuntos Residenciales',
            },
            {
                'username': 'evaluador4',
                'email': 'evaluador4@test.com',
                'first_name': 'Luis',
                'last_name': 'Hernández',
                'nombres': 'Luis Fernando',
                'apellidos': 'Hernández Silva',
                'tipo_evaluador': 'senior',
                'telefono': '+57 303 456 7890',
                'cargo': 'Evaluador Senior',
                'especialidad': 'Análisis Integral de Riesgos',
            }
        ]
        
        created_count = 0
        
        for data in evaluadores_data:
            # Verificar si el usuario ya existe
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                }
            )
            
            if created:
                user.set_password('testpass123')  # Contraseña por defecto
                user.save()
                self.stdout.write(f'Usuario creado: {user.username}')
            
            # Verificar si el evaluador ya existe
            evaluador, eval_created = Evaluador.objects.get_or_create(
                usuario_evaluador=user,
                defaults={
                    'nombres': data['nombres'],
                    'apellidos': data['apellidos'],
                    'tipo_evaluador': data['tipo_evaluador'],
                    'estado': 'active',
                    'fecha_ultimo_acceso': timezone.now(),
                    'modulos_permitidos': ['risk_hoteles', 'risk_conjuntos', 'security_probabilistic'],
                    'usuario_principal': main_user,  # Usar el usuario principal
                }
            )
            
            if eval_created:
                created_count += 1
                self.stdout.write(f'Evaluador creado: {evaluador.nombres} {evaluador.apellidos}')
            else:
                self.stdout.write(f'Evaluador ya existe: {evaluador.nombres} {evaluador.apellidos}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso completado. Se crearon {created_count} nuevos evaluadores.'
            )
        )
        
        total_evaluadores = Evaluador.objects.filter(estado='active').count()
        self.stdout.write(f'Total de evaluadores activos: {total_evaluadores}')
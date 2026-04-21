from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea datos de prueba para mostrar el uso de las suscripciones'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email del usuario')
        parser.add_argument(
            '--hotels', 
            type=int, 
            default=5, 
            help='Número de hoteles a crear (por defecto: 5)'
        )
        parser.add_argument(
            '--evaluations', 
            type=int, 
            default=15, 
            help='Número de evaluaciones a crear (por defecto: 15)'
        )

    def handle(self, *args, **options):
        email = options['email']
        num_hotels = options['hotels']
        num_evaluations = options['evaluations']
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(
                self.style.SUCCESS(f'Usuario encontrado: {email}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Usuario no encontrado: {email}')
            )
            return

        # Crear datos para el módulo risk_hoteles
        hotels_created = self._create_hotels_data(user, num_hotels, num_evaluations)
        
        # Comentar conjuntos por ahora para evitar errores
        # conjuntos_created = self._create_conjuntos_data(user, num_hotels, num_evaluations)
        conjuntos_created = 0
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Datos de prueba creados!'
                f'\nHoteles creados: {hotels_created}'
                f'\nConjuntos creados: {conjuntos_created} (deshabilitado)'
                f'\nEvaluaciones de hoteles: ~{num_evaluations}'
            )
        )

    def _create_hotels_data(self, user, num_hotels, num_evaluations):
        """Crear datos de prueba para risk_hoteles"""
        try:
            from apps.risk_hoteles.models import Hotel, SecurityAssessment, SecurityCategory
            
            # Nombres de hoteles de ejemplo
            hotel_names = [
                "Hotel Gran Colombia", "Hotel Emperador", "Hotel Vista Mar",
                "Hotel Monte Verde", "Hotel Plaza Real", "Hotel Boutique Centro",
                "Hotel Ejecutivo", "Hotel Panorama", "Hotel Elite", "Hotel Majestic"
            ]
            
            categories = ["1_star", "2_star", "3_star", "4_star", "5_star"]
            cities = ["Bogotá", "Medellín", "Cartagena", "Cali", "Barranquilla", "Santa Marta"]
            
            hotels_created = 0
            for i in range(num_hotels):
                # Verificar si ya existe un hotel con ese nombre para el usuario
                hotel_name = hotel_names[i % len(hotel_names)]
                if not Hotel.objects.filter(owner=user, name=hotel_name).exists():
                    hotel = Hotel.objects.create(
                        owner=user,
                        name=hotel_name,
                        address=f"Calle {random.randint(10, 100)} #{random.randint(10, 50)}-{random.randint(10, 99)}",
                        city=random.choice(cities),
                        country="Colombia",
                        category=random.choice(['1_star', '2_star', '3_star', '4_star', '5_star']),
                        total_rooms=random.randint(20, 200),
                        phone=f"601-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                        email=f"info@{hotel_name.lower().replace(' ', '').replace('hotel', '')}.com",
                        website=f"https://www.{hotel_name.lower().replace(' ', '').replace('hotel', '')}.com",
                        is_active=True
                    )
                    hotels_created += 1
                    
                    # Crear evaluaciones para este hotel
                    self._create_hotel_evaluations(hotel, num_evaluations // num_hotels)
                    
                    self.stdout.write(f'Hotel creado: {hotel.name}')
            
            return hotels_created
            
        except ImportError:
            self.stdout.write(
                self.style.WARNING('Módulo risk_hoteles no disponible')
            )
            return 0

    def _create_hotel_evaluations(self, hotel, num_evaluations):
        """Crear evaluaciones para un hotel"""
        try:
            from apps.risk_hoteles.models import SecurityAssessment, SecurityCategory
            
            # Obtener categorías de seguridad
            security_categories = list(SecurityCategory.objects.filter(is_active=True))
            if not security_categories:
                return
            
            for i in range(num_evaluations):
                # Fechas aleatorias en los últimos 3 meses
                days_ago = random.randint(1, 90)
                assessment_date = timezone.now() - timedelta(days=days_ago)
                
                assessment = SecurityAssessment.objects.create(
                    hotel=hotel,
                    assessment_type=random.choice(['completa', 'parcial', 'seguimiento']),
                    assessment_date=assessment_date.date(),
                    description=f"Evaluación de seguridad #{i+1}",
                    status=random.choice(['completed', 'pending', 'in_progress']),
                    overall_score=random.uniform(60, 95),
                    observations=f"Observaciones generales de la evaluación #{i+1}",
                    recommendations=f"Recomendaciones específicas para mejorar la seguridad",
                    created_by=hotel.owner,  # Agregar el usuario que crea la evaluación
                    created_at=assessment_date,
                    updated_at=assessment_date
                )
                
        except Exception as e:
            self.stdout.write(f'Error creando evaluaciones: {str(e)}')

    def _create_conjuntos_data(self, user, num_conjuntos, num_evaluations):
        """Crear datos de prueba para risk_conjuntos"""
        try:
            from apps.risk_conjuntos.models import Conjunto, EvaluacionSeguridad
            
            # Nombres de conjuntos de ejemplo
            conjunto_names = [
                "Conjunto Residencial Los Pinos", "Torres del Norte", "Conjunto Villa Real",
                "Residencias San Jorge", "Conjunto Portal de Oriente", "Torres del Centro",
                "Conjunto Los Arrayanes", "Residencial El Parque", "Conjunto Vista Hermosa"
            ]
            
            cities = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga"]
            
            conjuntos_created = 0
            for i in range(num_conjuntos):
                conjunto_name = conjunto_names[i % len(conjunto_names)]
                if not Conjunto.objects.filter(propietario=user, nombre=conjunto_name).exists():
                    # Generar un NIT único
                    nit_base = random.randint(800000000, 999999999)
                    nit = f"{nit_base}-{random.randint(1, 9)}"
                    
                    conjunto = Conjunto.objects.create(
                        propietario=user,
                        nombre=conjunto_name,
                        nit=nit,
                        tipo_conjunto_id=1,  # Asumiendo que existe un tipo con ID 1
                        direccion=f"Carrera {random.randint(10, 100)} #{random.randint(10, 50)}-{random.randint(10, 99)}",
                        ciudad=random.choice(cities),
                        departamento="Cundinamarca",
                        numero_unidades=random.randint(50, 300),
                        numero_torres=random.randint(1, 8),
                        tiene_piscina=random.choice([True, False]),
                        tiene_gimnasio=random.choice([True, False]),
                        tiene_salon_social=True,
                        administrador_nombre=f"Administración {conjunto_name}",
                        activo=True
                    )
                    conjuntos_created += 1
                    
                    # Crear evaluaciones para este conjunto
                    self._create_conjunto_evaluations(conjunto, num_evaluations // num_conjuntos)
                    
                    self.stdout.write(f'Conjunto creado: {conjunto.nombre}')
            
            return conjuntos_created
            
        except ImportError:
            self.stdout.write(
                self.style.WARNING('Módulo risk_conjuntos no disponible')
            )
            return 0

    def _create_conjunto_evaluations(self, conjunto, num_evaluations):
        """Crear evaluaciones para un conjunto"""
        try:
            from apps.risk_conjuntos.models import EvaluacionSeguridad
            
            for i in range(num_evaluations):
                # Fechas aleatorias en los últimos 3 meses
                days_ago = random.randint(1, 90)
                evaluation_date = timezone.now() - timedelta(days=days_ago)
                
                evaluation = EvaluacionSeguridad.objects.create(
                    conjunto=conjunto,
                    fecha_evaluacion=evaluation_date.date(),
                    tipo_evaluacion=random.choice(['inicial', 'seguimiento', 'auditoria']),
                    descripcion=f"Evaluación de seguridad #{i+1} para {conjunto.nombre}",
                    estado=random.choice(['completada', 'pendiente', 'en_proceso']),
                    puntaje_general=random.uniform(65, 90),
                    observaciones=f"Observaciones de la evaluación #{i+1}",
                    recomendaciones=f"Recomendaciones para mejorar la seguridad del conjunto",
                    fecha_creacion=evaluation_date,
                    fecha_actualizacion=evaluation_date
                )
                
        except Exception as e:
            self.stdout.write(f'Error creando evaluaciones de conjuntos: {str(e)}')
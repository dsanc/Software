from django.core.management.base import BaseCommand
from apps.risk_hoteles.models import SecurityCategory, SecurityQuestion


class Command(BaseCommand):
    help = 'Poblar categorías y preguntas de seguridad iniciales'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Creando categorías de seguridad...')
        
        # Definir las categorías con sus íconos y descripciones
        categories_data = [
            {
                'code': 'gestion_organizacion',
                'name': 'Gestión y Organización de la Seguridad',
                'description': 'Estructura organizacional, políticas de seguridad y responsabilidades del personal',
                'icon': 'fas fa-users-cog',
                'order': 1,
                'weight': 1.5
            },
            {
                'code': 'seguridad_externa',
                'name': 'Seguridad Externa',
                'description': 'Perímetro exterior y accesos exteriores al hotel',
                'icon': 'fas fa-shield-alt',
                'order': 2,
                'weight': 1.3
            },
            {
                'code': 'seguridad_perimetral',
                'name': 'Seguridad Perimetral',
                'description': 'Límites físicos, barreras y sistemas de control perimetral',
                'icon': 'fas fa-border-all',
                'order': 3,
                'weight': 1.2
            },
            {
                'code': 'seguridad_internas',
                'name': 'Seguridad en Áreas Internas',
                'description': 'Espacios comunes, áreas operativas y zonas restringidas',
                'icon': 'fas fa-home',
                'order': 4,
                'weight': 1.4
            },
            {
                'code': 'controles_accesos',
                'name': 'Controles de Accesos al Hotel',
                'description': 'Sistemas de control de acceso, llaves y identificación',
                'icon': 'fas fa-key',
                'order': 5,
                'weight': 1.3
            },
            {
                'code': 'seguridad_habitaciones',
                'name': 'Seguridad en Habitaciones',
                'description': 'Protección y seguridad de huéspedes en habitaciones',
                'icon': 'fas fa-bed',
                'order': 6,
                'weight': 1.5
            },
            {
                'code': 'seguridad_activos',
                'name': 'Seguridad de Activos Críticos del Hotel',
                'description': 'Equipos críticos, sistemas tecnológicos y activos valiosos',
                'icon': 'fas fa-server',
                'order': 7,
                'weight': 1.2
            },
            {
                'code': 'seguridad_parqueo',
                'name': 'Seguridad en Áreas de Parqueo',
                'description': 'Estacionamientos, garajes y áreas de vehículos',
                'icon': 'fas fa-car',
                'order': 8,
                'weight': 1.0
            },
            {
                'code': 'gestion_humana',
                'name': 'Seguridad en el Proceso de Gestión Humana',
                'description': 'Recursos humanos, capacitación y verificación de antecedentes',
                'icon': 'fas fa-user-tie',
                'order': 9,
                'weight': 1.4
            },
            {
                'code': 'seguridad_eventos',
                'name': 'Seguridad en Eventos',
                'description': 'Eventos especiales, conferencias y actividades masivas',
                'icon': 'fas fa-calendar-alt',
                'order': 10,
                'weight': 1.1
            },
            {
                'code': 'seguridad_ayb',
                'name': 'Seguridad en A&B',
                'description': 'Alimentos y bebidas, cocinas y áreas de servicio',
                'icon': 'fas fa-utensils',
                'order': 11,
                'weight': 1.2
            },
            {
                'code': 'seguridad_reservas',
                'name': 'Seguridad en Reservas',
                'description': 'Procesos de reservación, datos de huéspedes y sistemas',
                'icon': 'fas fa-clipboard-list',
                'order': 12,
                'weight': 1.1
            },
            {
                'code': 'seguridad_compras',
                'name': 'Seguridad en el Proceso de Compras',
                'description': 'Adquisiciones, proveedores y control de inventarios',
                'icon': 'fas fa-shopping-cart',
                'order': 13,
                'weight': 1.0
            },
            {
                'code': 'gestion_emergencias',
                'name': 'Seguridad y Gestión de Emergencias',
                'description': 'Planes de emergencia, evacuación y respuesta a crisis',
                'icon': 'fas fa-exclamation-triangle',
                'order': 14,
                'weight': 1.5
            }
        ]
        
        # Crear las categorías
        categories_created = 0
        for cat_data in categories_data:
            category, created = SecurityCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'order': cat_data['order'],
                    'weight': cat_data['weight']
                }
            )
            if created:
                categories_created += 1
                self.stdout.write(f'  ✅ Creada: {category.name}')
            else:
                self.stdout.write(f'  ⏭️  Ya existe: {category.name}')
        
        self.stdout.write(f'\n🎯 {categories_created} categorías nuevas creadas de {len(categories_data)} totales')
        
        # Crear preguntas de ejemplo para la categoría de Gestión y Organización
        self.stdout.write('\n🔄 Creando preguntas de ejemplo...')
        
        gestion_cat = SecurityCategory.objects.get(code='gestion_organizacion')
        
        example_questions = [
            {
                'question_text': '¿El hotel cuenta con una política de seguridad documentada y actualizada?',
                'help_text': 'Evalúe si existe un documento formal que establezca las políticas de seguridad del hotel',
                'weight': 1.5,
                'order': 1
            },
            {
                'question_text': '¿Existe un responsable de seguridad designado con funciones claramente definidas?',
                'help_text': 'Verifique si hay una persona específicamente responsable de la seguridad del hotel',
                'weight': 1.3,
                'order': 2
            },
            {
                'question_text': '¿Se realizan capacitaciones regulares en temas de seguridad para todo el personal?',
                'help_text': 'Evalúe la frecuencia y calidad de las capacitaciones de seguridad',
                'weight': 1.2,
                'order': 3
            },
            {
                'question_text': '¿El hotel tiene procedimientos documentados para situaciones de emergencia?',
                'help_text': 'Revise si existen protocolos escritos para diferentes tipos de emergencias',
                'weight': 1.4,
                'order': 4
            },
            {
                'question_text': '¿Se realizan auditorías internas de seguridad periódicamente?',
                'help_text': 'Evalúe si el hotel revisa regularmente sus medidas de seguridad',
                'weight': 1.1,
                'order': 5
            }
        ]
        
        questions_created = 0
        for q_data in example_questions:
            question, created = SecurityQuestion.objects.get_or_create(
                category=gestion_cat,
                question_text=q_data['question_text'],
                defaults={
                    'help_text': q_data['help_text'],
                    'weight': q_data['weight'],
                    'order': q_data['order']
                }
            )
            if created:
                questions_created += 1
                self.stdout.write(f'  ✅ Pregunta creada: {question.question_text[:60]}...')
            else:
                self.stdout.write(f'  ⏭️  Ya existe: {question.question_text[:60]}...')
        
        # Crear preguntas para seguridad externa
        seguridad_ext = SecurityCategory.objects.get(code='seguridad_externa')
        
        external_questions = [
            {
                'question_text': '¿El perímetro exterior del hotel cuenta con iluminación adecuada?',
                'help_text': 'Evalúe si todas las áreas externas tienen iluminación suficiente durante la noche',
                'weight': 1.2,
                'order': 1
            },
            {
                'question_text': '¿Existen cámaras de seguridad monitoreando las entradas principales?',
                'help_text': 'Verifique la presencia y funcionamiento de sistemas de videovigilancia',
                'weight': 1.4,
                'order': 2
            },
            {
                'question_text': '¿Se controla el acceso de vehículos al hotel?',
                'help_text': 'Evalúe si existe control sobre qué vehículos pueden ingresar',
                'weight': 1.1,
                'order': 3
            }
        ]
        
        for q_data in external_questions:
            question, created = SecurityQuestion.objects.get_or_create(
                category=seguridad_ext,
                question_text=q_data['question_text'],
                defaults={
                    'help_text': q_data['help_text'],
                    'weight': q_data['weight'],
                    'order': q_data['order']
                }
            )
            if created:
                questions_created += 1
                self.stdout.write(f'  ✅ Pregunta creada: {question.question_text[:60]}...')
        
        self.stdout.write(f'\n🎯 {questions_created} preguntas nuevas creadas')
        self.stdout.write(self.style.SUCCESS('\n✅ ¡Datos iniciales creados exitosamente!'))
        self.stdout.write('💡 Ahora puedes crear más preguntas desde el admin de Django o continuar con el sistema de evaluaciones.')
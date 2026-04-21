"""
Management command para crear datos de ejemplo para el módulo risk_hoteles
"""
from django.core.management.base import BaseCommand
from apps.risk_hoteles.models import RiskCategory


class Command(BaseCommand):
    help = 'Crear categorías de riesgo básicas para hoteles'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Incendio',
                'description': 'Riesgo de incendio en las instalaciones del hotel',
                'weight': 3.0,
            },
            {
                'name': 'Robo y Seguridad',
                'description': 'Riesgo de robo, asalto y problemas de seguridad',
                'weight': 2.5,
            },
            {
                'name': 'Desastres Naturales',
                'description': 'Riesgo por terremotos, inundaciones, huracanes, etc.',
                'weight': 2.8,
            },
            {
                'name': 'Accidentes de Huéspedes',
                'description': 'Riesgo de accidentes de los huéspedes en las instalaciones',
                'weight': 2.0,
            },
            {
                'name': 'Daños a la Propiedad',
                'description': 'Riesgo de daños a la infraestructura y equipamiento',
                'weight': 1.8,
            },
            {
                'name': 'Problemas de Salud Pública',
                'description': 'Riesgo de epidemias, intoxicaciones alimentarias, etc.',
                'weight': 2.3,
            },
            {
                'name': 'Fallas de Servicios',
                'description': 'Riesgo por fallas en agua, electricidad, internet, etc.',
                'weight': 1.5,
            },
            {
                'name': 'Riesgo Financiero',
                'description': 'Riesgo de pérdidas financieras y problemas económicos',
                'weight': 2.2,
            },
        ]

        created_count = 0
        for category_data in categories:
            category, created = RiskCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'weight': category_data['weight'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Categoría creada: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Categoría ya existe: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Proceso completado: {created_count} nuevas categorías creadas')
        )
"""
Comando para crear las categorías de seguridad para el módulo de hoteles
"""
from django.core.management.base import BaseCommand
from apps.risk_hoteles.models import SecurityCategory


class Command(BaseCommand):
    help = 'Crea las categorías de seguridad para el módulo de hoteles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando categorías de seguridad para hoteles...'))
        
        # Limpiar categorías existentes si es necesario (automático)
        existing_count = SecurityCategory.objects.count()
        if existing_count > 0:
            SecurityCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Se eliminaron {existing_count} categorías existentes.'))
        
        # Definir las categorías de seguridad
        categories_data = [
            {
                'code': 'gestion_organizacion',
                'name': 'Gestión y Organización de la Seguridad',
                'description': 'Políticas, procedimientos y estructura organizacional de seguridad del hotel.',
                'order': 1,
                'icon': 'fas fa-cogs',
                'weight': 1.0
            },
            {
                'code': 'seguridad_externa',
                'name': 'Seguridad Externa',
                'description': 'Medidas de seguridad en el perímetro exterior y accesos principales del hotel.',
                'order': 2,
                'icon': 'fas fa-shield-alt',
                'weight': 1.2
            },
            {
                'code': 'seguridad_perimetral',
                'name': 'Seguridad Perimetral',
                'description': 'Control y vigilancia del perímetro del establecimiento hotelero.',
                'order': 3,
                'icon': 'fas fa-border-style',
                'weight': 1.1
            },
            {
                'code': 'seguridad_internas',
                'name': 'Seguridad en Áreas Internas',
                'description': 'Protección y control de acceso en áreas internas como lobby, pasillos y zonas comunes.',
                'order': 4,
                'icon': 'fas fa-home',
                'weight': 1.0
            },
            {
                'code': 'controles_accesos',
                'name': 'Controles de Accesos al Hotel',
                'description': 'Sistemas de control de acceso para huéspedes, personal y visitantes.',
                'order': 5,
                'icon': 'fas fa-key',
                'weight': 1.3
            },
            {
                'code': 'seguridad_habitaciones',
                'name': 'Seguridad en Habitaciones',
                'description': 'Medidas de seguridad específicas para las habitaciones de huéspedes.',
                'order': 6,
                'icon': 'fas fa-bed',
                'weight': 1.2
            },
            {
                'code': 'seguridad_activos',
                'name': 'Seguridad de Activos Críticos del Hotel',
                'description': 'Protección de activos valiosos como caja fuerte, equipos tecnológicos y documentos importantes.',
                'order': 7,
                'icon': 'fas fa-gem',
                'weight': 1.4
            },
            {
                'code': 'seguridad_parqueo',
                'name': 'Seguridad en Áreas de Parqueo',
                'description': 'Vigilancia y control de seguridad en parqueaderos y garajes del hotel.',
                'order': 8,
                'icon': 'fas fa-parking',
                'weight': 0.9
            },
            {
                'code': 'gestion_humana',
                'name': 'Seguridad en el Proceso de Gestión Humana',
                'description': 'Procedimientos de seguridad en la selección, contratación y gestión del personal.',
                'order': 9,
                'icon': 'fas fa-users',
                'weight': 1.1
            },
            {
                'code': 'seguridad_eventos',
                'name': 'Seguridad en Eventos',
                'description': 'Medidas de seguridad para eventos, conferencias y celebraciones en el hotel.',
                'order': 10,
                'icon': 'fas fa-calendar-alt',
                'weight': 1.0
            },
            {
                'code': 'seguridad_ayb',
                'name': 'Seguridad en AyB',
                'description': 'Seguridad en el área de Alimentos y Bebidas, incluyendo restaurantes, bares y cocinas.',
                'order': 11,
                'icon': 'fas fa-utensils',
                'weight': 1.1
            },
            {
                'code': 'seguridad_reservas',
                'name': 'Seguridad en Reservas',
                'description': 'Protección de datos y procedimientos seguros en el sistema de reservas.',
                'order': 12,
                'icon': 'fas fa-calendar-check',
                'weight': 1.0
            },
            {
                'code': 'seguridad_compras',
                'name': 'Seguridad en el Proceso de Compras',
                'description': 'Procedimientos de seguridad en la adquisición de bienes y servicios para el hotel.',
                'order': 13,
                'icon': 'fas fa-shopping-cart',
                'weight': 0.8
            },
            {
                'code': 'gestion_emergencias',
                'name': 'Seguridad y Gestión de Emergencias',
                'description': 'Planes de contingencia, evacuación y respuesta ante emergencias.',
                'order': 14,
                'icon': 'fas fa-exclamation-triangle',
                'weight': 1.5
            }
        ]
        
        # Crear las categorías
        created_count = 0
        updated_count = 0
        
        for category_data in categories_data:
            category, created = SecurityCategory.objects.get_or_create(
                code=category_data['code'],
                defaults=category_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Categoría creada: {category.name}')
                )
            else:
                # Actualizar datos existentes
                for key, value in category_data.items():
                    if key != 'code':  # No actualizar el código
                        setattr(category, key, value)
                category.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Categoría actualizada: {category.name}')
                )
        
        # Resumen final
        total_categories = SecurityCategory.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Proceso completado exitosamente!\n'
                f'📊 Estadísticas:\n'
                f'   • Categorías creadas: {created_count}\n'
                f'   • Categorías actualizadas: {updated_count}\n'
                f'   • Total en sistema: {total_categories}\n'
                f'\n✅ Todas las categorías de seguridad han sido configuradas correctamente.'
            )
        )
        
        # Mostrar lista final
        self.stdout.write('\n📋 Categorías configuradas:')
        categories = SecurityCategory.objects.all().order_by('order')
        for i, category in enumerate(categories, 1):
            self.stdout.write(f'   {i:2d}. {category.name}')
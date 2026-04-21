"""
Comando para actualizar los planes de suscripción con los datos definitivos
"""
from django.core.management.base import BaseCommand
from apps.subscriptions.models import Module, PlanType, Plan
from decimal import Decimal


class Command(BaseCommand):
    help = 'Actualiza los planes de suscripción con los datos definitivos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando actualización de planes...'))
        
        # Limpiar planes existentes
        Plan.objects.all().delete()
        PlanType.objects.all().delete()
        Module.objects.all().delete()
        
        # Crear módulos (usar nombres que coincidan con los decoradores en las vistas)
        modules_data = [
            {
                'name': 'risk_hoteles',
                'display_name': 'HOTELES',
                'description': 'Módulo de gestión y evaluación de riesgos para hoteles',
                'icon': 'fas fa-hotel',
                'color': '#e74c3c',
                'order': 1
            },
            {
                'name': 'risk_conjuntos',
                'display_name': 'CONJUNTOS',
                'description': 'Módulo de gestión y evaluación de riesgos para conjuntos residenciales',
                'icon': 'fas fa-building',
                'color': '#3498db',
                'order': 2
            },
            {
                'name': 'security_probabilistic',
                'display_name': 'Security Probabilistic',
                'description': 'Módulo de análisis probabilístico de seguridad',
                'icon': 'fas fa-chart-line',
                'color': '#9b59b6',
                'order': 3
            }
        ]
        
        modules = {}
        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                name=module_data['name'],
                defaults=module_data
            )
            modules[module_data['name']] = module
            action = 'Creado' if created else 'Actualizado'
            self.stdout.write(f'{action} módulo: {module.display_name}')
        
        # Crear tipos de planes
        plan_types_data = [
            {'name': 'Demo', 'description': 'Plan gratuito de demostración', 'order': 1},
            {'name': 'Personal', 'description': 'Plan personal básico', 'order': 2},
            {'name': 'Consultoria', 'description': 'Plan de consultoría', 'order': 3},
            {'name': 'Plan Ejecutivo', 'description': 'Plan ejecutivo avanzado', 'order': 4},
            {'name': 'Plan Corporativo', 'description': 'Plan corporativo empresarial', 'order': 5},
            {'name': 'Enterprise', 'description': 'Plan empresarial', 'order': 6},
            {'name': 'Enterprise Plus', 'description': 'Plan empresarial premium', 'order': 7},
        ]
        
        plan_types = {}
        for plan_type_data in plan_types_data:
            plan_type, created = PlanType.objects.get_or_create(
                name=plan_type_data['name'],
                defaults=plan_type_data
            )
            plan_types[plan_type_data['name']] = plan_type
            action = 'Creado' if created else 'Actualizado'
            self.stdout.write(f'{action} tipo de plan: {plan_type.name}')
        
        # Definir planes por módulo
        plans_data = [
            # MÓDULO HOTELES
            {
                'module': 'risk_hoteles',
                'plan_type': 'Demo',
                'name': 'Plan Demo - Hoteles',
                'description': 'Plan gratuito de demostración para hoteles',
                'yearly_price': Decimal('0.00'),
                'trial_days': 15,
                'max_users': 1,
                'max_reports': 2,
                'max_storage_gb': 1,
                'features': {
                    'evaluaciones': 2,
                    'crear_evaluador': 0,
                    'soporte': 'Básico'
                },
                'is_featured': False,
                'order': 1
            },
            {
                'module': 'risk_hoteles',
                'plan_type': 'Consultoria',
                'name': 'Plan Consultoría - Hoteles',
                'description': 'Plan de consultoría especializada para hoteles',
                'yearly_price': Decimal('450000.00'),
                'trial_days': 15,
                'max_users': 1,
                'max_reports': -1,  # Ilimitadas
                'max_storage_gb': 5,
                'features': {
                    'evaluaciones': 'Ilimitadas',
                    'crear_evaluador': 0,
                    'soporte': 'Básico'
                },
                'is_featured': False,
                'order': 2
            },
            {
                'module': 'risk_hoteles',
                'plan_type': 'Plan Ejecutivo',
                'name': 'Plan Ejecutivo - Hoteles',
                'description': 'Plan ejecutivo para hoteles con funcionalidades avanzadas',
                'yearly_price': Decimal('700000.00'),
                'trial_days': 15,
                'max_users': 1,
                'max_reports': -1,  # Ilimitadas
                'max_storage_gb': 10,
                'features': {
                    'evaluaciones': 'Ilimitadas',
                    'crear_evaluador': 0,
                    'soporte': 'Email'
                },
                'is_featured': True,
                'order': 3
            },
            {
                'module': 'risk_hoteles',
                'plan_type': 'Plan Corporativo',
                'name': 'Plan Corporativo - Hoteles',
                'description': 'Plan corporativo para cadenas hoteleras',
                'yearly_price': Decimal('3500000.00'),
                'trial_days': 15,
                'max_users': 10,
                'max_reports': -1,  # Ilimitadas
                'max_storage_gb': 50,
                'features': {
                    'evaluaciones': 'Ilimitadas',
                    'crear_evaluador': 20,
                    'soporte': 'Avanzado'
                },
                'is_featured': False,
                'order': 4
            },
            
            # MÓDULO CONJUNTOS
            {
                'module': 'risk_conjuntos',
                'plan_type': 'Demo',
                'name': 'Plan Demo - Conjuntos',
                'description': 'Plan gratuito de demostración para conjuntos',
                'yearly_price': Decimal('0.00'),
                'trial_days': 15,
                'max_users': 1,
                'max_reports': 1,
                'max_storage_gb': 1,
                'features': {
                    'evaluaciones': 1,
                    'crear_evaluador': 0,
                    'soporte': 'Básico'
                },
                'is_featured': False,
                'order': 1
            },
            {
                'module': 'risk_conjuntos',
                'plan_type': 'Personal',
                'name': 'Plan Personal - Conjuntos',
                'description': 'Plan personal para administradores de conjuntos',
                'yearly_price': Decimal('120000.00'),
                'trial_days': 15,
                'max_users': 1,
                'max_reports': -1,  # Ilimitadas por año
                'max_storage_gb': 2,
                'features': {
                    'evaluaciones': 'Ilimitadas / Año',
                    'crear_evaluador': 0,
                    'soporte': 'Email'
                },
                'is_featured': False,
                'order': 2
            },
            {
                'module': 'risk_conjuntos',
                'plan_type': 'Consultoria',
                'name': 'Plan Consultoría - Conjuntos',
                'description': 'Plan de consultoría especializada para conjuntos',
                'yearly_price': Decimal('720000.00'),
                'trial_days': 15,
                'max_users': 7,
                'max_reports': -1,  # Ilimitadas por año
                'max_storage_gb': 10,
                'features': {
                    'evaluaciones': 'Ilimitadas / Año',
                    'crear_evaluador': 2,
                    'soporte': 'Especializado'
                },
                'is_featured': True,
                'order': 3
            },
            {
                'module': 'risk_conjuntos',
                'plan_type': 'Enterprise',
                'name': 'Plan Enterprise - Conjuntos',
                'description': 'Plan empresarial para grandes conjuntos',
                'yearly_price': Decimal('1320000.00'),
                'trial_days': 15,
                'max_users': 15,
                'max_reports': -1,  # Ilimitadas
                'max_storage_gb': 25,
                'features': {
                    'evaluaciones': 'Ilimitadas',
                    'crear_evaluador': 5,
                    'soporte': '24h /7'
                },
                'is_featured': False,
                'order': 4
            },
            {
                'module': 'risk_conjuntos',
                'plan_type': 'Enterprise Plus',
                'name': 'Plan Enterprise Plus - Conjuntos',
                'description': 'Plan empresarial premium para múltiples conjuntos',
                'yearly_price': Decimal('1920000.00'),
                'trial_days': 15,
                'max_users': 20,
                'max_reports': -1,  # Ilimitadas
                'max_storage_gb': 50,
                'features': {
                    'evaluaciones': 'Ilimitadas',
                    'crear_evaluador': 20,
                    'soporte': 'Prioridad'
                },
                'is_featured': False,
                'order': 5
            },
            
            # MÓDULO SECURITY PROBABILISTIC
            {
                'module': 'security_probabilistic',
                'plan_type': 'Demo',
                'name': 'Plan Demo - Security Probabilistic',
                'description': 'Plan gratuito de demostración para análisis probabilístico',
                'yearly_price': Decimal('0.00'),
                'trial_days': 15,
                'max_users': 1,
                'max_reports': 2,
                'max_storage_gb': 1,
                'features': {
                    'evaluaciones': 2,
                    'crear_evaluador': 0,
                    'soporte': 'Básico'
                },
                'is_featured': False,
                'order': 1
            },
            {
                'module': 'security_probabilistic',
                'plan_type': 'Consultoria',
                'name': 'Plan Consultoría - Security Probabilistic',
                'description': 'Plan de consultoría para análisis probabilístico',
                'yearly_price': Decimal('450000.00'),
                'trial_days': 15,
                'max_users': 1,
                'max_reports': -1,  # Ilimitadas
                'max_storage_gb': 5,
                'features': {
                    'evaluaciones': 'Ilimitadas',
                    'crear_evaluador': 0,
                    'soporte': 'Básico'
                },
                'is_featured': False,
                'order': 2
            },
            {
                'module': 'security_probabilistic',
                'plan_type': 'Plan Ejecutivo',
                'name': 'Plan Ejecutivo - Security Probabilistic',
                'description': 'Plan ejecutivo para análisis probabilístico avanzado',
                'yearly_price': Decimal('700000.00'),
                'trial_days': 15,
                'max_users': 1,
                'max_reports': -1,  # Ilimitadas
                'max_storage_gb': 10,
                'features': {
                    'evaluaciones': 'Ilimitadas',
                    'crear_evaluador': 0,
                    'soporte': 'Email'
                },
                'is_featured': True,
                'order': 3
            },
            {
                'module': 'security_probabilistic',
                'plan_type': 'Plan Corporativo',
                'name': 'Plan Corporativo - Security Probabilistic',
                'description': 'Plan corporativo para análisis probabilístico empresarial',
                'yearly_price': Decimal('3500000.00'),
                'trial_days': 15,
                'max_users': 10,
                'max_reports': -1,  # Ilimitadas
                'max_storage_gb': 50,
                'features': {
                    'evaluaciones': 'Ilimitadas',
                    'crear_evaluador': 20,
                    'soporte': 'Avanzado'
                },
                'is_featured': False,
                'order': 4
            }
        ]
        
        # Crear planes
        for plan_data in plans_data:
            module = modules[plan_data.pop('module')]
            plan_type = plan_types[plan_data.pop('plan_type')]
            
            plan, created = Plan.objects.get_or_create(
                module=module,
                plan_type=plan_type,
                defaults={
                    **plan_data,
                    'monthly_price': plan_data['yearly_price'] / 12 if plan_data['yearly_price'] > 0 else Decimal('0.00'),
                    'quarterly_price': plan_data['yearly_price'] / 4 if plan_data['yearly_price'] > 0 else Decimal('0.00'),
                }
            )
            
            action = 'Creado' if created else 'Actualizado'
            self.stdout.write(
                f'{action} plan: {plan.module.display_name} - {plan.plan_type.name} '
                f'(${plan.yearly_price:,.0f}/año)'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Actualización completada exitosamente!\n'
                f'📊 Módulos: {Module.objects.count()}\n'
                f'📋 Tipos de planes: {PlanType.objects.count()}\n'
                f'💼 Planes totales: {Plan.objects.count()}'
            )
        )
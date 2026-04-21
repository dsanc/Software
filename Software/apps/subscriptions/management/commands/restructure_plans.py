from django.core.management.base import BaseCommand
from django.db import transaction
from apps.subscriptions.models import Module, Plan, PlanType, Subscription

class Command(BaseCommand):
    help = 'Actualiza los planes según la estructura definida'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Primero, eliminar todas las suscripciones y planes existentes
            self.stdout.write('Eliminando suscripciones y planes existentes...')
            Subscription.objects.all().delete()
            Plan.objects.all().delete()
            PlanType.objects.all().delete()
            
            # Crear tipos de planes
            self.stdout.write('Creando tipos de planes...')
            plan_types = {
                'consultoria': PlanType.objects.create(name='Consultoría', order=1),
                'personal': PlanType.objects.create(name='Personal', order=2),
                'plan_ejecutivo': PlanType.objects.create(name='Plan Ejecutivo', order=3),
                'enterprise': PlanType.objects.create(name='Enterprise', order=4),
                'enterprise_plus': PlanType.objects.create(name='Enterprise Plus', order=5),
                'plan_corporativo': PlanType.objects.create(name='Plan Corporativo', order=6),
            }
            
            # Obtener módulos
            try:
                module_hoteles = Module.objects.get(name='risk_hoteles')
                module_conjuntos = Module.objects.get(name='risk_conjuntos')
                module_seguridad = Module.objects.get(name='security_probabilistic')
            except Module.DoesNotExist as e:
                self.stdout.write(
                    self.style.ERROR(f'Error: No se encontró el módulo {e}')
                )
                return
            
            # Crear planes para HOTELES
            self.stdout.write('Creando planes para HOTELES...')
            hoteles_plans = [
                {
                    'plan_type': plan_types['consultoria'],
                    'name': 'HOTELES - Consultoría',
                    'yearly_price': 450000,
                    'max_users': 1,
                    'max_reports': -1,  # Ilimitadas
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 0},
                    'features': {'soporte': 'Básico'},
                    'order': 1
                },
                {
                    'plan_type': plan_types['plan_ejecutivo'],
                    'name': 'HOTELES - Plan Ejecutivo',
                    'yearly_price': 700000,
                    'max_users': 1,
                    'max_reports': -1,  # Ilimitadas
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 0},
                    'features': {'soporte': 'Email'},
                    'order': 2
                },
                {
                    'plan_type': plan_types['plan_corporativo'],
                    'name': 'HOTELES - Plan Corporativo',
                    'yearly_price': 3500000,
                    'max_users': 10,
                    'max_reports': -1,  # Ilimitadas
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 20},
                    'features': {'soporte': 'Avanzado'},
                    'order': 3
                }
            ]
            
            for plan_data in hoteles_plans:
                Plan.objects.create(
                    module=module_hoteles,
                    plan_type=plan_data['plan_type'],
                    name=plan_data['name'],
                    description=f"Plan {plan_data['plan_type'].name} para análisis de riesgo hotelero",
                    yearly_price=plan_data['yearly_price'],
                    monthly_price=plan_data['yearly_price'] / 12,
                    quarterly_price=plan_data['yearly_price'] / 4,
                    max_users=plan_data['max_users'],
                    max_reports=plan_data['max_reports'],
                    limits=plan_data['limits'],
                    features=plan_data['features'],
                    order=plan_data['order'],
                    is_active=True
                )
                self.stdout.write(f"  ✓ {plan_data['name']}")
            
            # Crear planes para CONJUNTOS
            self.stdout.write('Creando planes para CONJUNTOS...')
            conjuntos_plans = [
                {
                    'plan_type': plan_types['personal'],
                    'name': 'CONJUNTOS - Personal',
                    'yearly_price': 120000,
                    'max_users': 1,
                    'max_reports': -1,  # Ilimitadas por año
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 0, 'periodo': 'anual'},
                    'features': {'soporte': 'Email'},
                    'order': 1
                },
                {
                    'plan_type': plan_types['consultoria'],
                    'name': 'CONJUNTOS - Consultoría',
                    'yearly_price': 720000,
                    'max_users': 7,
                    'max_reports': -1,  # Ilimitadas por año
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 2, 'periodo': 'anual'},
                    'features': {'soporte': 'Especializado'},
                    'order': 2
                },
                {
                    'plan_type': plan_types['enterprise'],
                    'name': 'CONJUNTOS - Enterprise',
                    'yearly_price': 1320000,
                    'max_users': 15,
                    'max_reports': -1,  # Ilimitadas
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 5},
                    'features': {'soporte': '24h/7'},
                    'order': 3
                },
                {
                    'plan_type': plan_types['enterprise_plus'],
                    'name': 'CONJUNTOS - Enterprise Plus',
                    'yearly_price': 1920000,
                    'max_users': 20,
                    'max_reports': -1,  # Ilimitadas
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 20},
                    'features': {'soporte': 'Prioridad'},
                    'order': 4
                }
            ]
            
            for plan_data in conjuntos_plans:
                Plan.objects.create(
                    module=module_conjuntos,
                    plan_type=plan_data['plan_type'],
                    name=plan_data['name'],
                    description=f"Plan {plan_data['plan_type'].name} para análisis de riesgo en conjuntos residenciales",
                    yearly_price=plan_data['yearly_price'],
                    monthly_price=plan_data['yearly_price'] / 12,
                    quarterly_price=plan_data['yearly_price'] / 4,
                    max_users=plan_data['max_users'],
                    max_reports=plan_data['max_reports'],
                    limits=plan_data['limits'],
                    features=plan_data['features'],
                    order=plan_data['order'],
                    is_active=True
                )
                self.stdout.write(f"  ✓ {plan_data['name']}")
            
            # Crear planes para SEGURIDAD PROBABILÍSTICA
            self.stdout.write('Creando planes para SEGURIDAD PROBABILÍSTICA...')
            seguridad_plans = [
                {
                    'plan_type': plan_types['consultoria'],
                    'name': 'SEGURIDAD PROBABILÍSTICA - Consultoría',
                    'yearly_price': 450000,
                    'max_users': 1,
                    'max_reports': -1,  # Ilimitadas
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 0},
                    'features': {'soporte': 'Básico'},
                    'order': 1
                },
                {
                    'plan_type': plan_types['plan_ejecutivo'],
                    'name': 'SEGURIDAD PROBABILÍSTICA - Plan Ejecutivo',
                    'yearly_price': 700000,
                    'max_users': 1,
                    'max_reports': -1,  # Ilimitadas
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 0},
                    'features': {'soporte': 'Email'},
                    'order': 2
                },
                {
                    'plan_type': plan_types['plan_corporativo'],
                    'name': 'SEGURIDAD PROBABILÍSTICA - Plan Corporativo',
                    'yearly_price': 3500000,
                    'max_users': 10,
                    'max_reports': -1,  # Ilimitadas
                    'limits': {'evaluaciones': -1, 'crear_evaluador': 20},
                    'features': {'soporte': 'Avanzado'},
                    'order': 3
                }
            ]
            
            for plan_data in seguridad_plans:
                Plan.objects.create(
                    module=module_seguridad,
                    plan_type=plan_data['plan_type'],
                    name=plan_data['name'],
                    description=f"Plan {plan_data['plan_type'].name} para evaluación de seguridad probabilística",
                    yearly_price=plan_data['yearly_price'],
                    monthly_price=plan_data['yearly_price'] / 12,
                    quarterly_price=plan_data['yearly_price'] / 4,
                    max_users=plan_data['max_users'],
                    max_reports=plan_data['max_reports'],
                    limits=plan_data['limits'],
                    features=plan_data['features'],
                    order=plan_data['order'],
                    is_active=True
                )
                self.stdout.write(f"  ✓ {plan_data['name']}")
            
            # Resumen final
            total_plans = Plan.objects.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n¡Actualización completada!'
                    f'\nTotal planes creados: {total_plans}'
                    f'\n- HOTELES: 3 planes'
                    f'\n- CONJUNTOS: 4 planes'
                    f'\n- SEGURIDAD PROBABILÍSTICA: 3 planes'
                    f'\n\nNOTA: Todas las suscripciones anteriores fueron eliminadas.'
                    f'\nDeberás reasignar las suscripciones a los usuarios.'
                )
            )
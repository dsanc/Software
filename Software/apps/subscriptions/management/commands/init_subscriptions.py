"""
Comando para inicializar los datos básicos del sistema de suscripciones
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.subscriptions.models import Module, PlanType, Plan
from apps.subscriptions.demo_service import DemoService


class Command(BaseCommand):
    help = 'Inicializa los datos básicos del sistema de suscripciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la creación incluso si ya existen datos',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Limpiar todos los datos existentes antes de crear',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Inicializando sistema de suscripciones...\n')
        )

        # Limpiar datos existentes si se solicita
        if options.get('clean', False):
            self._clean_existing_data()

        # Crear plan demo
        self._create_demo_plan()

        # Crear módulos básicos del sistema
        self._create_system_modules(options.get('force', False))

        # Crear tipos de planes
        self._create_plan_types()

        # Crear planes básicos
        self._create_basic_plans()

        self.stdout.write(
            self.style.SUCCESS('\n✅ Sistema de suscripciones inicializado exitosamente!')
        )

    def _clean_existing_data(self):
        """Limpiar datos existentes de planes y tipos"""
        self.stdout.write(
            self.style.WARNING('🧹 Limpiando datos existentes...')
        )
        
        try:
            # Eliminar suscripciones activas (solo para limpieza de desarrollo)
            from apps.subscriptions.models import Subscription
            subs_deleted = Subscription.objects.all().delete()[0]
            
            # Eliminar planes existentes
            plans_deleted = Plan.objects.all().delete()[0]
            
            # Eliminar tipos de planes (excepto Demo si existe)
            plan_types_deleted = PlanType.objects.exclude(name='Demo').delete()[0]
            
            # Eliminar módulos (excepto demo)
            modules_deleted = Module.objects.exclude(name='demo').delete()[0]
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Limpieza completada:\n'
                    f'   - Suscripciones: {subs_deleted}\n'
                    f'   - Planes: {plans_deleted}\n' 
                    f'   - Tipos de plan: {plan_types_deleted}\n'
                    f'   - Módulos: {modules_deleted}\n'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante limpieza: {e}')
            )

    def _create_demo_plan(self):
        """Crear el plan demo usando el servicio"""
        try:
            demo_plan = DemoService.get_or_create_demo_plan()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Plan demo: {demo_plan.name}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando plan demo: {e}')
            )

    def _create_system_modules(self, force=False):
        """Crear módulos principales del sistema"""
        modules_data = [
            {
                'name': 'risk_conjuntos',
                'display_name': 'Análisis de Riesgo - Conjuntos',
                'description': 'Herramientas avanzadas para análisis de riesgo por conjuntos',
                'icon': 'fas fa-shield-alt',
                'color': '#dc3545',
                'order': 1
            },
            {
                'name': 'risk_hoteles',
                'display_name': 'Análisis de Riesgo - Hoteles',
                'description': 'Análisis especializado de riesgo para la industria hotelera',
                'icon': 'fas fa-hotel',
                'color': '#fd7e14',
                'order': 2
            },
            {
                'name': 'security_probabilistic',
                'display_name': 'Seguridad Probabilística',
                'description': 'Modelos probabilísticos avanzados para análisis de seguridad',
                'icon': 'fas fa-lock',
                'color': '#6f42c1',
                'order': 3
            }
        ]

        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                name=module_data['name'],
                defaults=module_data
            )
            
            status = '✅ Creado' if created else '🔄 Existía'
            self.stdout.write(f'{status} Módulo: {module.display_name}')

    def _create_plan_types(self):
        """Crear todos los tipos de planes según especificación"""
        plan_types_data = [
            {'name': 'Demo', 'description': 'Plan gratuito de demostración', 'order': 1},
            {'name': 'Personal', 'description': 'Plan personal para usuarios individuales', 'order': 2},
            {'name': 'Consultoria', 'description': 'Plan de consultoría especializada', 'order': 3},
            {'name': 'Plan Ejecutivo', 'description': 'Plan ejecutivo para empresas medianas', 'order': 4},
            {'name': 'Plan Corporativo', 'description': 'Plan corporativo para grandes empresas', 'order': 5},
            {'name': 'Enterprise', 'description': 'Plan enterprise para organizaciones', 'order': 6},
            {'name': 'Enterprise Plus', 'description': 'Plan enterprise plus con máximas funciones', 'order': 7},
        ]

        for plan_type_data in plan_types_data:
            plan_type, created = PlanType.objects.get_or_create(
                name=plan_type_data['name'],
                defaults=plan_type_data
            )
            
            status = '✅ Creado' if created else '🔄 Existía'
            self.stdout.write(f'{status} Tipo de Plan: {plan_type.name}')

    def _create_basic_plans(self):
        """Crear planes específicos según la tabla de especificaciones"""
        try:
            plans_created = 0

            # Crear planes para HOTELES
            plans_created += self._create_hoteles_plans()
            
            # Crear planes para CONJUNTOS  
            plans_created += self._create_conjuntos_plans()
            
            # Crear planes para Security Probabilistic
            plans_created += self._create_security_plans()

            self.stdout.write(
                self.style.SUCCESS(f'\n📊 Total de planes creados: {plans_created}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando planes: {e}')
            )

    def _create_hoteles_plans(self):
        """Crear planes específicos para módulo HOTELES"""
        try:
            hoteles_module = Module.objects.get(name='risk_hoteles')
            plans_created = 0

            # Planes para HOTELES según especificación
            hoteles_plans = [
                {
                    'type': 'Demo',
                    'yearly_price': 0,
                    'max_users': 1,
                    'evaluaciones': 2,
                    'crear_evaluador': 0,
                    'soporte': 'Basico'
                },
                {
                    'type': 'Consultoria',
                    'yearly_price': 450000,
                    'max_users': 1,
                    'evaluaciones': -1,  # Ilimitadas
                    'crear_evaluador': 0,
                    'soporte': 'Basico'
                },
                {
                    'type': 'Plan Ejecutivo',
                    'yearly_price': 700000,
                    'max_users': 1,
                    'evaluaciones': -1,  # Ilimitadas
                    'crear_evaluador': 0,
                    'soporte': 'Email'
                },
                {
                    'type': 'Plan Corporativo',
                    'yearly_price': 3500000,
                    'max_users': 10,
                    'evaluaciones': -1,  # Ilimitadas
                    'crear_evaluador': 20,
                    'soporte': 'Avanzado'
                }
            ]

            for plan_config in hoteles_plans:
                plan_type = PlanType.objects.get(name=plan_config['type'])
                
                plan_data = {
                    'name': f"HOTELES - {plan_config['type']}",
                    'description': f"Plan {plan_config['type']} para análisis de riesgo hotelero",
                    'monthly_price': 0 if plan_config['yearly_price'] == 0 else plan_config['yearly_price'] // 12,
                    'quarterly_price': 0 if plan_config['yearly_price'] == 0 else plan_config['yearly_price'] // 4,
                    'yearly_price': plan_config['yearly_price'],
                    'trial_days': 30 if plan_config['type'] == 'Demo' else 14,
                    'max_users': plan_config['max_users'],
                    'max_reports': plan_config['evaluaciones'],
                    'max_storage_gb': 1 if plan_config['type'] == 'Demo' else 10,
                    'features': self._get_features_by_support(plan_config['soporte']),
                    'limits': {
                        'evaluaciones_mes': plan_config['evaluaciones'],
                        'crear_evaluadores': plan_config['crear_evaluador'],
                        'tipo_soporte': plan_config['soporte']
                    },
                    'is_active': True,
                    'is_featured': plan_config['type'] == 'Plan Ejecutivo',
                    'order': ['Demo', 'Consultoria', 'Plan Ejecutivo', 'Plan Corporativo'].index(plan_config['type']) + 1
                }

                plan, created = Plan.objects.get_or_create(
                    module=hoteles_module,
                    plan_type=plan_type,
                    defaults=plan_data
                )

                if created:
                    plans_created += 1
                    status = '✅ Creado'
                else:
                    status = '🔄 Existía'
                
                self.stdout.write(f'{status} Plan HOTELES: {plan.name} (${plan_config["yearly_price"]:,}/año)')

            return plans_created

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creando planes HOTELES: {e}'))
            return 0

    def _create_conjuntos_plans(self):
        """Crear planes específicos para módulo CONJUNTOS"""
        try:
            conjuntos_module = Module.objects.get(name='risk_conjuntos')
            plans_created = 0

            # Planes para CONJUNTOS según especificación
            conjuntos_plans = [
                {
                    'type': 'Demo',
                    'yearly_price': 0,
                    'max_users': 1,
                    'evaluaciones': 1,
                    'crear_evaluador': 0,
                    'soporte': 'Basico'
                },
                {
                    'type': 'Personal',
                    'yearly_price': 120000,
                    'max_users': 1,
                    'evaluaciones': -1,  # Ilimitadas / Año
                    'crear_evaluador': 0,
                    'soporte': 'Email'
                },
                {
                    'type': 'Consultoria',
                    'yearly_price': 720000,
                    'max_users': 7,
                    'evaluaciones': -1,  # Ilimitadas / Año
                    'crear_evaluador': 2,
                    'soporte': 'Especializado'
                },
                {
                    'type': 'Enterprise',
                    'yearly_price': 1320000,
                    'max_users': 15,
                    'evaluaciones': -1,  # Ilimitadas
                    'crear_evaluador': 5,
                    'soporte': '24h /7'
                },
                {
                    'type': 'Enterprise Plus',
                    'yearly_price': 1920000,
                    'max_users': 20,
                    'evaluaciones': -1,  # Ilimitadas
                    'crear_evaluador': 20,
                    'soporte': 'Prioridad'
                }
            ]

            for plan_config in conjuntos_plans:
                plan_type = PlanType.objects.get(name=plan_config['type'])
                
                plan_data = {
                    'name': f"CONJUNTOS - {plan_config['type']}",
                    'description': f"Plan {plan_config['type']} para análisis de riesgo por conjuntos",
                    'monthly_price': 0 if plan_config['yearly_price'] == 0 else plan_config['yearly_price'] // 12,
                    'quarterly_price': 0 if plan_config['yearly_price'] == 0 else plan_config['yearly_price'] // 4,
                    'yearly_price': plan_config['yearly_price'],
                    'trial_days': 30 if plan_config['type'] == 'Demo' else 14,
                    'max_users': plan_config['max_users'],
                    'max_reports': plan_config['evaluaciones'],
                    'max_storage_gb': 1 if plan_config['type'] == 'Demo' else 20,
                    'features': self._get_features_by_support(plan_config['soporte']),
                    'limits': {
                        'evaluaciones_mes': plan_config['evaluaciones'],
                        'crear_evaluadores': plan_config['crear_evaluador'],
                        'tipo_soporte': plan_config['soporte']
                    },
                    'is_active': True,
                    'is_featured': plan_config['type'] == 'Enterprise',
                    'order': ['Demo', 'Personal', 'Consultoria', 'Enterprise', 'Enterprise Plus'].index(plan_config['type']) + 1
                }

                plan, created = Plan.objects.get_or_create(
                    module=conjuntos_module,
                    plan_type=plan_type,
                    defaults=plan_data
                )

                if created:
                    plans_created += 1
                    status = '✅ Creado'
                else:
                    status = '🔄 Existía'
                
                self.stdout.write(f'{status} Plan CONJUNTOS: {plan.name} (${plan_config["yearly_price"]:,}/año)')

            return plans_created

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creando planes CONJUNTOS: {e}'))
            return 0

    def _create_security_plans(self):
        """Crear planes específicos para módulo Security Probabilistic"""
        try:
            security_module = Module.objects.get(name='security_probabilistic')
            plans_created = 0

            # Planes para Security Probabilistic según especificación (igual que HOTELES)
            security_plans = [
                {
                    'type': 'Demo',
                    'yearly_price': 0,
                    'max_users': 1,
                    'evaluaciones': 2,
                    'crear_evaluador': 0,
                    'soporte': 'Basico'
                },
                {
                    'type': 'Consultoria',
                    'yearly_price': 450000,
                    'max_users': 1,
                    'evaluaciones': -1,  # Ilimitadas
                    'crear_evaluador': 0,
                    'soporte': 'Basico'
                },
                {
                    'type': 'Plan Ejecutivo',
                    'yearly_price': 700000,
                    'max_users': 1,
                    'evaluaciones': -1,  # Ilimitadas
                    'crear_evaluador': 0,
                    'soporte': 'Email'
                },
                {
                    'type': 'Plan Corporativo',
                    'yearly_price': 3500000,
                    'max_users': 10,
                    'evaluaciones': -1,  # Ilimitadas
                    'crear_evaluador': 20,
                    'soporte': 'Avanzado'
                }
            ]

            for plan_config in security_plans:
                plan_type = PlanType.objects.get(name=plan_config['type'])
                
                plan_data = {
                    'name': f"SECURITY - {plan_config['type']}",
                    'description': f"Plan {plan_config['type']} para seguridad probabilística",
                    'monthly_price': 0 if plan_config['yearly_price'] == 0 else plan_config['yearly_price'] // 12,
                    'quarterly_price': 0 if plan_config['yearly_price'] == 0 else plan_config['yearly_price'] // 4,
                    'yearly_price': plan_config['yearly_price'],
                    'trial_days': 30 if plan_config['type'] == 'Demo' else 14,
                    'max_users': plan_config['max_users'],
                    'max_reports': plan_config['evaluaciones'],
                    'max_storage_gb': 1 if plan_config['type'] == 'Demo' else 15,
                    'features': self._get_features_by_support(plan_config['soporte']),
                    'limits': {
                        'evaluaciones_mes': plan_config['evaluaciones'],
                        'crear_evaluadores': plan_config['crear_evaluador'],
                        'tipo_soporte': plan_config['soporte']
                    },
                    'is_active': True,
                    'is_featured': plan_config['type'] == 'Plan Ejecutivo',
                    'order': ['Demo', 'Consultoria', 'Plan Ejecutivo', 'Plan Corporativo'].index(plan_config['type']) + 1
                }

                plan, created = Plan.objects.get_or_create(
                    module=security_module,
                    plan_type=plan_type,
                    defaults=plan_data
                )

                if created:
                    plans_created += 1
                    status = '✅ Creado'
                else:
                    status = '🔄 Existía'
                
                self.stdout.write(f'{status} Plan SECURITY: {plan.name} (${plan_config["yearly_price"]:,}/año)')

            return plans_created

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creando planes SECURITY: {e}'))
            return 0

    def _get_features_by_support(self, soporte_type):
        """Obtener características según el tipo de soporte"""
        base_features = {
            'basic_access': True,
            'reports': True,
            'export_pdf': True,
        }

        if soporte_type == 'Basico':
            return {
                **base_features,
                'email_support': True,
                'watermark': True,
                'advanced_features': False,
                'priority_support': False,
                'phone_support': False,
                'dedicated_support': False
            }
        elif soporte_type == 'Email':
            return {
                **base_features,
                'email_support': True,
                'export_excel': True,
                'watermark': False,
                'advanced_features': True,
                'priority_support': False,
                'phone_support': False,
                'dedicated_support': False
            }
        elif soporte_type == 'Especializado':
            return {
                **base_features,
                'email_support': True,
                'export_excel': True,
                'export_powerpoint': True,
                'watermark': False,
                'advanced_features': True,
                'priority_support': True,
                'phone_support': False,
                'dedicated_support': True
            }
        elif soporte_type == 'Avanzado':
            return {
                **base_features,
                'email_support': True,
                'phone_support': True,
                'export_excel': True,
                'export_powerpoint': True,
                'watermark': False,
                'advanced_features': True,
                'priority_support': True,
                'dedicated_support': True,
                'custom_branding': True
            }
        elif soporte_type == '24h /7':
            return {
                **base_features,
                'email_support': True,
                'phone_support': True,
                'export_excel': True,
                'export_powerpoint': True,
                'watermark': False,
                'advanced_features': True,
                'priority_support': True,
                'dedicated_support': True,
                'custom_branding': True,
                'api_access': True,
                'support_24_7': True
            }
        elif soporte_type == 'Prioridad':
            return {
                **base_features,
                'email_support': True,
                'phone_support': True,
                'export_excel': True,
                'export_powerpoint': True,
                'watermark': False,
                'advanced_features': True,
                'priority_support': True,
                'dedicated_support': True,
                'custom_branding': True,
                'api_access': True,
                'support_24_7': True,
                'priority_queue': True,
                'account_manager': True
            }
        else:
            return base_features
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.subscriptions.models import Module, Plan, PlanType, Subscription

User = get_user_model()

class Command(BaseCommand):
    help = 'Asigna todas las suscripciones de módulos específicos a un usuario'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email del usuario')
        parser.add_argument(
            '--modules', 
            nargs='+', 
            default=['risk_hoteles', 'risk_conjuntos', 'security_probabilistic'],
            help='Módulos a asignar (por defecto: risk_hoteles, risk_conjuntos, security_probabilistic)'
        )
        parser.add_argument(
            '--duration-months', 
            type=int, 
            default=12, 
            help='Duración de la suscripción en meses (por defecto: 12)'
        )

    def handle(self, *args, **options):
        email = options['email']
        modules_names = options['modules']
        duration_months = options['duration_months']
        
        try:
            # Buscar o crear el usuario
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': email.split('@')[0].title(),
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario creado: {email}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario encontrado: {email}')
                )

            # Crear o encontrar los módulos si no existen
            modules_created = self.ensure_modules_exist(modules_names)
            
            # Buscar todos los planes de los módulos especificados
            modules = Module.objects.filter(name__in=modules_names)
            if not modules.exists():
                self.stdout.write(
                    self.style.ERROR(f'No se encontraron módulos con nombres: {modules_names}')
                )
                return

            # Crear planes si no existen
            plans_created = self.ensure_plans_exist(modules)
            
            total_assigned = 0
            start_date = timezone.now()
            end_date = start_date + timedelta(days=duration_months * 30)
            
            # Asignar suscripciones para cada módulo
            for module in modules:
                plans = Plan.objects.filter(module=module, is_active=True)
                
                if not plans.exists():
                    self.stdout.write(
                        self.style.WARNING(f'No se encontraron planes para el módulo: {module.display_name}')
                    )
                    continue
                
                for plan in plans:
                    # Verificar si ya existe una suscripción
                    existing_subscription = Subscription.objects.filter(
                        user=user,
                        plan=plan
                    ).first()
                    
                    if existing_subscription:
                        # Actualizar la suscripción existente
                        existing_subscription.status = 'active'
                        existing_subscription.start_date = start_date
                        existing_subscription.end_date = end_date
                        existing_subscription.save()
                        
                        self.stdout.write(
                            self.style.WARNING(f'Suscripción actualizada: {plan}')
                        )
                    else:
                        # Crear nueva suscripción
                        subscription = Subscription.objects.create(
                            user=user,
                            plan=plan,
                            billing_cycle='yearly',
                            start_date=start_date,
                            end_date=end_date,
                            status='active',
                            is_trial=False
                        )
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'Suscripción creada: {plan}')
                        )
                        total_assigned += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n¡Proceso completado!'
                    f'\nUsuario: {email}'
                    f'\nSuscripciones asignadas/actualizadas: {total_assigned}'
                    f'\nDuración: {duration_months} meses'
                    f'\nFecha inicio: {start_date.strftime("%Y-%m-%d %H:%M")}'
                    f'\nFecha fin: {end_date.strftime("%Y-%m-%d %H:%M")}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )

    def ensure_modules_exist(self, module_names):
        """Crea los módulos si no existen"""
        module_configs = {
            'risk_hoteles': {
                'display_name': 'Análisis de Riesgo - Hoteles',
                'description': 'Módulo especializado en análisis y gestión de riesgos para la industria hotelera',
                'icon': 'fas fa-hotel',
                'color': '#1C69A8'
            },
            'risk_conjuntos': {
                'display_name': 'Análisis de Riesgo - Conjuntos Residenciales',
                'description': 'Módulo para evaluación de riesgos en conjuntos residenciales y propiedades inmobiliarias',
                'icon': 'fas fa-building',
                'color': '#059669'
            },
            'security_probabilistic': {
                'display_name': 'Evaluación de Seguridad Probabilística',
                'description': 'Módulo para análisis probabilístico de seguridad y gestión de amenazas',
                'icon': 'fas fa-shield-alt',
                'color': '#dc2626'
            }
        }
        
        created_count = 0
        for module_name in module_names:
            if module_name in module_configs:
                module, created = Module.objects.get_or_create(
                    name=module_name,
                    defaults=module_configs[module_name]
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Módulo creado: {module.display_name}')
                    )
        
        return created_count

    def ensure_plans_exist(self, modules):
        """Crea planes básicos si no existen"""
        # Crear tipos de planes si no existen
        plan_types = ['básico', 'profesional', 'empresarial']
        for i, plan_type_name in enumerate(plan_types):
            PlanType.objects.get_or_create(
                name=plan_type_name.title(),
                defaults={
                    'description': f'Plan {plan_type_name}',
                    'order': i,
                    'is_active': True
                }
            )
        
        created_count = 0
        for module in modules:
            for plan_type in PlanType.objects.filter(is_active=True):
                plan, created = Plan.objects.get_or_create(
                    module=module,
                    plan_type=plan_type,
                    defaults={
                        'name': f'{module.display_name} - {plan_type.name}',
                        'description': f'Plan {plan_type.name.lower()} para {module.display_name}',
                        'monthly_price': 50000 + (plan_type.order * 30000),  # COP
                        'quarterly_price': (50000 + (plan_type.order * 30000)) * 3 * 0.9,
                        'yearly_price': (50000 + (plan_type.order * 30000)) * 12 * 0.8,
                        'trial_days': 14,
                        'max_users': 1 + plan_type.order * 5,
                        'max_reports': 10 + plan_type.order * 20,
                        'max_storage_gb': 1 + plan_type.order * 5,
                        'features': {
                            'basic_features': True,
                            'advanced_analytics': plan_type.order >= 1,
                            'api_access': plan_type.order >= 2,
                            'priority_support': plan_type.order >= 1,
                            'custom_reports': plan_type.order >= 2,
                        },
                        'is_active': True,
                        'order': plan_type.order
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Plan creado: {plan.name}')
                    )
        
        return created_count
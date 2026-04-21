"""
Management command para asignar el plan más alto del módulo risk_hoteles a un usuario
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.subscriptions.models import Module, Plan, PlanType, Subscription

User = get_user_model()


class Command(BaseCommand):
    help = 'Asignar el plan más alto del módulo risk_hoteles a un usuario específico'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@ejemplo.com',
            help='Email del usuario (por defecto: admin@ejemplo.com)'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            # 1. Verificar/crear usuario
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': 'Admin',
                    'last_name': 'Usuario',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            
            if created:
                user.set_password('admin123')
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Usuario creado: {email} (password: admin123)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Usuario ya existe: {email}')
                )

            # 2. Obtener o crear módulo risk_hoteles
            module, created = Module.objects.get_or_create(
                name='risk_hoteles',
                defaults={
                    'display_name': 'Risk Analysis - Hotels',
                    'description': 'Análisis de riesgo para hoteles',
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Módulo creado: {module.display_name}')
                )

            # 3. Obtener o crear plan type
            plan_type, created = PlanType.objects.get_or_create(
                name='Subscription',
                defaults={'description': 'Plan de suscripción mensual'}
            )

            # 4. Crear planes si no existen
            plans_data = [
                {
                    'name': 'Basic',
                    'monthly_price': '29.99',
                    'description': 'Plan básico para hoteles pequeños',
                    'max_users': 2,
                    'max_reports': 10,
                    'max_storage_gb': 1,
                    'features': {
                        'api_calls': 1000,
                        'dashboard': True,
                    }
                },
                {
                    'name': 'Pro',
                    'monthly_price': '99.99',
                    'description': 'Plan profesional con características avanzadas',
                    'max_users': 10,
                    'max_reports': 100,
                    'max_storage_gb': 10,
                    'features': {
                        'api_calls': 10000,
                        'dashboard': True,
                        'advanced_reports': True,
                        'export_data': True,
                    }
                },
                {
                    'name': 'Enterprise',
                    'monthly_price': '299.99',
                    'description': 'Plan empresarial con acceso completo',
                    'max_users': -1,    # Unlimited
                    'max_reports': -1,  # Unlimited
                    'max_storage_gb': 100,
                    'features': {
                        'api_calls': -1,  # Unlimited
                        'dashboard': True,
                        'advanced_reports': True,
                        'export_data': True,
                        'priority_support': True,
                        'custom_integration': True,
                        'white_label': True,
                    }
                }
            ]

            created_plans = []
            for plan_data in plans_data:
                try:
                    plan, created = Plan.objects.get_or_create(
                        module=module,
                        name=plan_data['name'],
                        defaults={
                            'plan_type': plan_type,
                            'description': plan_data['description'],
                            'monthly_price': plan_data['monthly_price'],
                            'max_users': plan_data['max_users'],
                            'max_reports': plan_data['max_reports'],
                            'max_storage_gb': plan_data['max_storage_gb'],
                            'features': plan_data['features'],
                            'is_active': True,
                        }
                    )
                    created_plans.append(plan)
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Plan creado: {plan.name} - ${plan.monthly_price}/mes')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'- Plan ya existe: {plan.name}')
                        )
                except Exception as e:
                    # Si hay error de constraint, buscar el plan existente
                    existing_plan = Plan.objects.filter(
                        module=module,
                        name=plan_data['name']
                    ).first()
                    if existing_plan:
                        created_plans.append(existing_plan)
                        self.stdout.write(
                            self.style.WARNING(f'- Plan encontrado: {existing_plan.name}')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Error creando plan {plan_data["name"]}: {str(e)}')
                        )

            # 4. Obtener el plan más alto (Enterprise)
            highest_plan = Plan.objects.filter(
                module=module,
                name='Enterprise'
            ).first()

            if not highest_plan:
                self.stdout.write(
                    self.style.ERROR('❌ No se pudo encontrar el plan Enterprise')
                )
                return

            # 5. Verificar si ya tiene una suscripción activa
            existing_subscription = Subscription.objects.filter(
                user=user,
                plan__module=module,
                status='active'
            ).first()

            if existing_subscription:
                self.stdout.write(
                    self.style.WARNING(f'- Usuario ya tiene suscripción activa: {existing_subscription.plan.name}')
                )
                
                # Preguntar si actualizar
                self.stdout.write('¿Desea actualizar al plan Enterprise? (Actualizando...)')
                existing_subscription.plan = highest_plan
                existing_subscription.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Suscripción actualizada a: {highest_plan.name}')
                )
            else:
                # 6. Crear nueva suscripción con el plan más alto
                subscription = Subscription.objects.create(
                    user=user,
                    plan=highest_plan,
                    status='active',
                    start_date=timezone.now().date(),
                    next_billing_date=timezone.now().date() + timezone.timedelta(days=30),
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Suscripción creada: {highest_plan.name}')
                )

            # 7. Mostrar resumen
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('🎉 ASIGNACIÓN COMPLETADA'))
            self.stdout.write('='*50)
            self.stdout.write(f'👤 Usuario: {user.email}')
            self.stdout.write(f'🏨 Módulo: {module.display_name}')
            self.stdout.write(f'💎 Plan: {highest_plan.name}')
            self.stdout.write(f'💰 Precio: ${highest_plan.monthly_price}/mes')
            # Determinar la fecha de inicio
            start_date = subscription.start_date if 'subscription' in locals() else existing_subscription.start_date
            self.stdout.write(f'📅 Inicio: {start_date}')
            self.stdout.write(f'✅ Estado: Activo')
            
            # Mostrar características incluidas
            self.stdout.write('\n📋 Características incluidas:')
            features = highest_plan.features
            if isinstance(features, dict):
                for key, value in features.items():
                    if value == -1:
                        value_str = 'Ilimitado'
                    elif isinstance(value, bool) and value:
                        value_str = 'Incluido'
                    else:
                        value_str = str(value)
                    
                    self.stdout.write(f'   • {key.replace("_", " ").title()}: {value_str}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
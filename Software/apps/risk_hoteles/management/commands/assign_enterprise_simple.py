"""
Management command simplificado para asignar suscripción Enterprise a un usuario
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.subscriptions.models import Module, Plan, PlanType, Subscription

User = get_user_model()


class Command(BaseCommand):
    help = 'Asignar plan Enterprise del módulo risk_hoteles a un usuario'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@ejemplo.com',
            help='Email del usuario'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            # 1. Obtener o crear usuario
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': 'Admin',
                    'last_name': 'Usuario',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            
            if user_created:
                user.set_password('admin123')
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Usuario creado: {email}')
                )
            else:
                self.stdout.write(f'✓ Usuario encontrado: {email}')

            # 2. Obtener o crear módulo
            module, _ = Module.objects.get_or_create(
                name='risk_hoteles',
                defaults={
                    'display_name': 'Risk Analysis - Hotels',
                    'description': 'Análisis de riesgo para hoteles',
                    'is_active': True,
                }
            )

            # 3. Obtener o crear plan type
            plan_type, _ = PlanType.objects.get_or_create(
                name='Enterprise',
                defaults={'description': 'Plan empresarial'}
            )

            # 4. Buscar plan Enterprise existente o crear uno nuevo
            enterprise_plan = Plan.objects.filter(
                module=module,
                name__icontains='enterprise'
            ).first()

            if not enterprise_plan:
                # Crear plan Enterprise
                enterprise_plan = Plan.objects.create(
                    module=module,
                    plan_type=plan_type,
                    name='Enterprise Risk Hotels',
                    description='Plan empresarial completo para análisis de riesgo hotelero',
                    monthly_price='299.99',
                    max_users=-1,  # Unlimited
                    max_reports=-1,  # Unlimited
                    max_storage_gb=100,
                    features={
                        'api_calls': -1,
                        'dashboard': True,
                        'advanced_reports': True,
                        'export_data': True,
                        'priority_support': True,
                        'custom_integration': True,
                        'white_label': True,
                    },
                    is_active=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Plan Enterprise creado: ${enterprise_plan.monthly_price}/mes')
                )
            else:
                self.stdout.write(f'✓ Plan Enterprise encontrado: {enterprise_plan.name}')

            # 5. Verificar suscripción existente
            existing_subscription = Subscription.objects.filter(
                user=user,
                plan__module=module,
                status='active'
            ).first()

            if existing_subscription:
                # Actualizar a Enterprise
                existing_subscription.plan = enterprise_plan
                # Extender la suscripción si es necesario
                if existing_subscription.end_date < timezone.now() + timezone.timedelta(days=30):
                    existing_subscription.end_date = timezone.now() + timezone.timedelta(days=365)
                existing_subscription.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Suscripción actualizada a Enterprise')
                )
                subscription = existing_subscription
            else:
                # Crear nueva suscripción
                start_date = timezone.now()
                end_date = start_date + timezone.timedelta(days=365)  # 1 año de suscripción
                next_billing_date = start_date + timezone.timedelta(days=30)  # Próximo mes
                
                subscription = Subscription.objects.create(
                    user=user,
                    plan=enterprise_plan,
                    status='active',
                    billing_cycle='monthly',
                    start_date=start_date,
                    end_date=end_date,
                    next_billing_date=next_billing_date,
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Nueva suscripción Enterprise creada')
                )

            # 6. Mostrar resumen
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('🎉 SUSCRIPCIÓN ENTERPRISE ASIGNADA'))
            self.stdout.write('='*60)
            self.stdout.write(f'👤 Usuario: {user.email}')
            self.stdout.write(f'🏨 Módulo: {module.display_name}')
            self.stdout.write(f'💎 Plan: {enterprise_plan.name}')
            self.stdout.write(f'💰 Precio: ${enterprise_plan.monthly_price}/mes')
            self.stdout.write(f'📅 Inicio: {subscription.start_date.date()}')
            self.stdout.write(f'📅 Fin: {subscription.end_date.date()}')
            self.stdout.write(f'📅 Próximo pago: {subscription.next_billing_date.date()}')
            self.stdout.write(f'✅ Estado: {subscription.status.upper()}')
            
            # Mostrar características
            self.stdout.write('\n🚀 Características incluidas:')
            features = enterprise_plan.features
            if isinstance(features, dict):
                for key, value in features.items():
                    if value == -1:
                        value_str = 'Ilimitado'
                    elif isinstance(value, bool) and value:
                        value_str = 'Incluido ✓'
                    else:
                        value_str = str(value)
                    
                    feature_name = key.replace('_', ' ').title()
                    self.stdout.write(f'   • {feature_name}: {value_str}')
            
            # Mostrar límites
            self.stdout.write('\n📊 Límites del plan:')
            self.stdout.write(f'   • Usuarios: {"Ilimitados" if enterprise_plan.max_users == -1 else enterprise_plan.max_users}')
            self.stdout.write(f'   • Reportes/mes: {"Ilimitados" if enterprise_plan.max_reports == -1 else enterprise_plan.max_reports}')
            self.stdout.write(f'   • Almacenamiento: {enterprise_plan.max_storage_gb} GB')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
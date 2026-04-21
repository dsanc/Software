from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.subscriptions.models import Plan, Subscription

User = get_user_model()

class Command(BaseCommand):
    help = 'Asigna TODOS los planes a un usuario específico'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email del usuario')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f'👤 Usuario encontrado: {email}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuario no encontrado: {email}'))
            return

        # Eliminar suscripciones existentes del usuario
        existing_subs = Subscription.objects.filter(user=user)
        if existing_subs.exists():
            existing_subs.delete()
            self.stdout.write(f'🗑️  Suscripciones anteriores eliminadas')

        # Obtener TODOS los planes activos
        all_plans = Plan.objects.filter(is_active=True).order_by('module__order', 'order')
        
        if not all_plans.exists():
            self.stdout.write(self.style.ERROR('❌ No hay planes disponibles'))
            return

        # Crear suscripciones para TODOS los planes
        self.stdout.write(f'\n📝 Asignando {all_plans.count()} planes al usuario...')
        
        start_date = timezone.now()
        end_date = start_date + timedelta(days=365)  # 1 año de vigencia
        
        created_count = 0
        current_module = None
        
        for plan in all_plans:
            # Mostrar separador por módulo
            if current_module != plan.module.name:
                if current_module is not None:
                    self.stdout.write('')  # Línea en blanco
                current_module = plan.module.name
                self.stdout.write(f'\n🔗 {plan.module.display_name.upper()}:')
            
            # Crear suscripción
            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                billing_cycle='yearly',
                start_date=start_date,
                end_date=end_date,
                status='active',
                is_trial=False
            )
            
            # Mostrar información del plan asignado
            price_formatted = f'${plan.yearly_price:,.0f}'
            users_info = f'{plan.max_users} usuario{"s" if plan.max_users > 1 else ""}'
            evaluaciones = 'Ilimitadas' if plan.limits.get('evaluaciones', 0) == -1 else str(plan.limits.get('evaluaciones', 0))
            crear_eval = plan.limits.get('crear_evaluador', 0)
            soporte = plan.features.get('soporte', 'N/A')
            
            self.stdout.write(
                f'  ✅ {plan.plan_type.name:<18} | {price_formatted:>12} | {users_info:<12} | {evaluaciones:<12} | {crear_eval:<4} | {soporte}'
            )
            
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 ¡PROCESO COMPLETADO!'
                f'\n👤 Usuario: {email}'
                f'\n📋 Suscripciones asignadas: {created_count}'
                f'\n📅 Vigencia: {start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}'
                f'\n⏳ Duración: 12 meses'
                f'\n🔄 Estado: Todas activas'
            )
        )
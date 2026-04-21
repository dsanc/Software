from django.core.management.base import BaseCommand
from apps.subscriptions.models import Plan, Module, PlanType

class Command(BaseCommand):
    help = 'Muestra todos los planes actuales'

    def handle(self, *args, **options):
        self.stdout.write('PLANES ACTUALES:')
        self.stdout.write('='*80)
        
        for module in Module.objects.all():
            self.stdout.write(f'\nMÓDULO: {module.display_name.upper()}')
            self.stdout.write('-'*40)
            
            plans = Plan.objects.filter(module=module, is_active=True).order_by('order')
            for plan in plans:
                self.stdout.write(f'Plan: {plan.plan_type.name}')
                self.stdout.write(f'Precio/Año: ${plan.yearly_price:,.0f} COP')
                self.stdout.write(f'Clientes: {plan.max_users}')
                reportes = 'Ilimitadas' if plan.max_reports == -1 else str(plan.max_reports)
                self.stdout.write(f'Evaluaciones: {reportes}')
                
                if plan.limits and 'crear_evaluador' in plan.limits:
                    evaluador = plan.limits['crear_evaluador']
                    self.stdout.write(f'Crear/Evaluador: {evaluador}')
                
                if plan.features and 'soporte' in plan.features:
                    self.stdout.write(f'Soporte: {plan.features["soporte"]}')
                
                self.stdout.write('---')
            
            # Contar suscripciones por módulo
            from apps.subscriptions.models import Subscription
            suscripciones = Subscription.objects.filter(plan__module=module).count()
            self.stdout.write(f'Total suscripciones activas: {suscripciones}')
            self.stdout.write('')
        
        # Resumen total
        total_plans = Plan.objects.filter(is_active=True).count()
        total_subscriptions = Subscription.objects.filter(status='active').count()
        self.stdout.write(
            self.style.SUCCESS(
                f'RESUMEN TOTAL:'
                f'\nPlanes activos: {total_plans}'
                f'\nSuscripciones activas: {total_subscriptions}'
            )
        )
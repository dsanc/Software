from django.core.management.base import BaseCommand
from apps.subscriptions.models import Plan, PlanType


class Command(BaseCommand):
    help = 'Actualiza los períodos de prueba: Solo DEMO tendrá 15 días, los demás serán 0'

    def handle(self, *args, **options):
        """
        Actualiza los períodos de prueba:
        - Solo planes Demo: 15 días
        - Todos los demás: 0 días (pago inmediato)
        """
        
        # Primero obtener el plan type Demo
        demo_plan_type = PlanType.objects.filter(name='Demo').first()
        
        if not demo_plan_type:
            self.stdout.write(
                self.style.ERROR('No se encontró el plan type "Demo"')
            )
            return
        
        # Actualizar todos los planes a 0 días de prueba
        updated_plans = Plan.objects.update(trial_days=0)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Todos los planes actualizados a 0 días de prueba: {updated_plans} planes')
        )
        
        # Luego actualizar solo los planes Demo a 15 días
        demo_plans_updated = Plan.objects.filter(
            plan_type=demo_plan_type
        ).update(trial_days=15)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Planes Demo actualizados a 15 días: {demo_plans_updated} planes')
        )
        
        # Mostrar el resultado final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('RESUMEN DE PERÍODOS DE PRUEBA:'))
        self.stdout.write('='*50)
        
        for plan in Plan.objects.all().order_by('module__name', 'plan_type__order'):
            if plan.trial_days > 0:
                status = self.style.SUCCESS(f'{plan.trial_days} días GRATIS')
            else:
                status = self.style.ERROR('PAGO INMEDIATO')
            
            self.stdout.write(
                f'{plan.module.display_name} - {plan.plan_type.name}: {status}'
            )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS('✅ Actualización completada exitosamente!')
        )
        self.stdout.write(
            'Solo los planes DEMO mantienen 15 días gratis.'
        )
        self.stdout.write(
            'Todos los demás planes requieren pago inmediato.'
        )
from django.core.management.base import BaseCommand
from apps.subscriptions.models import Plan, PlanType


class Command(BaseCommand):
    help = 'Muestra un resumen de todos los planes y sus períodos de prueba'

    def handle(self, *args, **options):
        """
        Muestra un resumen organizado de todos los planes
        """
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RESUMEN COMPLETO DE PLANES Y PERÍODOS DE PRUEBA'))
        self.stdout.write('='*60)
        
        # Planes Demo (con días gratis)
        demo_plans = Plan.objects.filter(plan_type__name='Demo', is_active=True)
        if demo_plans.exists():
            self.stdout.write('\n' + self.style.SUCCESS('🎁 PLANES DEMO (15 DÍAS GRATIS):'))
            self.stdout.write('-' * 40)
            for plan in demo_plans.order_by('module__name'):
                self.stdout.write(
                    f'  ✓ {plan.module.display_name}: {plan.plan_type.name} '
                    f'(${plan.yearly_price}/año) - {plan.trial_days} días gratis'
                )
        
        # Planes de pago (sin días gratis)  
        paid_plans = Plan.objects.exclude(plan_type__name='Demo').filter(is_active=True)
        if paid_plans.exists():
            self.stdout.write('\n' + self.style.WARNING('💰 PLANES DE PAGO (PAGO INMEDIATO):'))
            self.stdout.write('-' * 40)
            for plan in paid_plans.order_by('module__name', 'yearly_price'):
                self.stdout.write(
                    f'  💳 {plan.module.display_name}: {plan.plan_type.name} '
                    f'(${plan.yearly_price}/año) - Pago inmediato'
                )
        
        # Estadísticas
        total_plans = Plan.objects.filter(is_active=True).count()
        demo_count = demo_plans.count()
        paid_count = paid_plans.count()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 ESTADÍSTICAS:'))
        self.stdout.write('='*60)
        self.stdout.write(f'Total de planes activos: {total_plans}')
        self.stdout.write(f'Planes con período gratis: {demo_count} (Solo Demo)')
        self.stdout.write(f'Planes de pago inmediato: {paid_count}')
        
        if demo_count == 3 and paid_count == (total_plans - 3):
            self.stdout.write('\n' + self.style.SUCCESS('✅ CONFIGURACIÓN CORRECTA:'))
            self.stdout.write('- Solo los planes Demo tienen período de prueba')
            self.stdout.write('- Todos los demás planes requieren pago inmediato')
        else:
            self.stdout.write('\n' + self.style.ERROR('❌ VERIFICAR CONFIGURACIÓN:'))
            self.stdout.write('- La configuración puede no estar como se esperaba')
        
        self.stdout.write('\n' + '='*60 + '\n')
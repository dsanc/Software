"""
Comando para mostrar todos los planes de suscripción actuales
"""
from django.core.management.base import BaseCommand
from apps.subscriptions.models import Module, Plan
from django.db.models import Count


class Command(BaseCommand):
    help = 'Muestra todos los planes de suscripción actuales'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📋 PLANES DE SUSCRIPCIÓN ACTUALES\n'))
        
        modules = Module.objects.filter(is_active=True).prefetch_related('plans__plan_type')
        
        for module in modules:
            self.stdout.write(
                self.style.WARNING(f'\n🏢 MÓDULO: {module.display_name.upper()}')
            )
            self.stdout.write(f'📝 Descripción: {module.description}')
            self.stdout.write(f'🎨 Color: {module.color} | 🎯 Icono: {module.icon}\n')
            
            plans = module.plans.filter(is_active=True).order_by('order')
            
            if not plans:
                self.stdout.write('   ❌ No hay planes disponibles\n')
                continue
            
            for plan in plans:
                featured = '⭐ DESTACADO' if plan.is_featured else ''
                price_text = f'${plan.yearly_price:,.0f}/año' if plan.yearly_price > 0 else 'GRATUITO'
                
                self.stdout.write(f'   📦 {plan.plan_type.name} {featured}')
                self.stdout.write(f'      💰 Precio: {price_text}')
                self.stdout.write(f'      👥 Usuarios: {plan.max_users}')
                
                reports_text = 'Ilimitados' if plan.max_reports == -1 else str(plan.max_reports)
                self.stdout.write(f'      📊 Reportes: {reports_text}')
                self.stdout.write(f'      💾 Almacenamiento: {plan.max_storage_gb} GB')
                self.stdout.write(f'      🎁 Prueba gratuita: {plan.trial_days} días')
                
                if plan.features:
                    self.stdout.write('      ✨ Características:')
                    for key, value in plan.features.items():
                        self.stdout.write(f'         • {key}: {value}')
                
                self.stdout.write('')
        
        # Resumen final
        total_modules = Module.objects.filter(is_active=True).count()
        total_plans = Plan.objects.filter(is_active=True).count()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n📈 RESUMEN:\n'
            f'   🏢 Módulos activos: {total_modules}\n'
            f'   📦 Planes totales: {total_plans}\n'
            f'   💰 Rango de precios: $0 - ${Plan.objects.filter(is_active=True).order_by("-yearly_price").first().yearly_price:,.0f}/año'
        ))
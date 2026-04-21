from django.core.management.base import BaseCommand
from django.db import transaction
from apps.subscriptions.models import Module, Plan, PlanType

class Command(BaseCommand):
    help = 'Agrega plan DEMO a todos los módulos'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Crear o obtener el tipo de plan Demo
            demo_plan_type, created = PlanType.objects.get_or_create(
                name='Demo',
                defaults={
                    'description': 'Plan de demostración gratuito',
                    'order': 0,  # Orden 0 para que aparezca primero
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write('✅ Tipo de plan Demo creado')
            else:
                self.stdout.write('✅ Tipo de plan Demo ya existía')

            # Obtener todos los módulos
            modules = Module.objects.all().order_by('order')
            
            if not modules.exists():
                self.stdout.write(self.style.ERROR('❌ No se encontraron módulos'))
                return

            self.stdout.write(f'\n🎯 Agregando plan DEMO a {modules.count()} módulos...\n')
            
            for module in modules:
                # Verificar si ya existe un plan Demo para este módulo
                existing_demo = Plan.objects.filter(
                    module=module,
                    plan_type=demo_plan_type
                ).first()
                
                if existing_demo:
                    self.stdout.write(f'⚠️  {module.display_name}: Plan Demo ya existe - {existing_demo.name}')
                    continue

                # Crear plan Demo
                demo_plan = Plan.objects.create(
                    module=module,
                    plan_type=demo_plan_type,
                    name=f'{module.display_name.upper()} - Demo',
                    description=f'Plan de demostración gratuito para {module.display_name}',
                    yearly_price=0,  # Gratis
                    monthly_price=0,
                    quarterly_price=0,
                    max_users=2,  # 2 clientes
                    max_reports=2,  # 2 evaluaciones
                    max_storage_gb=1,  # Almacenamiento mínimo
                    trial_days=30,  # 30 días de prueba
                    limits={
                        'evaluaciones': 2,  # 2 evaluaciones
                        'crear_evaluador': 0  # 0 evaluadores
                    },
                    features={
                        'soporte': 'Básico'
                    },
                    order=0,  # Primer orden para que aparezca primero
                    is_active=True,
                    is_featured=False
                )
                
                self.stdout.write(f'✅ {module.display_name}: Plan Demo creado')
                self.stdout.write(f'   📋 {demo_plan.name}')
                self.stdout.write(f'   💰 Precio: GRATIS')
                self.stdout.write(f'   👥 Clientes: 2')
                self.stdout.write(f'   📊 Evaluaciones: 2')
                self.stdout.write(f'   👨‍💼 Crear/Evaluador: 0')
                self.stdout.write(f'   🛠️  Soporte: Básico')
                self.stdout.write('')

            # Verificar totales finales
            total_demo_plans = Plan.objects.filter(plan_type=demo_plan_type).count()
            total_all_plans = Plan.objects.filter(is_active=True).count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎉 ¡PLANES DEMO AGREGADOS EXITOSAMENTE!'
                    f'\n📊 Planes Demo creados: {total_demo_plans}'
                    f'\n📋 Total planes activos: {total_all_plans}'
                    f'\n🎯 Cada módulo ahora tiene un plan Demo gratuito'
                    f'\n'
                    f'\n💡 CARACTERÍSTICAS DEL PLAN DEMO:'
                    f'\n   • Precio: $0 (GRATIS)'
                    f'\n   • Clientes: 2 usuarios máximo'
                    f'\n   • Evaluaciones: 2 evaluaciones máximo' 
                    f'\n   • Crear/Evaluador: 0 (no puede crear evaluadores)'
                    f'\n   • Soporte: Básico'
                    f'\n   • Duración: 30 días de prueba'
                )
            )
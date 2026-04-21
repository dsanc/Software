"""
Comando de gestión Django para generar datos de prueba del carrito
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from apps.subscriptions.models import Plan, Cart, CartItem
from apps.subscriptions.services import CartService

User = get_user_model()


class Command(BaseCommand):
    help = 'Genera datos de prueba para el sistema de carrito'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Número de usuarios de prueba a crear'
        )
        parser.add_argument(
            '--carts',
            type=int,
            default=10,
            help='Número de carritos de prueba a crear'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpiar datos existentes antes de crear nuevos'
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('🧹 Limpiando datos existentes...')
            Cart.objects.all().delete()
            # No eliminamos usuarios existentes
        
        num_users = options['users']
        num_carts = options['carts']
        
        self.stdout.write(f'🚀 Creando {num_users} usuarios y {num_carts} carritos de prueba...')
        
        # Crear usuarios de prueba
        test_users = []
        for i in range(num_users):
            email = f'test_user_{i+1}@ejemplo.com'
            username = f'test_user_{i+1}'
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': f'Usuario',
                    'last_name': f'Prueba {i+1}',
                    'is_active': True
                }
            )
            if created:
                user.set_password('test123')
                user.save()
            test_users.append(user)
            
        self.stdout.write(f'✅ {len(test_users)} usuarios creados/encontrados')
        
        # Obtener planes disponibles
        plans = list(Plan.objects.filter(is_active=True))
        if not plans:
            self.stderr.write('❌ No hay planes disponibles. Crear planes primero.')
            return
        
        # Crear carritos de prueba
        created_carts = 0
        billing_cycles = ['monthly', 'quarterly', 'yearly']
        
        for i in range(num_carts):
            # Decidir si es carrito de usuario o anónimo
            if i < num_carts * 0.6:  # 60% carritos de usuarios
                user = random.choice(test_users)
                session_key = ''  # String vacío en lugar de None
                expires_days = 30
            else:  # 40% carritos anónimos
                user = None
                session_key = f'test_session_{i}'
                expires_days = 7
            
            # Crear carrito
            cart = Cart.objects.create(
                user=user,
                session_key=session_key,
                created_at=timezone.now() - timedelta(days=random.randint(0, 15)),
                expires_at=timezone.now() + timedelta(days=expires_days)
            )
            
            # Agregar 1-3 items aleatorios (respetando regla de un plan por módulo)
            modules_used = set()
            num_items = random.randint(1, 3)
            
            for _ in range(num_items):
                # Filtrar planes de módulos no usados
                available_plans = [p for p in plans if p.module not in modules_used]
                if not available_plans:
                    break
                    
                plan = random.choice(available_plans)
                modules_used.add(plan.module)
                
                billing_cycle = random.choice(billing_cycles)
                quantity = random.randint(1, 2)
                
                CartItem.objects.create(
                    cart=cart,
                    plan=plan,
                    billing_cycle=billing_cycle,
                    quantity=quantity,
                    unit_price=plan.get_price(billing_cycle)
                )
            
            created_carts += 1
            
            # Crear algunos carritos abandonados (vacíos)
            if random.random() < 0.2:  # 20% carritos abandonados
                user_for_abandoned = random.choice(test_users) if random.random() < 0.5 else None
                session_key_abandoned = f'abandoned_{i}' if user_for_abandoned is None else ''
                
                abandoned_cart = Cart.objects.create(
                    user=user_for_abandoned,
                    session_key=session_key_abandoned,
                    created_at=timezone.now() - timedelta(days=random.randint(1, 10)),
                    expires_at=timezone.now() + timedelta(days=expires_days)
                )
                created_carts += 1
        
        # Estadísticas finales
        total_carts = Cart.objects.count()
        total_items = CartItem.objects.count()
        carts_with_items = Cart.objects.filter(items__isnull=False).distinct().count()
        
        self.stdout.write('📊 ESTADÍSTICAS GENERADAS:')
        self.stdout.write(f'   Carritos totales: {total_carts}')
        self.stdout.write(f'   Carritos con items: {carts_with_items}')
        self.stdout.write(f'   Items totales: {total_items}')
        self.stdout.write(f'   Usuarios de prueba: {len(test_users)}')
        
        # Mostrar ejemplos
        sample_carts = Cart.objects.filter(items__isnull=False).distinct()[:3]
        if sample_carts:
            self.stdout.write('🛒 EJEMPLOS DE CARRITOS:')
            for cart in sample_carts:
                user_info = cart.user.email if cart.user else f'Anónimo ({cart.session_key[:10]}...)'
                items_count = cart.items.count()
                total = cart.total_amount
                self.stdout.write(f'   {user_info}: {items_count} items, ${total:,.0f}')
        
        self.stdout.write(self.style.SUCCESS('✅ Datos de prueba generados exitosamente!'))
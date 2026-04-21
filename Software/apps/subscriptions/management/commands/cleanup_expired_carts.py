"""
Comando de gestión Django para limpiar carritos expirados
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.subscriptions.models import Cart, CartItem


class Command(BaseCommand):
    help = 'Limpia carritos expirados y optimiza la base de datos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=0,
            help='Eliminar carritos expirados hace X días (0 = solo expirados)'
        )
        parser.add_argument(
            '--empty-carts',
            action='store_true',
            help='También eliminar carritos vacíos más antiguos de 7 días'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se eliminará sin hacer cambios'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ejecutar sin confirmación'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        days_buffer = options['days']
        clean_empty = options['empty_carts']
        
        now = timezone.now()
        buffer_time = now - timedelta(days=days_buffer)
        
        self.stdout.write('🧹 LIMPIEZA DE CARRITOS')
        self.stdout.write('=' * 50)
        
        # 1. Carritos expirados
        expired_carts = Cart.objects.filter(
            expires_at__lt=buffer_time if days_buffer > 0 else now
        )
        
        expired_count = expired_carts.count()
        expired_items = CartItem.objects.filter(cart__in=expired_carts).count()
        
        self.stdout.write(f'📋 Carritos expirados encontrados: {expired_count}')
        self.stdout.write(f'📦 Items en carritos expirados: {expired_items}')
        
        # 2. Carritos vacíos antiguos (opcional)
        empty_carts_count = 0
        if clean_empty:
            week_ago = now - timedelta(days=7)
            empty_carts = Cart.objects.filter(
                items__isnull=True,
                created_at__lt=week_ago
            )
            empty_carts_count = empty_carts.count()
            self.stdout.write(f'🗑️  Carritos vacíos antiguos: {empty_carts_count}')
        
        # 3. Mostrar estadísticas antes
        total_carts = Cart.objects.count()
        total_items = CartItem.objects.count()
        
        self.stdout.write(f'📊 ANTES - Carritos: {total_carts}, Items: {total_items}')
        
        # 4. Confirmación o dry run
        total_to_delete = expired_count + (empty_carts_count if clean_empty else 0)
        
        if total_to_delete == 0:
            self.stdout.write(self.style.SUCCESS('✅ No hay carritos para limpiar'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'🔍 DRY RUN: Se eliminarían {total_to_delete} carritos'))
            
            # Mostrar ejemplos
            if expired_count > 0:
                self.stdout.write('📋 Ejemplos de carritos expirados:')
                for cart in expired_carts[:3]:
                    user_info = cart.user.email if cart.user else f'Anónimo ({cart.session_key[:10]}...)'
                    expired_days = (now - cart.expires_at).days
                    items_count = cart.items.count()
                    self.stdout.write(f'   - {user_info}: {items_count} items, expirado hace {expired_days} días')
            return
        
        if not force:
            confirm = input(f'¿Eliminar {total_to_delete} carritos? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('❌ Operación cancelada')
                return
        
        # 5. Ejecutar limpieza
        deleted_count = 0
        
        # Eliminar carritos expirados
        if expired_count > 0:
            # Los items se eliminan automáticamente por CASCADE
            deleted_expired = expired_carts.delete()
            self.stdout.write(f'🗑️  Eliminados {deleted_expired[0]} carritos expirados')
            deleted_count += deleted_expired[0]
        
        # Eliminar carritos vacíos antiguos
        if clean_empty and empty_carts_count > 0:
            deleted_empty = empty_carts.delete()
            self.stdout.write(f'🗑️  Eliminados {deleted_empty[0]} carritos vacíos antiguos')
            deleted_count += deleted_empty[0]
        
        # 6. Estadísticas finales
        final_carts = Cart.objects.count()
        final_items = CartItem.objects.count()
        
        self.stdout.write('📊 DESPUÉS:')
        self.stdout.write(f'   Carritos: {final_carts} (-{total_carts - final_carts})')
        self.stdout.write(f'   Items: {final_items} (-{total_items - final_items})')
        
        # 7. Recomendaciones
        self.stdout.write('💡 RECOMENDACIONES:')
        
        active_carts = Cart.objects.filter(expires_at__gt=now).count()
        if active_carts > 100:
            self.stdout.write('   ⚠️  Muchos carritos activos, considerar reducir tiempo de vida')
        
        carts_without_expiry = Cart.objects.filter(expires_at__isnull=True).count()
        if carts_without_expiry > 0:
            self.stdout.write(f'   ⚠️  {carts_without_expiry} carritos sin fecha de expiración')
        
        # Sugerir programar limpieza automática
        self.stdout.write('   💻 Programar este comando en cron/task scheduler:')
        self.stdout.write('      Diario: python manage.py cleanup_expired_carts')
        self.stdout.write('      Semanal: python manage.py cleanup_expired_carts --empty-carts')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Limpieza completada: {deleted_count} carritos eliminados'))
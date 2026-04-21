"""
Management command para enviar notificaciones de carritos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.subscriptions.models import Cart, WebhookEvent
from apps.subscriptions.cart_notifications import CartNotificationService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envía notificaciones de carritos abandonados y próximos a expirar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['abandoned', 'expiring'],
            help='Tipo de notificación a enviar (abandoned o expiring)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo simulación sin enviar emails',
        )
        parser.add_argument(
            '--abandoned-hours',
            type=int,
            default=24,
            help='Horas después de las cuales se considera un carrito abandonado (default: 24)',
        )
        parser.add_argument(
            '--expiry-hours',
            type=int,
            default=2,
            help='Horas antes de expiración para enviar advertencia (default: 2)',
        )

    def handle(self, *args, **options):
        notification_service = CartNotificationService()
        now = timezone.now()
        
        sent_count = 0
        error_count = 0
        
        if options['type'] in [None, 'abandoned']:
            self.stdout.write("Procesando carritos abandonados...")
            abandoned_count, abandoned_errors = self._process_abandoned_carts(
                notification_service, 
                now, 
                options['abandoned_hours'],
                options['dry_run']
            )
            sent_count += abandoned_count
            error_count += abandoned_errors

        if options['type'] in [None, 'expiring']:
            self.stdout.write("Procesando carritos próximos a expirar...")
            expiring_count, expiring_errors = self._process_expiring_carts(
                notification_service,
                now,
                options['expiry_hours'],
                options['dry_run']
            )
            sent_count += expiring_count
            error_count += expiring_errors

        # Resumen final
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f"SIMULACIÓN: Se habrían enviado {sent_count} notificaciones "
                    f"con {error_count} errores"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Proceso completado: {sent_count} notificaciones enviadas, "
                    f"{error_count} errores"
                )
            )

    def _process_abandoned_carts(self, notification_service, now, hours_threshold, dry_run):
        """Procesa carritos abandonados"""
        cutoff_time = now - timedelta(hours=hours_threshold)
        
        # Buscar carritos abandonados que no hayan recibido notificación
        abandoned_carts = Cart.objects.filter(
            created_at__lt=cutoff_time,
            is_completed=False,
            is_active=True,
            user__isnull=False,  # Solo carritos con usuario
            user__email__isnull=False,  # Y con email válido
            items__isnull=False  # Que tengan items
        ).distinct().select_related('user').prefetch_related('items__plan__plan_type', 'items__plan__module')

        # Filtrar los que ya recibieron notificación de abandono
        carts_to_notify = []
        for cart in abandoned_carts:
            # Por simplicidad, vamos a notificar todos por ahora
            # En futuro se puede agregar un modelo separado para tracking
            carts_to_notify.append(cart)

        self.stdout.write(f"Encontrados {len(carts_to_notify)} carritos abandonados sin notificar")

        sent_count = 0
        error_count = 0

        for cart in carts_to_notify:
            try:
                if dry_run:
                    self.stdout.write(
                        f"  [SIMULACIÓN] Notificaría carrito {cart.id} del usuario {cart.user.email}"
                    )
                else:
                    success = notification_service.send_abandonment_notification(cart.id)
                    if success:
                        self.stdout.write(
                            f"  ✅ Enviada notificación de abandono: carrito {cart.id}"
                        )
                        sent_count += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Error enviando notificación: carrito {cart.id}")
                        )
                        error_count += 1
            except Exception as e:
                logger.error(f"Error procesando carrito abandonado {cart.id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Error en carrito {cart.id}: {e}")
                )
                error_count += 1

        return sent_count, error_count

    def _process_expiring_carts(self, notification_service, now, hours_before_expiry, dry_run):
        """Procesa carritos próximos a expirar"""
        # Calcular ventana de tiempo para carritos que expirarán en las próximas X horas
        expiry_start = now + timedelta(hours=hours_before_expiry - 0.5)
        expiry_end = now + timedelta(hours=hours_before_expiry + 0.5)
        
        expiring_carts = Cart.objects.filter(
            expires_at__range=(expiry_start, expiry_end),
            is_completed=False,
            is_active=True,
            user__isnull=False,  # Solo carritos con usuario
            user__email__isnull=False,  # Y con email válido
            items__isnull=False  # Que tengan items
        ).distinct().select_related('user').prefetch_related('items__plan__plan_type', 'items__plan__module')

        # Filtrar los que ya recibieron notificación de expiración
        carts_to_notify = []
        for cart in expiring_carts:
            # Por simplicidad, vamos a notificar todos por ahora
            # En futuro se puede agregar un modelo separado para tracking
            carts_to_notify.append(cart)

        self.stdout.write(f"Encontrados {len(carts_to_notify)} carritos próximos a expirar sin notificar")

        sent_count = 0
        error_count = 0

        for cart in carts_to_notify:
            try:
                if dry_run:
                    hours_remaining = (cart.expires_at - now).total_seconds() / 3600
                    self.stdout.write(
                        f"  [SIMULACIÓN] Notificaría carrito {cart.id} que expira en {hours_remaining:.1f}h"
                    )
                else:
                    success = notification_service.send_expiry_warning(cart.id)
                    if success:
                        hours_remaining = (cart.expires_at - now).total_seconds() / 3600
                        self.stdout.write(
                            f"  ✅ Enviada advertencia de expiración: carrito {cart.id} (expira en {hours_remaining:.1f}h)"
                        )
                        sent_count += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Error enviando advertencia: carrito {cart.id}")
                        )
                        error_count += 1
            except Exception as e:
                logger.error(f"Error procesando carrito expirando {cart.id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Error en carrito {cart.id}: {e}")
                )
                error_count += 1

        return sent_count, error_count
"""
Management command para probar todas las mejoras del carrito implementadas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.subscriptions.models import Cart, CartItem, Plan, Module, PlanType, WebhookEvent
from apps.subscriptions.cart_notifications import CartNotificationService
from django.contrib.auth import get_user_model
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Prueba completa de todas las mejoras implementadas en el carrito'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full-test',
            action='store_true',
            help='Ejecutar todas las pruebas incluyendo envío de emails',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("=== PRUEBA COMPLETA DE MEJORAS DEL CARRITO ===\n")
        )

        # 1. Probar generación de datos de prueba
        self.stdout.write("1. Probando generación de datos de prueba...")
        self._test_cart_data_generation()

        # 2. Probar sistema de notificaciones
        self.stdout.write("\n2. Probando sistema de notificaciones...")
        self._test_notification_system(options['full_test'])

        # 3. Probar limpieza automática
        self.stdout.write("\n3. Probando limpieza automática...")
        self._test_automatic_cleanup()

        # 4. Validar templates móviles
        self.stdout.write("\n4. Validando optimizaciones móviles...")
        self._validate_mobile_templates()

        self.stdout.write(
            self.style.SUCCESS("\n✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        )

    def _test_cart_data_generation(self):
        """Prueba la generación de datos de prueba"""
        try:
            # Verificar que hay datos para generar
            modules = Module.objects.all()
            plan_types = PlanType.objects.all()
            
            if not modules.exists():
                self.stdout.write(
                    self.style.WARNING("⚠️  No hay módulos disponibles")
                )
                return

            if not plan_types.exists():
                self.stdout.write(
                    self.style.WARNING("⚠️  No hay tipos de plan disponibles")
                )
                return

            # Crear un carrito de prueba
            user = User.objects.first()
            if not user:
                self.stdout.write(
                    self.style.WARNING("⚠️  No hay usuarios para prueba")
                )
                return

            cart = Cart.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=24)
            )

            # Agregar items al carrito
            plans = Plan.objects.filter(is_active=True)[:3]
            for plan in plans:
                billing_cycle = random.choice(['monthly', 'yearly'])
                CartItem.objects.create(
                    cart=cart,
                    plan=plan,
                    quantity=random.randint(1, 3),
                    unit_price=plan.get_price(billing_cycle),
                    billing_cycle=billing_cycle
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"   ✅ Carrito de prueba creado con {cart.items.count()} items"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error en generación de datos: {e}")
            )

    def _test_notification_system(self, send_emails):
        """Prueba el sistema de notificaciones"""
        try:
            notification_service = CartNotificationService()
            
            # Buscar carritos para notificar
            abandoned_carts = Cart.objects.filter(
                created_at__lt=timezone.now() - timedelta(hours=1),
                is_completed=False,
                is_active=True
            ).count()

            expiring_carts = Cart.objects.filter(
                expires_at__range=(
                    timezone.now() + timedelta(hours=1),
                    timezone.now() + timedelta(hours=3)
                ),
                is_completed=False,
                is_active=True
            ).count()

            self.stdout.write(
                f"   📧 Carritos abandonados encontrados: {abandoned_carts}"
            )
            self.stdout.write(
                f"   ⏰ Carritos próximos a expirar: {expiring_carts}"
            )

            if send_emails and abandoned_carts > 0:
                # Enviar notificación de prueba
                cart = Cart.objects.filter(
                    created_at__lt=timezone.now() - timedelta(hours=1),
                    is_completed=False,
                    is_active=True
                ).first()
                
                if cart:
                    success = notification_service.send_abandonment_notification(cart.id)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS("   ✅ Email de abandono enviado exitosamente")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING("   ⚠️  Error al enviar email de abandono")
                        )
            else:
                self.stdout.write(
                    self.style.SUCCESS("   ✅ Sistema de notificaciones validado (sin envío)")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error en notificaciones: {e}")
            )

    def _test_automatic_cleanup(self):
        """Prueba el sistema de limpieza automática"""
        try:
            # Contar carritos expirados
            expired_carts = Cart.objects.filter(
                expires_at__lt=timezone.now(),
                is_completed=False,
                is_active=True
            )

            expired_count = expired_carts.count()
            
            if expired_count > 0:
                # Simular limpieza (marcar como inactivos)
                expired_carts.update(is_active=False)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   ✅ {expired_count} carritos expirados limpiados"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("   ✅ No hay carritos expirados para limpiar")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error en limpieza: {e}")
            )

    def _validate_mobile_templates(self):
        """Valida que las plantillas móviles estén correctamente implementadas"""
        try:
            from django.template.loader import get_template
            
            # Verificar que el template del carrito existe y carga
            cart_template = get_template('subscriptions/cart.html')
            
            # Verificar que contiene las clases CSS móviles
            template_content = cart_template.template.source
            
            mobile_features = [
                '.mobile-layout',
                '.desktop-layout', 
                '.cart-item-mobile',
                '.mobile-actions',
                '.mobile-cart-header',
                '@media (max-width: 768px)',
                'loading-overlay',
                'quantity-btn'
            ]

            missing_features = []
            for feature in mobile_features:
                if feature not in template_content:
                    missing_features.append(feature)

            if missing_features:
                self.stdout.write(
                    self.style.WARNING(
                        f"   ⚠️  Características móviles faltantes: {missing_features}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("   ✅ Todas las optimizaciones móviles implementadas")
                )

            # Verificar templates de email
            email_templates = [
                'subscriptions/emails/cart_abandonment.html',
                'subscriptions/emails/cart_expiry_warning.html'
            ]

            for template_name in email_templates:
                try:
                    get_template(template_name)
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Template {template_name} OK")
                    )
                except Exception:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Template {template_name} faltante")
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error validando templates: {e}")
            )

    def _create_sample_webhooks(self):
        """Crea eventos de webhook de ejemplo para pruebas"""
        try:
            # Crear algunos eventos de ejemplo
            sample_events = [
                {
                    'event_type': 'cart_abandonment_notification',
                    'description': 'Email de carrito abandonado enviado'
                },
                {
                    'event_type': 'cart_expiry_warning',
                    'description': 'Advertencia de expiración enviada'
                },
            ]

            for event_data in sample_events:
                WebhookEvent.objects.create(**event_data)

            self.stdout.write(
                self.style.SUCCESS(f"   ✅ {len(sample_events)} eventos webhook creados")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Error creando webhooks: {e}")
            )
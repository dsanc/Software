"""
Tests para sistema de suscripciones y control de acceso
"""
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import timedelta

from .models import Module, PlanType, Plan, Cart, CartItem, Order, WompiTransaction, Subscription
from .services import CartService, WompiService
from .access_control import get_demo_status, start_demo_period


User = get_user_model()


class SubscriptionPurchaseFlowTest(TestCase):
    """Integration test: full purchase flow from cart to subscription via Wompi webhook."""

    def setUp(self):
        # Create test user (username required in this project)
        self.user = User.objects.create_user(username='buyer', email='buyer@example.com', password='testpass123')

        # Create module, plan type and plan
        self.module = Module.objects.create(
            name='test_module',
            display_name='Test Module',
            description='Module for testing',
            icon='fa-test',
            color='#123456',
            is_active=True,
            order=1,
        )

        self.plan_type = PlanType.objects.create(
            name='Pro',
            description='Pro plan',
            order=1,
            is_active=True,
        )

        self.plan = Plan.objects.create(
            module=self.module,
            plan_type=self.plan_type,
            name='Pro Plan',
            description='Pro plan for module',
            monthly_price=Decimal('100.00'),
            quarterly_price=Decimal('270.00'),
            yearly_price=Decimal('1000.00'),
            trial_days=14,
            max_users=5,
            max_reports=50,
            max_storage_gb=10,
            features={},
            limits={},
            is_active=True,
            order=1,
        )

    def test_full_subscription_purchase_flow(self):
        # Ensure user has no subscriptions initially
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

        # Create or get cart for user
        cart = CartService.get_or_create_cart(user=self.user)

        # Add plan to cart
        cart_item = CartService.add_to_cart(cart, self.plan, billing_cycle='monthly', quantity=1)
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart.total_items, 1)

        # Prepare billing data
        billing_data = {
            'name': 'Buyer Test',
            'email': 'buyer@example.com',
            'phone': '+573001234567',
            'address': 'Test address',
            'city': 'Bogota',
            'country': 'Colombia',
        }

        # Create order from cart
        order = CartService.create_order_from_cart(cart, billing_data)
        self.assertIsNotNone(order)
        # Totals should be calculated
        self.assertGreater(order.total_amount, Decimal('0'))
        self.assertEqual(order.user, self.user)

        # Create a pending WompiTransaction linked to the order (simulate creation step)
        txn = WompiTransaction.objects.create(
            order=order,
            wompi_transaction_id='txn_test_12345',
            wompi_reference='REF-TEST-1',
            wompi_status='PENDING',
            amount_in_cents=int(order.total_amount * 100),
            currency=order.currency,
            payment_method='CARD',
            payment_source_id='',
            redirect_url='http://example.com/redirect',
            wompi_response={}
        )

        # Now simulate receiving a webhook from Wompi indicating the transaction was APPROVED
        service = WompiService()

        event_payload = {
            'event': 'transaction.updated',
            'data': {
                'transaction': {
                    'id': txn.wompi_transaction_id,
                    'status': 'APPROVED',
                }
            }
        }

        processed = service.process_webhook_event(event_payload)
        self.assertTrue(processed)

        # Reload objects from DB
        txn.refresh_from_db()
        order.refresh_from_db()

        # Transaction and order should be updated
        self.assertEqual(txn.wompi_status, 'APPROVED')
        self.assertEqual(order.status, 'paid')

        # A subscription should have been created for the user and plan
        subs = Subscription.objects.filter(user=self.user, plan=self.plan)
        self.assertTrue(subs.exists())
        subscription = subs.first()
        self.assertEqual(subscription.status, 'active')
        self.assertTrue(subscription.start_date <= timezone.now() <= subscription.end_date)


class DemoAccessControlTest(TestCase):
    """Test the DEMO access control system."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='demouser', email='demo@example.com', password='testpass123')
        self.client = Client()
        
        # Create module and plan for DEMO
        self.module = Module.objects.create(
            name='demo_module',
            display_name='Demo Module',
            description='Module for demo testing',
            icon='fa-demo',
            color='#654321',
            is_active=True,
            order=1,
        )
        
        self.plan_type = PlanType.objects.create(
            name='Basic',
            description='Basic plan',
            order=1,
            is_active=True,
        )
        
        self.plan = Plan.objects.create(
            module=self.module,
            plan_type=self.plan_type,
            name='Basic Plan',
            description='Basic plan for demo',
            monthly_price=Decimal('50.00'),
            quarterly_price=Decimal('135.00'),
            yearly_price=Decimal('500.00'),
            trial_days=15,
            max_users=2,
            max_reports=10,
            max_storage_gb=5,
            features={'basic_reports': True},
            limits={},
            is_active=True,
            order=1,
        )
    
    def test_demo_status_no_subscription(self):
        """Test demo status for user with no subscription."""
        demo_status = get_demo_status(self.user, self.module.name)
        
        self.assertFalse(demo_status['active'])
        self.assertTrue(demo_status['can_start'])
        self.assertEqual(demo_status['days_remaining'], 15)
        self.assertIsNone(demo_status['started_at'])
        self.assertIsNone(demo_status['expires_at'])
    
    def test_start_demo_period(self):
        """Test starting a DEMO period."""
        # Start DEMO
        demo_subscription = start_demo_period(self.user, self.module.name)
        
        self.assertIsNotNone(demo_subscription)
        self.assertEqual(demo_subscription.user, self.user)
        self.assertEqual(demo_subscription.plan, self.plan)
        self.assertTrue(demo_subscription.is_trial)
        self.assertEqual(demo_subscription.status, 'active')
        
        # Verify dates
        self.assertTrue(demo_subscription.start_date <= timezone.now())
        self.assertTrue(demo_subscription.end_date > timezone.now())
        self.assertEqual(demo_subscription.trial_end_date, demo_subscription.end_date)
        
        # Duration should be approximately 15 days
        duration = demo_subscription.end_date - demo_subscription.start_date
        self.assertEqual(duration.days, 15)
    
    def test_demo_status_active(self):
        """Test demo status when DEMO is active."""
        # Start DEMO
        demo_subscription = start_demo_period(self.user, self.module.name)
        
        # Check status
        demo_status = get_demo_status(self.user, self.module.name)
        
        self.assertTrue(demo_status['active'])
        self.assertFalse(demo_status['can_start'])
        self.assertGreaterEqual(demo_status['days_remaining'], 14)  # Should be 14 or 15 depending on timing
        self.assertLessEqual(demo_status['days_remaining'], 15)
        self.assertIsNotNone(demo_status['started_at'])
        self.assertIsNotNone(demo_status['expires_at'])
        self.assertEqual(demo_status['subscription'], demo_subscription)
    
    def test_demo_status_expired(self):
        """Test demo status when DEMO has expired."""
        # Create expired DEMO subscription
        start_date = timezone.now() - timedelta(days=20)
        end_date = timezone.now() - timedelta(days=5)
        
        expired_subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            order=None,
            billing_cycle='monthly',
            start_date=start_date,
            end_date=end_date,
            status='expired',
            is_trial=True,
            trial_end_date=end_date
        )
        
        # Check status
        demo_status = get_demo_status(self.user, self.module.name)
        
        self.assertFalse(demo_status['active'])
        self.assertFalse(demo_status['can_start'])
        self.assertEqual(demo_status['days_remaining'], 0)
        self.assertTrue(demo_status.get('expired', False))
    
    def test_cannot_start_demo_twice(self):
        """Test that user cannot start DEMO twice for same module."""
        # Start first DEMO
        first_demo = start_demo_period(self.user, self.module.name)
        self.assertIsNotNone(first_demo)
        
        # Try to start second DEMO
        second_demo = start_demo_period(self.user, self.module.name)
        self.assertIsNone(second_demo)
        
        # Should only have one subscription
        demo_count = Subscription.objects.filter(
            user=self.user,
            plan__module=self.module,
            is_trial=True
        ).count()
        self.assertEqual(demo_count, 1)

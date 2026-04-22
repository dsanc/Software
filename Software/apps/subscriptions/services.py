"""
Servicios para integración con Wompi y gestión de carrito de compras
"""
import requests
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import (
    Cart, CartItem, Order, OrderItem, WompiTransaction, 
    Subscription, WebhookEvent, Plan
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class WompiService:
    """Servicio para integración con Wompi"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'WOMPI_BASE_URL', 'https://sandbox.wompi.co/v1')
        self.public_key = getattr(settings, 'WOMPI_PUBLIC_KEY', '')
        self.private_key = getattr(settings, 'WOMPI_PRIVATE_KEY', '')
        self.event_secret = getattr(settings, 'WOMPI_EVENT_SECRET', '')
        self.is_sandbox = getattr(settings, 'WOMPI_SANDBOX', True)
        
        if not self.public_key or not self.private_key:
            logger.warning("Wompi credentials not configured properly")
            
        self.integrity_secret = getattr(settings, 'WOMPI_INTEGRITY_SECRET', '')
    
    def generate_widget_data(self, order):
        """Genera los datos necesarios para el Widget de Wompi"""
        reference = f"ORDER-{order.order_number}-{int(timezone.now().timestamp())}"
        amount_in_cents = int(order.total_amount * 100)
        currency = order.currency
        
        # Calcular firma de integridad
        # Cadena: Referencia + MontoEnCentavos + Moneda + SecretoIntegridad
        signature_string = f"{reference}{amount_in_cents}{currency}{self.integrity_secret}"
        signature = hashlib.sha256(signature_string.encode('utf-8')).hexdigest()
        
        return {
            'public_key': self.public_key,
            'currency': currency,
            'amount_in_cents': amount_in_cents,
            'reference': reference,
            'signature': signature,
            'redirect_url': self._build_redirect_url(order.id)
        }

    def create_acceptance_token(self):
        """Crea token de aceptación para términos y condiciones"""
        url = f"{self.base_url}/merchants/{self.public_key}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            return {
                'acceptance_token': data['data']['presigned_acceptance']['acceptance_token'],
                'permalink': data['data']['presigned_acceptance']['permalink']
            }
        except requests.RequestException as e:
            logger.error(f"Error creating acceptance token: {e}")
            return None
    
    def create_payment_source(self, token, customer_email, acceptance_token):
        """Crea fuente de pago con tarjeta tokenizada"""
        url = f"{self.base_url}/payment_sources"
        
        headers = {
            'Authorization': f'Bearer {self.private_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'type': 'CARD',
            'token': token,
            'customer_email': customer_email,
            'acceptance_token': acceptance_token
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['data']
        except requests.RequestException as e:
            logger.error(f"Error creating payment source: {e}")
            return None
    
    def create_transaction(self, order, payment_source_id=None, payment_method=None):
        """Crea transacción en Wompi"""
        url = f"{self.base_url}/transactions"
        
        headers = {
            'Authorization': f'Bearer {self.private_key}',
            'Content-Type': 'application/json'
        }
        
        # Generar referencia única
        reference = f"ORDER-{order.order_number}-{int(timezone.now().timestamp())}"
        
        # URL de redirección
        redirect_url = self._build_redirect_url(order.id)
        
        data = {
            'amount_in_cents': int(order.total_amount * 100),  # Convertir a centavos
            'currency': order.currency,
            'customer_email': order.billing_email,
            'reference': reference,
            'redirect_url': redirect_url,
        }
        
        # Agregar método de pago
        if payment_source_id:
            data['payment_source_id'] = payment_source_id
        elif payment_method:
            data['payment_method'] = payment_method
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            transaction_data = response.json()['data']
            
            # Crear registro de transacción
            wompi_transaction = WompiTransaction.objects.create(
                order=order,
                wompi_transaction_id=transaction_data['id'],
                wompi_reference=reference,
                amount_in_cents=data['amount_in_cents'],
                currency=order.currency,
                payment_method=payment_method or 'CARD',
                payment_source_id=payment_source_id or '',
                redirect_url=redirect_url,
                wompi_response=transaction_data
            )
            
            return wompi_transaction
            
        except requests.RequestException as e:
            logger.error(f"Error creating transaction: {e}")
            return None
    
    def get_transaction_status(self, transaction_id):
        """Obtiene el estado actual de una transacción"""
        url = f"{self.base_url}/transactions/{transaction_id}"
        
        headers = {
            'Authorization': f'Bearer {self.private_key}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()['data']
        except requests.RequestException as e:
            logger.error(f"Error getting transaction status: {e}")
            return None
    
    def verify_webhook_signature(self, payload, signature):
        """Verifica la firma del webhook"""
        if not self.event_secret:
            logger.warning("Wompi event secret not configured")
            return False
        
        expected_signature = hmac.new(
            self.event_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_webhook_event(self, event_data):
        """Procesa evento de webhook"""
        try:
            event_type = event_data.get('event')
            transaction_data = event_data.get('data', {}).get('transaction', {})
            transaction_id = transaction_data.get('id')
            
            if not transaction_id:
                logger.error("No transaction ID in webhook event")
                return False
            
            # Buscar transacción existente o crearla
            wompi_transaction = WompiTransaction.objects.filter(
                wompi_transaction_id=transaction_id
            ).first()
            
            if not wompi_transaction:
                # Intentar buscar por referencia para encontrar la orden
                reference = transaction_data.get('reference')
                if reference:
                    # Formato esperado: ORDER-{order_number}-{timestamp}
                    try:
                        parts = reference.split('-')
                        if len(parts) >= 2 and parts[0] == 'ORDER':
                            order_number = parts[1] # Asumiendo que order_number no tiene guiones
                            # Si order_number tiene guiones, necesitamos una estrategia mejor o guardar la referencia en la orden
                            
                            # Buscar orden por número (más seguro buscar por referencia exacta si la guardáramos, pero no la guardamos antes)
                            # Mejor estrategia: Buscar la orden que coincida con el número extraído
                            order = Order.objects.filter(order_number=order_number).first()
                            
                            if order:
                                # Crear la transacción
                                wompi_transaction = WompiTransaction.objects.create(
                                    order=order,
                                    wompi_transaction_id=transaction_id,
                                    wompi_reference=reference,
                                    amount_in_cents=transaction_data.get('amount_in_cents', 0),
                                    currency=transaction_data.get('currency', 'COP'),
                                    payment_method=transaction_data.get('payment_method_type', 'UNKNOWN'),
                                    wompi_status=transaction_data.get('status', 'PENDING'),
                                    wompi_response=transaction_data
                                )
                    except Exception as e:
                        logger.error(f"Error parsing reference {reference}: {e}")
            
            if not wompi_transaction:
                logger.error(f"Transaction {transaction_id} not found and could not be created")
                return False
            
            # Actualizar estado
            old_status = wompi_transaction.wompi_status
            wompi_transaction.wompi_status = transaction_data.get('status', 'PENDING')
            wompi_transaction.wompi_response = transaction_data
            wompi_transaction.processed_at = timezone.now()
            wompi_transaction.save()
            
            # Procesar cambio de estado
            if old_status != wompi_transaction.wompi_status:
                self._handle_status_change(wompi_transaction)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            return False
            
    def sync_transaction(self, transaction_id):
        """Sincroniza una transacción consultando a Wompi"""
        try:
            transaction_data = self.get_transaction_status(transaction_id)
            if not transaction_data:
                return None
                
            # Simular estructura de evento para reutilizar lógica
            event_data = {
                'event': 'transaction.updated',
                'data': {
                    'transaction': transaction_data
                }
            }
            
            # Reutilizar process_webhook_event para consistencia
            self.process_webhook_event(event_data)
            
            return WompiTransaction.objects.filter(wompi_transaction_id=transaction_id).first()
            
        except Exception as e:
            logger.error(f"Error syncing transaction {transaction_id}: {e}")
            return None
    
    def _handle_status_change(self, wompi_transaction):
        """Maneja cambios de estado de transacción"""
        order = wompi_transaction.order
        
        if wompi_transaction.wompi_status == 'APPROVED':
            # Pago aprobado
            order.status = 'paid'
            order.completed_at = timezone.now()
            order.save()
            
            # Crear suscripciones
            self._create_subscriptions_from_order(order)
            
            logger.info(f"Order {order.order_number} paid successfully")
            
        elif wompi_transaction.wompi_status == 'DECLINED':
            # Pago rechazado
            order.status = 'failed'
            order.save()
            
            logger.info(f"Order {order.order_number} payment declined")
            
        elif wompi_transaction.wompi_status == 'VOIDED':
            # Pago anulado
            order.status = 'cancelled'
            order.save()
            
            logger.info(f"Order {order.order_number} payment voided")
    
    def _create_subscriptions_from_order(self, order):
        """Crea o renueva suscripciones a partir de una orden pagada"""
        for item in order.items.all():
            # Determinar duración según ciclo
            duration_days = 30
            if item.billing_cycle == 'quarterly':
                duration_days = 90
            elif item.billing_cycle == 'yearly':
                duration_days = 365
            
            now = timezone.now()
            
            # Buscar suscripción existente para este plan
            subscription = Subscription.objects.filter(
                user=order.user,
                plan=item.plan
            ).first()
            
            if subscription:
                # Lógica de renovación
                if subscription.end_date < now:
                    # Si ya expiró, reiniciamos el periodo desde hoy
                    subscription.start_date = now
                    subscription.end_date = now + timedelta(days=duration_days)
                else:
                    # Si sigue activa, extendemos desde la fecha de fin actual
                    subscription.end_date = subscription.end_date + timedelta(days=duration_days)
                
                # Actualizar metadatos
                subscription.status = 'active'
                subscription.billing_cycle = item.billing_cycle
                subscription.order = order
                subscription.save()
                
                logger.info(f"Subscription renewed for {order.user.email} - {item.plan}. New end date: {subscription.end_date}")
                
            else:
                # Crear nueva suscripción
                Subscription.objects.create(
                    user=order.user,
                    plan=item.plan,
                    order=order,
                    billing_cycle=item.billing_cycle,
                    start_date=now,
                    end_date=now + timedelta(days=duration_days),
                    status='active'
                )
                
                logger.info(f"New subscription created for {order.user.email} - {item.plan}")
    
    def _build_redirect_url(self, order_id):
        """Construye URL de redirección después del pago"""
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f"{base_url}{reverse('subscriptions:payment_result', kwargs={'order_id': order_id})}"


class CartService:
    """Servicio para gestión del carrito de compras"""
    
    @staticmethod
    def get_or_create_cart(user=None, session_key=None, request=None):
        """Obtiene o crea un carrito para el usuario o sesión"""
        cart = None
        
        # Intentar recuperar carrito desde la sesión (persiste tras login)
        if request and 'cart_id' in request.session:
            try:
                session_cart = Cart.objects.get(id=request.session['cart_id'])
                # Si el carrito de sesión es anónimo y ahora tenemos usuario, es candidato a merge
                if session_cart.user is None and user and user.is_authenticated:
                    # Este es el carrito que debemos fusionar
                    pass
                elif session_cart.user == user:
                    cart = session_cart
                elif session_cart.user is None and not user:
                    cart = session_cart
            except Cart.DoesNotExist:
                if 'cart_id' in request.session:
                    del request.session['cart_id']

        if user and user.is_authenticated:
            # Para usuarios autenticados, buscar su carrito persistente
            user_cart, created = Cart.objects.get_or_create(
                user=user,
                defaults={
                    'expires_at': timezone.now() + timedelta(days=30)
                }
            )
            
            # Si encontramos un carrito anónimo en la sesión, fusionarlo
            if request and 'cart_id' in request.session:
                try:
                    anonymous_cart = Cart.objects.get(id=request.session['cart_id'], user__isnull=True)
                    if anonymous_cart and anonymous_cart != user_cart:
                        CartService.merge_carts(anonymous_cart, user_cart)
                        # Limpiar referencia de sesión ya que ahora usamos el user_cart
                        del request.session['cart_id']
                except Cart.DoesNotExist:
                    pass
            
            cart = user_cart
            
        else:
            # Para usuarios anónimos
            if not cart:
                if session_key:
                    try:
                        cart = Cart.objects.get(session_key=session_key)
                    except Cart.DoesNotExist:
                        pass
            
            # Si no encontramos carrito, crear uno nuevo
            if not cart:
                cart = Cart.objects.create(
                    session_key=session_key,
                    expires_at=timezone.now() + timedelta(days=7)
                )
        
        # Guardar ID en sesión para persistencia
        if request and cart:
            request.session['cart_id'] = str(cart.id)
            
        return cart

    @staticmethod
    def merge_carts(source_cart, target_cart):
        """Fusiona items del carrito origen al destino"""
        for item in source_cart.items.all():
            # Verificar si ya existe un item similar en el destino
            existing_item = CartItem.objects.filter(
                cart=target_cart,
                plan=item.plan,
                billing_cycle=item.billing_cycle
            ).first()
            
            if existing_item:
                # Si existe, sumar cantidad
                existing_item.quantity += item.quantity
                existing_item.save()
            else:
                # Si no existe, mover el item
                # Verificar si hay conflicto de reglas de negocio (ej. solo un plan por módulo)
                # Por simplicidad, permitimos el movimiento y dejamos que el usuario limpie su carrito si hay duplicados lógicos
                # Pero debemos evitar IntegrityError
                item.cart = target_cart
                item.save()
        
        # Eliminar carrito origen
        source_cart.delete()
    
    @staticmethod
    def add_to_cart(cart, plan, billing_cycle='yearly', quantity=1):
        """Agrega un plan al carrito - Con validaciones de negocio"""
        try:
            # VALIDACIÓN 1: Verificar si es plan Demo y el usuario ya lo ha usado
            if plan.plan_type.name.lower() == 'demo':
                if CartService.user_has_used_demo(cart.user, plan.module):
                    return {
                        'success': False,
                        'error': 'demo_already_used',
                        'message': f'Ya has usado el plan Demo de {plan.module.display_name}. Solo se permite un uso por usuario.'
                    }
            
            # VALIDACIÓN 2: Solo un plan pago por módulo (excluir Demo)
            existing_item = CartItem.objects.filter(
                cart=cart,
                plan__module=plan.module
            ).first()
            
            if existing_item:
                # Si es plan Demo y ya hay otro plan del módulo, no permitir
                if plan.plan_type.name.lower() == 'demo':
                    return {
                        'success': False,
                        'error': 'demo_with_paid_plan',
                        'message': f'Ya tienes un plan pago de {plan.module.display_name} en tu carrito. No puedes agregar el Demo.'
                    }
                
                # Si hay plan Demo y se intenta agregar plan pago, reemplazar
                if existing_item.plan.plan_type.name.lower() == 'demo' and plan.plan_type.name.lower() != 'demo':
                    existing_item.plan = plan
                    existing_item.billing_cycle = billing_cycle
                    existing_item.quantity = quantity
                    existing_item.unit_price = plan.get_price(billing_cycle)
                    existing_item.save()
                    return {
                        'success': True,
                        'item': existing_item,
                        'replaced': True,
                        'message': f'Plan Demo reemplazado por {plan.plan_type.name} en {plan.module.display_name}'
                    }
                
                # Si es el mismo plan y ciclo, actualizar cantidad
                elif existing_item.plan == plan and existing_item.billing_cycle == billing_cycle:
                    existing_item.quantity += quantity
                    existing_item.save()
                    return {
                        'success': True,
                        'item': existing_item,
                        'updated': True,
                        'message': f'Cantidad actualizada para {plan.plan_type.name} de {plan.module.display_name}'
                    }
                
                # Si es plan diferente del mismo módulo (ambos pagos), reemplazar
                elif plan.plan_type.name.lower() != 'demo' and existing_item.plan.plan_type.name.lower() != 'demo':
                    existing_item.plan = plan
                    existing_item.billing_cycle = billing_cycle
                    existing_item.quantity = quantity
                    existing_item.unit_price = plan.get_price(billing_cycle)
                    existing_item.save()
                    return {
                        'success': True,
                        'item': existing_item,
                        'replaced': True,
                        'message': f'Plan {existing_item.plan.plan_type.name} reemplazado por {plan.plan_type.name} en {plan.module.display_name}'
                    }
            
            # No hay plan del módulo, crear nuevo item
            cart_item = CartItem.objects.create(
                cart=cart,
                plan=plan,
                billing_cycle=billing_cycle,
                quantity=quantity,
                unit_price=plan.get_price(billing_cycle)
            )
            return {
                'success': True,
                'item': cart_item,
                'added': True,
                'message': f'{plan.plan_type.name} de {plan.module.display_name} agregado al carrito'
            }
            
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return {
                'success': False,
                'error': 'system_error',
                'message': 'Error interno del sistema'
            }
    
    @staticmethod
    def user_has_used_demo(user, module):
        """Verifica si el usuario ya ha usado el plan Demo de un módulo"""
        if not user or not user.is_authenticated:
            return False
        
        from .models import Subscription, PlanType
        
        try:
            # Buscar suscripciones activas o pasadas del plan Demo para este módulo
            demo_plan_type = PlanType.objects.get(name__iexact='demo')
            
            has_demo_subscription = Subscription.objects.filter(
                user=user,
                plan__module=module,
                plan__plan_type=demo_plan_type
            ).exists()
            
            return has_demo_subscription
            
        except PlanType.DoesNotExist:
            logger.warning("Demo plan type not found")
            return False
        except Exception as e:
            logger.error(f"Error checking demo usage: {e}")
            return False
    
    @staticmethod
    def remove_from_cart(cart, plan, billing_cycle=None):
        """Remueve un plan del carrito"""
        try:
            if billing_cycle:
                CartItem.objects.filter(
                    cart=cart,
                    plan=plan,
                    billing_cycle=billing_cycle
                ).delete()
            else:
                CartItem.objects.filter(
                    cart=cart,
                    plan=plan
                ).delete()
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing from cart: {e}")
            return False
    
    @staticmethod
    def update_quantity(cart, plan, billing_cycle, quantity):
        """Actualiza la cantidad de un item en el carrito"""
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                plan=plan,
                billing_cycle=billing_cycle
            )
            
            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            
            return True
            
        except CartItem.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error updating cart quantity: {e}")
            return False
    
    @staticmethod
    def clear_cart(cart):
        """Vacía el carrito"""
        try:
            cart.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            return False
    
    @staticmethod
    def add_to_cart_by_id(user, plan_id, billing_cycle='yearly', quantity=1):
        """
        Agregar un plan al carrito por ID con validaciones de negocio
        
        Reglas de negocio:
        1. Solo se puede agregar un plan pago por módulo
        2. El Demo solo es de un solo uso por usuario por módulo
        3. Si ya existe un plan en el módulo, se reemplaza
        """
        try:
            # Obtener el plan
            try:
                plan = Plan.objects.select_related('module', 'plan_type').get(id=plan_id)
            except Plan.DoesNotExist:
                return {
                    'success': False,
                    'error_type': 'system_error',
                    'message': 'Plan no encontrado'
                }
            
            # Validar si el usuario ya usó el demo de este módulo
            if plan.plan_type.name == 'Demo':
                if CartService.user_has_used_demo(user, plan.module):
                    return {
                        'success': False,
                        'error_type': 'demo_already_used',
                        'message': f'Ya has utilizado el Demo de {plan.module.display_name}. Solo se permite un uso por módulo.'
                    }
            
            # Obtener o crear carrito activo
            cart, created = Cart.objects.get_or_create(
                user=user,
                is_active=True,
                defaults={'is_completed': False}
            )
            
            # Buscar si ya existe un plan del mismo módulo en el carrito
            existing_item = CartItem.objects.filter(
                cart=cart,
                plan__module=plan.module
            ).first()
            
            if existing_item:
                # Validar reglas de negocio para el reemplazo
                
                # Si hay demo en carrito y queremos agregar plan pago
                if existing_item.plan.plan_type.name == 'Demo' and plan.plan_type.name != 'Demo':
                    # Permitir reemplazo de demo por plan pago
                    existing_item.plan = plan
                    existing_item.billing_cycle = billing_cycle
                    existing_item.quantity = quantity
                    existing_item.unit_price = plan.get_price(billing_cycle)
                    existing_item.save()
                    return {
                        'success': True,
                        'item': existing_item,
                        'replaced': True,
                        'message': f'Demo reemplazado por {plan.plan_type.name} en {plan.module.display_name}'
                    }
                
                # Si hay plan pago y queremos agregar demo
                elif existing_item.plan.plan_type.name != 'Demo' and plan.plan_type.name == 'Demo':
                    return {
                        'success': False,
                        'error_type': 'demo_with_paid_plan',
                        'message': f'Ya tienes un plan pago en {plan.module.display_name}. No puedes agregar el Demo.'
                    }
                
                # Si hay plan pago y queremos agregar otro plan pago
                elif existing_item.plan.plan_type.name != 'Demo' and plan.plan_type.name != 'Demo':
                    return {
                        'success': False,
                        'error_type': 'multiple_paid_plans',
                        'message': f'Solo puedes tener un plan pago por módulo. Ya tienes {existing_item.plan.plan_type.name} en {plan.module.display_name}.'
                    }
                
                # Si es el mismo tipo de plan, actualizar
                else:
                    existing_item.plan = plan
                    existing_item.billing_cycle = billing_cycle
                    existing_item.quantity = quantity
                    existing_item.unit_price = plan.get_price(billing_cycle)
                    existing_item.save()
                    return {
                        'success': True,
                        'item': existing_item,
                        'replaced': True,
                        'message': f'Plan {plan.plan_type.name} reemplazado en {plan.module.display_name}'
                    }
            
            # No hay plan del módulo, crear nuevo item
            cart_item = CartItem.objects.create(
                cart=cart,
                plan=plan,
                billing_cycle=billing_cycle,
                quantity=quantity,
                unit_price=plan.get_price(billing_cycle)
            )
            return {
                'success': True,
                'item': cart_item,
                'added': True,
                'message': f'{plan.plan_type.name} de {plan.module.display_name} agregado al carrito'
            }
            
        except Exception as e:
            print(f"Error adding to cart: {e}")
            return {
                'success': False,
                'error_type': 'system_error',
                'message': 'Error interno del sistema'
            }
    
    @staticmethod
    def get_module_plan_in_cart(cart, module):
        """Obtiene el plan de un módulo específico que está en el carrito"""
        try:
            cart_item = CartItem.objects.filter(
                cart=cart,
                plan__module=module
            ).first()
            return cart_item.plan if cart_item else None
        except Exception:
            return None
    
    @staticmethod
    def has_module_in_cart(cart, module):
        """Verifica si hay algún plan del módulo en el carrito"""
        return CartItem.objects.filter(
            cart=cart,
            plan__module=module
        ).exists()
    
    @staticmethod
    def create_order_from_cart(cart, billing_data):
        """Crea una orden a partir del carrito"""
        try:
            if not cart.items.exists():
                raise ValueError("Cart is empty")
            
            # Crear orden
            order = Order.objects.create(
                user=cart.user,
                billing_name=billing_data.get('name', ''),
                billing_email=billing_data.get('email', ''),
                billing_phone=billing_data.get('phone', ''),
                billing_address=billing_data.get('address', ''),
                billing_city=billing_data.get('city', ''),
                billing_country=billing_data.get('country', 'Colombia'),
            )
            
            # Crear items de la orden
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    plan=cart_item.plan,
                    plan_name=str(cart_item.plan),
                    billing_cycle=cart_item.billing_cycle,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    features_snapshot=cart_item.plan.features or {}
                )
            
            # Calcular totales
            order.calculate_totals()
            
            # Limpiar carrito
            cart.clear()
            
            return order
            
        except Exception as e:
            logger.error(f"Error creating order from cart: {e}")
            return None


class SubscriptionService:
    """Servicio para gestión de suscripciones"""
    
    @staticmethod
    def get_user_subscriptions(user, module_name=None):
        """Obtiene suscripciones activas del usuario"""
        subscriptions = Subscription.objects.filter(
            user=user,
            status='active'
        ).select_related('plan', 'plan__module')
        
        if module_name:
            subscriptions = subscriptions.filter(plan__module__name=module_name)
        
        return subscriptions
    
    @staticmethod
    def has_module_access(user, module_name):
        """Verifica si el usuario tiene acceso a un módulo.
        Para evaluadores, verifica la suscripción del usuario principal."""
        # Verificación directa del usuario
        if SubscriptionService.get_user_subscriptions(user, module_name).exists():
            return True

        # Si es evaluador, verificar suscripción del usuario principal
        try:
            from apps.evaluadores.models import Evaluador
            evaluador = Evaluador.objects.select_related('usuario_principal').get(
                usuario_evaluador=user,
                estado='active',
                is_active=True
            )
            # Verificar que el módulo esté permitido para este evaluador
            if evaluador.modulos_permitidos and module_name not in evaluador.modulos_permitidos:
                return False
            # Verificar suscripción del usuario principal
            return SubscriptionService.get_user_subscriptions(
                evaluador.usuario_principal, module_name
            ).exists()
        except Exception:
            pass

        return False
    
    @staticmethod
    def has_feature_access(user, module_name, feature_code):
        """Verifica si el usuario puede usar una característica"""
        subscriptions = SubscriptionService.get_user_subscriptions(user, module_name)
        
        for subscription in subscriptions:
            if subscription.can_use_feature(feature_code):
                return True
        
        return False
    
    @staticmethod
    def get_usage_limits(user, module_name):
        """Obtiene límites de uso y estadísticas completas para un módulo"""
        from .usage_tracker import get_subscription_usage_stats
        
        subscription = SubscriptionService.get_user_subscriptions(user, module_name).first()
        
        if not subscription:
            return {
                'current_users': 0,
                'current_evaluations': 0,
                'current_reports': 0,
                'max_users': 0,
                'max_reports': 0,
                'max_storage_gb': 0,
                'users_percentage': 0,
                'evaluations_percentage': 0,
                'reports_percentage': 0,
                'storage_percentage': 0,
            }
        
        # Obtener estadísticas detalladas del tracker
        usage_stats = get_subscription_usage_stats(user, subscription)
        
        return {
            'current_users': usage_stats.get('users_count', 0),
            'current_evaluations': usage_stats.get('evaluations_count', 0), 
            'current_reports': usage_stats.get('reports_used', 0),
            'current_storage_gb': usage_stats.get('storage_used_gb', 0),
            'max_users': subscription.plan.max_users,
            'max_reports': subscription.plan.max_reports,
            'max_storage_gb': subscription.plan.max_storage_gb,
            'users_percentage': usage_stats.get('users_percentage', 0),
            'evaluations_percentage': usage_stats.get('evaluations_percentage', 0),
            'reports_percentage': usage_stats.get('reports_percentage', 0),
            'storage_percentage': usage_stats.get('storage_percentage', 0),
            'period_start': usage_stats.get('period_start'),
            'period_end': usage_stats.get('period_end'),
            'module_specific': usage_stats.get('module_specific', {}),
        }
    
    @staticmethod
    def can_add_user(user, module_name):
        """Verifica si se puede agregar un usuario más"""
        limits = SubscriptionService.get_usage_limits(user, module_name)
        
        if not limits:
            return False
        
        if limits['max_users'] <= 0:  # Ilimitado
            return True
        
        return limits['current_users'] < limits['max_users']
    
    @staticmethod
    def can_generate_report(user, module_name):
        """Verifica si se puede generar un reporte más"""
        limits = SubscriptionService.get_usage_limits(user, module_name)
        
        if not limits:
            return False
        
        if limits['max_reports'] <= 0:  # Ilimitado
            return True
        
        return limits['current_reports'] < limits['max_reports']
    
    @staticmethod
    def increment_usage(user, module_name, resource_type, amount=1):
        """Incrementa el uso de un recurso"""
        subscription = SubscriptionService.get_user_subscriptions(user, module_name).first()
        
        if not subscription:
            return False
        
        if resource_type == 'reports':
            subscription.current_reports += amount
        elif resource_type == 'users':
            subscription.current_users += amount
        elif resource_type == 'storage':
            subscription.current_storage_gb += amount
        
        subscription.save()
        return True
# WebSocket Consumer for Real-time Cart Updates
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache


class CartConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time cart updates
    Handles cart synchronization across multiple devices/tabs
    """
    
    async def connect(self):
        """Accept WebSocket connection if user is authenticated or has session"""
        self.user = self.scope["user"]
        self.session = self.scope.get("session")
        
        if self.user.is_authenticated:
            # Create user-specific group for cart updates
            self.cart_group_name = f"cart_user_{self.user.id}"
            user_id = self.user.id
        elif self.session and self.session.session_key:
            # Create session-specific group for guest users
            self.cart_group_name = f"cart_session_{self.session.session_key}"
            user_id = None
        else:
            await self.close()
            return
        
        # Join cart group
        await self.channel_layer.group_add(
            self.cart_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message with current cart status
        cart_data = await self.get_cart_data()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado al carrito en tiempo real',
            'cart': cart_data,
            'user_id': user_id
        }))
    
    async def disconnect(self, close_code):
        """Clean up when WebSocket disconnects"""
        if hasattr(self, 'cart_group_name'):
            await self.channel_layer.group_discard(
                self.cart_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
            
            elif message_type == 'item_updated':
                await self.handle_item_update(text_data_json)
            
            elif message_type == 'item_removed':
                await self.handle_item_removal(text_data_json)
            
            elif message_type == 'cart_cleared':
                await self.handle_cart_clear()
            
            elif message_type == 'request_cart_sync':
                await self.sync_cart_status()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato de mensaje inválido'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error interno: {str(e)}'
            }))
    
    async def handle_item_update(self, data):
        """Handle real-time item quantity updates"""
        item_id = data.get('item_id')
        quantity = data.get('quantity')
        
        if item_id and quantity:
            # Broadcast update to all user's connected devices
            await self.channel_layer.group_send(
                self.cart_group_name,
                {
                    'type': 'cart_item_updated',
                    'item_id': item_id,
                    'quantity': quantity,
                    'sender_channel': self.channel_name
                }
            )
    
    async def handle_item_removal(self, data):
        """Handle real-time item removal"""
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle')
        
        if plan_id and billing_cycle:
            await self.channel_layer.group_send(
                self.cart_group_name,
                {
                    'type': 'cart_item_removed',
                    'plan_id': plan_id,
                    'billing_cycle': billing_cycle,
                    'sender_channel': self.channel_name
                }
            )
    
    async def handle_cart_clear(self):
        """Handle real-time cart clearing"""
        await self.channel_layer.group_send(
            self.cart_group_name,
            {
                'type': 'cart_cleared',
                'sender_channel': self.channel_name
            }
        )
    
    async def sync_cart_status(self):
        """Sync current cart status across all devices"""
        cart_data = await self.get_cart_data()
        
        await self.channel_layer.group_send(
            self.cart_group_name,
            {
                'type': 'cart_synced',
                'cart': cart_data,
                'sender_channel': self.channel_name
            }
        )
    
    # Group message handlers
    async def cart_item_updated(self, event):
        """Send item update to WebSocket"""
        # Don't send back to the sender
        if event.get('sender_channel') == self.channel_name:
            return
            
        await self.send(text_data=json.dumps({
            'type': 'item_updated',
            'item_id': event['item_id'],
            'quantity': event['quantity'],
            'message': 'Item actualizado desde otro dispositivo'
        }))
    
    async def cart_item_removed(self, event):
        """Send item removal to WebSocket"""
        if event.get('sender_channel') == self.channel_name:
            return
            
        await self.send(text_data=json.dumps({
            'type': 'item_removed',
            'plan_id': event['plan_id'],
            'billing_cycle': event['billing_cycle'],
            'message': 'Item eliminado desde otro dispositivo'
        }))
    
    async def cart_cleared(self, event):
        """Send cart clear to WebSocket"""
        if event.get('sender_channel') == self.channel_name:
            return
            
        await self.send(text_data=json.dumps({
            'type': 'cart_cleared',
            'message': 'Carrito vaciado desde otro dispositivo'
        }))
    
    async def cart_synced(self, event):
        """Send cart sync to WebSocket"""
        if event.get('sender_channel') == self.channel_name:
            return
            
        await self.send(text_data=json.dumps({
            'type': 'cart_updated',
            'cart': event['cart'],
            'message': 'Carrito sincronizado'
        }))
    
    async def price_update(self, event):
        """Send price updates to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'price_updated',
            'pricing': event['pricing'],
            'message': 'Precios actualizados'
        }))
    
    @database_sync_to_async
    def get_cart_data(self):
        """Get current cart data from database"""
        from .models import Cart
        
        try:
            if self.user.is_authenticated:
                cart = Cart.objects.filter(
                    user=self.user, 
                    is_active=True
                ).first()
            elif self.session and self.session.session_key:
                cart = Cart.objects.filter(
                    session_key=self.session.session_key,
                    is_active=True
                ).first()
            else:
                cart = None
            
            if not cart:
                return {
                    'total_items': 0,
                    'total_amount': 0,
                    'items': []
                }
            
            return {
                'total_items': cart.total_items,
                'total_amount': float(cart.total_amount),
                'items': [
                    {
                        'id': str(item.id),
                        'plan_name': item.plan.name,
                        'plan_id': item.plan.id,
                        'billing_cycle': item.billing_cycle,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'subtotal': float(item.subtotal)
                    }
                    for item in cart.items.all()
                ]
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_items': 0,
                'total_amount': 0,
                'items': []
            }


# Background task for price updates
async def broadcast_price_updates():
    """
    Background task to check for price updates and broadcast to connected clients
    Run this as a scheduled task or with Django-RQ/Celery
    """
    from channels.layers import get_channel_layer
    from .models import Plan
    
    channel_layer = get_channel_layer()
    
    # Check for price updates (this would be more sophisticated in production)
    # For now, we'll just send updates when plans are modified
    
    # This could be triggered by:
    # 1. Admin panel plan updates
    # 2. Scheduled promotions
    # 3. Currency rate changes
    # 4. Seasonal pricing
    
    try:
        # Get plans with recent price changes (last 5 minutes)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_updates = Plan.objects.filter(
            updated_at__gte=timezone.now() - timedelta(minutes=5)
        )
        
        if recent_updates.exists():
            pricing_data = {
                'items': [
                    {
                        'id': plan.id,
                        'name': plan.name,
                        'monthly_price': float(plan.monthly_price),
                        'yearly_price': float(plan.yearly_price),
                        'updated_at': plan.updated_at.isoformat()
                    }
                    for plan in recent_updates
                ]
            }
            
            # Broadcast to all cart groups
            # In production, you'd want to be more selective
            await channel_layer.group_send(
                'cart_updates',  # Global cart updates group
                {
                    'type': 'price_update',
                    'pricing': pricing_data
                }
            )
            
    except Exception as e:
        print(f"Error in price update broadcast: {e}")


# Utility functions for external triggers
async def trigger_cart_update(user_id=None, session_key=None, update_type='cart_updated', data=None):
    """
    Utility function to trigger cart updates from views or other parts of the app
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    
    if user_id:
        group_name = f"cart_user_{user_id}"
    elif session_key:
        group_name = f"cart_session_{session_key}"
    else:
        return
    
    message = {
        'type': update_type,
        'sender_channel': 'system',
        **(data or {})
    }
    
    await channel_layer.group_send(group_name, message)
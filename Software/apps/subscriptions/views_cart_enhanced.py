# Enhanced Cart Views for PWA and Real-time features
import json
import hashlib
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction

from .models import Cart, CartItem, Plan
from .services import CartService


@login_required
@require_http_methods(["GET"])
def cart_status(request):
    """
    API endpoint para verificar el estado del carrito
    Usado por WebSocket polling fallback y PWA sync
    """
    try:
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        
        if not cart:
            return JsonResponse({
                'success': True,
                'updated': False,
                'cart': {
                    'total_items': 0,
                    'total_amount': 0,
                    'items': []
                }
            })
        
        # Generate cart hash for change detection
        cart_data = {
            'total_items': cart.total_items,
            'total_amount': float(cart.total_amount),
            'items': [
                {
                    'id': str(item.id),
                    'plan_name': item.plan.name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'subtotal': float(item.subtotal)
                }
                for item in cart.items.all()
            ]
        }
        
        # Check if cart has been updated since last check
        cart_hash = hashlib.md5(
            json.dumps(cart_data, sort_keys=True).encode()
        ).hexdigest()
        
        last_hash = cache.get(f'cart_hash_{request.user.id}')
        updated = last_hash != cart_hash
        
        if updated:
            cache.set(f'cart_hash_{request.user.id}', cart_hash, 300)  # 5 min cache
        
        return JsonResponse({
            'success': True,
            'updated': updated,
            'cart': cart_data,
            'hash': cart_hash,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def update_cart_item_api(request):
    """
    API optimizada para actualizar items del carrito
    Compatible con Service Worker background sync
    """
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        if not item_id or quantity < 1:
            return JsonResponse({
                'success': False,
                'error': 'Datos inválidos'
            }, status=400)
        
        # Get cart item
        try:
            cart_item = CartItem.objects.select_related('cart', 'plan').get(
                id=item_id,
                cart__user=request.user,
                cart__is_active=True
            )
        except CartItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Item no encontrado'
            }, status=404)
        
        # Update quantity
        with transaction.atomic():
            cart_item.quantity = quantity
            cart_item.save()
            
            # Recalculate cart totals
            cart = cart_item.cart
            cart.save()  # This triggers the total calculation
        
        # Return updated cart data
        return JsonResponse({
            'success': True,
            'message': f'Cantidad actualizada a {quantity}',
            'cart': {
                'total_items': cart.total_items,
                'total_amount': float(cart.total_amount)
            },
            'item': {
                'id': str(cart_item.id),
                'quantity': cart_item.quantity,
                'subtotal': float(cart_item.subtotal)
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def sync_offline_actions(request):
    """
    Sincronizar acciones realizadas offline
    Usado por Service Worker background sync
    """
    try:
        data = json.loads(request.body)
        actions = data.get('actions', [])
        
        if not actions:
            return JsonResponse({
                'success': True,
                'message': 'No hay acciones para sincronizar',
                'synced_count': 0
            })
        
        synced_count = 0
        failed_actions = []
        
        with transaction.atomic():
            for action in actions:
                try:
                    action_type = action.get('action')
                    action_data = action.get('data', {})
                    timestamp = action.get('timestamp')
                    
                    if action_type == 'update_item':
                        item_id = action_data.get('itemId')
                        quantity = action_data.get('quantity')
                        
                        cart_item = CartItem.objects.get(
                            id=item_id,
                            cart__user=request.user,
                            cart__is_active=True
                        )
                        cart_item.quantity = quantity
                        cart_item.save()
                        
                    elif action_type == 'remove_item':
                        plan_id = action_data.get('planId')
                        billing_cycle = action_data.get('billingCycle')
                        
                        CartItem.objects.filter(
                            cart__user=request.user,
                            cart__is_active=True,
                            plan_id=plan_id,
                            billing_cycle=billing_cycle
                        ).delete()
                        
                    elif action_type == 'clear_cart':
                        Cart.objects.filter(
                            user=request.user,
                            is_active=True
                        ).delete()
                    
                    synced_count += 1
                    
                except Exception as e:
                    failed_actions.append({
                        'action': action,
                        'error': str(e)
                    })
        
        return JsonResponse({
            'success': True,
            'message': f'{synced_count} acciones sincronizadas',
            'synced_count': synced_count,
            'failed_count': len(failed_actions),
            'failed_actions': failed_actions[:5]  # Limit error details
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error en sincronización: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def backup_cart_data(request):
    """
    Crear backup del carrito en el servidor
    Para recuperación cross-device
    """
    try:
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        
        if not cart:
            return JsonResponse({
                'success': True,
                'backup': None,
                'message': 'No hay carrito activo para respaldar'
            })
        
        backup_data = {
            'user_id': request.user.id,
            'cart_id': str(cart.id),
            'items': [
                {
                    'plan_id': item.plan.id,
                    'billing_cycle': item.billing_cycle,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price)
                }
                for item in cart.items.all()
            ],
            'timestamp': timezone.now().isoformat(),
            'device_info': {
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': request.META.get('REMOTE_ADDR', '')
            }
        }
        
        # Store backup in cache with 7-day expiry
        backup_key = f'cart_backup_{request.user.id}'
        cache.set(backup_key, backup_data, 604800)  # 7 days
        
        return JsonResponse({
            'success': True,
            'backup': {
                'items_count': len(backup_data['items']),
                'timestamp': backup_data['timestamp']
            },
            'message': 'Carrito respaldado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al respaldar carrito: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def restore_cart_data(request):
    """
    Restaurar carrito desde backup
    Para recuperación cross-device
    """
    try:
        backup_key = f'cart_backup_{request.user.id}'
        backup_data = cache.get(backup_key)
        
        if not backup_data:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró backup del carrito'
            }, status=404)
        
        # Check if backup is recent (within 7 days)
        backup_time = datetime.fromisoformat(backup_data['timestamp'].replace('Z', '+00:00'))
        if (timezone.now() - backup_time).days > 7:
            return JsonResponse({
                'success': False,
                'error': 'El backup es demasiado antiguo'
            }, status=400)
        
        # Clear existing cart
        Cart.objects.filter(user=request.user, is_active=True).delete()
        
        # Restore items
        with transaction.atomic():
            cart = Cart.objects.create(user=request.user, is_active=True)
            
            restored_items = []
            for item_data in backup_data['items']:
                try:
                    plan = Plan.objects.get(id=item_data['plan_id'])
                    
                    cart_item = CartItem.objects.create(
                        cart=cart,
                        plan=plan,
                        billing_cycle=item_data['billing_cycle'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price']
                    )
                    
                    restored_items.append({
                        'plan_name': plan.name,
                        'quantity': cart_item.quantity
                    })
                    
                except Plan.DoesNotExist:
                    continue  # Skip items with deleted plans
        
        return JsonResponse({
            'success': True,
            'message': f'Carrito restaurado con {len(restored_items)} items',
            'restored_items': restored_items,
            'backup_date': backup_data['timestamp']
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al restaurar carrito: {str(e)}'
        }, status=500)
# URL patterns para nuevas funcionalidades del carrito
from django.urls import path
from . import views

app_name = 'cart_enhanced'

urlpatterns = [
    # Existing cart URLs...
    
    # New enhanced cart URLs
    path('api/cart/status/', views.cart_status, name='cart_status'),
    path('api/cart/update/', views.update_cart_item_api, name='update_cart_item_api'),
    path('api/cart/sync/', views.sync_offline_actions, name='sync_offline_actions'),
    path('api/cart/backup/', views.backup_cart_data, name='backup_cart_data'),
    path('api/cart/restore/', views.restore_cart_data, name='restore_cart_data'),
]
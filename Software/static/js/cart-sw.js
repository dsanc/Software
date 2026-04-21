// Cart Service Worker for PWA capabilities
const CACHE_NAME = 'cart-cache-v1';
const STATIC_CACHE = 'static-cache-v1';

// Cache static resources (only cache existing files)
const staticResources = [
    '/static/css/main.css',
    '/static/js/main.js'
    // Other resources will be cached on first fetch
];

// Install event - cache static resources
self.addEventListener('install', event => {
    console.log('Cart Service Worker installing...');
    
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE).then(cache => {
                // Try to cache resources, ignore failures for missing files
                return Promise.allSettled(
                    staticResources.map(url => cache.add(url).catch(err => {
                        console.log(`Skipping cache for ${url}: not found`);
                        return null;
                    }))
                );
            }),
            self.skipWaiting()
        ])
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Cart Service Worker activating...');
    
    event.waitUntil(
        Promise.all([
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME && cacheName !== STATIC_CACHE) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            }),
            self.clients.claim()
        ])
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    
    // Cart API requests - Network First with fallback
    if (url.pathname.includes('/subscriptions/')) {
        event.respondWith(networkFirstWithFallback(event.request));
    }
    // Static resources - Cache First
    else if (isStaticResource(event.request)) {
        event.respondWith(cacheFirst(event.request));
    }
    // HTML pages - Network First
    else if (event.request.mode === 'navigate') {
        event.respondWith(networkFirstWithFallback(event.request));
    }
});

// Background sync for offline cart actions
self.addEventListener('sync', event => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'cart-sync') {
        event.waitUntil(syncCartActions());
    }
});

// Push notifications for cart updates
self.addEventListener('push', event => {
    console.log('Push notification received:', event);
    
    const options = {
        body: event.data ? event.data.text() : 'Tu carrito ha sido actualizado',
        icon: '/static/images/cart-icon.png',
        badge: '/static/images/badge.png',
        vibrate: [200, 100, 200],
        data: {
            url: '/subscriptions/cart/'
        },
        actions: [
            {
                action: 'view',
                title: 'Ver Carrito',
                icon: '/static/images/view-icon.png'
            },
            {
                action: 'dismiss',
                title: 'Cerrar',
                icon: '/static/images/close-icon.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Carrito Actualizado', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event);
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            self.clients.openWindow(event.notification.data.url)
        );
    }
});

// =========================== HELPER FUNCTIONS ===========================

async function networkFirstWithFallback(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Network failed, trying cache:', error);
        
        // Fallback to cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // If it's a cart request, return offline page
        if (request.url.includes('/cart/')) {
            return new Response(
                JSON.stringify({
                    success: false,
                    message: 'Conexión offline. Los cambios se sincronizarán automáticamente.',
                    offline: true
                }),
                {
                    headers: { 'Content-Type': 'application/json' },
                    status: 200
                }
            );
        }
        
        // For other requests, return a basic error response
        throw error;
    }
}

async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Failed to fetch resource:', request.url);
        throw error;
    }
}

function isStaticResource(request) {
    const url = new URL(request.url);
    return url.pathname.startsWith('/static/') || 
           url.pathname.endsWith('.css') || 
           url.pathname.endsWith('.js') || 
           url.pathname.endsWith('.png') || 
           url.pathname.endsWith('.jpg') || 
           url.pathname.endsWith('.svg');
}

async function syncCartActions() {
    try {
        // Get stored offline actions
        const data = await getStoredData('cart_offline_queue');
        
        if (!data || data.length === 0) {
            console.log('No offline cart actions to sync');
            return;
        }
        
        console.log(`Syncing ${data.length} offline cart actions`);
        
        for (const action of data) {
            try {
                await syncSingleAction(action);
            } catch (error) {
                console.error('Failed to sync action:', action, error);
            }
        }
        
        // Clear the queue after successful sync
        await clearStoredData('cart_offline_queue');
        
        // Notify main thread about successful sync
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'sync_complete',
                success: true
            });
        });
        
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

async function syncSingleAction(action) {
    const { action: actionType, data, timestamp } = action;
    
    let url = '';
    let method = 'POST';
    let body = JSON.stringify(data);
    
    switch (actionType) {
        case 'update_item':
            url = '/subscriptions/api/cart/update/';
            body = JSON.stringify({
                item_id: data.itemId,
                quantity: data.quantity
            });
            break;
            
        case 'remove_item':
            url = '/subscriptions/api/cart/remove/';
            body = JSON.stringify({
                plan_id: data.planId,
                billing_cycle: data.billingCycle
            });
            break;
            
        case 'clear_cart':
            url = '/subscriptions/api/cart/clear/';
            body = JSON.stringify({});
            break;
            
        default:
            throw new Error(`Unknown action type: ${actionType}`);
    }
    
    const response = await fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
        body
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
}

// IndexedDB helpers for persistent storage
async function getStoredData(key) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('CartDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['cart_data'], 'readonly');
            const store = transaction.objectStore('cart_data');
            const getRequest = store.get(key);
            
            getRequest.onsuccess = () => resolve(getRequest.result?.data);
            getRequest.onerror = () => reject(getRequest.error);
        };
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('cart_data')) {
                db.createObjectStore('cart_data', { keyPath: 'key' });
            }
        };
    });
}

async function clearStoredData(key) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('CartDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['cart_data'], 'readwrite');
            const store = transaction.objectStore('cart_data');
            const deleteRequest = store.delete(key);
            
            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => reject(deleteRequest.error);
        };
    });
}
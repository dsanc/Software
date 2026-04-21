"""
Views para funcionalidades PWA del módulo risk_hoteles
"""
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
import json
import os


def manifest_json(request):
    """Generar manifest.json para PWA"""
    manifest = {
        "name": "Risk Hoteles - Análisis de Riesgo",
        "short_name": "Risk Hoteles",
        "description": "Sistema de análisis de riesgo para hoteles",
        "start_url": "/risk-hoteles/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#2563eb",
        "orientation": "portrait-primary",
        "scope": "/",
        "icons": [
            {
                "src": "/static/images/icons/icon-72x72.png",
                "sizes": "72x72",
                "type": "image/png"
            },
            {
                "src": "/static/images/icons/icon-96x96.png",
                "sizes": "96x96",
                "type": "image/png"
            },
            {
                "src": "/static/images/icons/icon-128x128.png",
                "sizes": "128x128",
                "type": "image/png"
            },
            {
                "src": "/static/images/icons/icon-144x144.png",
                "sizes": "144x144",
                "type": "image/png"
            },
            {
                "src": "/static/images/icons/icon-152x152.png",
                "sizes": "152x152",
                "type": "image/png"
            },
            {
                "src": "/static/images/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/images/icons/icon-384x384.png",
                "sizes": "384x384",
                "type": "image/png"
            },
            {
                "src": "/static/images/icons/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "shortcuts": [
            {
                "name": "Dashboard",
                "short_name": "Dashboard",
                "description": "Ver dashboard principal",
                "url": "/risk-hoteles/",
                "icons": [{"src": "/static/images/icons/icon-96x96.png", "sizes": "96x96"}]
            },
            {
                "name": "Hoteles",
                "short_name": "Hoteles",
                "description": "Lista de hoteles",
                "url": "/risk-hoteles/hoteles/",
                "icons": [{"src": "/static/images/icons/icon-96x96.png", "sizes": "96x96"}]
            },
            {
                "name": "Alertas",
                "short_name": "Alertas",
                "description": "Ver alertas activas",
                "url": "/risk-hoteles/alertas/",
                "icons": [{"src": "/static/images/icons/icon-96x96.png", "sizes": "96x96"}]
            }
        ]
    }
    
    return JsonResponse(manifest, json_dumps_params={'indent': 2})


@cache_control(max_age=86400)  # Cache por 24 horas
def service_worker(request):
    """Servir el service worker"""
    service_worker_content = """
// Service Worker para Risk Hoteles PWA
const CACHE_NAME = 'risk-hoteles-v1';
const STATIC_CACHE_NAME = 'risk-hoteles-static-v1';
const DYNAMIC_CACHE_NAME = 'risk-hoteles-dynamic-v1';

// Recursos estáticos para cachear
const STATIC_ASSETS = [
    '/static/css/styles.css',
    '/static/js/app.js',
    '/static/images/logo.png',
    '/static/images/icons/icon-192x192.png',
    '/static/images/icons/icon-512x512.png',
    '/risk-hoteles/',
    '/risk-hoteles/hoteles/',
    '/risk-hoteles/dashboard/',
];

// Instalar Service Worker
self.addEventListener('install', event => {
    console.log('Service Worker instalando...');
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                console.log('Cacheando recursos estáticos');
                return cache.addAll(STATIC_ASSETS.map(url => new Request(url, {credentials: 'same-origin'})));
            })
            .catch(error => {
                console.error('Error cacheando recursos estáticos:', error);
                // Continuar sin fallar si algunos recursos no se pueden cachear
                return Promise.resolve();
            })
    );
    self.skipWaiting();
});

// Activar Service Worker
self.addEventListener('activate', event => {
    console.log('Service Worker activando...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
                        console.log('Eliminando cache obsoleto:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Interceptar requests
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Skip non-http requests
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    // Skip chrome-extension requests
    if (url.protocol === 'chrome-extension:') {
        return;
    }
    
    event.respondWith(
        caches.match(request)
            .then(response => {
                // Si está en cache, devolverlo
                if (response) {
                    return response;
                }
                
                // Si no, hacer fetch y cachear dinámicamente
                return fetch(request)
                    .then(fetchResponse => {
                        // Solo cachear respuestas exitosas
                        if (fetchResponse.status === 200) {
                            const responseClone = fetchResponse.clone();
                            
                            // Cachear contenido dinámico
                            if (shouldCacheDynamically(request)) {
                                caches.open(DYNAMIC_CACHE_NAME)
                                    .then(cache => {
                                        cache.put(request, responseClone);
                                    });
                            }
                        }
                        
                        return fetchResponse;
                    })
                    .catch(error => {
                        console.error('Error en fetch:', error);
                        
                        // Devolver página offline si está disponible
                        if (request.destination === 'document') {
                            return caches.match('/offline/') || new Response('Offline', {status: 503});
                        }
                        
                        throw error;
                    });
            })
    );
});

// Determinar si se debe cachear dinámicamente
function shouldCacheDynamically(request) {
    const url = new URL(request.url);
    
    // Cachear páginas del proyecto
    if (url.pathname.startsWith('/risk-hoteles/')) {
        return true;
    }
    
    // Cachear APIs de datos
    if (url.pathname.startsWith('/api/')) {
        return true;
    }
    
    // Cachear recursos estáticos
    if (url.pathname.startsWith('/static/')) {
        return true;
    }
    
    return false;
}

// Manejar mensajes del cliente
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// Notificaciones push (si se implementan)
self.addEventListener('push', event => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/static/images/icons/icon-192x192.png',
            badge: '/static/images/icons/icon-96x96.png',
            vibrate: [200, 100, 200],
            data: data.data || {},
            actions: data.actions || []
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Manejar clicks en notificaciones
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.action) {
        // Manejar acciones específicas
        event.waitUntil(
            clients.openWindow(event.action)
        );
    } else {
        // Abrir la aplicación
        event.waitUntil(
            clients.matchAll().then(clientList => {
                if (clientList.length > 0) {
                    return clientList[0].focus();
                }
                return clients.openWindow('/risk-hoteles/');
            })
        );
    }
});
"""
    
    return HttpResponse(
        service_worker_content,
        content_type='application/javascript'
    )


@login_required
def pwa_install_prompt(request):
    """Vista para mostrar prompt de instalación PWA"""
    context = {
        'title': 'Instalar Risk Hoteles',
        'app_name': 'Risk Hoteles',
        'description': 'Instala la aplicación para acceso rápido y funcionalidad offline'
    }
    return render(request, 'risk_hoteles/pwa/install_prompt.html', context)


@csrf_exempt
def pwa_install_event(request):
    """Registrar evento de instalación PWA"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Aquí podrías registrar el evento en analytics
            # AnalyticsEvent.objects.create(
            #     user=request.user if request.user.is_authenticated else None,
            #     event_type='pwa_install',
            #     event_data=data
            # )
            
            return JsonResponse({
                'success': True,
                'message': 'Evento registrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)


def offline_page(request):
    """Página offline para PWA"""
    context = {
        'title': 'Sin conexión',
        'message': 'No hay conexión a internet disponible',
        'retry_url': request.GET.get('url', '/risk-hoteles/')
    }
    return render(request, 'risk_hoteles/pwa/offline.html', context)


@login_required
def pwa_settings(request):
    """Configuraciones PWA"""
    context = {
        'title': 'Configuraciones PWA',
        'notifications_enabled': request.user.profile.notifications_enabled if hasattr(request.user, 'profile') else False,
        'offline_mode': True,
        'cache_size': get_cache_size(),
    }
    return render(request, 'risk_hoteles/pwa/settings.html', context)


def get_cache_size():
    """Obtener tamaño estimado del cache"""
    # En un entorno real, esto podría calcularse desde el cliente
    return "~5 MB"


@csrf_exempt
def clear_cache(request):
    """Limpiar cache PWA"""
    if request.method == 'POST':
        try:
            # En el cliente se ejecutaría la limpieza del cache
            return JsonResponse({
                'success': True,
                'message': 'Cache limpiado correctamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)


def check_update(request):
    """Verificar actualizaciones de la PWA"""
    # Versión actual (podría venir de settings o base de datos)
    current_version = "1.0.0"
    
    return JsonResponse({
        'current_version': current_version,
        'update_available': False,
        'update_url': '/risk-hoteles/update/',
        'release_notes': []
    })


def pwa_share(request):
    """Funcionalidad de compartir PWA"""
    context = {
        'title': 'Compartir Risk Hoteles',
        'description': 'Sistema de análisis de riesgo para hoteles',
        'url': request.build_absolute_uri('/risk-hoteles/'),
        'image': request.build_absolute_uri('/static/images/share-image.png')
    }
    return render(request, 'risk_hoteles/pwa/share.html', context)


def browserconfig_xml(request):
    """Generar browserconfig.xml para Windows"""
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square70x70logo src="/static/images/icons/icon-70x70.png"/>
            <square150x150logo src="/static/images/icons/icon-150x150.png"/>
            <square310x310logo src="/static/images/icons/icon-310x310.png"/>
            <TileColor>#2563eb</TileColor>
        </tile>
    </msapplication>
</browserconfig>"""
    
    return HttpResponse(xml_content, content_type='application/xml')


@csrf_exempt
def push_subscription(request):
    """Manejar suscripciones push"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Aquí guardarías la suscripción en la base de datos
            # PushSubscription.objects.create(
            #     user=request.user if request.user.is_authenticated else None,
            #     endpoint=data['endpoint'],
            #     p256dh=data['keys']['p256dh'],
            #     auth=data['keys']['auth']
            # )
            
            return JsonResponse({
                'success': True,
                'message': 'Suscripción registrada'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    elif request.method == 'DELETE':
        try:
            # Eliminar suscripción
            return JsonResponse({
                'success': True,
                'message': 'Suscripción eliminada'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)
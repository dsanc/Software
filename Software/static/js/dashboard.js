// Dashboard JavaScript - Funcionalidades interactivas
document.addEventListener('DOMContentLoaded', function() {
    
    // Animación de entrada mejorada para las tarjetas
    const cards = document.querySelectorAll('.dashboard-card, .user-info-card, .quick-actions-card');
    
    // Observador de intersección para animaciones al hacer scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Aplicar observador a todas las tarjetas
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
    
    // Efectos hover mejorados para las tarjetas del dashboard
    const dashboardCards = document.querySelectorAll('.dashboard-card');
    
    dashboardCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
            this.style.transition = 'all 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Animación de click para botones
    const buttons = document.querySelectorAll('.btn-dashboard, .btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Crear efecto ripple
            let ripple = document.createElement('span');
            ripple.classList.add('ripple');
            this.appendChild(ripple);
            
            let x = e.clientX - e.target.offsetLeft;
            let y = e.clientY - e.target.offsetTop;
            
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Tooltip personalizado para elementos con texto truncado
    const textElements = document.querySelectorAll('.card-text, .card-title');
    
    textElements.forEach(element => {
        if (element.scrollWidth > element.clientWidth) {
            element.setAttribute('title', element.textContent);
        }
    });
    
    // Contador animado para números en el dashboard
    function animateNumber(element, finalNumber, duration = 2000) {
        const startNumber = 0;
        const increment = finalNumber / (duration / 16);
        let currentNumber = startNumber;
        
        const timer = setInterval(() => {
            currentNumber += increment;
            if (currentNumber >= finalNumber) {
                currentNumber = finalNumber;
                clearInterval(timer);
            }
            element.textContent = Math.floor(currentNumber);
        }, 16);
    }
    
    // Detectar elementos con números para animar
    const numberElements = document.querySelectorAll('[data-animate-number]');
    numberElements.forEach(element => {
        const number = parseInt(element.getAttribute('data-animate-number'));
        animateNumber(element, number);
    });
    
    // Funcionalidad de refresco de datos
    function refreshDashboardData() {
        const refreshButton = document.querySelector('#refresh-dashboard');
        if (refreshButton) {
            refreshButton.addEventListener('click', function() {
                // Agregar efecto de carga
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Actualizando...';
                this.disabled = true;
                
                // Simular carga de datos (aquí se haría una llamada AJAX real)
                setTimeout(() => {
                    this.innerHTML = '<i class="fas fa-sync-alt"></i> Actualizar';
                    this.disabled = false;
                    
                    // Mostrar mensaje de éxito
                    showNotification('Datos actualizados correctamente', 'success');
                }, 2000);
            });
        }
    }
    
    // Sistema de notificaciones
    function showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
    
    // Lazy loading para contenido pesado
    const lazyElements = document.querySelectorAll('[data-lazy]');
    
    const lazyObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const src = element.getAttribute('data-lazy');
                
                if (element.tagName === 'IMG') {
                    element.src = src;
                } else {
                    // Cargar contenido dinámico
                    loadDynamicContent(element, src);
                }
                
                lazyObserver.unobserve(element);
            }
        });
    });
    
    lazyElements.forEach(element => {
        lazyObserver.observe(element);
    });
    
    // Función para cargar contenido dinámico
    function loadDynamicContent(element, url) {
        fetch(url)
            .then(response => response.text())
            .then(html => {
                element.innerHTML = html;
                element.classList.add('loaded');
            })
            .catch(error => {
                console.error('Error loading content:', error);
                element.innerHTML = '<p class="text-muted">Error al cargar el contenido</p>';
            });
    }
    
    // Detectar cambios de orientación en móviles
    window.addEventListener('orientationchange', function() {
        setTimeout(() => {
            // Reajustar elementos si es necesario
            cards.forEach(card => {
                card.style.transition = 'none';
                // Force reflow
                card.offsetHeight;
                card.style.transition = '';
            });
        }, 100);
    });
    
    // Gestión de estado offline/online
    window.addEventListener('online', function() {
        showNotification('Conexión restablecida', 'success');
    });
    
    window.addEventListener('offline', function() {
        showNotification('Sin conexión a internet', 'warning');
    });
    
    // Inicializar funcionalidades
    refreshDashboardData();
    
    // Preloader para la página
    const preloader = document.querySelector('#page-preloader');
    if (preloader) {
        setTimeout(() => {
            preloader.style.opacity = '0';
            setTimeout(() => {
                preloader.remove();
            }, 300);
        }, 500);
    }
    
    // Agregar estilos CSS para efectos JavaScript
    const style = document.createElement('style');
    style.textContent = `
        .ripple {
            position: absolute;
            border-radius: 50%;
            background-color: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            pointer-events: none;
        }
        
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .dashboard-card {
            transition: all 0.3s ease !important;
        }
        
        .loaded {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        #page-preloader {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: white;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: opacity 0.3s ease;
        }
    `;
    
    document.head.appendChild(style);
});

// Funciones globales disponibles
window.DashboardUtils = {
    showNotification: function(message, type = 'info', duration = 3000) {
        // Implementation moved to internal function above
    },
    
    refreshCard: function(cardSelector) {
        const card = document.querySelector(cardSelector);
        if (card) {
            card.style.opacity = '0.5';
            // Simulate refresh
            setTimeout(() => {
                card.style.opacity = '1';
            }, 1000);
        }
    },
    
    addCardLoadingState: function(cardSelector) {
        const card = document.querySelector(cardSelector);
        if (card) {
            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
            overlay.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255,255,255,0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10;
            `;
            
            card.style.position = 'relative';
            card.appendChild(overlay);
            
            return overlay;
        }
    },
    
    removeCardLoadingState: function(cardSelector) {
        const card = document.querySelector(cardSelector);
        if (card) {
            const overlay = card.querySelector('.loading-overlay');
            if (overlay) {
                overlay.remove();
            }
        }
    }
};
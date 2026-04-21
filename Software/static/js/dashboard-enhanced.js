/**
 * Dashboard Enhanced JavaScript
 * Versión: 2.0 - Noviembre 2025 - Updated 19:21
 * Funciones mejoradas para el dashboard con mejor rendimiento y accesibilidad
 * FIXED: e.target.matches TypeError
 */

class DashboardEnhanced {
    constructor() {
        this.animationSpeed = 1000;
        this.updateInterval = 60000; // 1 minuto
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initAnimatedCounters();
        this.initMetricCounters();
        this.startRealtimeClock();
        this.initTooltips();
        this.initProgressBars();
        this.initSkeletonLoaders();
        this.initAccessibility();
    }

    setupEventListeners() {
        // Listener para resize de ventana
        window.addEventListener('resize', this.debounce(() => {
            this.updateLayoutResponsive();
        }, 250));

        // Listener para prefetch de páginas
        document.addEventListener('mouseenter', (e) => {
            // Debug: verificar que la versión corregida esté cargada
            if (!window.debugEnhancedFixLogged) {
                console.log('✅ DashboardEnhanced: Fix para e.target.matches aplicado correctamente');
                window.debugEnhancedFixLogged = true;
            }
            
            if (e.target && typeof e.target.matches === 'function' && e.target.matches('a[href^="/"]')) {
                this.prefetchPage(e.target.href);
            }
        }, true);

        // Listener para animaciones de scroll
        window.addEventListener('scroll', this.throttle(() => {
            this.updateScrollAnimations();
        }, 16));
    }

    initAnimatedCounters() {
        const counters = document.querySelectorAll('[data-counter]');
        
        // Usar Intersection Observer para animar solo cuando sea visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.hasAttribute('data-animated')) {
                    const target = parseInt(entry.target.getAttribute('data-counter'));
                    this.animateCounter(entry.target, 0, target, this.animationSpeed);
                    entry.target.setAttribute('data-animated', 'true');
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(counter => observer.observe(counter));
    }

    animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        
        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Función de easing cubic-bezier
            const easeProgress = this.easeOutCubic(progress);
            const value = Math.floor(start + (end - start) * easeProgress);
            
            element.textContent = this.formatNumber(value);
            
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = this.formatNumber(end);
                this.triggerCounterComplete(element);
            }
        };
        
        requestAnimationFrame(update);
    }

    formatNumber(num) {
        // Formatear números con separadores de miles si es necesario
        if (num >= 1000) {
            return num.toLocaleString('es-ES');
        }
        return num;
    }

    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    triggerCounterComplete(element) {
        // Agregar efecto visual cuando el contador termine
        element.style.transform = 'scale(1.1)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }

    startRealtimeClock() {
        const clockElement = document.getElementById('current-time');
        if (!clockElement) return;

        const updateClock = () => {
            const now = new Date();
            const time = now.toLocaleTimeString('es-ES', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: false 
            });
            clockElement.textContent = time;
        };

        updateClock(); // Actualizar inmediatamente
        setInterval(updateClock, 1000); // Actualizar cada segundo
    }

    initTooltips() {
        // Inicializar tooltips con configuración mejorada
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        
        this.tooltips = tooltipTriggerList.map(tooltipTriggerEl => {
            return new bootstrap.Tooltip(tooltipTriggerEl, {
                delay: { show: 500, hide: 100 },
                trigger: 'hover focus',
                placement: 'auto',
                customClass: 'tooltip-enhanced'
            });
        });
    }

    initProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const width = bar.style.width || bar.getAttribute('aria-valuenow') + '%';
                    
                    // Animar el progreso
                    bar.style.width = '0%';
                    setTimeout(() => {
                        bar.style.width = width;
                        bar.style.transition = 'width 1s cubic-bezier(0.4, 0, 0.2, 1)';
                    }, 100);
                }
            });
        }, { threshold: 0.3 });

        progressBars.forEach(bar => observer.observe(bar));
    }

    initSkeletonLoaders() {
        // Simular carga de datos y remover skeletons
        const skeletons = document.querySelectorAll('.skeleton');
        
        if (skeletons.length > 0) {
            setTimeout(() => {
                skeletons.forEach(skeleton => {
                    skeleton.classList.remove('skeleton');
                    skeleton.style.opacity = '0';
                    setTimeout(() => {
                        skeleton.style.opacity = '1';
                        skeleton.style.transition = 'opacity 0.3s ease';
                    }, 50);
                });
            }, 300);
        }
    }

    initAccessibility() {
        // Mejorar navegación con teclado
        this.setupKeyboardNavigation();
        
        // Agregar skip links
        this.addSkipLinks();
        
        // Anunciar cambios dinámicos
        this.setupLiveRegion();
    }

    setupKeyboardNavigation() {
        // Manejar navegación con Tab más fluida
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('using-keyboard');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('using-keyboard');
        });

        // Mejorar foco en cards
        const cards = document.querySelectorAll('.dashboard-card');
        cards.forEach(card => {
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    const link = card.querySelector('a');
                    if (link) {
                        e.preventDefault();
                        link.click();
                    }
                }
            });
        });
    }

    addSkipLinks() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Saltar al contenido principal';
        skipLink.className = 'skip-link sr-only-focusable';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--dashboard-primary);
            color: white;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 9999;
        `;
        
        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });

        document.body.prepend(skipLink);
    }

    setupLiveRegion() {
        // Crear región ARIA para anuncios dinámicos
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.id = 'live-region';
        document.body.appendChild(liveRegion);

        this.liveRegion = liveRegion;
    }

    announce(message) {
        if (this.liveRegion) {
            this.liveRegion.textContent = message;
            setTimeout(() => {
                this.liveRegion.textContent = '';
            }, 1000);
        }
    }

    updateLayoutResponsive() {
        // Actualizar layout para diferentes tamaños de pantalla
        const cards = document.querySelectorAll('.dashboard-card');
        const isSmallScreen = window.innerWidth < 768;

        cards.forEach(card => {
            if (isSmallScreen) {
                card.style.marginBottom = '1rem';
            } else {
                card.style.marginBottom = '';
            }
        });
    }

    updateScrollAnimations() {
        const scrollY = window.scrollY;
        const cards = document.querySelectorAll('.dashboard-card');

        cards.forEach((card, index) => {
            const rect = card.getBoundingClientRect();
            const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
            
            if (isVisible) {
                const translateY = scrollY * 0.1 * (index % 2 === 0 ? 1 : -1);
                card.style.transform = `translateY(${Math.min(translateY, 10)}px)`;
            }
        });
    }

    prefetchPage(url) {
        // Prefetch inteligente de páginas para mejorar rendimiento
        if (this.prefetchedPages?.has(url)) return;
        
        if (!this.prefetchedPages) {
            this.prefetchedPages = new Set();
        }

        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
        
        this.prefetchedPages.add(url);
    }

    // Utility functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // API para interacciones externas
    static getInstance() {
        if (!window.dashboardInstance) {
            window.dashboardInstance = new DashboardEnhanced();
        }
        return window.dashboardInstance;
    }

    updateMetric(metricId, newValue) {
        const element = document.querySelector(`[data-counter="${metricId}"]`);
        if (element) {
            const currentValue = parseInt(element.textContent);
            this.animateCounter(element, currentValue, newValue, 500);
            this.announce(`Métrica actualizada: ${newValue}`);
        }
    }

    showNotification(message, type = 'info') {
        // Sistema de notificaciones mejorado
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 300px;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);

        this.announce(message);
    }

    initMetricCounters() {
        const metricValues = document.querySelectorAll('.metric-value[data-target]');
        if (metricValues.length === 0) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.hasAttribute('data-animated')) {
                    const target = parseInt(entry.target.getAttribute('data-target'));
                    this.animateMetricCounter(entry.target, 0, target, 1000);
                    entry.target.setAttribute('data-animated', 'true');
                }
            });
        }, { threshold: 0.5 });

        metricValues.forEach(counter => observer.observe(counter));
    }

    animateMetricCounter(element, start, end, duration) {
        const startTime = performance.now();
        
        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const easeProgress = this.easeOutBack(progress);
            const value = Math.floor(start + (end - start) * easeProgress);
            
            element.textContent = this.formatNumber(value);
            
            // Agregar efecto de pulso durante la animación
            element.style.textShadow = `0 0 ${10 * (1 - progress)}px rgba(0, 123, 255, 0.3)`;
            
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = this.formatNumber(end);
                element.style.textShadow = '';
                this.triggerMetricComplete(element);
            }
        };
        
        requestAnimationFrame(update);
    }

    easeOutBack(t) {
        const c1 = 1.70158;
        const c3 = c1 + 1;
        return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
    }

    triggerMetricComplete(element) {
        // Efecto visual de completado para métricas
        const card = element.closest('.metric-card');
        if (card) {
            card.style.animation = 'metricComplete 0.6s ease-out';
            setTimeout(() => {
                card.style.animation = '';
            }, 600);
        }
    }
}

// Auto-inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    DashboardEnhanced.getInstance();
});

// Exportar para uso global
window.Dashboard = DashboardEnhanced;
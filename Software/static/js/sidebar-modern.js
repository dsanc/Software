    /**
     * Modern Sidebar Controller
     * Version: 2025 Edition
     */
    class ModernSidebar {
        constructor() {
            this.sidebar = null;
            this.overlay = null;
            this.toggleBtn = null;
            this.mobileToggleBtn = null;
            this.isCollapsed = false;
            this.isMobile = false;
            this.isAnimating = false;
            
            this.init();
        }

        init() {
            
            // Obtener elementos
            this.sidebar = document.getElementById('modernSidebar');
            this.overlay = document.getElementById('sidebarOverlay');
            this.toggleBtn = document.getElementById('sidebarToggle');
            this.mobileToggleBtn = document.getElementById('sidebarToggleMobile');
            
            if (!this.sidebar) {
                console.error('�O Sidebar no encontrado');
                return;
            }

            // Configurar estado inicial
            this.setupInitialState();
            
            // Configurar eventos
            this.setupEventListeners();
            
            // Configurar click en logo para cambiar modo
            this.setupLogoClickHandler();
            
            // Configurar navegación con teclado
            this.initKeyboardNavigation();
            
            // Configurar submenús
            this.setupSubmenus();
            
            // Configurar tooltips
            this.setupTooltips();
            
            // Configurar gestos móviles
            this.setupMobileGestures();
            
        }

        setupInitialState() {
            // Verificar estado guardado - POR DEFECTO COLAPSADO
            const savedState = localStorage.getItem('modernSidebarCollapsed');
            this.isCollapsed = savedState !== null ? savedState === 'true' : true; // true = colapsado por defecto
            this.isMobile = window.innerWidth <= 991;
            
            // Aplicar estado inicial
            this.updateSidebarState();
            
            // Inicializar logo display
            setTimeout(() => {
                this.updateLogoDisplay();
            }, 100);
            
        }

        setupEventListeners() {
            // Toggle desktop
            if (this.toggleBtn) {
                this.toggleBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggleSidebar();
                    this.updateAriaAttributes();
                });
                
                // Keyboard support for toggle
                this.toggleBtn.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.toggleSidebar();
                        this.updateAriaAttributes();
                    }
                });
            }

            // Toggle mobile
            if (this.mobileToggleBtn) {
                this.mobileToggleBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggleMobileSidebar();
                });
            }

            // Overlay click
            if (this.overlay) {
                this.overlay.addEventListener('click', () => {
                    this.closeMobileSidebar();
                });
            }

            // Resize handler
            window.addEventListener('resize', this.debounce(() => {
                this.handleResize();
            }, 250));

            // Enhanced keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isMobile) {
                    this.closeMobileSidebar();
                }
                // Alt + M para toggle sidebar (solo desktop)
                if (e.altKey && e.key === 'm' && !this.isMobile) {
                    e.preventDefault();
                    this.toggleSidebar();
                    this.updateAriaAttributes();
                }
            });
            
            // Hover effect para expandir sidebar cuando está colapsado (solo desktop)
            if (this.sidebar) {
                let hoverTimeout;
                
                this.sidebar.addEventListener('mouseenter', () => {
                    if (this.isCollapsed && !this.isMobile) {
                        clearTimeout(hoverTimeout);
                        this.sidebar.classList.add('hover-expanded');
                    }
                });
                
                this.sidebar.addEventListener('mouseleave', () => {
                    if (this.isCollapsed && !this.isMobile) {
                        // Pequeño delay para suavizar la transición
                        hoverTimeout = setTimeout(() => {
                            this.sidebar.classList.remove('hover-expanded');
                        }, 100);
                    }
                });
            }
        }

        setupSubmenus() {
            // Configurar submenús con manejo mejorado
            document.querySelectorAll('.has-submenu > .nav-link').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const item = e.target.closest('.has-submenu');
                    this.toggleSubmenu(item);
                    this.updateSubmenuAriaAttributes(item);
                });

                // Enhanced keyboard navigation
                link.addEventListener('keydown', (e) => {
                    const item = e.target.closest('.has-submenu');
                    
                    switch(e.key) {
                        case 'Enter':
                        case ' ':
                            e.preventDefault();
                            this.toggleSubmenu(item);
                            this.updateSubmenuAriaAttributes(item);
                            break;
                        case 'ArrowDown':
                            e.preventDefault();
                            this.focusNextMenuItem(e.target);
                            break;
                        case 'ArrowUp':
                            e.preventDefault();
                            this.focusPreviousMenuItem(e.target);
                            break;
                        case 'Home':
                            e.preventDefault();
                            this.focusFirstMenuItem();
                            break;
                        case 'End':
                            e.preventDefault();
                            this.focusLastMenuItem();
                            break;
                    }
                });
            });

        }

        // Nuevos métodos de accesibilidad
        updateAriaAttributes() {
            if (this.toggleBtn) {
                this.toggleBtn.setAttribute('aria-expanded', (!this.isCollapsed).toString());
            }
        }

        updateSubmenuAriaAttributes(item) {
            const link = item.querySelector('.nav-link');
            const submenu = item.querySelector('.submenu');
            const isActive = item.classList.contains('active');
            
            if (link) {
                link.setAttribute('aria-expanded', isActive.toString());
            }
        }

        focusNextMenuItem(currentElement) {
            const menuItems = Array.from(document.querySelectorAll('.nav-link[role="menuitem"]'));
            const currentIndex = menuItems.indexOf(currentElement);
            const nextIndex = (currentIndex + 1) % menuItems.length;
            menuItems[nextIndex].focus();
        }

        focusPreviousMenuItem(currentElement) {
            const menuItems = Array.from(document.querySelectorAll('.nav-link[role="menuitem"]'));
            const currentIndex = menuItems.indexOf(currentElement);
            const prevIndex = currentIndex <= 0 ? menuItems.length - 1 : currentIndex - 1;
            menuItems[prevIndex].focus();
        }

        focusFirstMenuItem() {
            const firstMenuItem = document.querySelector('.nav-link[role="menuitem"]');
            if (firstMenuItem) firstMenuItem.focus();
        }

        focusLastMenuItem() {
            const menuItems = document.querySelectorAll('.nav-link[role="menuitem"]');
            const lastMenuItem = menuItems[menuItems.length - 1];
            if (lastMenuItem) lastMenuItem.focus();
        }

        setupTooltips() {
            // Los tooltips se muestran automáticamente con CSS
            // Aquí podríamos agregar lógica adicional si es necesario
        }

        /**
         * Gestión de foco y navegación con teclado
         */
        initKeyboardNavigation() {
            // Permitir navegación con Tab y Arrow Keys
            this.sidebar.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e));
            
            // Gestión de foco al expandir/colapsar
            if (this.toggleBtn) {
                this.toggleBtn.addEventListener('focus', () => {
                    this.toggleBtn.setAttribute('aria-describedby', 'sidebar-toggle-help');
                });
            }
        }

        handleKeyboardNavigation(e) {
            const focusableElements = this.sidebar.querySelectorAll(
                'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
            );
            const focusableArray = Array.from(focusableElements);
            const currentIndex = focusableArray.indexOf(document.activeElement);

            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    const nextIndex = (currentIndex + 1) % focusableArray.length;
                    focusableArray[nextIndex]?.focus();
                    break;
                
                case 'ArrowUp':
                    e.preventDefault();
                    const prevIndex = currentIndex === 0 ? focusableArray.length - 1 : currentIndex - 1;
                    focusableArray[prevIndex]?.focus();
                    break;
                
                case 'Home':
                    e.preventDefault();
                    focusableArray[0]?.focus();
                    break;
                
                case 'End':
                    e.preventDefault();
                    focusableArray[focusableArray.length - 1]?.focus();
                    break;
            }
        }

        manageFocus(element) {
            // Asegurar que el elemento sea visible y focuseable
            if (element && typeof element.focus === 'function') {
                element.focus();
                element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }

        setupMobileGestures() {
            let touchStartX = 0;
            let touchStartY = 0;

            document.addEventListener('touchstart', (e) => {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
            }, { passive: true });

            document.addEventListener('touchend', (e) => {
                if (!touchStartX || !touchStartY) return;

                const touchEndX = e.changedTouches[0].clientX;
                const touchEndY = e.changedTouches[0].clientY;
                const diffX = touchStartX - touchEndX;
                const diffY = touchStartY - touchEndY;

                // Solo gestos horizontales
                if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 100) {
                    if (this.isMobile) {
                        const isVisible = this.sidebar.classList.contains('mobile-open');
                        
                        // Swipe right para abrir
                        if (diffX < 0 && touchStartX < 50 && !isVisible) {
                            this.openMobileSidebar();
                        }
                        
                        // Swipe left para cerrar
                        if (diffX > 0 && isVisible) {
                            this.closeMobileSidebar();
                        }
                    }
                }

                touchStartX = 0;
                touchStartY = 0;
            }, { passive: true });
        }

        toggleSidebar() {
            if (this.isAnimating || this.isMobile) return;
            
            this.isAnimating = true;
            const wasCollapsed = this.isCollapsed;
            this.isCollapsed = !this.isCollapsed;
            
            // Animación del botón
            this.animateToggleButton();
            
            // Actualizar estado
            this.updateSidebarState();
            
            // Gestión de foco mejorada
            if (wasCollapsed && !this.isCollapsed) {
                // Sidebar se expandió - devolver foco al primer elemento navegable
                setTimeout(() => {
                    const firstNavLink = this.sidebar.querySelector('.nav-link:not(.dropdown-toggle)');
                    this.manageFocus(firstNavLink);
                }, 300);
            }
            
            // Guardar estado
            localStorage.setItem('modernSidebarCollapsed', this.isCollapsed);
            
            setTimeout(() => {
                this.isAnimating = false;
            }, 300);
            
        }
        
        setupLogoClickHandler() {
            const logoContainer = document.querySelector('.logo-icon');
            const logoLink = document.querySelector('.sidebar-logo');
            
            if (logoContainer) {
                logoContainer.addEventListener('click', (e) => {
                    // Solo permitir cambio si está colapsado y no es mobile
                    if (this.isCollapsed && !this.isMobile) {
                        e.preventDefault();
                        e.stopPropagation();
                        this.cycleLogo();
                    }
                });
                
                // Prevenir navegación cuando está colapsado
                if (logoLink) {
                    logoLink.addEventListener('click', (e) => {
                        if (this.isCollapsed && !this.isMobile) {
                            e.preventDefault();
                        }
                    });
                }
                
            } else {
                console.warn('�s�️ Logo container no encontrado');
            }
        }

        toggleMobileSidebar() {
            const isOpen = this.sidebar.classList.contains('mobile-open');
            
            if (isOpen) {
                this.closeMobileSidebar();
            } else {
                this.openMobileSidebar();
            }
        }

        openMobileSidebar() {
            this.sidebar.classList.add('mobile-open');
            this.overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        closeMobileSidebar() {
            this.sidebar.classList.remove('mobile-open');
            this.overlay.classList.remove('active');
            document.body.style.overflow = '';
        }

        toggleSubmenu(item) {
            const isActive = item.classList.contains('active');
            
            // Cerrar otros submenús
            this.sidebar.querySelectorAll('.has-submenu.active').forEach(el => {
                if (el !== item) {
                    el.classList.remove('active');
                }
            });
            
            // Toggle este submenú
            if (isActive) {
                item.classList.remove('active');
            } else {
                item.classList.add('active');
            }
        }

        animateToggleButton() {
            if (this.toggleBtn) {
                this.toggleBtn.style.transform = 'rotate(180deg) scale(0.9)';
                setTimeout(() => {
                    this.toggleBtn.style.transform = '';
                }, 200);
            }
        }

        updateSidebarState() {
            const body = document.body;
            const logoContainer = document.querySelector('.logo-icon');
            
            if (this.isMobile) {
                // En móvil, solo manejar overlay
                body.classList.remove('sidebar-collapsed');
            } else {
                // En desktop, manejar collapsed state
                if (this.isCollapsed) {
                    this.sidebar.classList.add('collapsed');
                    body.classList.add('sidebar-collapsed');
                    
                    // Logo clickeable cuando está colapsado
                    if (logoContainer) {
                        logoContainer.style.cursor = 'pointer';
                        logoContainer.title = 'Click para cambiar logo';
                    }
                } else {
                    this.sidebar.classList.remove('collapsed');
                    body.classList.remove('sidebar-collapsed');
                    
                    // Logo no clickeable cuando está expandido
                    if (logoContainer) {
                        logoContainer.style.cursor = 'default';
                        logoContainer.title = '';
                    }
                }
            }
            
            // Actualizar logo según estado
            this.updateLogoDisplay();
        }
        
        updateLogoDisplay() {
            const logoExpanded = document.getElementById('logoExpanded');
            const logoCollapsed = document.getElementById('logoCollapsed');
            const logoFallback = document.getElementById('logoFallback');
            const logoSiteName = document.getElementById('logoSiteName');
            
            // Verificar que el elemento principal exista (logoCollapsed es opcional)
            if (!logoExpanded) {
                console.warn('�s�️ No se encontró el elemento logoExpanded');
                return;
            }
            
            // Obtener estado de configuración (0: logo SVG, 1: logo PNG)
            const logoMode = parseInt(localStorage.getItem('modernSidebarLogoMode') || '0');
            
            // Ocultar todos los elementos primero
            this.hideElement(logoExpanded);
            this.hideElement(logoCollapsed);
            if (logoFallback) this.hideElement(logoFallback);
            
            if (!this.isCollapsed) {
                // Sidebar expandido - mostrar logo principal y texto del sitio
                this.showElement(logoExpanded);
                if (logoSiteName) this.showElement(logoSiteName);
            } else {
                // Sidebar colapsado - ocultar texto del sitio y rotar entre logos
                if (logoSiteName) this.hideElement(logoSiteName);
                
                if (logoMode === 1) {
                    // Modo 1: Logo colapsado (PNG)
                    this.showElement(logoCollapsed);
                } else {
                    // Modo 0: Logo principal (SVG)
                    this.showElement(logoExpanded);
                }
            }
            
        }
        
        getVisibleLogo() {
            const logos = {
                'logoExpanded': 'Logo Principal',
                'logoCollapsed': 'Logo Colapsado',
                'logoFallback': 'Icono Fallback'
            };
            
            for (const [id, name] of Object.entries(logos)) {
                const element = document.getElementById(id);
                if (element && element.style.display !== 'none') {
                    return name;
                }
            }
            return 'Ninguno';
        }
        
        cycleLogo() {
            if (!this.isCollapsed) {
                return;
            }
            
            const logoContainer = document.querySelector('.logo-icon');
            const currentMode = parseInt(localStorage.getItem('modernSidebarLogoMode') || '0');
            const nextMode = (currentMode + 1) % 2; // Rotar entre 0 y 1 solamente
            
            
            // Agregar animación de cambio
            if (logoContainer) {
                logoContainer.classList.add('changing');
                
                // Pequeña animación visual
                logoContainer.style.transform = 'scale(0.8)';
                
                setTimeout(() => {
                    localStorage.setItem('modernSidebarLogoMode', nextMode.toString());
                    this.updateLogoDisplay();
                    
                    // Restaurar transformación y remover clase de animación
                    logoContainer.style.transform = 'scale(1)';
                    setTimeout(() => {
                        logoContainer.classList.remove('changing');
                    }, 150);
                }, 150);
            }
            
            const modes = ['Logo Principal (SVG)', 'Logo Colapsado (PNG)'];
            
            // Feedback visual temporal
            this.showTemporaryFeedback(modes[nextMode]);
        }
        
        showTemporaryFeedback(message) {
            // Crear elemento de feedback temporal
            const feedback = document.createElement('div');
            feedback.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 10000;
                transition: opacity 0.3s ease;
            `;
            feedback.textContent = message;
            
            document.body.appendChild(feedback);
            
            // Remover después de 2 segundos
            setTimeout(() => {
                feedback.style.opacity = '0';
                setTimeout(() => {
                    if (feedback.parentNode) {
                        feedback.parentNode.removeChild(feedback);
                    }
                }, 300);
            }, 2000);
        }
        
        showElement(element) {
            if (element) {
                element.style.display = 'block';
                element.style.opacity = '1';
                element.style.visibility = 'visible';
            }
        }
        
        hideElement(element) {
            if (element) {
                element.style.display = 'none';
                element.style.opacity = '0';
                element.style.visibility = 'hidden';
            }
        }

        handleResize() {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 991;

            if (wasMobile !== this.isMobile) {
                
                // Limpiar estado mobile si cambió a desktop
                if (!this.isMobile) {
                    this.closeMobileSidebar();
                }
                
                this.updateSidebarState();
            }
        }

        // Utility function
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
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            new ModernSidebar();
        });
    } else {
        new ModernSidebar();
    }

    // Bootstrap dropdowns compatibility
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(() => {
            if (typeof bootstrap !== 'undefined') {
                const dropdownTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'));
                dropdownTriggerList.map(function (dropdownTriggerEl) {
                    return new bootstrap.Dropdown(dropdownTriggerEl);
                });
            }
        }, 100);
    });
    

// Modern Sidebar JavaScript - Funcionalidad completa del menú lateral
document.addEventListener('DOMContentLoaded', function() {
    
    // Referencias a elementos del DOM
    const sidebar = document.querySelector('.sidebar-wrapper');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    const body = document.body;
    const mainContent = document.querySelector('.main-content');
    
    // Estado del sidebar
    let sidebarState = {
        isCollapsed: localStorage.getItem('sidebarCollapsed') === 'true',
        isMobile: window.innerWidth <= 991,
        isAnimating: false,
        theme: localStorage.getItem('sidebarTheme') || 'default'
    };
    
    // Configuración de interactividad
    const interactivityConfig = {
        enableParticles: true,
        enableSoundEffects: localStorage.getItem('sidebarSounds') === 'true',
        enableHapticFeedback: 'vibrate' in navigator,
        enableAdvancedAnimations: true,
        autoCollapseDelay: 5000 // ms
    };
    
    // Inicialización
    init();
    
    function init() {
        createSidebarElements();
        setupEventListeners();
        handleResponsive();
        setSidebarState();
        highlightActiveMenuItem();
        setupSubmenuHandlers();
        setupTooltips();
        restoreMenuOrder();
        initAdvancedFeatures();
        setupGestureSupport();
        initSidebarAnalytics();
    }
    
    // Crear elementos necesarios del sidebar si no existen
    function createSidebarElements() {
        if (!sidebarOverlay) {
            const overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
            
            overlay.addEventListener('click', function() {
                hideSidebarMobile();
            });
        }
    }
    
    // Configurar event listeners
    function setupEventListeners() {
        // Toggle del sidebar
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function(e) {
                e.preventDefault();
                toggleSidebar();
            });
        }
        
        // Responsive handling
        window.addEventListener('resize', debounce(handleResponsive, 250));
        
        // Teclado shortcuts
        document.addEventListener('keydown', handleKeyboardShortcuts);
        
        // Click fuera del sidebar en móvil
        document.addEventListener('click', function(e) {
            if (sidebarState.isMobile && 
                !sidebar?.contains(e.target) && 
                !e.target.closest('.sidebar-toggle')) {
                hideSidebarMobile();
            }
        });
        
        // Escape key para cerrar sidebar en móvil
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebarState.isMobile) {
                hideSidebarMobile();
            }
        });
    }
    
    // Toggle del sidebar
    function toggleSidebar() {
        if (sidebarState.isMobile) {
            toggleSidebarMobile();
        } else {
            toggleSidebarDesktop();
        }
    }
    
    // Toggle en desktop
    function toggleSidebarDesktop() {
        sidebarState.isCollapsed = !sidebarState.isCollapsed;
        setSidebarState();
        localStorage.setItem('sidebarCollapsed', sidebarState.isCollapsed);
        
        // Dispatch evento personalizado
        window.dispatchEvent(new CustomEvent('sidebarToggle', {
            detail: { collapsed: sidebarState.isCollapsed }
        }));
    }
    
    // Toggle en móvil
    function toggleSidebarMobile() {
        const isVisible = sidebar?.classList.contains('mobile-show');
        
        if (isVisible) {
            hideSidebarMobile();
        } else {
            showSidebarMobile();
        }
    }
    
    // Mostrar sidebar en móvil
    function showSidebarMobile() {
        sidebar?.classList.add('mobile-show');
        document.querySelector('.sidebar-overlay')?.classList.add('active');
        body.style.overflow = 'hidden';
        
        // Añadir animación
        sidebar?.classList.add('animate-in');
        setTimeout(() => {
            sidebar?.classList.remove('animate-in');
        }, 300);
    }
    
    // Ocultar sidebar en móvil
    function hideSidebarMobile() {
        sidebar?.classList.remove('mobile-show');
        document.querySelector('.sidebar-overlay')?.classList.remove('active');
        body.style.overflow = '';
    }
    
    // Aplicar estado del sidebar
    function setSidebarState() {
        if (!sidebar) return;
        
        if (sidebarState.isMobile) {
            // En móvil, siempre expandido cuando se muestra
            sidebar.classList.remove('collapsed');
            body.classList.remove('sidebar-collapsed');
        } else {
            // En desktop, aplicar estado de colapso
            if (sidebarState.isCollapsed) {
                sidebar.classList.add('collapsed');
                body.classList.add('sidebar-collapsed');
            } else {
                sidebar.classList.remove('collapsed');
                body.classList.remove('sidebar-collapsed');
            }
        }
    }
    
    // Manejo responsive
    function handleResponsive() {
        const wasMobile = sidebarState.isMobile;
        sidebarState.isMobile = window.innerWidth <= 991;
        
        if (wasMobile !== sidebarState.isMobile) {
            // Cambió el estado móvil/desktop
            if (sidebarState.isMobile) {
                // Cambió a móvil
                hideSidebarMobile();
                body.classList.remove('sidebar-collapsed');
            } else {
                // Cambió a desktop
                body.style.overflow = '';
                document.querySelector('.sidebar-overlay')?.classList.remove('active');
                sidebar?.classList.remove('mobile-show');
            }
            
            setSidebarState();
        }
    }
    
    // Resaltar elemento activo del menú
    function highlightActiveMenuItem() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            
            const href = link.getAttribute('href');
            if (href && (currentPath === href || 
                        (href !== '/' && currentPath.startsWith(href)))) {
                link.classList.add('active');
                
                // Si es un submenú, abrir el padre
                const parentSubmenu = link.closest('.submenu');
                if (parentSubmenu) {
                    const parentItem = parentSubmenu.closest('.nav-item');
                    parentItem?.classList.add('open');
                }
            }
        });
    }
    
    // Configurar submenús
    function setupSubmenuHandlers() {
        const submenuToggles = document.querySelectorAll('.nav-item.has-submenu > .nav-link');
        
        submenuToggles.forEach(toggle => {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                
                const parentItem = this.closest('.nav-item');
                const isOpen = parentItem.classList.contains('open');
                
                // Cerrar otros submenús (opcional)
                document.querySelectorAll('.nav-item.has-submenu.open').forEach(item => {
                    if (item !== parentItem) {
                        item.classList.remove('open');
                    }
                });
                
                // Toggle el submenú actual
                parentItem.classList.toggle('open', !isOpen);
                
                // Guardar estado en localStorage
                saveSubmenuState();
            });
        });
        
        // Restaurar estado de submenús
        restoreSubmenuState();
    }
    
    // Guardar estado de submenús
    function saveSubmenuState() {
        const openSubmenus = [];
        document.querySelectorAll('.nav-item.has-submenu.open').forEach(item => {
            const link = item.querySelector('.nav-link');
            if (link) {
                openSubmenus.push(link.textContent.trim());
            }
        });
        localStorage.setItem('openSubmenus', JSON.stringify(openSubmenus));
    }
    
    // Restaurar estado de submenús
    function restoreSubmenuState() {
        try {
            const openSubmenus = JSON.parse(localStorage.getItem('openSubmenus') || '[]');
            
            openSubmenus.forEach(submenuText => {
                const submenuToggle = Array.from(document.querySelectorAll('.nav-item.has-submenu > .nav-link'))
                    .find(link => link.textContent.trim() === submenuText);
                
                if (submenuToggle) {
                    submenuToggle.closest('.nav-item').classList.add('open');
                }
            });
        } catch (e) {
            console.warn('Error restoring submenu state:', e);
        }
    }
    
    // Configurar tooltips para sidebar colapsado
    function setupTooltips() {
        const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
        
        navItems.forEach(item => {
            const link = item.querySelector('.nav-link');
            const text = link?.querySelector('.nav-text')?.textContent.trim();
            
            if (text && !item.classList.contains('has-submenu')) {
                item.classList.add('tooltip-enabled');
                item.setAttribute('data-tooltip', text);
            }
        });
    }
    
    // Atajos de teclado
    function handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + B para toggle del sidebar
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            toggleSidebar();
        }
        
        // Alt + M para toggle en móvil
        if (e.altKey && e.key === 'm' && sidebarState.isMobile) {
            e.preventDefault();
            toggleSidebarMobile();
        }
    }
    
    // Inicializar funcionalidades avanzadas
    function initAdvancedFeatures() {
        setupAdvancedAnimations();
        setupContextMenu();
        setupDragAndDrop();
        setupVoiceCommands();
        setupSmartCollapse();
        setupThemeDetection();
        initPerformanceOptimizations();
    }
    
    // Animaciones avanzadas
    function setupAdvancedAnimations() {
        if (!interactivityConfig.enableAdvancedAnimations) return;
        
        // Efecto de ondas en click
        document.addEventListener('click', function(e) {
            const navLink = e.target.closest('.nav-link');
            if (navLink && !navLink.classList.contains('has-submenu')) {
                createRippleEffect(navLink, e);
                playClickSound();
                triggerHapticFeedback();
            }
        });
        
        // Animación de entrada escalonada
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach((item, index) => {
            item.style.animationDelay = `${(index + 1) * 0.05}s`;
            item.classList.add('animate-in');
        });
        
        // Efectos de parallax en scroll
        const sidebarNav = document.querySelector('.sidebar-nav');
        if (sidebarNav) {
            sidebarNav.addEventListener('scroll', throttle(handleParallaxScroll, 16));
        }
    }
    
    // Efecto parallax en scroll del sidebar
    function handleParallaxScroll() {
        const nav = document.querySelector('.sidebar-nav');
        if (!nav) return;
        
        const scrollTop = nav.scrollTop;
        const scrollHeight = nav.scrollHeight;
        const clientHeight = nav.clientHeight;
        const scrollPercent = scrollTop / (scrollHeight - clientHeight);
        
        // Aplicar efecto parallax sutil a los elementos
        const navItems = nav.querySelectorAll('.nav-item');
        navItems.forEach((item, index) => {
            const rect = item.getBoundingClientRect();
            const navRect = nav.getBoundingClientRect();
            const itemCenter = rect.top + rect.height / 2;
            const navCenter = navRect.top + navRect.height / 2;
            const distance = Math.abs(itemCenter - navCenter);
            const maxDistance = navRect.height / 2;
            const parallaxStrength = Math.max(0, 1 - distance / maxDistance);
            
            // Aplicar transformación sutil
            const translateX = parallaxStrength * 2;
            const scale = 0.98 + (parallaxStrength * 0.02);
            
            item.style.transform = `translateX(${translateX}px) scale(${scale})`;
            item.style.opacity = 0.7 + (parallaxStrength * 0.3);
        });
        
        // Actualizar indicador de scroll
        updateScrollIndicators();
    }
    
    // Crear efecto de ondas
    function createRippleEffect(element, event) {
        const rect = element.getBoundingClientRect();
        const ripple = document.createElement('span');
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.className = 'ripple-effect';
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: radial-gradient(circle, rgba(255,255,255,0.6) 0%, transparent 70%);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
            z-index: 1000;
        `;
        
        element.style.position = 'relative';
        element.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    }
    
    // Sonidos de interacción
    function playClickSound() {
        if (!interactivityConfig.enableSoundEffects) return;
        
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(400, audioContext.currentTime + 0.1);
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    }
    
    // Feedback háptico
    function triggerHapticFeedback() {
        if (interactivityConfig.enableHapticFeedback && navigator.vibrate) {
            navigator.vibrate(10);
        }
    }
    
    // Menú contextual
    function setupContextMenu() {
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            link.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                showContextMenu(e, this);
            });
        });
    }
    
    function showContextMenu(event, element) {
        const existingMenu = document.querySelector('.sidebar-context-menu');
        if (existingMenu) existingMenu.remove();
        
        const menu = document.createElement('div');
        menu.className = 'sidebar-context-menu';
        menu.innerHTML = `
            <div class="context-menu-item" data-action="pin">
                <i class="fas fa-thumbtack"></i> Fijar
            </div>
            <div class="context-menu-item" data-action="hide">
                <i class="fas fa-eye-slash"></i> Ocultar
            </div>
            <div class="context-menu-item" data-action="edit">
                <i class="fas fa-edit"></i> Personalizar
            </div>
        `;
        
        menu.style.cssText = `
            position: fixed;
            left: ${event.clientX}px;
            top: ${event.clientY}px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 2000;
            padding: 8px 0;
            min-width: 150px;
            animation: fadeInScale 0.2s ease-out;
        `;
        
        document.body.appendChild(menu);
        
        // Cerrar menú al hacer click fuera
        setTimeout(() => {
            document.addEventListener('click', function closeMenu() {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            });
        }, 10);
        
        // Manejar acciones del menú
        menu.addEventListener('click', function(e) {
            const action = e.target.closest('[data-action]')?.dataset.action;
            if (action) {
                handleContextMenuAction(action, element);
                menu.remove();
            }
        });
    }
    
    function handleContextMenuAction(action, element) {
        switch (action) {
            case 'pin':
                element.classList.toggle('pinned');
                showSidebarNotification('Elemento fijado', 'success');
                break;
            case 'hide':
                element.style.display = 'none';
                showSidebarNotification('Elemento ocultado', 'info');
                break;
            case 'edit':
                openCustomizationPanel(element);
                break;
        }
    }
    
    // Panel de personalización
    function openCustomizationPanel(element) {
        const panel = document.createElement('div');
        panel.className = 'customization-panel';
        panel.innerHTML = `
            <div class="panel-header">
                <h3>Personalizar Elemento</h3>
                <button class="panel-close">&times;</button>
            </div>
            <div class="panel-body">
                <div class="form-group">
                    <label>Icono:</label>
                    <input type="text" class="icon-input" placeholder="fas fa-home">
                </div>
                <div class="form-group">
                    <label>Texto:</label>
                    <input type="text" class="text-input" placeholder="Texto del menú">
                </div>
                <div class="form-group">
                    <label>Color:</label>
                    <input type="color" class="color-input" value="#3498db">
                </div>
                <div class="form-actions">
                    <button class="btn-save">Guardar</button>
                    <button class="btn-cancel">Cancelar</button>
                </div>
            </div>
        `;
        
        panel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.2);
            z-index: 3000;
            padding: 0;
            min-width: 300px;
            animation: slideInDown 0.3s ease-out;
        `;
        
        document.body.appendChild(panel);
        
        // Event listeners del panel
        panel.querySelector('.panel-close').addEventListener('click', () => panel.remove());
        panel.querySelector('.btn-cancel').addEventListener('click', () => panel.remove());
        panel.querySelector('.btn-save').addEventListener('click', () => {
            // Implementar lógica de guardado
            showSidebarNotification('Cambios guardados', 'success');
            panel.remove();
        });
    }
    
    // Funcionalidad de arrastrar y soltar para reordenar elementos del menú
    function setupDragAndDrop() {
        if (!sidebar) return;
        
        const menuItems = sidebar.querySelectorAll('.nav-link');
        let draggedElement = null;
        let placeholder = null;
        
        menuItems.forEach(item => {
            const parentLi = item.closest('li');
            if (!parentLi) return;
            
            // Hacer elementos arrastrables
            parentLi.draggable = true;
            
            // Eventos de drag
            parentLi.addEventListener('dragstart', (e) => {
                draggedElement = parentLi;
                e.dataTransfer.effectAllowed = 'move';
                
                // Crear placeholder visual
                placeholder = document.createElement('li');
                placeholder.className = 'drag-placeholder';
                placeholder.innerHTML = '<div class="placeholder-content">Soltar aquí</div>';
                
                // Estilo del placeholder
                Object.assign(placeholder.style, {
                    height: parentLi.offsetHeight + 'px',
                    border: '2px dashed var(--bs-primary)',
                    background: 'rgba(var(--bs-primary-rgb), 0.1)',
                    borderRadius: '8px',
                    margin: '4px 0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--bs-primary)',
                    fontSize: '0.875rem',
                    opacity: '0.7'
                });
                
                // Añadir clase visual al elemento siendo arrastrado
                setTimeout(() => {
                    if (draggedElement) {
                        draggedElement.style.opacity = '0.5';
                        draggedElement.style.transform = 'scale(0.95)';
                    }
                }, 0);
                
                // Notificación
                showSidebarNotification('Arrastra para reordenar', 'info');
            });
            
            parentLi.addEventListener('dragend', (e) => {
                // Restaurar estilos
                if (draggedElement) {
                    draggedElement.style.opacity = '';
                    draggedElement.style.transform = '';
                }
                
                // Remover placeholder
                if (placeholder && placeholder.parentNode) {
                    placeholder.remove();
                }
                
                draggedElement = null;
                placeholder = null;
                
                // Limpiar todos los indicadores visuales
                menuItems.forEach(item => {
                    const li = item.closest('li');
                    if (li) {
                        li.classList.remove('drag-over');
                        li.style.borderTop = '';
                        li.style.borderBottom = '';
                    }
                });
            });
            
            parentLi.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                
                if (draggedElement && draggedElement !== parentLi) {
                    const rect = parentLi.getBoundingClientRect();
                    const midpoint = rect.top + rect.height / 2;
                    
                    // Remover placeholder anterior
                    if (placeholder && placeholder.parentNode) {
                        placeholder.remove();
                    }
                    
                    // Insertar placeholder en la posición correcta
                    if (e.clientY < midpoint) {
                        parentLi.parentNode.insertBefore(placeholder, parentLi);
                    } else {
                        parentLi.parentNode.insertBefore(placeholder, parentLi.nextSibling);
                    }
                }
            });
            
            parentLi.addEventListener('drop', (e) => {
                e.preventDefault();
                
                if (draggedElement && draggedElement !== parentLi && placeholder) {
                    // Realizar el reordenamiento
                    placeholder.parentNode.replaceChild(draggedElement, placeholder);
                    
                    // Animación de confirmación
                    createRippleEffect(draggedElement, e.clientX, e.clientY);
                    
                    // Guardar nuevo orden en localStorage
                    saveMenuOrder();
                    
                    // Notificación de éxito
                    showSidebarNotification('Elemento reordenado exitosamente', 'success');
                    
                    // Reproducir sonido de confirmación
                    if (interactivityConfig.enableSoundEffects) {
                        playClickSound();
                    }
                }
            });
        });
    }
    
    // Guardar orden del menú en localStorage
    function saveMenuOrder() {
        if (!sidebar) return;
        
        const menuItems = sidebar.querySelectorAll('.nav-link');
        const order = Array.from(menuItems).map(item => {
            return {
                href: item.getAttribute('href'),
                text: item.textContent.trim(),
                icon: item.querySelector('i')?.className || ''
            };
        });
        
        localStorage.setItem('sidebarMenuOrder', JSON.stringify(order));
    }
    
    // Restaurar orden del menú desde localStorage
    function restoreMenuOrder() {
        const savedOrder = localStorage.getItem('sidebarMenuOrder');
        if (!savedOrder || !sidebar) return;
        
        try {
            const order = JSON.parse(savedOrder);
            const navList = sidebar.querySelector('.nav');
            if (!navList) return;
            
            // Reorganizar elementos según el orden guardado
            order.forEach((itemData, index) => {
                const item = navList.querySelector(`a[href="${itemData.href}"]`);
                if (item) {
                    const li = item.closest('li');
                    if (li) {
                        navList.appendChild(li);
                    }
                }
            });
        } catch (e) {
            console.warn('Error al restaurar orden del menú:', e);
        }
    }
    
    // Soporte para gestos táctiles
    function setupGestureSupport() {
        if (!('ontouchstart' in window)) return;
        
        let touchStartX = 0;
        let touchStartY = 0;
        let isSwiping = false;
        
        document.addEventListener('touchstart', function(e) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            isSwiping = false;
        });
        
        document.addEventListener('touchmove', function(e) {
            if (!isSwiping) {
                const touchX = e.touches[0].clientX;
                const touchY = e.touches[0].clientY;
                const deltaX = touchX - touchStartX;
                const deltaY = touchY - touchStartY;
                
                if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 20) {
                    isSwiping = true;
                    
                    if (deltaX > 0 && touchStartX < 50) {
                        // Swipe right desde el borde izquierdo
                        showSidebarMobile();
                    } else if (deltaX < -50 && sidebar?.classList.contains('mobile-show')) {
                        // Swipe left para cerrar
                        hideSidebarMobile();
                    }
                }
            }
        });
    }
    
    // Comandos de voz
    function setupVoiceCommands() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) return;
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'es-ES';
        
        recognition.onresult = function(event) {
            const command = event.results[0][0].transcript.toLowerCase();
            handleVoiceCommand(command);
        };
        
        // Activar con Ctrl + Shift + V
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.shiftKey && e.key === 'V') {
                e.preventDefault();
                recognition.start();
                showSidebarNotification('Escuchando comando...', 'info');
            }
        });
    }
    
    function handleVoiceCommand(command) {
        const commands = {
            'abrir menú': () => showSidebarMobile(),
            'cerrar menú': () => hideSidebarMobile(),
            'colapsar': () => sidebarState.isCollapsed || toggleSidebarDesktop(),
            'expandir': () => !sidebarState.isCollapsed || toggleSidebarDesktop(),
            'ir al perfil': () => window.location.href = '/users/profile/',
            'ir al dashboard': () => window.location.href = '/dashboard/',
            'modo oscuro': () => toggleDarkMode(),
            'configuración': () => openConfigurationPanel()
        };
        
        const matchedCommand = Object.keys(commands).find(cmd => 
            command.includes(cmd) || cmd.includes(command)
        );
        
        if (matchedCommand) {
            commands[matchedCommand]();
            showSidebarNotification(`Comando ejecutado: ${matchedCommand}`, 'success');
        } else {
            showSidebarNotification('Comando no reconocido', 'warning');
        }
    }
    
    // Auto-colapso inteligente
    function setupSmartCollapse() {
        let inactivityTimer;
        
        function resetInactivityTimer() {
            clearTimeout(inactivityTimer);
            
            if (!sidebarState.isMobile && !sidebarState.isCollapsed) {
                inactivityTimer = setTimeout(() => {
                    if (!sidebar?.matches(':hover')) {
                        toggleSidebarDesktop();
                        showSidebarNotification('Sidebar auto-colapsado por inactividad', 'info', 2000);
                    }
                }, interactivityConfig.autoCollapseDelay);
            }
        }
        
        // Reset timer en actividad
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, resetInactivityTimer, true);
        });
        
        // Pausar timer cuando el mouse está sobre el sidebar
        sidebar?.addEventListener('mouseenter', () => clearTimeout(inactivityTimer));
        sidebar?.addEventListener('mouseleave', resetInactivityTimer);
    }
    
    // Detección automática de tema
    function setupThemeDetection() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        function handleThemeChange(e) {
            const newTheme = e.matches ? 'dark' : 'light';
            applySidebarTheme(newTheme);
            showSidebarNotification(`Tema cambiado a ${newTheme}`, 'info', 1500);
        }
        
        mediaQuery.addEventListener('change', handleThemeChange);
        handleThemeChange(mediaQuery); // Aplicar tema inicial
    }
    
    function applySidebarTheme(theme) {
        sidebar?.setAttribute('data-theme', theme);
        localStorage.setItem('sidebarTheme', theme);
        sidebarState.theme = theme;
    }
    
    // Optimizaciones de rendimiento
    function initPerformanceOptimizations() {
        // Lazy loading de elementos no visibles
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        });
        
        document.querySelectorAll('.nav-item').forEach(item => {
            observer.observe(item);
        });
        
        // Throttle para eventos de scroll
        const sidebarNav = document.querySelector('.sidebar-nav');
        if (sidebarNav) {
            sidebarNav.addEventListener('scroll', throttle(updateScrollIndicators, 16));
        }
        
        // Prefetch de páginas en hover
        document.querySelectorAll('.nav-link[href]').forEach(link => {
            link.addEventListener('mouseenter', function() {
                if (this.href && !this.href.includes('#')) {
                    prefetchPage(this.href);
                }
            });
        });
    }
    
    function prefetchPage(url) {
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
    }
    
    function updateScrollIndicators() {
        const nav = document.querySelector('.sidebar-nav');
        const scrollPercent = (nav.scrollTop / (nav.scrollHeight - nav.clientHeight)) * 100;
        
        // Actualizar indicador de scroll si existe
        const indicator = document.querySelector('.scroll-indicator');
        if (indicator) {
            indicator.style.height = `${scrollPercent}%`;
        }
    }
    
    // Analytics del sidebar
    function initSidebarAnalytics() {
        const analytics = {
            interactions: 0,
            mostUsedItems: {},
            sessionStart: Date.now(),
            heatmap: {}
        };
        
        // Tracking de clicks
        document.addEventListener('click', function(e) {
            const navLink = e.target.closest('.nav-link');
            if (navLink) {
                const itemText = navLink.querySelector('.nav-text')?.textContent;
                if (itemText) {
                    analytics.interactions++;
                    analytics.mostUsedItems[itemText] = (analytics.mostUsedItems[itemText] || 0) + 1;
                    
                    // Guardar heatmap position
                    const rect = navLink.getBoundingClientRect();
                    const key = `${Math.round(rect.top / 50)}-${Math.round(rect.left / 50)}`;
                    analytics.heatmap[key] = (analytics.heatmap[key] || 0) + 1;
                }
            }
        });
        
        // Enviar analytics cada 30 segundos
        setInterval(() => {
            if (analytics.interactions > 0) {
                console.log('Sidebar Analytics:', analytics);
                // Aquí se podría enviar a un endpoint de analytics
            }
        }, 30000);
        
        // Guardar analytics al cerrar
        window.addEventListener('beforeunload', () => {
            localStorage.setItem('sidebarAnalytics', JSON.stringify(analytics));
        });
    }
    
    // Utilidades
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    function debounce(func, wait) {
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
    
    // API pública del sidebar
    window.SidebarAPI = {
        toggle: toggleSidebar,
        collapse: () => {
            if (!sidebarState.isMobile) {
                sidebarState.isCollapsed = true;
                setSidebarState();
                localStorage.setItem('sidebarCollapsed', true);
            }
        },
        expand: () => {
            if (!sidebarState.isMobile) {
                sidebarState.isCollapsed = false;
                setSidebarState();
                localStorage.setItem('sidebarCollapsed', false);
            }
        },
        show: showSidebarMobile,
        hide: hideSidebarMobile,
        getState: () => ({ ...sidebarState }),
        refreshActiveItem: highlightActiveMenuItem,
        addMenuItem: addMenuItem,
        removeMenuItem: removeMenuItem,
        updateBadge: updateBadge
    };
    
    // Agregar elemento de menú dinámicamente
    function addMenuItem(config) {
        const {
            text,
            icon,
            href,
            parent = null,
            badge = null,
            position = 'append'
        } = config;
        
        const navItem = document.createElement('li');
        navItem.className = 'nav-item';
        
        const navLink = document.createElement('a');
        navLink.className = 'nav-link';
        navLink.href = href || '#';
        
        const iconElement = document.createElement('i');
        iconElement.className = `nav-icon ${icon}`;
        
        const textElement = document.createElement('span');
        textElement.className = 'nav-text';
        textElement.textContent = text;
        
        navLink.appendChild(iconElement);
        navLink.appendChild(textElement);
        
        if (badge) {
            const badgeElement = document.createElement('span');
            badgeElement.className = 'nav-badge';
            badgeElement.textContent = badge;
            navLink.appendChild(badgeElement);
        }
        
        navItem.appendChild(navLink);
        
        // Agregar al DOM
        const targetParent = parent ? 
            document.querySelector(parent) : 
            document.querySelector('.sidebar-nav');
        
        if (targetParent) {
            if (position === 'prepend') {
                targetParent.insertBefore(navItem, targetParent.firstChild);
            } else {
                targetParent.appendChild(navItem);
            }
        }
        
        return navItem;
    }
    
    // Remover elemento de menú
    function removeMenuItem(selector) {
        const item = document.querySelector(selector);
        if (item) {
            item.remove();
            return true;
        }
        return false;
    }
    
    // Actualizar badge de elemento
    function updateBadge(selector, value) {
        const navLink = document.querySelector(selector);
        if (!navLink) return false;
        
        let badge = navLink.querySelector('.nav-badge');
        
        if (value) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'nav-badge';
                navLink.appendChild(badge);
            }
            badge.textContent = value;
        } else if (badge) {
            badge.remove();
        }
        
        return true;
    }
    
    // Notificaciones del sidebar
    function showSidebarNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `sidebar-notification sidebar-notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="notification-icon fas fa-${getNotificationIcon(type)}"></i>
                <span class="notification-text">${message}</span>
            </div>
        `;
        
        // Estilos inline para la notificación
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: ${sidebarState.isCollapsed ? '90px' : '300px'};
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1002;
            transform: translateX(-20px);
            opacity: 0;
            transition: all 0.3s ease;
            max-width: 300px;
            border-left: 4px solid ${getNotificationColor(type)};
        `;
        
        document.body.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        }, 100);
        
        // Auto-remove
        setTimeout(() => {
            notification.style.transform = 'translateX(-20px)';
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, duration);
    }
    
    function getNotificationIcon(type) {
        const icons = {
            info: 'info-circle',
            success: 'check-circle',
            warning: 'exclamation-triangle',
            error: 'times-circle'
        };
        return icons[type] || icons.info;
    }
    
    function getNotificationColor(type) {
        const colors = {
            info: '#3498db',
            success: '#27ae60',
            warning: '#f39c12',
            error: '#e74c3c'
        };
        return colors[type] || colors.info;
    }
    
    // Exponer función de notificación
    window.SidebarAPI.showNotification = showSidebarNotification;
    
    // Event listeners para integración con otros sistemas
    window.addEventListener('sidebarToggle', function(e) {
        console.log('Sidebar toggled:', e.detail);
    });
    
    // Auto-hide en móvil después de hacer clic en enlace
    document.addEventListener('click', function(e) {
        if (sidebarState.isMobile && 
            e.target.closest('.sidebar-nav .nav-link') && 
            !e.target.closest('.has-submenu')) {
            
            setTimeout(() => {
                hideSidebarMobile();
            }, 150);
        }
    });
    
    // Smooth scroll para anchors
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[href^="#"]');
        if (link && link.hash) {
            const target = document.querySelector(link.hash);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Utilidades globales del sidebar
window.SidebarUtils = {
    // Inicializar sidebar con configuración personalizada
    init: function(config = {}) {
        // Configuración personalizada
        Object.assign(window.SidebarAPI, config);
    },
    
    // Cambiar tema del sidebar
    setTheme: function(theme) {
        const sidebar = document.querySelector('.sidebar-wrapper');
        if (sidebar) {
            sidebar.setAttribute('data-theme', theme);
        }
    },
    
    // Obtener estadísticas del sidebar
    getStats: function() {
        return {
            totalItems: document.querySelectorAll('.sidebar-nav .nav-item').length,
            activeItems: document.querySelectorAll('.sidebar-nav .nav-link.active').length,
            openSubmenus: document.querySelectorAll('.nav-item.has-submenu.open').length,
            isCollapsed: document.querySelector('.sidebar-wrapper')?.classList.contains('collapsed'),
            isMobile: window.innerWidth <= 991
        };
    }
};
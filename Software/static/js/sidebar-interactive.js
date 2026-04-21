// Funcionalidades adicionales para el sidebar interactivo
document.addEventListener('DOMContentLoaded', function() {
    
    // Búsqueda rápida
    initQuickSearch();
    
    // Atajos de teclado
    setupKeyboardShortcuts();
    
    // Efectos visuales adicionales
    setupVisualEffects();
    
    // Configuración de usuario
    initUserPreferences();
    
    function initQuickSearch() {
        // Crear overlay de búsqueda
        const searchOverlay = document.createElement('div');
        searchOverlay.className = 'quick-search-overlay';
        searchOverlay.innerHTML = `
            <div class="quick-search-box">
                <input type="text" class="quick-search-input" placeholder="Buscar en el menú... (Ctrl+K)">
                <div class="quick-search-results"></div>
                <div class="search-shortcuts">
                    <small class="text-muted">
                        <kbd>↑</kbd><kbd>↓</kbd> navegar &bull; 
                        <kbd>Enter</kbd> seleccionar &bull; 
                        <kbd>Esc</kbd> cerrar
                    </small>
                </div>
            </div>
        `;
        document.body.appendChild(searchOverlay);
        
        const searchInput = searchOverlay.querySelector('.quick-search-input');
        const searchResults = searchOverlay.querySelector('.quick-search-results');
        let selectedIndex = -1;
        
        // Recopilar elementos del menú para búsqueda
        const menuItems = Array.from(document.querySelectorAll('.nav-link')).map(link => ({
            element: link,
            text: link.querySelector('.nav-text')?.textContent || '',
            href: link.getAttribute('href') || '#',
            icon: link.querySelector('.nav-icon')?.className || '',
            keywords: link.getAttribute('data-keywords') || ''
        })).filter(item => item.text && item.href !== '#');
        
        // Mostrar búsqueda
        function showQuickSearch() {
            searchOverlay.classList.add('active');
            searchInput.focus();
            selectedIndex = -1;
        }
        
        // Ocultar búsqueda
        function hideQuickSearch() {
            searchOverlay.classList.remove('active');
            searchInput.value = '';
            searchResults.innerHTML = '';
            selectedIndex = -1;
        }
        
        // Buscar elementos
        function performSearch(query) {
            if (!query) {
                searchResults.innerHTML = '';
                return;
            }
            
            const results = menuItems.filter(item => 
                item.text.toLowerCase().includes(query.toLowerCase()) ||
                item.keywords.toLowerCase().includes(query.toLowerCase())
            ).slice(0, 5);
            
            searchResults.innerHTML = results.map((item, index) => `
                <div class="search-result-item" data-index="${index}" data-href="${item.href}">
                    <i class="${item.icon}"></i>
                    <span>${highlightMatch(item.text, query)}</span>
                </div>
            `).join('');
            
            selectedIndex = -1;
        }
        
        function highlightMatch(text, query) {
            const regex = new RegExp(`(${query})`, 'gi');
            return text.replace(regex, '<mark>$1</mark>');
        }
        
        // Navegación con teclado
        function handleKeyNavigation(e) {
            const results = searchResults.querySelectorAll('.search-result-item');
            
            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    selectedIndex = Math.min(selectedIndex + 1, results.length - 1);
                    updateSelection();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    selectedIndex = Math.max(selectedIndex - 1, -1);
                    updateSelection();
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (selectedIndex >= 0) {
                        const selected = results[selectedIndex];
                        const href = selected.getAttribute('data-href');
                        if (href && href !== '#') {
                            window.location.href = href;
                        }
                    }
                    hideQuickSearch();
                    break;
                case 'Escape':
                    hideQuickSearch();
                    break;
            }
        }
        
        function updateSelection() {
            const results = searchResults.querySelectorAll('.search-result-item');
            results.forEach((result, index) => {
                result.classList.toggle('selected', index === selectedIndex);
            });
        }
        
        // Event listeners
        document.getElementById('quick-search-toggle')?.addEventListener('click', (e) => {
            e.preventDefault();
            showQuickSearch();
        });
        
        searchInput.addEventListener('input', (e) => {
            performSearch(e.target.value);
        });
        
        searchInput.addEventListener('keydown', handleKeyNavigation);
        
        searchOverlay.addEventListener('click', (e) => {
            if (e.target === searchOverlay) {
                hideQuickSearch();
            }
        });
        
        searchResults.addEventListener('click', (e) => {
            const item = e.target.closest('.search-result-item');
            if (item) {
                const href = item.getAttribute('data-href');
                if (href && href !== '#') {
                    window.location.href = href;
                }
                hideQuickSearch();
            }
        });
        
        // Atajo global Ctrl+K
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                showQuickSearch();
            }
        });
    }
    
    function setupKeyboardShortcuts() {
        const shortcuts = {
            'F1': () => {
                // Mostrar ayuda
                showHelpModal();
            },
            'ctrl+h': () => {
                // Toggle sidebar
                window.SidebarAPI?.toggle();
            },
            'ctrl+shift+d': () => {
                // Ir al dashboard
                window.location.href = '/dashboard/';
            },
            'ctrl+shift+p': () => {
                // Ir al perfil
                window.location.href = '/users/profile/';
            },
            'alt+t': () => {
                // Toggle tema
                toggleSidebarTheme();
            }
        };
        
        document.addEventListener('keydown', (e) => {
            const key = [
                e.ctrlKey && 'ctrl',
                e.shiftKey && 'shift',
                e.altKey && 'alt',
                e.key.toLowerCase()
            ].filter(Boolean).join('+');
            
            if (shortcuts[key] || shortcuts[e.key]) {
                e.preventDefault();
                (shortcuts[key] || shortcuts[e.key])();
            }
        });
    }
    
    function setupVisualEffects() {
        // Efecto de partículas en hover
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('mouseenter', function() {
                if (Math.random() > 0.7) { // 30% de probabilidad
                    createParticleEffect(this);
                }
            });
        });
        
        // Animación de iconos en función del tiempo
        setInterval(() => {
            const specialItems = document.querySelectorAll('.nav-item.special .nav-icon');
            specialItems.forEach(icon => {
                icon.style.transform = `rotate(${Math.sin(Date.now() / 1000) * 5}deg)`;
            });
        }, 100);
        
        // Efecto de typing en elementos de texto
        const typingElements = document.querySelectorAll('[data-typing]');
        typingElements.forEach(element => {
            const text = element.textContent;
            element.textContent = '';
            element.classList.add('typing-effect');
            
            let i = 0;
            const typeInterval = setInterval(() => {
                element.textContent += text[i];
                i++;
                if (i >= text.length) {
                    clearInterval(typeInterval);
                    element.classList.remove('typing-effect');
                }
            }, 100);
        });
    }
    
    function createParticleEffect(element) {
        const rect = element.getBoundingClientRect();
        const particle = document.createElement('div');
        
        particle.style.cssText = `
            position: fixed;
            width: 4px;
            height: 4px;
            background: var(--sidebar-accent);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            left: ${rect.left + Math.random() * rect.width}px;
            top: ${rect.top + Math.random() * rect.height}px;
        `;
        
        document.body.appendChild(particle);
        
        // Animar partícula
        const animation = particle.animate([
            { transform: 'translateY(0) scale(1)', opacity: 1 },
            { transform: 'translateY(-20px) scale(0)', opacity: 0 }
        ], {
            duration: 1000,
            easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
        });
        
        animation.onfinish = () => particle.remove();
    }
    
    function initUserPreferences() {
        // Cargar preferencias guardadas
        const preferences = JSON.parse(localStorage.getItem('sidebarPreferences') || '{}');
        
        // Aplicar preferencias
        if (preferences.soundEffects !== undefined) {
            interactivityConfig.enableSoundEffects = preferences.soundEffects;
        }
        
        if (preferences.theme) {
            applySidebarTheme(preferences.theme);
        }
        
        // Crear panel de configuración
        createPreferencesPanel();
    }
    
    function createPreferencesPanel() {
        // Agregar opción de configuración en el menú
        const configItem = document.createElement('li');
        configItem.className = 'nav-item';
        configItem.innerHTML = `
            <a href="#" class="nav-link" id="preferences-toggle">
                <i class="nav-icon fas fa-sliders-h"></i>
                <span class="nav-text">Personalizar</span>
            </a>
        `;
        
        // Insertar antes del separador final
        const separator = document.querySelector('.nav-separator');
        if (separator) {
            separator.parentNode.insertBefore(configItem, separator);
        }
        
        // Event listener para abrir configuración
        document.getElementById('preferences-toggle').addEventListener('click', (e) => {
            e.preventDefault();
            showPreferencesModal();
        });
    }
    
    function showPreferencesModal() {
        const modal = document.createElement('div');
        modal.className = 'preferences-modal';
        modal.innerHTML = `
            <div class="modal-backdrop">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Configuración del Sidebar</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="preference-group">
                            <label class="preference-label">
                                <input type="checkbox" id="pref-sounds" ${interactivityConfig.enableSoundEffects ? 'checked' : ''}>
                                <span class="preference-text">Efectos de sonido</span>
                            </label>
                        </div>
                        <div class="preference-group">
                            <label class="preference-label">
                                <input type="checkbox" id="pref-haptic" ${interactivityConfig.enableHapticFeedback ? 'checked' : ''}>
                                <span class="preference-text">Vibración (haptic feedback)</span>
                            </label>
                        </div>
                        <div class="preference-group">
                            <label class="preference-label">
                                <input type="checkbox" id="pref-animations" ${interactivityConfig.enableAdvancedAnimations ? 'checked' : ''}>
                                <span class="preference-text">Animaciones avanzadas</span>
                            </label>
                        </div>
                        <div class="preference-group">
                            <label class="preference-text">Tema del sidebar:</label>
                            <select id="pref-theme">
                                <option value="default">Por defecto</option>
                                <option value="dark">Oscuro</option>
                                <option value="light">Claro</option>
                                <option value="auto">Automático</option>
                            </select>
                        </div>
                        <div class="preference-group">
                            <label class="preference-text">Auto-colapso (segundos):</label>
                            <input type="range" id="pref-collapse" min="0" max="30" value="${interactivityConfig.autoCollapseDelay / 1000}">
                            <span id="collapse-value">${interactivityConfig.autoCollapseDelay / 1000}s</span>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-save-prefs">Guardar</button>
                        <button class="btn-reset-prefs">Restablecer</button>
                    </div>
                </div>
            </div>
        `;
        
        // Estilos del modal
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 5000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        document.body.appendChild(modal);
        
        // Event listeners del modal
        modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
        modal.querySelector('.modal-backdrop').addEventListener('click', (e) => {
            if (e.target === modal.querySelector('.modal-backdrop')) {
                modal.remove();
            }
        });
        
        // Actualizar valor del slider
        const collapseSlider = modal.querySelector('#pref-collapse');
        const collapseValue = modal.querySelector('#collapse-value');
        collapseSlider.addEventListener('input', () => {
            collapseValue.textContent = collapseSlider.value + 's';
        });
        
        // Guardar preferencias
        modal.querySelector('.btn-save-prefs').addEventListener('click', () => {
            savePreferences({
                soundEffects: modal.querySelector('#pref-sounds').checked,
                hapticFeedback: modal.querySelector('#pref-haptic').checked,
                advancedAnimations: modal.querySelector('#pref-animations').checked,
                theme: modal.querySelector('#pref-theme').value,
                autoCollapseDelay: parseInt(collapseSlider.value) * 1000
            });
            modal.remove();
            window.SidebarAPI?.showNotification('Configuración guardada', 'success');
        });
        
        // Restablecer preferencias
        modal.querySelector('.btn-reset-prefs').addEventListener('click', () => {
            localStorage.removeItem('sidebarPreferences');
            modal.remove();
            location.reload();
        });
    }
    
    function savePreferences(prefs) {
        localStorage.setItem('sidebarPreferences', JSON.stringify(prefs));
        
        // Aplicar cambios inmediatamente
        Object.assign(interactivityConfig, prefs);
        
        if (prefs.theme) {
            applySidebarTheme(prefs.theme);
        }
    }
    
    function showHelpModal() {
        const helpModal = document.createElement('div');
        helpModal.className = 'help-modal';
        helpModal.innerHTML = `
            <div class="modal-backdrop">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Ayuda del Sidebar</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <h4>Atajos de Teclado</h4>
                        <div class="shortcut-list">
                            <div><kbd>Ctrl</kbd> + <kbd>K</kbd> - Búsqueda rápida</div>
                            <div><kbd>Ctrl</kbd> + <kbd>B</kbd> - Toggle sidebar</div>
                            <div><kbd>F1</kbd> - Mostrar ayuda</div>
                            <div><kbd>Alt</kbd> + <kbd>T</kbd> - Cambiar tema</div>
                            <div><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd> - Comando de voz</div>
                        </div>
                        
                        <h4>Gestos</h4>
                        <div class="gesture-list">
                            <div>Deslizar desde la izquierda - Abrir sidebar (móvil)</div>
                            <div>Deslizar hacia la izquierda - Cerrar sidebar (móvil)</div>
                            <div>Click derecho en elementos - Menú contextual</div>
                        </div>
                        
                        <h4>Funciones Especiales</h4>
                        <div class="feature-list">
                            <div>• Auto-colapso por inactividad</div>
                            <div>• Comandos de voz</div>
                            <div>• Búsqueda inteligente</div>
                            <div>• Efectos visuales y sonoros</div>
                            <div>• Personalización completa</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        helpModal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 5000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        document.body.appendChild(helpModal);
        
        helpModal.querySelector('.modal-close').addEventListener('click', () => helpModal.remove());
        helpModal.querySelector('.modal-backdrop').addEventListener('click', (e) => {
            if (e.target === helpModal.querySelector('.modal-backdrop')) {
                helpModal.remove();
            }
        });
    }
    
    function toggleSidebarTheme() {
        const currentTheme = document.querySelector('.sidebar-wrapper')?.getAttribute('data-theme') || 'default';
        const themes = ['default', 'dark', 'light'];
        const nextTheme = themes[(themes.indexOf(currentTheme) + 1) % themes.length];
        
        applySidebarTheme(nextTheme);
        window.SidebarAPI?.showNotification(`Tema cambiado a ${nextTheme}`, 'info');
    }
    
    function applySidebarTheme(theme) {
        const sidebar = document.querySelector('.sidebar-wrapper');
        if (sidebar) {
            sidebar.setAttribute('data-theme', theme);
            
            // Guardar preferencia
            const prefs = JSON.parse(localStorage.getItem('sidebarPreferences') || '{}');
            prefs.theme = theme;
            localStorage.setItem('sidebarPreferences', JSON.stringify(prefs));
        }
    }
    
    // Agregar estilos CSS para los modales
    const modalStyles = document.createElement('style');
    modalStyles.textContent = `
        .modal-backdrop {
            background: rgba(0, 0, 0, 0.8);
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(5px);
        }
        
        .modal-content {
            background: white;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        .modal-header {
            padding: 1.5rem;
            border-bottom: 1px solid #e3e6f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(135deg, var(--sidebar-accent), var(--sidebar-accent-hover));
            color: white;
            border-radius: 12px 12px 0 0;
        }
        
        .modal-header h3 {
            margin: 0;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            color: white;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background-color 0.2s ease;
        }
        
        .modal-close:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .modal-body {
            padding: 1.5rem;
        }
        
        .modal-footer {
            padding: 1rem 1.5rem;
            border-top: 1px solid #e3e6f0;
            display: flex;
            gap: 0.5rem;
            justify-content: flex-end;
        }
        
        .preference-group {
            margin-bottom: 1rem;
        }
        
        .preference-label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
        }
        
        .preference-text {
            font-weight: 500;
        }
        
        .shortcut-list, .gesture-list, .feature-list {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 1rem;
            margin-top: 0.5rem;
        }
        
        .shortcut-list div, .gesture-list div {
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        kbd {
            background: #e9ecef;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-size: 0.8rem;
            border: 1px solid #adb5bd;
        }
        
        .btn-save-prefs, .btn-reset-prefs {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn-save-prefs {
            background: var(--sidebar-accent);
            color: white;
        }
        
        .btn-save-prefs:hover {
            background: var(--sidebar-accent-hover);
        }
        
        .btn-reset-prefs {
            background: #6c757d;
            color: white;
        }
        
        .btn-reset-prefs:hover {
            background: #5a6268;
        }
    `;
    
    document.head.appendChild(modalStyles);
});
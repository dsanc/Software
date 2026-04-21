/**
 * Sistema de manejo de errores de permisos para evaluadores
 * Este script intercepta errores de permisos y muestra modales informativos
 */

// Configuración global
window.PermissionHandler = {
    // Mapeo de módulos
    moduleMap: {
        'risk_hoteles': 'Risk Hoteles',
        'risk_conjuntos': 'Risk Conjuntos', 
        'security_probabilistic': 'Security Probabilistic'
    },
    
    // Mapeo de acciones
    actionMap: {
        'read': 'ver',
        'create': 'crear',
        'update': 'editar',
        'delete': 'eliminar',
        'export': 'exportar',
        'approve': 'aprobar'
    },

    /**
     * Muestra el modal de permisos denegados
     */
    showModal: function(module, action, errorType = 'permission_denied') {
        const moduleDisplay = this.moduleMap[module] || module;
        const actionDisplay = this.actionMap[action] || action;
        
        let title, message, suggestion;
        
        if (errorType === 'module_access') {
            title = 'Acceso Denegado al Módulo';
            message = `No tienes permisos para acceder al módulo <strong>${moduleDisplay}</strong>.`;
            suggestion = `Contacta a tu administrador para solicitar acceso al módulo ${moduleDisplay}.`;
        } else {
            title = 'Permisos Insuficientes';
            message = `No tienes permisos para <strong>${actionDisplay}</strong> en el módulo <strong>${moduleDisplay}</strong>.`;
            suggestion = `Solo puedes realizar las acciones para las que tienes permisos en ${moduleDisplay}.`;
        }
        
        // Actualizar contenido del modal
        document.getElementById('permissionDeniedModalLabel').innerHTML = `<i class="fas fa-ban me-2"></i>${title}`;
        document.getElementById('permissionDeniedMessage').innerHTML = message;
        document.getElementById('permissionDeniedDetailsText').innerHTML = 
            `Módulo: ${moduleDisplay}<br>Acción: ${actionDisplay}<br>Usuario: ${window.currentUser || 'Desconocido'}`;
        document.getElementById('permissionDeniedSuggestionText').innerHTML = suggestion;
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('permissionDeniedModal'));
        modal.show();
        
        // Log del error para debugging
        console.warn('🚫 Permission Denied:', { module, action, errorType, moduleDisplay, actionDisplay });
    },

    /**
     * Intercepta clics en enlaces y botones para verificar permisos
     */
    interceptPermissionErrors: function() {
        // Interceptar errores en peticiones AJAX
        $(document).ajaxError(function(event, xhr, settings) {
            if (xhr.status === 403) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.error === 'permission_denied' || response.error === 'module_access') {
                        event.preventDefault();
                        PermissionHandler.showModal(
                            response.module || 'unknown',
                            response.action || 'access',
                            response.error
                        );
                        return false;
                    }
                } catch (e) {
                    // Si no es JSON o no tiene la estructura esperada, mostrar modal genérico
                    PermissionHandler.showModal('unknown', 'access', 'permission_denied');
                }
            }
        });

        // Interceptar formularios que pueden dar errores de permisos
        $('form').on('submit', function(e) {
            const form = $(this);
            const action = form.attr('action');
            
            // Verificar si es un formulario que puede dar errores de permisos
            if (action && (action.includes('/crear') || action.includes('/edit') || action.includes('/delete'))) {
                // Aquí podrías añadir lógica adicional para verificar permisos antes del envío
            }
        });
    },

    /**
     * Maneja redirecciones por errores de permisos
     */
    handlePermissionRedirect: function() {
        // Verificar si estamos en una página de error de permisos por URL
        const urlParams = new URLSearchParams(window.location.search);
        const errorType = urlParams.get('error_type');
        const module = urlParams.get('module');
        const action = urlParams.get('action');
        
        if (errorType && module) {
            // Si estamos en una página de error, podríamos mostrar el modal automáticamente
            // O realizar otras acciones específicas
            console.info('📄 Permission error page loaded:', { errorType, module, action });
        }
    },

    /**
     * Inicializa el sistema de manejo de permisos
     */
    init: function() {
        $(document).ready(() => {
            this.interceptPermissionErrors();
            this.handlePermissionRedirect();
            
            // Establecer usuario actual para mostrar en modales
            window.currentUser = $('meta[name="current-user"]').attr('content') || 'Usuario';
            
            console.log('✅ Permission Handler initialized');
        });
    }
};

// Auto-inicializar cuando se carga el script
PermissionHandler.init();

// Función global para uso directo desde templates
window.showPermissionDeniedModal = function(module, action, errorType) {
    PermissionHandler.showModal(module, action, errorType);
};

// Funciones de utilidad para templates
window.PermissionUtils = {
    /**
     * Verifica si el usuario actual tiene un permiso específico
     * Útil para lógica del lado cliente
     */
    hasPermission: function(module, action) {
        // Esta función podría hacer una petición AJAX para verificar permisos
        // Por ahora retorna true (la verificación real se hace en el servidor)
        return true;
    },

    /**
     * Obtiene información del usuario actual
     */
    getCurrentUser: function() {
        return {
            username: window.currentUser || 'Usuario',
            isEvaluator: window.isEvaluator || false
        };
    }
};
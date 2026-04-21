// JavaScript personalizado para el proyecto Django Modular

// Mejorar experiencia de formularios
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema inicializado');
    
    // Mejorar formulario de login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        // Agregar estados de loading
        loginForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // Re-habilitar después de 5 segundos por seguridad
                setTimeout(() => {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
        
        // Auto-focus en primer campo
        const firstInput = loginForm.querySelector('input[type="email"], input[type="text"]');
        if (firstInput && !firstInput.value) {
            firstInput.focus();
        }
        
        // Mejorar validación visual
        const inputs = loginForm.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('invalid', function() {
                this.classList.add('is-invalid');
            });
            
            input.addEventListener('input', function() {
                if (this.validity.valid) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
    }
    
    // Mejorar experiencia de navegación
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Smooth transition effect
            document.body.style.opacity = '0.9';
            setTimeout(() => {
                document.body.style.opacity = '1';
            }, 100);
        });
    });
    
    // Mejorar cards interactivas
    const cards = document.querySelectorAll('.card, .dashboard-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Utilidad para mostrar mensajes
    window.showMessage = function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    };
    
    // Utilidad para validación de formularios
    window.validateForm = function(formElement) {
        const inputs = formElement.querySelectorAll('input[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.validity.valid) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }
        });
        
        return isValid;
    };
});

// Manejo global de errores
window.addEventListener('error', function(e) {
    if (e.message !== 'Script error.') {
        console.warn('Error capturado:', e.message, 'en', e.filename, 'línea', e.lineno);
    }
});

// Manejo de errores de promesas no capturadas
window.addEventListener('unhandledrejection', function(e) {
    console.warn('Promesa rechazada no manejada:', e.reason);
});

// Utilidades globales
window.utils = {
    // Función para copiar texto al clipboard
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                window.showMessage('Texto copiado al portapapeles', 'success');
            });
        }
    },
    
    // Función para formatear fechas
    formatDate: function(date) {
        return new Date(date).toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    
    // Función para validar email
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
};

// Cargar contador del carrito en el navbar
document.addEventListener('DOMContentLoaded', function() {
    // Solo cargar si existe el elemento del carrito flotante
    const cartCountFloating = document.getElementById('cart-count-floating');
    if (cartCountFloating) {
        loadCartCount();
    }
});

async function loadCartCount() {
    try {
        const response = await fetch('/subscriptions/api/cart/count/');
        if (response.ok) {
            const data = await response.json();
            updateCartUI(data.count, data.total);
        }
    } catch (error) {
        console.log('Error cargando contador del carrito:', error);
        // No mostrar error ya que puede ser normal si no hay carrito
    }
}

function updateCartUI(count, total) {
    // Actualizar solo el contador del botón flotante
    const cartCountFloating = document.getElementById('cart-count-floating');
    if (cartCountFloating) {
        cartCountFloating.textContent = count;
        cartCountFloating.style.display = count > 0 ? 'flex' : 'none';
    }
}

// Mejorar funcionalidad del navbar toggle
document.addEventListener('DOMContentLoaded', function() {
    const navbarToggler = document.querySelector('.navbar-toggler-professional');
    const navbarCollapse = document.querySelector('#navbarNav');
    
    if (navbarToggler && navbarCollapse) {
        // Manejar el estado aria-expanded
        navbarToggler.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !isExpanded);
        });
        
        // Cerrar menú al hacer clic en un enlace (móvil)
        const navLinks = navbarCollapse.querySelectorAll('.nav-link-professional');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) { // Solo en móvil
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                        toggle: false
                    });
                    bsCollapse.hide();
                    navbarToggler.setAttribute('aria-expanded', 'false');
                }
            });
        });
        
        // Cerrar menú al hacer clic fuera (móvil)
        document.addEventListener('click', function(e) {
            if (window.innerWidth < 992) {
                const isClickInsideNav = navbarCollapse.contains(e.target) || navbarToggler.contains(e.target);
                if (!isClickInsideNav && navbarCollapse.classList.contains('show')) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                        toggle: false
                    });
                    bsCollapse.hide();
                    navbarToggler.setAttribute('aria-expanded', 'false');
                }
            }
        });
    }
});
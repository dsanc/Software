// plans-cart.js - JavaScript para funcionalidad del carrito en planes
console.log('Plans Cart JS loaded');

// ==================== UTILITY FUNCTIONS ====================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    if (!cookieValue) {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            cookieValue = csrfInput.value;
        }
    }
    
    return cookieValue;
}

function createToast(type, title, message) {
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle';
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${icon} me-2"></i>
                    <strong>${title}</strong><br>
                    <small>${message}</small>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    return { id: toastId, html: toastHtml };
}

function showToast(toast) {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1060';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toast.html);
    
    const toastElement = document.getElementById(toast.id);
    const bsToast = new bootstrap.Toast(toastElement, { delay: 4000 });
    bsToast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// ==================== CART FUNCTIONS ====================

async function addPlanToCart(planId, billingCycle, quantity, planType) {
    try {
        const csrfToken = getCookie('csrftoken');
        
        if (!csrfToken) {
            throw new Error('CSRF token not found. Please refresh the page.');
        }
        
        const response = await fetch('/subscriptions/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                plan_id: planId,
                billing_cycle: billingCycle,
                quantity: quantity,
                plan_type: planType
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }
        
        return data;
        
    } catch (error) {
        console.error('Error adding plan to cart:', error);
        throw error;
    }
}

function updateCartUI(response) {
    const cartBadge = document.querySelector('.cart-badge');
    if (cartBadge && response.cart_count !== undefined) {
        cartBadge.textContent = response.cart_count;
        cartBadge.style.transform = 'scale(1.3)';
        setTimeout(() => {
            cartBadge.style.transform = 'scale(1)';
        }, 200);
    }
}

function showSuccessMessage(title, message) {
    const toast = createToast('success', title, message);
    showToast(toast);
}

function showErrorMessage(title, message) {
    const toast = createToast('error', title, message);
    showToast(toast);
}

// ==================== GUEST CART FUNCTIONS ====================

function showGuestCartOptions(planId, buttonElement) {
    const planName = buttonElement.getAttribute('data-plan-name') || 'Plan seleccionado';
    
    const modalHtml = `
        <div class="modal fade" id="guestCartModal" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-shopping-cart text-primary"></i>
                            Agregar "${planName}" al Carrito
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-4">¡Genial elección! Para continuar, elige una opción:</p>
                        
                        <div class="d-grid gap-3">
                            <button type="button" class="btn btn-primary btn-lg" onclick="proceedAsGuest('${planId}', this)">
                                <i class="fas fa-shopping-cart me-2"></i>
                                Agregar como Invitado
                                <small class="d-block text-white-50">Tu carrito se guardará durante esta sesión</small>
                            </button>
                            
                            <button type="button" class="btn btn-success btn-lg" onclick="goToLogin()">
                                <i class="fas fa-sign-in-alt me-2"></i>
                                Iniciar Sesión
                                <small class="d-block text-white-50">Accede a tu cuenta existente</small>
                            </button>
                            
                            <button type="button" class="btn btn-info btn-lg" onclick="goToRegister()">
                                <i class="fas fa-user-plus me-2"></i>
                                Crear Cuenta Nueva
                                <small class="d-block text-white-50">Obtén acceso completo a tu dashboard</small>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('guestCartModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modal = new bootstrap.Modal(document.getElementById('guestCartModal'));
    modal.show();
}

function proceedAsGuest(planId, buttonElement) {
    const modal = bootstrap.Modal.getInstance(document.getElementById('guestCartModal'));
    if (modal) {
        modal.hide();
    }
    
    const originalButtonText = buttonElement.innerHTML;
    buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Agregando...';
    buttonElement.disabled = true;
    
    addPlanToCart(planId, 'yearly', 1, 'standard')
        .then(response => {
            if (response.success) {
                showSuccessMessage('¡Agregado al carrito!', response.message);
                updateCartUI(response);
                
                if ('vibrate' in navigator) {
                    navigator.vibrate(100);
                }
            } else {
                showErrorMessage('Error', response.message);
            }
        })
        .catch(error => {
            console.error('Guest cart error:', error);
            let errorMessage = 'No se pudo agregar al carrito';
            
            if (error.message.includes('CSRF')) {
                errorMessage = 'Error de seguridad. Recarga la página e inténtalo de nuevo.';
            } else if (error.message.includes('HTTP')) {
                errorMessage = error.message;
            }
            
            showErrorMessage('Error al agregar', errorMessage);
        })
        .finally(() => {
            buttonElement.innerHTML = originalButtonText;
            buttonElement.disabled = false;
        });
}

// ==================== NAVIGATION FUNCTIONS ====================

function goToRegister() {
    window.location.href = '/users/register/';
}

function goToLogin() {
    window.location.href = '/users/login/';
}

function showContactModal(planId) {
    const modalHtml = `
        <div class="modal fade" id="contactModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Solicitar Cotización</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Para obtener información sobre precios empresariales, por favor contáctanos:</p>
                        <div class="contact-info">
                            <div class="mb-3">
                                <i class="fas fa-envelope text-primary"></i>
                                <strong>Email:</strong> ventas@empresa.com
                            </div>
                            <div class="mb-3">
                                <i class="fas fa-phone text-primary"></i>
                                <strong>Teléfono:</strong> +57 (1) 234-5678
                            </div>
                            <div class="mb-3">
                                <i class="fas fa-whatsapp text-success"></i>
                                <strong>WhatsApp:</strong> +57 300 123 4567
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        <a href="mailto:ventas@empresa.com?subject=Cotización Plan ID ${planId}" class="btn btn-primary">
                            <i class="fas fa-envelope"></i> Enviar Email
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('contactModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modal = new bootstrap.Modal(document.getElementById('contactModal'));
    modal.show();
}

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Plans Cart initialized');
    
    // Verificar CSRF token
    const csrfToken = getCookie('csrftoken');
    console.log('CSRF Token available:', !!csrfToken);
    
    // Verificar usuario autenticado
    const userMenu = document.querySelector('.user-menu');
    console.log('User authenticated:', !!userMenu);
    
    // Inicializar funcionalidad de botones de plan
    const planButtons = document.querySelectorAll('.btn-plan-select');
    planButtons.forEach(button => {
        button.addEventListener('click', function() {
            const planId = this.getAttribute('data-plan-id');
            
            if (!userMenu) {
                showGuestCartOptions(planId, this);
                return;
            }
            
            // Usuario autenticado - agregar directamente
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            this.disabled = true;
            
            if (this.classList.contains('demo')) {
                addPlanToCart(planId, 'yearly', 1, 'demo')
                    .then(response => {
                        if (response.success) {
                            showSuccessMessage('¡Plan Demo agregado!', response.message);
                            updateCartUI(response);
                        } else {
                            showErrorMessage('Error al agregar Demo', response.message);
                        }
                    })
                    .catch(error => {
                        console.error('Demo cart error:', error);
                        showErrorMessage('Error al agregar Demo', 'No se pudo agregar el plan demo al carrito');
                    })
                    .finally(() => {
                        this.innerHTML = originalText;
                        this.disabled = false;
                    });
            } else if (this.classList.contains('contact')) {
                showContactModal(planId);
                this.innerHTML = originalText;
                this.disabled = false;
            } else {
                showGuestCartOptions(planId, this);
                this.innerHTML = originalText;
                this.disabled = false;
            }
        });
    });
});

console.log('Plans Cart JS fully loaded');
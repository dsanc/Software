document.addEventListener('DOMContentLoaded', function() {
    // Función para cargar el contador del carrito
    function loadCartCount() {
        fetch('/subscriptions/api/cart/count/')
            .then(response => response.json())
            .then(data => {
                // Solo actualizar el contador del botón flotante
                const cartBadgeFloating = document.getElementById('cart-count-floating');
                if (cartBadgeFloating) {
                    if (data.count > 0) {
                        cartBadgeFloating.textContent = data.count;
                        cartBadgeFloating.style.display = 'block';
                    } else {
                        cartBadgeFloating.style.display = 'none';
                    }
                }
            })
            .catch(error => console.log('Error loading cart count:', error));
    }
    
    // Función para cargar el contenido del carrito
    function loadCartContent() {
        fetch('/subscriptions/api/cart/summary/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateCartOffcanvas(data);
                }
            })
            .catch(error => {
                console.error('Error loading cart content:', error);
                showEmptyCart();
            });
    }
    
    // Función para actualizar el contenido del offcanvas
    function updateCartOffcanvas(data) {
        const cartContent = document.getElementById('cart-content');
        const cartTotal = document.getElementById('cart-total');
        const checkoutBtn = document.getElementById('checkout-btn');
        
        if (!cartContent || !cartTotal) return;
        
        if (data.items && data.items.length > 0) {
            // Mostrar items del carrito
            let itemsHtml = '';
            data.items.forEach(item => {
                itemsHtml += `
                    <div class="cart-item-offcanvas mb-3 p-3 border rounded position-relative">
                        <button class="btn-close position-absolute top-0 end-0 m-2 remove-item-btn" 
                                data-item-id="${item.id}" 
                                aria-label="Eliminar"
                                style="font-size: 0.7rem;"></button>
                        
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1 pe-3">
                                <h6 class="mb-1">${item.plan.name}</h6>
                                <small class="text-muted d-block mb-2">${item.plan.module}</small>
                                
                                <div class="d-flex align-items-center gap-2 mt-2">
                                    <span class="badge bg-secondary">${item.billing_cycle}</span>
                                    
                                    <div class="input-group input-group-sm" style="width: 100px;">
                                        <button class="btn btn-outline-secondary update-qty-btn" 
                                                type="button" 
                                                data-action="decrease"
                                                data-item-id="${item.id}">-</button>
                                        <input type="text" class="form-control text-center p-0" value="${item.quantity}" readonly>
                                        <button class="btn btn-outline-secondary update-qty-btn" 
                                                type="button" 
                                                data-action="increase"
                                                data-item-id="${item.id}">+</button>
                                    </div>
                                </div>
                            </div>
                            <div class="text-end mt-4">
                                <div class="fw-bold text-primary">$${item.subtotal.toLocaleString()}</div>
                                <small class="text-muted" style="font-size: 0.75rem;">$${item.unit_price.toLocaleString()} c/u</small>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            cartContent.innerHTML = itemsHtml;
            cartTotal.textContent = data.total_amount.toLocaleString();
            
            // Mostrar botón de checkout
            if (checkoutBtn) {
                checkoutBtn.style.display = 'block';
            }
            
            // Asignar eventos a los nuevos botones
            attachCartItemEvents();
            
        } else {
            showEmptyCart();
        }
    }

    // Función para asignar eventos a los elementos del carrito
    function attachCartItemEvents() {
        // Botones de eliminar
        document.querySelectorAll('.remove-item-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                removeFromCart(itemId);
            });
        });
        
        // Botones de cantidad
        document.querySelectorAll('.update-qty-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                const action = this.dataset.action;
                const input = this.parentElement.querySelector('input');
                let currentQty = parseInt(input.value);
                
                if (action === 'increase') {
                    updateCartItem(itemId, currentQty + 1);
                } else if (action === 'decrease' && currentQty > 1) {
                    updateCartItem(itemId, currentQty - 1);
                }
            });
        });
    }

    // Función para eliminar item del carrito
    function removeFromCart(itemId) {
        // Visual feedback: disable button and fade out item
        const removeBtn = document.querySelector(`.remove-item-btn[data-item-id="${itemId}"]`);
        const itemRow = removeBtn?.closest('.cart-item-offcanvas');
        
        if (itemRow) {
            itemRow.style.opacity = '0.5';
            itemRow.style.pointerEvents = 'none';
        }
        
        fetch('/subscriptions/cart/remove/', {
            method: 'POST',
            body: JSON.stringify({ item_id: itemId }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Item eliminado del carrito', 'info');
                loadCartCount();
                loadCartContent();
            } else {
                // Revert visual changes if error
                if (itemRow) {
                    itemRow.style.opacity = '1';
                    itemRow.style.pointerEvents = 'auto';
                }
                showToast(data.message || 'Error al eliminar item', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Revert visual changes if error
            if (itemRow) {
                itemRow.style.opacity = '1';
                itemRow.style.pointerEvents = 'auto';
            }
            showToast('Error de conexión', 'error');
        });
    }

    // Función para actualizar cantidad
    function updateCartItem(itemId, quantity) {
        // Visual feedback: disable inputs
        const container = document.querySelector(`.update-qty-btn[data-item-id="${itemId}"]`)?.closest('.input-group');
        const input = container?.querySelector('input');
        const buttons = container?.querySelectorAll('button');
        
        if (input) input.style.opacity = '0.5';
        if (buttons) buttons.forEach(btn => btn.disabled = true);
        
        fetch('/subscriptions/cart/update/', {
            method: 'POST',
            body: JSON.stringify({ 
                item_id: itemId,
                quantity: quantity 
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadCartCount();
                loadCartContent(); // Recargar para actualizar subtotales
            } else {
                // Revert visual changes
                if (input) input.style.opacity = '1';
                if (buttons) buttons.forEach(btn => btn.disabled = false);
                showToast(data.message || 'Error al actualizar cantidad', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Revert visual changes
            if (input) input.style.opacity = '1';
            if (buttons) buttons.forEach(btn => btn.disabled = false);
            showToast('Error de conexión', 'error');
        });
    }
    
    // Función para mostrar carrito vacío
    function showEmptyCart() {
        const cartContent = document.getElementById('cart-content');
        const cartTotal = document.getElementById('cart-total');
        const checkoutBtn = document.getElementById('checkout-btn');
        
        if (cartContent) {
            cartContent.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-shopping-cart fa-3x mb-3"></i>
                    <p>Tu carrito está vacío</p>
                    <a href="/subscriptions/" class="btn btn-primary">Ver Planes</a>
                </div>
            `;
        }
        
        if (cartTotal) {
            cartTotal.textContent = '0';
        }
        
        if (checkoutBtn) {
            checkoutBtn.style.display = 'none';
        }
    }
    
    // Función para agregar al carrito
    function addToCart(planId, billingPeriod = 'yearly', quantity = 1) {
        // Mostrar loading en el botón
        const button = document.querySelector(`[data-plan-id="${planId}"]`);
        const originalText = button?.textContent;
        if (button) {
            button.disabled = true;
            button.textContent = 'Agregando...';
        }
        
        // CORRECCIÓN: URL actualizada para coincidir con urls.py
        fetch('/subscriptions/cart/add/', {
            method: 'POST',
            body: JSON.stringify({
                plan_id: planId,
                billing_cycle: billingPeriod,
                quantity: quantity
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Mostrar toast de éxito
                showToast(data.message, 'success');
                
                // Actualizar contador del carrito
                loadCartCount();
                
                // Si el offcanvas está abierto, actualizar su contenido
                const cartOffcanvas = document.getElementById('cartOffcanvas');
                if (cartOffcanvas && cartOffcanvas.classList.contains('show')) {
                    loadCartContent();
                }
                
                // Actualizar texto del botón según el resultado
                if (button) {
                    if (data.replaced) {
                        button.textContent = 'Reemplazado';
                        button.classList.remove('btn-primary');
                        button.classList.add('btn-warning');
                    } else if (data.updated) {
                        button.textContent = 'Actualizado';
                        button.classList.remove('btn-primary'); 
                        button.classList.add('btn-info');
                    } else {
                        button.textContent = 'Agregado ✓';
                        button.classList.remove('btn-primary');
                        button.classList.add('btn-success');
                    }
                    
                    // Restaurar después de 2 segundos
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.className = 'btn btn-primary add-to-cart-btn';
                        button.disabled = false;
                    }, 2000);
                }
            } else {
                // Manejar diferentes tipos de error
                let toastType = 'error';
                let title = 'Error';
                
                if (data.error_type === 'demo_already_used') {
                    title = 'Demo ya utilizado';
                    toastType = 'warning';
                } else if (data.error_type === 'demo_with_paid_plan') {
                    title = 'Conflicto de planes';
                    toastType = 'warning';
                } else if (data.error_type === 'system_error') {
                    title = 'Error del sistema';
                    toastType = 'error';
                }
                
                showToast(data.message, toastType, title);
                
                // Restaurar botón
                if (button) {
                    button.textContent = originalText;
                    button.disabled = false;
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error de conexión. Inténtalo de nuevo.', 'error');
            
            // Restaurar botón
            if (button) {
                button.textContent = originalText;
                button.disabled = false;
            }
        });
    }
    
    // Función para mostrar toasts mejorados
    function showToast(message, type = 'info', title = '') {
        // Crear toast dinámicamente si no existe
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // Configurar colores según el tipo
        const typeConfig = {
            'success': { bg: 'bg-success', icon: 'fas fa-check-circle', textTitle: title || 'Éxito' },
            'error': { bg: 'bg-danger', icon: 'fas fa-exclamation-triangle', textTitle: title || 'Error' },
            'warning': { bg: 'bg-warning', icon: 'fas fa-exclamation-circle', textTitle: title || 'Atención' },
            'info': { bg: 'bg-info', icon: 'fas fa-info-circle', textTitle: title || 'Información' }
        };
        
        const config = typeConfig[type] || typeConfig['info'];
        
        // Crear toast HTML
        const toastId = `toast-${Date.now()}`;
        const toastHTML = `
            <div id="${toastId}" class="toast" role="alert" data-bs-delay="5000">
                <div class="toast-header ${config.bg} text-white">
                    <i class="${config.icon} me-2"></i>
                    <strong class="me-auto">${config.textTitle}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        // Agregar al container
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        // Mostrar toast
        const toastElement = document.getElementById(toastId);
        const bsToast = new bootstrap.Toast(toastElement);
        bsToast.show();
        
        // Remover del DOM después de que se oculte
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
    
    // Expose functions to global scope
    window.addToCart = addToCart;
    window.removeFromCart = removeFromCart;
    window.updateCartItem = updateCartItem;
    window.loadCartCount = loadCartCount;
    window.loadCartContent = loadCartContent;

    // Cargar contador inicial
    loadCartCount();
    
    // Asegurar que el botón flotante sea visible
    const cartFloating = document.getElementById('cart-floating');
    if (cartFloating) {
        cartFloating.style.display = 'block';
        cartFloating.style.opacity = '1';
        cartFloating.style.visibility = 'visible';
        console.log('Cart floating button initialized and made visible');
    } else {
        console.warn('Cart floating button not found!');
    }
    
    // Event listener para cuando se abra el offcanvas del carrito
    const cartOffcanvas = document.getElementById('cartOffcanvas');
    if (cartOffcanvas) {
        cartOffcanvas.addEventListener('show.bs.offcanvas', function() {
            loadCartContent();
        });
    }
    
    // Manejar botones "Agregar al carrito"
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function() {
            const planId = this.dataset.planId;
            const moduleName = this.dataset.moduleName;
            const billingPeriod = this.dataset.billingPeriod || 'yearly';
            
            // Agregar al carrito
            addToCart(planId, billingPeriod, 1);
        });
    });
});

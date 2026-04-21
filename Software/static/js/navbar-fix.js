/**
 * Navbar Fix - Mejoras de funcionalidad del navbar
 */

document.addEventListener('DOMContentLoaded', function() {
    // Fix para navbar responsive: cerrar el menú collapse al hacer clic en un enlace
    const navbarToggler = document.querySelector('.navbar-toggler-professional');
    const navbarCollapse = document.querySelector('#navbarNav');

    if (navbarToggler && navbarCollapse) {
        const navLinks = navbarCollapse.querySelectorAll('.nav-link-professional');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (navbarCollapse.classList.contains('show') && window.innerWidth < 992) {
                    const bsCollapse = bootstrap.Collapse.getOrCreateInstance(navbarCollapse);
                    bsCollapse.hide();
                }
            });
        });
    }
    // NOTA: Los dropdowns de Bootstrap (.dropdown-toggle) se manejan
    // completamente por Bootstrap JS. No se añaden handlers manuales
    // para evitar conflictos con data-bs-toggle="dropdown".
});
/**
 * Navbar Fix - Mejoras de funcionalidad del navbar
 */

document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.querySelector('.navbar-professional');

    // Efecto scroll: aplicar clase .scrolled al bajar de 50px
    if (navbar) {
        var handleScroll = function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll(); // Aplicar estado inicial al cargar
    }

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
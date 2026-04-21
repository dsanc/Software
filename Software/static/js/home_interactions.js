document.addEventListener('DOMContentLoaded', function() {
    // Navbar scroll effect y navegación activa profesional
    const navbar = document.querySelector('.navbar-professional');
    const navLinks = document.querySelectorAll('.nav-link-professional[data-section]');
    const sections = document.querySelectorAll('section[id]');
    
    function handleScroll() {
        // Efecto de scroll en navbar
        if (window.scrollY > 50) {
            navbar?.classList.add('scrolled');
        } else {
            navbar?.classList.remove('scrolled');
        }
        
        // Navegación activa basada en scroll
        let currentSection = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 120;
            const sectionHeight = section.clientHeight;
            if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
                currentSection = section.getAttribute('id');
            }
        });
        
        // Actualizar enlaces activos
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-section') === currentSection) {
                link.classList.add('active');
            }
        });
    }
    
    // Smooth scroll para enlaces de navegación profesional
    document.querySelectorAll('.nav-link-professional[href^="#"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 100;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
            
            // Cerrar menú móvil si está abierto
            const navbarCollapse = document.querySelector('.navbar-collapse');
            const toggleButton = document.querySelector('.navbar-toggler-professional');
            if (navbarCollapse?.classList.contains('show') && toggleButton) {
                // Simular click en el toggle button
                const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                    toggle: false
                });
                bsCollapse.hide();
            }
        });
    });
    
    // Event listener para scroll
    window.addEventListener('scroll', handleScroll);
    
    // Inicializar estado del navbar
    handleScroll();
    
    // Fallback para navegación legacy (si existe)
    const legacyNavLinks = document.querySelectorAll('.navbar-nav .nav-link[href^="#"]');
    legacyNavLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                window.scrollTo({
                    top: targetSection.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Manejar formulario de contacto
    const contactForm = document.querySelector('#contacto form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Simular envío del formulario
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';
            submitBtn.disabled = true;
            
            setTimeout(() => {
                alert('¡Gracias por tu mensaje! Te contactaremos pronto.');
                this.reset();
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 2000);
        });
    }
    
    // Media Carousel mejorado
    const mediaSlides = document.querySelectorAll('.media-slide');
    let currentSlide = 0;
    
    function showNextSlide() {
        if (mediaSlides.length > 1) {
            mediaSlides[currentSlide].classList.remove('active');
            currentSlide = (currentSlide + 1) % mediaSlides.length;
            mediaSlides[currentSlide].classList.add('active');
        }
    }
    
    // Cambiar slide cada 5 segundos
    if (mediaSlides.length > 1) {
        setInterval(showNextSlide, 5000);
    }
    
    // Animaciones de entrada
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);
    
    // Observar elementos para animaciones
    document.querySelectorAll('.service-card, .enterprise-module-card, .solution-card').forEach(el => {
        observer.observe(el);
    });
});

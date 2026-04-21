# Configuración de Logos y Branding

Este documento explica cómo personalizar los logos y elementos de branding en la aplicación Django modular.

## Configuración Básica

### Variables de Entorno

Copia el archivo `.env.logo.example` como referencia y añade estas variables a tu archivo `.env`:

```bash
# Logo principal
SITE_LOGO_URL=images/logo-sidebar.svg
SITE_NAME=Mi Aplicación

# Logos específicos del sidebar
LOGO_SIDEBAR_STANDARD=images/logo-sidebar.svg
LOGO_SIDEBAR_HIDPI=images/logo-sidebar-@2x.svg
LOGO_SIDEBAR_FALLBACK=fas fa-cube
LOGO_ALT_TEXT=Mi Empresa
```

## Archivos de Logo

### Estructura Recomendada

Coloca tus logos en `static/images/` con la siguiente estructura:

```
static/images/
├── logo-sidebar.svg          # Logo estándar (34x34px)
├── logo-sidebar-@2x.svg      # Logo HiDPI (68x68px)
├── logo-navbar.svg           # Logo para navbar (opcional)
├── logo-navbar-@2x.svg       # Logo navbar HiDPI (opcional)
├── favicon.ico               # Favicon ICO
└── favicon.png               # Favicon PNG
```

### Formatos Soportados

- **SVG**: Recomendado para mejor calidad y escalabilidad
- **PNG**: Fallback para navegadores que no soporten SVG
- **JPG**: Soportado pero no recomendado

### Dimensiones

- **Sidebar estándar**: 34x34 píxeles
- **Sidebar HiDPI**: 68x68 píxeles (2x)
- **Navbar**: 40x40 píxeles (estándar), 80x80 píxeles (HiDPI)

## Personalización Avanzada

### Logos Externos

Puedes usar URLs externas para los logos:

```bash
SITE_LOGO_URL=https://mi-cdn.com/logos/logo-empresarial.svg
LOGO_SIDEBAR_STANDARD=https://mi-cdn.com/logos/sidebar-logo.png
```

### Iconos de Fallback

Si el logo no carga, se muestra un icono de FontAwesome. Puedes personalizarlo:

```bash
LOGO_SIDEBAR_FALLBACK=fas fa-building    # Para empresas
LOGO_SIDEBAR_FALLBACK=fas fa-rocket      # Para startups
LOGO_SIDEBAR_FALLBACK=fas fa-heart       # Para ONGs
```

### Colores de Branding

```bash
PRIMARY_COLOR=#1e40af        # Azul corporativo
SECONDARY_COLOR=#7c3aed      # Púrpura de acento
```

## Configuración Programática

### Context Processors

El sistema usa context processors para hacer las configuraciones disponibles en todos los templates:

- `core.context_processors.branding_context`
- `core.context_processors.site_context`

### Configuración en Settings

```python
LOGO_CONFIG = {
    'sidebar': {
        'standard': 'images/mi-logo.svg',
        'hidpi': 'images/mi-logo-@2x.svg',
        'fallback_icon': 'fas fa-building',
        'alt_text': 'Mi Empresa',
    }
}
```

## Soporte HiDPI/Retina

El sistema automáticamente detecta pantallas de alta resolución y carga el logo apropiado:

```html
<img src="logo.svg" 
     srcset="logo.svg 1x, logo-@2x.svg 2x"
     alt="Mi Logo">
```

## Troubleshooting

### El logo no aparece

1. Verifica que el archivo existe en `static/images/`
2. Ejecuta `python manage.py collectstatic` si estás en producción
3. Revisa la consola del navegador por errores 404
4. Verifica que las variables de entorno están configuradas

### El logo se ve pixelado

- Asegúrate de tener versiones @2x para pantallas HiDPI
- Usa formato SVG cuando sea posible
- Verifica las dimensiones del archivo

### El fallback no funciona

- Verifica que FontAwesome está cargado
- Comprueba que el nombre del icono es válido (ej: `fas fa-cube`)
- Revisa la consola del navegador por errores JavaScript

## Ejemplos de Uso

### Logo Corporativo

```bash
SITE_NAME=EmpresaCorp
LOGO_SIDEBAR_STANDARD=images/empresacorp-logo.svg
LOGO_SIDEBAR_FALLBACK=fas fa-building
LOGO_ALT_TEXT=EmpresaCorp
PRIMARY_COLOR=#003d7a
```

### Startup Tech

```bash
SITE_NAME=TechStartup
LOGO_SIDEBAR_STANDARD=images/rocket-logo.svg
LOGO_SIDEBAR_FALLBACK=fas fa-rocket
LOGO_ALT_TEXT=TechStartup
PRIMARY_COLOR=#6366f1
```

### ONG/Fundación

```bash
SITE_NAME=FundaciónAyuda
LOGO_SIDEBAR_STANDARD=images/heart-logo.svg
LOGO_SIDEBAR_FALLBACK=fas fa-heart
LOGO_ALT_TEXT=Fundación Ayuda
PRIMARY_COLOR=#059669
```
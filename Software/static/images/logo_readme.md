# Logo Sidebar

Este directorio contiene los logos del sidebar en diferentes formatos y resoluciones:

## Archivos disponibles

- `logo-sidebar.svg` - Logo principal en formato SVG (34x34px)
- `logo-sidebar-@2x.svg` - Logo en alta resolución para pantallas HiDPI (68x68px)
- `logo-sidebar.png` - Fallback PNG estándar (34x34px)
- `logo-sidebar-@2x.png` - Fallback PNG alta resolución (68x68px)

## Uso

El template automáticamente detecta la resolución de pantalla y carga el logo apropiado:

- Pantallas normales: `logo-sidebar.svg` o `logo-sidebar.png`
- Pantallas HiDPI/Retina: `logo-sidebar-@2x.svg` o `logo-sidebar-@2x.png`

## Personalización

Para reemplazar el logo:

1. Mantén las mismas dimensiones (34x34px para estándar, 68x68px para @2x)
2. Usa preferiblemente formato SVG para mejor calidad
3. Asegúrate de que el logo sea legible en fondo oscuro
4. Testa tanto en modo colapsado como expandido del sidebar
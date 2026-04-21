# Proyecto Django Modular

Este es un proyecto Django diseñado con una arquitectura modular para facilitar el mantenimiento y escalabilidad.

## Estructura del Proyecto

- `apps/` - Contiene todas las aplicaciones Django modulares
- `config/` - Configuraciones del proyecto (settings modulares)
- `core/` - Funcionalidades base y utilidades compartidas
- `static/` - Archivos estáticos globales
- `templates/` - Plantillas base del proyecto
- `requirements/` - Archivos de dependencias por entorno

## Comandos Principales

- `python manage.py runserver` - Ejecutar servidor de desarrollo
- `python manage.py migrate` - Aplicar migraciones
- `python manage.py createsuperuser` - Crear usuario administrador
- `python manage.py collectstatic` - Recopilar archivos estáticos

## Aplicaciones Modulares

Cada aplicación se encuentra en el directorio `apps/` y tiene su propia responsabilidad específica.
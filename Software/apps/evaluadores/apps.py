from django.apps import AppConfig


class EvaluadoresConfig(AppConfig):
    """Configuración de la aplicación evaluadores"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.evaluadores'
    verbose_name = 'Evaluadores'
    
    def ready(self):
        """Importar signals al cargar la aplicación"""
        import apps.evaluadores.signals
from django.apps import AppConfig


class RiskHotelesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.risk_hoteles'
    verbose_name = 'Risk Analysis - Hotels'
    
    def ready(self):
        """
        Importa las señales cuando la aplicación está lista
        """
        try:
            import apps.risk_hoteles.signals  # noqa F401
            import apps.risk_hoteles.websocket_signals  # noqa F401
        except ImportError:
            pass
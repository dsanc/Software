from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.subscriptions'
    verbose_name = 'Suscripciones y Pagos'
    
    def ready(self):
        # Importar señales cuando la app esté lista
        import apps.subscriptions.signals
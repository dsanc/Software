from django.apps import AppConfig


class RiskConjuntosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.risk_conjuntos'
    verbose_name = 'Análisis de Riesgo - Conjuntos Residenciales'
    
    def ready(self):
        # Importar signals si los necesitamos
        pass

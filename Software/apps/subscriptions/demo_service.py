"""
Servicios para gestión de planes demo
"""
from django.utils import timezone
from datetime import timedelta
from .models import Module, PlanType, Plan, Subscription
import logging

logger = logging.getLogger(__name__)


class DemoService:
    """
    Servicio para manejar la funcionalidad de planes demo
    """
    
    @staticmethod
    def get_or_create_demo_plan():
        """
        Obtiene o crea el plan demo estándar del sistema
        """
        try:
            # Crear o obtener el módulo "Demo"
            demo_module, created = Module.objects.get_or_create(
                name='demo',
                defaults={
                    'display_name': 'Acceso Demo',
                    'description': 'Acceso básico al sistema con limitaciones para explorar funcionalidades',
                    'icon': 'fas fa-gift',
                    'color': '#28a745',
                    'is_active': True,
                    'order': 0
                }
            )
            
            if created:
                logger.info("Módulo demo creado exitosamente")
            
            # Crear o obtener el tipo de plan "Demo"
            demo_plan_type, created = PlanType.objects.get_or_create(
                name='Demo',
                defaults={
                    'description': 'Plan gratuito con funciones limitadas para explorar el sistema',
                    'order': 0,
                    'is_active': True
                }
            )
            
            if created:
                logger.info("Tipo de plan demo creado exitosamente")
            
            # Crear o obtener el plan demo
            demo_plan, created = Plan.objects.get_or_create(
                module=demo_module,
                plan_type=demo_plan_type,
                defaults={
                    'name': 'Plan Demo Gratuito',
                    'description': 'Acceso gratuito con limitaciones para explorar todas las funciones del sistema',
                    'monthly_price': 0,
                    'quarterly_price': 0,
                    'yearly_price': 0,
                    'trial_days': 30,
                    'max_users': 1,
                    'max_reports': 3,
                    'max_storage_gb': 1,  # 500MB expresado como fracción de GB
                    'features': {
                        'basic_access': True,
                        'dashboard_access': True,
                        'reports': True,
                        'limited_reports': True,
                        'watermark': True,
                        'email_support': True,
                        'data_export': False,
                        'advanced_features': False,
                        'api_access': False,
                        'custom_branding': False
                    },
                    'limits': {
                        'monthly_reports': 3,
                        'storage_mb': 500,
                        'watermark_reports': True,
                        'export_formats': ['pdf'],
                        'concurrent_users': 1
                    },
                    'is_active': True,
                    'order': 0
                }
            )
            
            if created:
                logger.info("Plan demo creado exitosamente")
            
            return demo_plan
            
        except Exception as e:
            logger.error(f"Error creando/obteniendo plan demo: {e}")
            raise
    
    @staticmethod
    def activate_demo_for_user(user):
        """
        Activa el plan demo para un usuario específico
        
        Args:
            user: Instancia del usuario
            
        Returns:
            Subscription: La suscripción demo creada
            
        Raises:
            Exception: Si ocurre un error durante la activación
        """
        try:
            # Verificar si ya tiene una suscripción activa
            existing_subscription = Subscription.objects.filter(
                user=user,
                status='active'
            ).first()
            
            if existing_subscription:
                raise ValueError(f"El usuario {user.email} ya tiene una suscripción activa")
            
            # Obtener el plan demo
            demo_plan = DemoService.get_or_create_demo_plan()
            
            # Crear la suscripción demo
            demo_subscription = Subscription.objects.create(
                user=user,
                plan=demo_plan,
                billing_cycle='monthly',
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=30),
                status='active',
                is_trial=True,
                trial_end_date=timezone.now() + timedelta(days=30),
                current_users=1,  # El usuario que lo activó
                current_reports=0,
                current_storage_gb=0.0
            )
            
            logger.info(f"Plan demo activado exitosamente para usuario {user.email}")
            
            return demo_subscription
            
        except Exception as e:
            logger.error(f"Error activando plan demo para {user.email}: {e}")
            raise
    
    @staticmethod
    def get_user_demo_subscription(user):
        """
        Obtiene la suscripción demo activa de un usuario
        
        Args:
            user: Instancia del usuario
            
        Returns:
            Subscription: La suscripción demo activa o None
        """
        try:
            demo_plan = DemoService.get_or_create_demo_plan()
            
            demo_subscription = Subscription.objects.filter(
                user=user,
                plan=demo_plan,
                status='active',
                is_trial=True
            ).first()
            
            return demo_subscription
            
        except Exception as e:
            logger.error(f"Error obteniendo suscripción demo para {user.email}: {e}")
            return None
    
    @staticmethod
    def is_user_on_demo(user):
        """
        Verifica si un usuario está usando el plan demo
        
        Args:
            user: Instancia del usuario
            
        Returns:
            bool: True si está usando demo, False en caso contrario
        """
        demo_subscription = DemoService.get_user_demo_subscription(user)
        return demo_subscription is not None
    
    @staticmethod
    def get_demo_usage_stats(user):
        """
        Obtiene estadísticas de uso del plan demo para un usuario
        
        Args:
            user: Instancia del usuario
            
        Returns:
            dict: Estadísticas de uso o None si no está en demo
        """
        demo_subscription = DemoService.get_user_demo_subscription(user)
        
        if not demo_subscription:
            return None
        
        # Calcular días restantes
        days_remaining = (demo_subscription.end_date - timezone.now()).days
        
        # Calcular porcentajes de uso
        reports_usage_percent = (demo_subscription.current_reports / demo_subscription.plan.max_reports) * 100
        storage_usage_percent = (demo_subscription.current_storage_gb / demo_subscription.plan.max_storage_gb) * 100
        
        return {
            'days_remaining': max(0, days_remaining),
            'total_days': 30,
            'reports_used': demo_subscription.current_reports,
            'reports_limit': demo_subscription.plan.max_reports,
            'reports_usage_percent': min(100, reports_usage_percent),
            'storage_used_gb': demo_subscription.current_storage_gb,
            'storage_limit_gb': demo_subscription.plan.max_storage_gb,
            'storage_usage_percent': min(100, storage_usage_percent),
            'is_expired': demo_subscription.is_expired(),
            'expires_at': demo_subscription.end_date
        }
    
    @staticmethod
    def can_user_perform_action(user, action_type):
        """
        Verifica si un usuario demo puede realizar una acción específica
        
        Args:
            user: Instancia del usuario
            action_type: Tipo de acción ('create_report', 'upload_file', etc.)
            
        Returns:
            tuple: (bool, str) - (puede_realizar, mensaje_error)
        """
        demo_subscription = DemoService.get_user_demo_subscription(user)
        
        if not demo_subscription:
            return True, ""  # No está en demo, no hay limitaciones
        
        if demo_subscription.is_expired():
            return False, "Tu período de demo ha expirado. Actualiza a un plan de pago para continuar."
        
        # Verificar límites específicos por acción
        if action_type == 'create_report':
            if demo_subscription.current_reports >= demo_subscription.plan.max_reports:
                return False, f"Has alcanzado el límite de {demo_subscription.plan.max_reports} reportes para el plan demo."
        
        elif action_type == 'upload_file':
            # Convertir storage a MB para comparación
            storage_limit_mb = demo_subscription.plan.max_storage_gb * 1024
            storage_used_mb = demo_subscription.current_storage_gb * 1024
            
            if storage_used_mb >= storage_limit_mb:
                return False, f"Has alcanzado el límite de {storage_limit_mb:.0f}MB de almacenamiento para el plan demo."
        
        elif action_type == 'export_data':
            if not demo_subscription.plan.features.get('data_export', False):
                return False, "La exportación de datos no está disponible en el plan demo. Actualiza tu plan para acceder a esta función."
        
        elif action_type == 'advanced_features':
            if not demo_subscription.plan.features.get('advanced_features', False):
                return False, "Las funciones avanzadas no están disponibles en el plan demo. Actualiza tu plan para acceder."
        
        return True, ""
    
    @staticmethod
    def increment_usage(user, usage_type, amount=1):
        """
        Incrementa el uso de un recurso para un usuario demo
        
        Args:
            user: Instancia del usuario
            usage_type: Tipo de uso ('reports', 'storage_gb')
            amount: Cantidad a incrementar
        """
        demo_subscription = DemoService.get_user_demo_subscription(user)
        
        if not demo_subscription:
            return  # No está en demo, no necesitamos trackear
        
        try:
            if usage_type == 'reports':
                demo_subscription.current_reports += amount
            elif usage_type == 'storage_gb':
                demo_subscription.current_storage_gb += amount
            
            demo_subscription.save()
            
            logger.info(f"Uso incrementado para {user.email}: {usage_type} += {amount}")
            
        except Exception as e:
            logger.error(f"Error incrementando uso para {user.email}: {e}")
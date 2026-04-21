"""
Comando para crear datos de ejemplo para el sistema de suscripciones
"""
from django.core.management.base import BaseCommand
from apps.subscriptions.models import Module, PlanType, Plan


class Command(BaseCommand):
    help = 'Crea datos de ejemplo para módulos y planes de suscripción'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de ejemplo...'))
        
        # Crear tipos de planes
        plan_types_data = [
            {'name': 'Básico', 'description': 'Plan básico con funcionalidades esenciales', 'order': 1},
            {'name': 'Pro', 'description': 'Plan profesional con características avanzadas', 'order': 2},
            {'name': 'Enterprise', 'description': 'Plan empresarial con todas las funcionalidades', 'order': 3},
            {'name': 'Starter', 'description': 'Plan de inicio para pequeñas empresas', 'order': 1},
            {'name': 'Advanced', 'description': 'Plan avanzado para empresas medianas', 'order': 2},
            {'name': 'Premium', 'description': 'Plan premium con características exclusivas', 'order': 3},
            {'name': 'Essential', 'description': 'Plan esencial para comenzar', 'order': 1},
            {'name': 'Professional', 'description': 'Plan profesional para equipos', 'order': 2},
        ]
        
        plan_types = {}
        for pt_data in plan_types_data:
            plan_type, created = PlanType.objects.get_or_create(
                name=pt_data['name'],
                defaults=pt_data
            )
            plan_types[pt_data['name']] = plan_type
            if created:
                self.stdout.write(f'✓ Tipo de plan creado: {plan_type.name}')
        
        # Crear módulos
        modules_data = [
            {
                'name': 'risk_hoteles',
                'display_name': 'Risk Hoteles',
                'description': 'Análisis integral de riesgos para hoteles y establecimientos turísticos. Evalúa riesgos operacionales, financieros y de seguridad.',
                'icon': 'fas fa-hotel',
                'color': '#e74c3c',
                'order': 1
            },
            {
                'name': 'risk_conjuntos',
                'display_name': 'Risk Conjuntos',
                'description': 'Evaluación de riesgos para conjuntos residenciales y propiedades horizontales. Análisis de seguridad y gestión comunitaria.',
                'icon': 'fas fa-building',
                'color': '#3498db',
                'order': 2
            },
            {
                'name': 'security_probabilistic',
                'display_name': 'Security Probabilistic',
                'description': 'Análisis probabilístico de seguridad usando machine learning e inteligencia artificial para predicción de riesgos.',
                'icon': 'fas fa-brain',
                'color': '#9b59b6',
                'order': 3
            }
        ]
        
        modules = {}
        for mod_data in modules_data:
            module, created = Module.objects.get_or_create(
                name=mod_data['name'],
                defaults=mod_data
            )
            modules[mod_data['name']] = module
            if created:
                self.stdout.write(f'✓ Módulo creado: {module.display_name}')
        
        # Crear planes para Risk Hoteles
        risk_hoteles_plans = [
            {
                'plan_type': 'Básico',
                'name': 'Análisis básico de riesgos hoteleros',
                'description': 'Plan básico para hoteles pequeños con análisis esencial de riesgos operacionales.',
                'monthly_price': 45000,
                'quarterly_price': 120000,
                'yearly_price': 432000,
                'max_users': 2,
                'max_reports': 10,
                'max_storage_gb': 1,
                'features': {
                    'basic_risk_analysis': True,
                    'occupancy_reports': True,
                    'basic_alerts': True,
                    'email_support': True,
                    'advanced_reports': False,
                    'custom_alerts': False,
                    'api_access': False
                },
                'is_featured': False,
                'order': 1
            },
            {
                'plan_type': 'Pro',
                'name': 'Análisis profesional de riesgos hoteleros',
                'description': 'Plan profesional con análisis avanzado y reportes detallados para hoteles medianos.',
                'monthly_price': 85000,
                'quarterly_price': 230000,
                'yearly_price': 816000,
                'max_users': 10,
                'max_reports': 100,
                'max_storage_gb': 10,
                'features': {
                    'basic_risk_analysis': True,
                    'occupancy_reports': True,
                    'basic_alerts': True,
                    'email_support': True,
                    'advanced_reports': True,
                    'custom_alerts': True,
                    'financial_analysis': True,
                    'competitor_analysis': True,
                    'api_access': True
                },
                'is_featured': True,
                'order': 2
            },
            {
                'plan_type': 'Enterprise',
                'name': 'Solución empresarial completa',
                'description': 'Solución completa para cadenas hoteleras con análisis predictivo y soporte premium.',
                'monthly_price': 150000,
                'quarterly_price': 405000,
                'yearly_price': 1440000,
                'max_users': -1,
                'max_reports': -1,
                'max_storage_gb': 100,
                'features': {
                    'basic_risk_analysis': True,
                    'occupancy_reports': True,
                    'basic_alerts': True,
                    'email_support': True,
                    'advanced_reports': True,
                    'custom_alerts': True,
                    'financial_analysis': True,
                    'competitor_analysis': True,
                    'api_access': True,
                    'predictive_analysis': True,
                    'custom_integrations': True,
                    'dedicated_support': True,
                    'white_label': True
                },
                'is_featured': False,
                'order': 3
            }
        ]
        
        for plan_data in risk_hoteles_plans:
            plan_type_name = plan_data.pop('plan_type')
            plan, created = Plan.objects.get_or_create(
                module=modules['risk_hoteles'],
                plan_type=plan_types[plan_type_name],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'✓ Plan creado: Risk Hoteles - {plan_type_name}')
        
        # Crear planes para Risk Conjuntos
        risk_conjuntos_plans = [
            {
                'plan_type': 'Starter',
                'name': 'Gestión básica de conjuntos',
                'description': 'Plan inicial para conjuntos residenciales pequeños con análisis básico de seguridad.',
                'monthly_price': 35000,
                'quarterly_price': 94500,
                'yearly_price': 336000,
                'max_users': 1,
                'max_reports': 5,
                'max_storage_gb': 1,
                'features': {
                    'basic_security_analysis': True,
                    'resident_reports': True,
                    'basic_incidents': True,
                    'email_notifications': True,
                    'advanced_analytics': False,
                    'visitor_management': False
                },
                'is_featured': False,
                'order': 1
            },
            {
                'plan_type': 'Advanced',
                'name': 'Gestión avanzada de conjuntos',
                'description': 'Plan avanzado con gestión completa de seguridad y análisis detallado de incidentes.',
                'monthly_price': 65000,
                'quarterly_price': 175500,
                'yearly_price': 624000,
                'max_users': 5,
                'max_reports': 50,
                'max_storage_gb': 5,
                'features': {
                    'basic_security_analysis': True,
                    'resident_reports': True,
                    'basic_incidents': True,
                    'email_notifications': True,
                    'advanced_analytics': True,
                    'visitor_management': True,
                    'incident_tracking': True,
                    'security_trends': True,
                    'mobile_app': True
                },
                'is_featured': True,
                'order': 2
            },
            {
                'plan_type': 'Premium',
                'name': 'Solución premium para conjuntos',
                'description': 'Solución premium con IA para análisis predictivo y gestión integral de mega-conjuntos.',
                'monthly_price': 120000,
                'quarterly_price': 324000,
                'yearly_price': 1152000,
                'max_users': -1,
                'max_reports': -1,
                'max_storage_gb': 50,
                'features': {
                    'basic_security_analysis': True,
                    'resident_reports': True,
                    'basic_incidents': True,
                    'email_notifications': True,
                    'advanced_analytics': True,
                    'visitor_management': True,
                    'incident_tracking': True,
                    'security_trends': True,
                    'mobile_app': True,
                    'ai_predictions': True,
                    'smart_integrations': True,
                    'priority_support': True
                },
                'is_featured': False,
                'order': 3
            }
        ]
        
        for plan_data in risk_conjuntos_plans:
            plan_type_name = plan_data.pop('plan_type')
            plan, created = Plan.objects.get_or_create(
                module=modules['risk_conjuntos'],
                plan_type=plan_types[plan_type_name],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'✓ Plan creado: Risk Conjuntos - {plan_type_name}')
        
        # Crear planes para Security Probabilistic
        security_plans = [
            {
                'plan_type': 'Essential',
                'name': 'Análisis probabilístico esencial',
                'description': 'Análisis básico de probabilidades de seguridad con algoritmos estándar.',
                'monthly_price': 55000,
                'quarterly_price': 148500,
                'yearly_price': 528000,
                'max_users': 3,
                'max_reports': 20,
                'max_storage_gb': 2,
                'features': {
                    'probability_analysis': True,
                    'risk_scoring': True,
                    'basic_ml_models': True,
                    'standard_alerts': True,
                    'report_exports': True,
                    'advanced_ml': False,
                    'custom_models': False
                },
                'is_featured': False,
                'order': 1
            },
            {
                'plan_type': 'Professional',
                'name': 'Análisis profesional con IA',
                'description': 'Análisis avanzado con machine learning y modelos predictivos personalizados.',
                'monthly_price': 95000,
                'quarterly_price': 256500,
                'yearly_price': 912000,
                'max_users': 15,
                'max_reports': 200,
                'max_storage_gb': 20,
                'features': {
                    'probability_analysis': True,
                    'risk_scoring': True,
                    'basic_ml_models': True,
                    'standard_alerts': True,
                    'report_exports': True,
                    'advanced_ml': True,
                    'custom_models': True,
                    'predictive_analytics': True,
                    'real_time_analysis': True,
                    'api_integration': True
                },
                'is_featured': True,
                'order': 2
            },
            {
                'plan_type': 'Enterprise',
                'name': 'Plataforma empresarial de IA',
                'description': 'Plataforma completa con IA avanzada, deep learning y análisis en tiempo real.',
                'monthly_price': 180000,
                'quarterly_price': 486000,
                'yearly_price': 1728000,
                'max_users': -1,
                'max_reports': -1,
                'max_storage_gb': 200,
                'features': {
                    'probability_analysis': True,
                    'risk_scoring': True,
                    'basic_ml_models': True,
                    'standard_alerts': True,
                    'report_exports': True,
                    'advanced_ml': True,
                    'custom_models': True,
                    'predictive_analytics': True,
                    'real_time_analysis': True,
                    'api_integration': True,
                    'deep_learning': True,
                    'neural_networks': True,
                    'quantum_analysis': True,
                    'enterprise_support': True,
                    'on_premise_deployment': True
                },
                'is_featured': False,
                'order': 3
            }
        ]
        
        for plan_data in security_plans:
            plan_type_name = plan_data.pop('plan_type')
            plan, created = Plan.objects.get_or_create(
                module=modules['security_probabilistic'],
                plan_type=plan_types[plan_type_name],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'✓ Plan creado: Security Probabilistic - {plan_type_name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Datos de ejemplo creados exitosamente!\n'
                f'• {Module.objects.count()} módulos\n'
                f'• {PlanType.objects.count()} tipos de planes\n'
                f'• {Plan.objects.count()} planes\n\n'
                f'Puedes ver los planes en: /subscriptions/plans/'
            )
        )
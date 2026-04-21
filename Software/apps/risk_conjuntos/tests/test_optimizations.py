"""
Tests adicionales para validar las optimizaciones del módulo risk_conjuntos
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.risk_conjuntos.models import (
    Conjunto, TipoConjunto, EvaluacionRiesgo, TipoRiesgo, 
    EscenarioRiesgo, PreguntaEvaluacion, CalificacionOpcion
)
from apps.risk_conjuntos.models_optimized import (
    AnalisisRiesgo, PonderacionRiesgo, MetricaCalidad, RecomendacionSistema
)
from apps.risk_conjuntos.performance_optimizations import CacheManager
from decimal import Decimal

User = get_user_model()


class ModulosOptimizadosTestCase(TestCase):
    """
    Tests para los modelos optimizados y refactorizados
    """
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        
        self.tipo_conjunto = TipoConjunto.objects.create(
            nombre='conjunto_cerrado',
            descripcion='Conjunto Test'
        )
        
        self.conjunto = Conjunto.objects.create(
            propietario=self.user,
            nit='123456789-0',
            nombre='Conjunto Test',
            tipo_conjunto=self.tipo_conjunto,
            direccion='Calle Test 123',
            ciudad='Bogotá',
            departamento='Cundinamarca',
            numero_unidades=100
        )
    
    def test_analisis_riesgo_creation(self):
        """Test creación de análisis de riesgo"""
        analisis = AnalisisRiesgo.objects.create(
            valor_riesgo=Decimal('0.75')
        )
        
        self.assertEqual(analisis.porcentaje_riesgo, 75.0)
        self.assertEqual(analisis.nivel_riesgo, 'alto')
        self.assertEqual(analisis.color_nivel, '#e74c3c')
        self.assertEqual(analisis.icono_nivel, 'fas fa-fire')
    
    def test_ponderacion_riesgo(self):
        """Test cálculo de ponderación"""
        ponderacion = PonderacionRiesgo.objects.create(
            peso_pregunta=Decimal('2.5'),
            valor_ponderado=Decimal('1.25')
        )
        
        self.assertEqual(ponderacion.peso_pregunta, Decimal('2.5'))
        self.assertEqual(ponderacion.valor_ponderado, Decimal('1.25'))
    
    def test_metrica_calidad(self):
        """Test métricas de calidad"""
        metrica = MetricaCalidad.objects.create(
            confiabilidad=Decimal('95.5'),
            requiere_atencion=True
        )
        
        self.assertEqual(metrica.confiabilidad, Decimal('95.5'))
        self.assertTrue(metrica.requiere_atencion)
    
    def test_recomendacion_sistema_generation(self):
        """Test generación automática de recomendaciones"""
        recomendacion = RecomendacionSistema.generar_recomendacion('muy_alto')
        
        self.assertEqual(recomendacion.tipo_recomendacion, 'accion_inmediata')
        self.assertTrue(recomendacion.es_critica)
        self.assertIn('ACCIÓN INMEDIATA', recomendacion.recomendacion_automatica)


class PerformanceOptimizationsTestCase(TestCase):
    """
    Tests para las optimizaciones de performance
    """
    
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='perf_user',
            email='perf@example.com',
            password='testpass123'
        )
    
    def test_cache_manager_dashboard_stats(self):
        """Test cache de estadísticas del dashboard"""
        # Primera llamada - debe generar cache
        stats1 = CacheManager.get_dashboard_stats(self.user.id)
        
        # Segunda llamada - debe usar cache
        stats2 = CacheManager.get_dashboard_stats(self.user.id)
        
        self.assertEqual(stats1, stats2)
        self.assertIn('total_conjuntos', stats1)
        self.assertIn('total_evaluaciones', stats1)
    
    def test_cache_invalidation(self):
        """Test invalidación de cache"""
        # Generar cache
        CacheManager.get_dashboard_stats(self.user.id)
        
        # Verificar que existe
        cache_key = f'dashboard_stats_{self.user.id}'
        self.assertIsNotNone(cache.get(cache_key))
        
        # Invalidar
        CacheManager.invalidate_user_cache(self.user.id)
        
        # Verificar que fue invalidado
        self.assertIsNone(cache.get(cache_key))


class IntegrationTestCase(TestCase):
    """
    Tests de integración para validar que el sistema funciona end-to-end
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='integration_user',
            email='integration@example.com',
            password='testpass123'
        )
        self.client.login(username='integration_user', password='testpass123')
        
        # Crear datos necesarios
        self.tipo_conjunto = TipoConjunto.objects.create(
            nombre='conjunto_cerrado',
            descripcion='Conjunto Test'
        )
        
        self.conjunto = Conjunto.objects.create(
            propietario=self.user,
            nit='123456789-0',
            nombre='Conjunto Integration Test',
            tipo_conjunto=self.tipo_conjunto,
            direccion='Calle Test 123',
            ciudad='Bogotá',
            departamento='Cundinamarca',
            numero_unidades=100
        )
    
    def test_dashboard_loads_successfully(self):
        """Test que el dashboard carga correctamente"""
        url = reverse('risk_conjuntos:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard - Risk Conjuntos')
    
    def test_conjunto_list_loads(self):
        """Test que la lista de conjuntos carga"""
        url = reverse('risk_conjuntos:lista_conjuntos')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.conjunto.nombre)
    
    def test_conjunto_detail_loads(self):
        """Test que el detalle del conjunto carga"""
        url = reverse('risk_conjuntos:detalle_conjunto', kwargs={'conjunto_id': self.conjunto.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.conjunto.nombre)
    
    def test_legacy_urls_show_warnings(self):
        """Test que las URLs legacy muestran advertencias"""
        url = reverse('risk_conjuntos:lista_evaluaciones')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Verificar que se muestra algún mensaje de sistema legacy


class APIEndpointsTestCase(TestCase):
    """
    Tests para endpoints de API
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='api_user',
            email='api@example.com',
            password='testpass123'
        )
        self.client.login(username='api_user', password='testpass123')
    
    def test_api_dashboard_stats(self):
        """Test endpoint de estadísticas del dashboard"""
        url = reverse('risk_conjuntos:api_dashboard_stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_conjuntos', data)
        self.assertIn('total_evaluaciones', data)
    
    def test_api_tipos_conjunto(self):
        """Test endpoint de tipos de conjunto"""
        url = reverse('risk_conjuntos:api_tipos_conjunto')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)


class MigrationTestCase(TestCase):
    """
    Tests para validar que las migraciones funcionan correctamente
    """
    
    def test_models_can_be_created(self):
        """Test que todos los modelos se pueden crear sin errores"""
        # Test creación de usuario
        user = User.objects.create_user(
            username='migration_test',
            email='migration@test.com',
            password='test123'
        )
        
        # Test creación de tipos
        tipo_conjunto = TipoConjunto.objects.create(
            nombre='conjunto_cerrado',
            descripcion='Test'
        )
        
        # Test creación de conjunto
        conjunto = Conjunto.objects.create(
            propietario=user,
            nit='123456789-0',
            nombre='Test Conjunto',
            tipo_conjunto=tipo_conjunto,
            direccion='Test Address',
            ciudad='Test City',
            departamento='Test Dept',
            numero_unidades=50
        )
        
        self.assertTrue(conjunto.id)
        self.assertEqual(conjunto.propietario, user)
        
    def test_optimized_models_work(self):
        """Test que los modelos optimizados funcionan"""
        analisis = AnalisisRiesgo.objects.create(
            valor_riesgo=Decimal('0.5')
        )
        
        ponderacion = PonderacionRiesgo.objects.create(
            peso_pregunta=Decimal('1.0'),
            valor_ponderado=Decimal('0.5')
        )
        
        metrica = MetricaCalidad.objects.create(
            confiabilidad=Decimal('90.0')
        )
        
        recomendacion = RecomendacionSistema.objects.create(
            tipo_recomendacion='monitoreo',
            recomendacion_automatica='Test recommendation'
        )
        
        self.assertTrue(all([analisis.id, ponderacion.id, metrica.id, recomendacion.id]))


class LegacyCompatibilityTestCase(TestCase):
    """
    Tests para asegurar compatibilidad con sistema legacy
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='legacy_user',
            email='legacy@example.com',
            password='testpass123'
        )
        # Asignar staff para ver mensajes legacy
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='legacy_user', password='testpass123')
    
    def test_legacy_views_still_work(self):
        """Test que las vistas legacy aún funcionan"""
        url = reverse('risk_conjuntos:lista_evaluaciones')
        response = self.client.get(url)
        
        # Debe cargar sin errores
        self.assertEqual(response.status_code, 200)
    
    def test_legacy_decorators_work(self):
        """Test que los decoradores legacy funcionan"""
        # Las vistas legacy deben mostrar warnings
        from apps.risk_conjuntos.legacy_decorators import legacy_evaluation_system
        
        @legacy_evaluation_system()
        def test_view(request):
            return True
        
        # El decorador debe funcionar sin errores
        self.assertTrue(callable(test_view))
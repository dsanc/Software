"""
Script de validación de integridad para el módulo risk_conjuntos
Verifica que todas las optimizaciones funcionen correctamente
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev_sqlite')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.risk_conjuntos.models import (
    Conjunto, TipoConjunto, EvaluacionRiesgo, 
    TipoRiesgo, EscenarioRiesgo, PreguntaEvaluacion
)
from apps.risk_conjuntos.models_optimized import (
    AnalisisRiesgo, PonderacionRiesgo, MetricaCalidad, RecomendacionSistema
)
from apps.risk_conjuntos.performance_optimizations import CacheManager
from decimal import Decimal

User = get_user_model()

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def validate_migrations():
    """Valida que todas las migraciones estén aplicadas"""
    print_info("Validando migraciones...")
    
    try:
        from django.db.migrations.recorder import MigrationRecorder
        recorder = MigrationRecorder.Migration.objects.filter(app='risk_conjuntos')
        migrations_count = recorder.count()
        
        if migrations_count >= 16:  # Esperamos al menos 16 migraciones
            print_success(f"Migraciones OK: {migrations_count} aplicadas")
            return True
        else:
            print_error(f"Migraciones incompletas: solo {migrations_count} aplicadas")
            return False
    except Exception as e:
        print_error(f"Error validando migraciones: {e}")
        return False

def validate_models():
    """Valida que todos los modelos funcionen correctamente"""
    print_info("Validando modelos...")
    
    try:
        # Test modelos principales
        user = User.objects.create_user(
            username='validation_user',
            email='validation@test.com',
            password='test123'
        )
        
        tipo_conjunto = TipoConjunto.objects.create(
            nombre='conjunto_cerrado',
            descripcion='Test conjunto'
        )
        
        conjunto = Conjunto.objects.create(
            propietario=user,
            nit='123456789-0',
            nombre='Conjunto Validación',
            tipo_conjunto=tipo_conjunto,
            direccion='Test Address',
            ciudad='Test City',
            departamento='Test Dept',
            numero_unidades=50
        )
        
        print_success("Modelos principales OK")
        
        # Test modelos optimizados
        analisis = AnalisisRiesgo.objects.create(
            valor_riesgo=Decimal('0.75')
        )
        
        ponderacion = PonderacionRiesgo.objects.create(
            peso_pregunta=Decimal('2.0'),
            valor_ponderado=Decimal('1.5')
        )
        
        metrica = MetricaCalidad.objects.create(
            confiabilidad=Decimal('95.0')
        )
        
        recomendacion = RecomendacionSistema.generar_recomendacion('alto')
        
        print_success("Modelos optimizados OK")
        
        # Cleanup
        user.delete()
        tipo_conjunto.delete()
        
        return True
        
    except Exception as e:
        print_error(f"Error validando modelos: {e}")
        return False

def validate_performance_optimizations():
    """Valida que las optimizaciones de performance funcionen"""
    print_info("Validando optimizaciones de performance...")
    
    try:
        # Test cache
        user = User.objects.create_user(
            username='perf_test_user',
            email='perf@test.com',
            password='test123'
        )
        
        # Test cache manager
        stats = CacheManager.get_dashboard_stats(user.id)
        if isinstance(stats, dict) and 'total_conjuntos' in stats:
            print_success("Cache manager OK")
        else:
            print_error("Cache manager falló")
            return False
        
        # Test invalidación de cache
        CacheManager.invalidate_user_cache(user.id)
        print_success("Invalidación de cache OK")
        
        # Cleanup
        user.delete()
        
        return True
        
    except Exception as e:
        print_error(f"Error validando performance: {e}")
        return False

def validate_legacy_compatibility():
    """Valida que la compatibilidad legacy funcione"""
    print_info("Validando compatibilidad legacy...")
    
    try:
        # Test importaciones legacy
        from apps.risk_conjuntos.models import EvaluacionSeguridad, CategoriaSeguridad
        from apps.risk_conjuntos.legacy_decorators import legacy_evaluation_system
        
        # Test decorador
        @legacy_evaluation_system("Test mensaje")
        def test_function():
            return True
        
        if test_function():
            print_success("Compatibilidad legacy OK")
            return True
        else:
            print_error("Compatibilidad legacy falló")
            return False
            
    except Exception as e:
        print_error(f"Error validando legacy: {e}")
        return False

def validate_admin_interface():
    """Valida que la interfaz de admin funcione"""
    print_info("Validando interfaz de admin...")
    
    try:
        from apps.risk_conjuntos import admin
        from django.contrib import admin as django_admin
        
        # Verificar que los modelos estén registrados
        registered_models = django_admin.site._registry.keys()
        risk_models = [model for model in registered_models 
                      if hasattr(model, '_meta') and 
                      model._meta.app_label == 'risk_conjuntos']
        
        if len(risk_models) >= 10:  # Esperamos varios modelos registrados
            print_success(f"Admin interface OK: {len(risk_models)} modelos registrados")
            return True
        else:
            print_error(f"Admin interface incompleto: solo {len(risk_models)} modelos")
            return False
            
    except Exception as e:
        print_error(f"Error validando admin: {e}")
        return False

def validate_data_integrity():
    """Valida la integridad de datos existentes"""
    print_info("Validando integridad de datos...")
    
    try:
        # Contar registros existentes
        conjuntos_count = Conjunto.objects.count()
        evaluaciones_count = EvaluacionRiesgo.objects.count()
        
        print_success(f"Datos existentes: {conjuntos_count} conjuntos, {evaluaciones_count} evaluaciones")
        
        # Verificar que no hay registros corruptos
        conjuntos_validos = Conjunto.objects.filter(
            propietario__isnull=False,
            nit__isnull=False,
            nombre__isnull=False
        ).count()
        
        if conjuntos_validos == conjuntos_count:
            print_success("Integridad de datos OK")
            return True
        else:
            print_error(f"Datos corruptos detectados: {conjuntos_count - conjuntos_validos} registros inválidos")
            return False
            
    except Exception as e:
        print_error(f"Error validando integridad: {e}")
        return False

def main():
    """Ejecuta todas las validaciones"""
    print("🔍 VALIDACIÓN DE INTEGRIDAD - MÓDULO RISK_CONJUNTOS")
    print("=" * 60)
    
    validations = [
        ("Migraciones", validate_migrations),
        ("Modelos", validate_models),
        ("Optimizaciones de Performance", validate_performance_optimizations),
        ("Compatibilidad Legacy", validate_legacy_compatibility),
        ("Interfaz de Admin", validate_admin_interface),
        ("Integridad de Datos", validate_data_integrity),
    ]
    
    results = []
    
    for name, validation_func in validations:
        print(f"\n📋 {name}")
        print("-" * 40)
        try:
            with transaction.atomic():
                result = validation_func()
                results.append((name, result))
                if result:
                    print_success(f"{name} completado")
                else:
                    print_error(f"{name} falló")
        except Exception as e:
            print_error(f"{name} error: {e}")
            results.append((name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    print("\n" + "=" * 60)
    if passed == total:
        print("🎉 ¡TODAS LAS VALIDACIONES PASARON!")
        print("✅ El módulo risk_conjuntos está listo para producción")
    else:
        print(f"⚠️  {total - passed} validaciones fallaron de {total}")
        print("❌ Revisar errores antes de continuar")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
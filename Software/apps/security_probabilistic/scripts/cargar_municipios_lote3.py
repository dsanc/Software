#!/usr/bin/env python3
"""
Script para cargar municipios de Colombia - LOTE 3
(Cesar, Chocó, Córdoba, Cundinamarca parte 1)
"""

import os
# import django

# Configurar Django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev_sqlite')
# django.setup()

from apps.security_probabilistic.models import Departamento, Municipio

def cargar_municipios_lote3():
    """Carga municipios del lote 3"""
    
    print("🇨🇴 Cargando municipios - LOTE 3...")
    
    # Obtener departamentos existentes
    departamentos = {dept.codigo_dane: dept for dept in Departamento.objects.all()}
    
    # Datos del lote 3
    municipios_data = {
        
        # CESAR (20) - 25 municipios
        '20': [
            {'codigo_dane': '20001', 'nombre': 'Valledupar', 'categoria': 'primera', 'poblacion': 491570},
            {'codigo_dane': '20011', 'nombre': 'Aguachica', 'categoria': 'cuarta'},
            {'codigo_dane': '20013', 'nombre': 'Agustín Codazzi', 'categoria': 'quinta'},
            {'codigo_dane': '20032', 'nombre': 'Astrea', 'categoria': 'sexta'},
            {'codigo_dane': '20045', 'nombre': 'Becerril', 'categoria': 'sexta'},
            {'codigo_dane': '20060', 'nombre': 'Bosconia', 'categoria': 'quinta'},
            {'codigo_dane': '20175', 'nombre': 'Chimichagua', 'categoria': 'sexta'},
            {'codigo_dane': '20178', 'nombre': 'Chiriguaná', 'categoria': 'sexta'},
            {'codigo_dane': '20228', 'nombre': 'Curumaní', 'categoria': 'sexta'},
            {'codigo_dane': '20238', 'nombre': 'El Copey', 'categoria': 'sexta'},
            {'codigo_dane': '20250', 'nombre': 'El Paso', 'categoria': 'sexta'},
            {'codigo_dane': '20295', 'nombre': 'Gamarra', 'categoria': 'sexta'},
            {'codigo_dane': '20310', 'nombre': 'González', 'categoria': 'sexta'},
            {'codigo_dane': '20383', 'nombre': 'La Gloria', 'categoria': 'sexta'},
            {'codigo_dane': '20400', 'nombre': 'La Jagua de Ibirico', 'categoria': 'sexta'},
            {'codigo_dane': '20443', 'nombre': 'Manaure Balcón del Cesar', 'categoria': 'sexta'},
            {'codigo_dane': '20517', 'nombre': 'Pailitas', 'categoria': 'sexta'},
            {'codigo_dane': '20550', 'nombre': 'Pelaya', 'categoria': 'sexta'},
            {'codigo_dane': '20570', 'nombre': 'Pueblo Bello', 'categoria': 'sexta'},
            {'codigo_dane': '20614', 'nombre': 'Río de Oro', 'categoria': 'sexta'},
            {'codigo_dane': '20621', 'nombre': 'La Paz', 'categoria': 'sexta'},
            {'codigo_dane': '20710', 'nombre': 'San Alberto', 'categoria': 'sexta'},
            {'codigo_dane': '20750', 'nombre': 'San Diego', 'categoria': 'sexta'},
            {'codigo_dane': '20770', 'nombre': 'San Martín', 'categoria': 'sexta'},
            {'codigo_dane': '20787', 'nombre': 'Tamalameque', 'categoria': 'sexta'},
        ],
        
        # CHOCÓ (27) - 30 municipios
        '27': [
            {'codigo_dane': '27001', 'nombre': 'Quibdó', 'categoria': 'segunda', 'poblacion': 129237},
            {'codigo_dane': '27006', 'nombre': 'Acandí', 'categoria': 'sexta'},
            {'codigo_dane': '27025', 'nombre': 'Alto Baudó', 'categoria': 'sexta'},
            {'codigo_dane': '27050', 'nombre': 'Atrato', 'categoria': 'sexta'},
            {'codigo_dane': '27073', 'nombre': 'Bagadó', 'categoria': 'sexta'},
            {'codigo_dane': '27075', 'nombre': 'Bahía Solano', 'categoria': 'sexta'},
            {'codigo_dane': '27077', 'nombre': 'Bajo Baudó', 'categoria': 'sexta'},
            {'codigo_dane': '27099', 'nombre': 'Bojayá', 'categoria': 'sexta'},
            {'codigo_dane': '27135', 'nombre': 'El Cantón del San Pablo', 'categoria': 'sexta'},
            {'codigo_dane': '27150', 'nombre': 'Carmen del Darién', 'categoria': 'sexta'},
            {'codigo_dane': '27160', 'nombre': 'Cértegui', 'categoria': 'sexta'},
            {'codigo_dane': '27205', 'nombre': 'Condoto', 'categoria': 'sexta'},
            {'codigo_dane': '27245', 'nombre': 'El Carmen de Atrato', 'categoria': 'sexta'},
            {'codigo_dane': '27250', 'nombre': 'El Litoral del San Juan', 'categoria': 'sexta'},
            {'codigo_dane': '27361', 'nombre': 'Istmina', 'categoria': 'sexta'},
            {'codigo_dane': '27372', 'nombre': 'Juradó', 'categoria': 'sexta'},
            {'codigo_dane': '27413', 'nombre': 'Lloró', 'categoria': 'sexta'},
            {'codigo_dane': '27425', 'nombre': 'Medio Atrato', 'categoria': 'sexta'},
            {'codigo_dane': '27430', 'nombre': 'Medio Baudó', 'categoria': 'sexta'},
            {'codigo_dane': '27450', 'nombre': 'Medio San Juan', 'categoria': 'sexta'},
            {'codigo_dane': '27491', 'nombre': 'Nóvita', 'categoria': 'sexta'},
            {'codigo_dane': '27495', 'nombre': 'Nuquí', 'categoria': 'sexta'},
            {'codigo_dane': '27580', 'nombre': 'Río Iró', 'categoria': 'sexta'},
            {'codigo_dane': '27600', 'nombre': 'Río Quito', 'categoria': 'sexta'},
            {'codigo_dane': '27615', 'nombre': 'Riosucio', 'categoria': 'sexta'},
            {'codigo_dane': '27660', 'nombre': 'San José del Palmar', 'categoria': 'sexta'},
            {'codigo_dane': '27745', 'nombre': 'Sipí', 'categoria': 'sexta'},
            {'codigo_dane': '27787', 'nombre': 'Tadó', 'categoria': 'sexta'},
            {'codigo_dane': '27800', 'nombre': 'Unguía', 'categoria': 'sexta'},
            {'codigo_dane': '27810', 'nombre': 'Unión Panamericana', 'categoria': 'sexta'},
        ],
        
        # CÓRDOBA (23) - 30 municipios
        '23': [
            {'codigo_dane': '23001', 'nombre': 'Montería', 'categoria': 'primera', 'poblacion': 506823},
            {'codigo_dane': '23068', 'nombre': 'Ayapel', 'categoria': 'sexta'},
            {'codigo_dane': '23079', 'nombre': 'Buenavista', 'categoria': 'sexta'},
            {'codigo_dane': '23090', 'nombre': 'Canalete', 'categoria': 'sexta'},
            {'codigo_dane': '23162', 'nombre': 'Cereté', 'categoria': 'quinta'},
            {'codigo_dane': '23168', 'nombre': 'Chimá', 'categoria': 'sexta'},
            {'codigo_dane': '23182', 'nombre': 'Chinú', 'codigo_dane': '23182', 'categoria': 'sexta'},
            {'codigo_dane': '23189', 'nombre': 'Ciénaga de Oro', 'categoria': 'quinta'},
            {'codigo_dane': '23300', 'nombre': 'Cotorra', 'categoria': 'sexta'},
            {'codigo_dane': '23350', 'nombre': 'La Apartada', 'categoria': 'sexta'},
            {'codigo_dane': '23417', 'nombre': 'Lorica', 'categoria': 'cuarta'},
            {'codigo_dane': '23419', 'nombre': 'Los Córdobas', 'categoria': 'sexta'},
            {'codigo_dane': '23464', 'nombre': 'Momil', 'categoria': 'sexta'},
            {'codigo_dane': '23466', 'nombre': 'Montelíbano', 'categoria': 'quinta'},
            {'codigo_dane': '23500', 'nombre': 'Moñitos', 'categoria': 'sexta'},
            {'codigo_dane': '23555', 'nombre': 'Planeta Rica', 'categoria': 'quinta'},
            {'codigo_dane': '23570', 'nombre': 'Pueblo Nuevo', 'categoria': 'sexta'},
            {'codigo_dane': '23574', 'nombre': 'Puerto Escondido', 'categoria': 'sexta'},
            {'codigo_dane': '23580', 'nombre': 'Puerto Libertador', 'categoria': 'sexta'},
            {'codigo_dane': '23586', 'nombre': 'Purísima', 'categoria': 'sexta'},
            {'codigo_dane': '23660', 'nombre': 'Sahagún', 'categoria': 'quinta'},
            {'codigo_dane': '23670', 'nombre': 'San Andrés de Sotavento', 'categoria': 'sexta'},
            {'codigo_dane': '23672', 'nombre': 'San Antero', 'categoria': 'sexta'},
            {'codigo_dane': '23675', 'nombre': 'San Bernardo del Viento', 'categoria': 'sexta'},
            {'codigo_dane': '23678', 'nombre': 'San Carlos', 'categoria': 'sexta'},
            {'codigo_dane': '23682', 'nombre': 'San José de Uré', 'categoria': 'sexta'},
            {'codigo_dane': '23686', 'nombre': 'San Pelayo', 'categoria': 'quinta'},
            {'codigo_dane': '23807', 'nombre': 'Tierralta', 'categoria': 'quinta'},
            {'codigo_dane': '23815', 'nombre': 'Tuchín', 'categoria': 'sexta'},
            {'codigo_dane': '23855', 'nombre': 'Valencia', 'categoria': 'sexta'},
        ],
        
        # CUNDINAMARCA (25) - Parte 1: 58 municipios (de 116)
        '25': [
            {'codigo_dane': '25001', 'nombre': 'Agua de Dios', 'categoria': 'sexta'},
            {'codigo_dane': '25019', 'nombre': 'Albán', 'categoria': 'sexta'},
            {'codigo_dane': '25035', 'nombre': 'Anapoima', 'categoria': 'sexta'},
            {'codigo_dane': '25040', 'nombre': 'Anolaima', 'categoria': 'sexta'},
            {'codigo_dane': '25053', 'nombre': 'Arbeláez', 'categoria': 'sexta'},
            {'codigo_dane': '25086', 'nombre': 'Beltrán', 'categoria': 'sexta'},
            {'codigo_dane': '25095', 'nombre': 'Bituima', 'categoria': 'sexta'},
            {'codigo_dane': '25099', 'nombre': 'Bojacá', 'categoria': 'sexta'},
            {'codigo_dane': '25120', 'nombre': 'Cabrera', 'categoria': 'sexta'},
            {'codigo_dane': '25123', 'nombre': 'Cachipay', 'categoria': 'sexta'},
            {'codigo_dane': '25126', 'nombre': 'Cajicá', 'categoria': 'cuarta'},
            {'codigo_dane': '25148', 'nombre': 'Caparrapí', 'categoria': 'sexta'},
            {'codigo_dane': '25151', 'nombre': 'Cáqueza', 'categoria': 'sexta'},
            {'codigo_dane': '25154', 'nombre': 'Carmen de Carupa', 'categoria': 'sexta'},
            {'codigo_dane': '25168', 'nombre': 'Chaguaní', 'categoria': 'sexta'},
            {'codigo_dane': '25175', 'nombre': 'Chía', 'categoria': 'primera', 'poblacion': 140406},
            {'codigo_dane': '25178', 'nombre': 'Chipaque', 'categoria': 'sexta'},
            {'codigo_dane': '25181', 'nombre': 'Choachí', 'categoria': 'sexta'},
            {'codigo_dane': '25183', 'nombre': 'Chocontá', 'categoria': 'sexta'},
            {'codigo_dane': '25200', 'nombre': 'Cogua', 'categoria': 'sexta'},
            {'codigo_dane': '25214', 'nombre': 'Cota', 'categoria': 'cuarta'},
            {'codigo_dane': '25224', 'nombre': 'Cucunubá', 'categoria': 'sexta'},
            {'codigo_dane': '25245', 'nombre': 'El Colegio', 'categoria': 'sexta'},
            {'codigo_dane': '25253', 'nombre': 'El Peñón', 'categoria': 'sexta'},
            {'codigo_dane': '25258', 'nombre': 'El Rosal', 'categoria': 'sexta'},
            {'codigo_dane': '25260', 'nombre': 'Facatativá', 'categoria': 'segunda'},
            {'codigo_dane': '25269', 'nombre': 'Fómeque', 'categoria': 'sexta'},
            {'codigo_dane': '25279', 'nombre': 'Fosca', 'categoria': 'sexta'},
            {'codigo_dane': '25281', 'nombre': 'Funza', 'categoria': 'cuarta'},
            {'codigo_dane': '25286', 'nombre': 'Fúquene', 'categoria': 'sexta'},
            {'codigo_dane': '25288', 'nombre': 'Fusagasugá', 'categoria': 'segunda'},
            {'codigo_dane': '25290', 'nombre': 'Gachalá', 'categoria': 'sexta'},
            {'codigo_dane': '25293', 'nombre': 'Gachancipá', 'categoria': 'sexta'},
            {'codigo_dane': '25295', 'nombre': 'Gachetá', 'categoria': 'sexta'},
            {'codigo_dane': '25297', 'nombre': 'Gama', 'categoria': 'sexta'},
            {'codigo_dane': '25299', 'nombre': 'Girardot', 'categoria': 'tercera'},
            {'codigo_dane': '25307', 'nombre': 'Granada', 'categoria': 'sexta'},
            {'codigo_dane': '25312', 'nombre': 'Guachetá', 'categoria': 'sexta'},
            {'codigo_dane': '25317', 'nombre': 'Guaduas', 'categoria': 'sexta'},
            {'codigo_dane': '25320', 'nombre': 'Guasca', 'categoria': 'sexta'},
            {'codigo_dane': '25322', 'nombre': 'Guataquí', 'categoria': 'sexta'},
            {'codigo_dane': '25324', 'nombre': 'Guatavita', 'categoria': 'sexta'},
            {'codigo_dane': '25326', 'nombre': 'Guayabal de Síquima', 'categoria': 'sexta'},
            {'codigo_dane': '25328', 'nombre': 'Guayabetal', 'categoria': 'sexta'},
            {'codigo_dane': '25335', 'nombre': 'Gutiérrez', 'categoria': 'sexta'},
            {'codigo_dane': '25339', 'nombre': 'Jerusalén', 'categoria': 'sexta'},
            {'codigo_dane': '25368', 'nombre': 'Junín', 'categoria': 'sexta'},
            {'codigo_dane': '25372', 'nombre': 'La Calera', 'categoria': 'quinta'},
            {'codigo_dane': '25377', 'nombre': 'La Mesa', 'categoria': 'quinta'},
            {'codigo_dane': '25386', 'nombre': 'La Palma', 'categoria': 'sexta'},
            {'codigo_dane': '25394', 'nombre': 'La Peña', 'categoria': 'sexta'},
            {'codigo_dane': '25398', 'nombre': 'La Vega', 'categoria': 'sexta'},
            {'codigo_dane': '25402', 'nombre': 'Lenguazaque', 'categoria': 'sexta'},
            {'codigo_dane': '25407', 'nombre': 'Macheta', 'categoria': 'sexta'},
            {'codigo_dane': '25426', 'nombre': 'Madrid', 'categoria': 'cuarta'},
            {'codigo_dane': '25430', 'nombre': 'Manta', 'categoria': 'sexta'},
            {'codigo_dane': '25436', 'nombre': 'Medina', 'categoria': 'sexta'},
            {'codigo_dane': '25438', 'nombre': 'Mosquera', 'categoria': 'segunda'},
        ],
    }
    
    # Procesar lote 3
    total_municipios_creados = 0
    total_municipios_existentes = 0
    
    for dept_codigo, municipios in municipios_data.items():
        if dept_codigo not in departamentos:
            print(f"  ⚠️ Departamento {dept_codigo} no encontrado")
            continue
            
        departamento = departamentos[dept_codigo]
        print(f"\n📍 {departamento.nombre} ({len(municipios)} municipios):")
        
        municipios_creados_dept = 0
        
        for mun_data in municipios:
            try:
                mun, created = Municipio.objects.get_or_create(
                    codigo_dane=mun_data['codigo_dane'],
                    defaults={
                        'departamento': departamento,
                        'nombre': mun_data['nombre'],
                        'categoria': mun_data.get('categoria', 'sexta'),
                        'poblacion': mun_data.get('poblacion', None),
                        'usa_riesgo_departamento': True,
                        'activo': True
                    }
                )
                
                if created:
                    municipios_creados_dept += 1
                    total_municipios_creados += 1
                    status = "✅"
                else:
                    total_municipios_existentes += 1
                    status = "ℹ️"
                
                poblacion_info = f" ({mun.poblacion:,} hab)" if mun.poblacion else ""
                print(f"    {status} {mun.nombre}{poblacion_info}")
                
            except Exception as e:
                print(f"    ❌ Error con {mun_data['nombre']}: {e}")
        
        print(f"    📊 Creados: {municipios_creados_dept}/{len(municipios)}")
    
    print(f"\n📊 RESUMEN LOTE 3:")
    print(f"  - Municipios procesados: {len([m for dept_muns in municipios_data.values() for m in dept_muns])}")
    print(f"  - Municipios creados: {total_municipios_creados}")
    print(f"  - Municipios existentes: {total_municipios_existentes}")
    print(f"  - Total en base de datos: {Municipio.objects.count()}")
    
    return total_municipios_creados

if __name__ == "__main__":
    cargar_municipios_lote3()
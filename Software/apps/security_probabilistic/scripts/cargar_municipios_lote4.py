#!/usr/bin/env python3
"""
Script para cargar municipios de Colombia - LOTE 4
(Cundinamarca parte 2, Guainía, Guaviare, Huila)
"""

import os
# import django

# Configurar Django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev_sqlite')
# django.setup()

from apps.security_probabilistic.models import Departamento, Municipio

def cargar_municipios_lote4():
    """Carga municipios del lote 4"""
    
    print("🇨🇴 Cargando municipios - LOTE 4...")
    
    # Obtener departamentos existentes
    departamentos = {dept.codigo_dane: dept for dept in Departamento.objects.all()}
    
    # Datos del lote 4
    municipios_data = {
        
        # CUNDINAMARCA (25) - Parte 2: restantes 58 municipios
        '25': [
            {'codigo_dane': '25473', 'nombre': 'Nariño', 'categoria': 'sexta'},
            {'codigo_dane': '25483', 'nombre': 'Nemocón', 'categoria': 'sexta'},
            {'codigo_dane': '25486', 'nombre': 'Nilo', 'categoria': 'sexta'},
            {'codigo_dane': '25488', 'nombre': 'Nimaima', 'categoria': 'sexta'},
            {'codigo_dane': '25489', 'nombre': 'Nocaima', 'categoria': 'sexta'},
            {'codigo_dane': '25491', 'nombre': 'Venecia', 'categoria': 'sexta'},
            {'codigo_dane': '25506', 'nombre': 'Pacho', 'categoria': 'quinta'},
            {'codigo_dane': '25513', 'nombre': 'Paime', 'categoria': 'sexta'},
            {'codigo_dane': '25518', 'nombre': 'Pandi', 'categoria': 'sexta'},
            {'codigo_dane': '25524', 'nombre': 'Paratebueno', 'categoria': 'sexta'},
            {'codigo_dane': '25530', 'nombre': 'Pasca', 'categoria': 'sexta'},
            {'codigo_dane': '25535', 'nombre': 'Puerto Salgar', 'categoria': 'sexta'},
            {'codigo_dane': '25572', 'nombre': 'Pulí', 'categoria': 'sexta'},
            {'codigo_dane': '25580', 'nombre': 'Quebradanegra', 'categoria': 'sexta'},
            {'codigo_dane': '25592', 'nombre': 'Quetame', 'categoria': 'sexta'},
            {'codigo_dane': '25594', 'nombre': 'Quipile', 'categoria': 'sexta'},
            {'codigo_dane': '25596', 'nombre': 'Apulo', 'categoria': 'sexta'},
            {'codigo_dane': '25599', 'nombre': 'Ricaurte', 'categoria': 'sexta'},
            {'codigo_dane': '25612', 'nombre': 'San Antonio del Tequendama', 'categoria': 'sexta'},
            {'codigo_dane': '25645', 'nombre': 'San Bernardo', 'categoria': 'sexta'},
            {'codigo_dane': '25649', 'nombre': 'San Cayetano', 'categoria': 'sexta'},
            {'codigo_dane': '25653', 'nombre': 'San Francisco', 'categoria': 'sexta'},
            {'codigo_dane': '25658', 'nombre': 'San Juan de Rioseco', 'categoria': 'sexta'},
            {'codigo_dane': '25662', 'nombre': 'Sasaima', 'categoria': 'sexta'},
            {'codigo_dane': '25718', 'nombre': 'Sesquilé', 'categoria': 'sexta'},
            {'codigo_dane': '25736', 'nombre': 'Sibaté', 'categoria': 'quinta'},
            {'codigo_dane': '25740', 'nombre': 'Silvania', 'categoria': 'sexta'},
            {'codigo_dane': '25743', 'nombre': 'Simijaca', 'categoria': 'sexta'},
            {'codigo_dane': '25745', 'nombre': 'Soacha', 'categoria': 'primera', 'poblacion': 523846},
            {'codigo_dane': '25754', 'nombre': 'Sopó', 'categoria': 'quinta'},
            {'codigo_dane': '25758', 'nombre': 'Subachoque', 'categoria': 'sexta'},
            {'codigo_dane': '25769', 'nombre': 'Suesca', 'categoria': 'sexta'},
            {'codigo_dane': '25772', 'nombre': 'Supatá', 'categoria': 'sexta'},
            {'codigo_dane': '25777', 'nombre': 'Susa', 'categoria': 'sexta'},
            {'codigo_dane': '25779', 'nombre': 'Sutatausa', 'categoria': 'sexta'},
            {'codigo_dane': '25781', 'nombre': 'Tabio', 'categoria': 'quinta'},
            {'codigo_dane': '25785', 'nombre': 'Tausa', 'categoria': 'sexta'},
            {'codigo_dane': '25793', 'nombre': 'Tena', 'categoria': 'sexta'},
            {'codigo_dane': '25797', 'nombre': 'Tenjo', 'categoria': 'quinta'},
            {'codigo_dane': '25799', 'nombre': 'Tibacuy', 'categoria': 'sexta'},
            {'codigo_dane': '25805', 'nombre': 'Tibirita', 'categoria': 'sexta'},
            {'codigo_dane': '25807', 'nombre': 'Tocaima', 'categoria': 'sexta'},
            {'codigo_dane': '25815', 'nombre': 'Tocancipá', 'categoria': 'quinta'},
            {'codigo_dane': '25817', 'nombre': 'Topaipí', 'categoria': 'sexta'},
            {'codigo_dane': '25823', 'nombre': 'Ubalá', 'categoria': 'sexta'},
            {'codigo_dane': '25839', 'nombre': 'Ubaque', 'categoria': 'sexta'},
            {'codigo_dane': '25841', 'nombre': 'Villa de San Diego de Ubaté', 'categoria': 'quinta'},
            {'codigo_dane': '25843', 'nombre': 'Une', 'categoria': 'sexta'},
            {'codigo_dane': '25845', 'nombre': 'Útica', 'categoria': 'sexta'},
            {'codigo_dane': '25851', 'nombre': 'Vergara', 'categoria': 'sexta'},
            {'codigo_dane': '25862', 'nombre': 'Vianí', 'categoria': 'sexta'},
            {'codigo_dane': '25867', 'nombre': 'Villagómez', 'categoria': 'sexta'},
            {'codigo_dane': '25871', 'nombre': 'Villapinzón', 'categoria': 'sexta'},
            {'codigo_dane': '25873', 'nombre': 'Villeta', 'categoria': 'quinta'},
            {'codigo_dane': '25875', 'nombre': 'Viotá', 'categoria': 'sexta'},
            {'codigo_dane': '25878', 'nombre': 'Yacopí', 'categoria': 'sexta'},
            {'codigo_dane': '25885', 'nombre': 'Zipacón', 'categoria': 'sexta'},
            {'codigo_dane': '25898', 'nombre': 'Zipaquirá', 'categoria': 'segunda'},
        ],
        
        # GUAINÍA (94) - 9 municipios
        '94': [
            {'codigo_dane': '94001', 'nombre': 'Inírida', 'categoria': 'quinta', 'poblacion': 21447},
            {'codigo_dane': '94343', 'nombre': 'Barranco Minas', 'categoria': 'sexta'},
            {'codigo_dane': '94663', 'nombre': 'Mapiripana', 'categoria': 'sexta'},
            {'codigo_dane': '94883', 'nombre': 'San Felipe', 'categoria': 'sexta'},
            {'codigo_dane': '94884', 'nombre': 'Puerto Colombia', 'categoria': 'sexta'},
            {'codigo_dane': '94885', 'nombre': 'La Guadalupe', 'categoria': 'sexta'},
            {'codigo_dane': '94886', 'nombre': 'Cacahual', 'categoria': 'sexta'},
            {'codigo_dane': '94887', 'nombre': 'Pana Pana', 'categoria': 'sexta'},
            {'codigo_dane': '94888', 'nombre': 'Morichal', 'categoria': 'sexta'},
        ],
        
        # GUAVIARE (95) - 4 municipios
        '95': [
            {'codigo_dane': '95001', 'nombre': 'San José del Guaviare', 'categoria': 'quinta', 'poblacion': 57859},
            {'codigo_dane': '95015', 'nombre': 'Calamar', 'categoria': 'sexta'},
            {'codigo_dane': '95025', 'nombre': 'El Retorno', 'categoria': 'sexta'},
            {'codigo_dane': '95200', 'nombre': 'Miraflores', 'categoria': 'sexta'},
        ],
        
        # HUILA (41) - 37 municipios
        '41': [
            {'codigo_dane': '41001', 'nombre': 'Neiva', 'categoria': 'primera', 'poblacion': 357392},
            {'codigo_dane': '41006', 'nombre': 'Acevedo', 'categoria': 'sexta'},
            {'codigo_dane': '41013', 'nombre': 'Agrado', 'categoria': 'sexta'},
            {'codigo_dane': '41016', 'nombre': 'Aipe', 'categoria': 'sexta'},
            {'codigo_dane': '41020', 'nombre': 'Algeciras', 'categoria': 'sexta'},
            {'codigo_dane': '41026', 'nombre': 'Altamira', 'categoria': 'sexta'},
            {'codigo_dane': '41078', 'nombre': 'Baraya', 'categoria': 'sexta'},
            {'codigo_dane': '41132', 'nombre': 'Campoalegre', 'categoria': 'quinta'},
            {'codigo_dane': '41206', 'nombre': 'Colombia', 'categoria': 'sexta'},
            {'codigo_dane': '41244', 'nombre': 'Elías', 'categoria': 'sexta'},
            {'codigo_dane': '41298', 'nombre': 'Garzón', 'categoria': 'quinta'},
            {'codigo_dane': '41306', 'nombre': 'Gigante', 'categoria': 'sexta'},
            {'codigo_dane': '41319', 'nombre': 'Guadalupe', 'categoria': 'sexta'},
            {'codigo_dane': '41349', 'nombre': 'Hobo', 'categoria': 'sexta'},
            {'codigo_dane': '41357', 'nombre': 'Íquira', 'categoria': 'sexta'},
            {'codigo_dane': '41359', 'nombre': 'Isnos', 'categoria': 'sexta'},
            {'codigo_dane': '41378', 'nombre': 'La Argentina', 'categoria': 'sexta'},
            {'codigo_dane': '41396', 'nombre': 'La Plata', 'categoria': 'quinta'},
            {'codigo_dane': '41483', 'nombre': 'Nátaga', 'categoria': 'sexta'},
            {'codigo_dane': '41503', 'nombre': 'Oporapa', 'categoria': 'sexta'},
            {'codigo_dane': '41518', 'nombre': 'Paicol', 'categoria': 'sexta'},
            {'codigo_dane': '41524', 'nombre': 'Palermo', 'categoria': 'sexta'},
            {'codigo_dane': '41530', 'nombre': 'Palestina', 'categoria': 'sexta'},
            {'codigo_dane': '41548', 'nombre': 'Pital', 'categoria': 'quinta'},
            {'codigo_dane': '41551', 'nombre': 'Pitalito', 'categoria': 'segunda'},
            {'codigo_dane': '41615', 'nombre': 'Rivera', 'categoria': 'quinta'},
            {'codigo_dane': '41660', 'nombre': 'Saladoblanco', 'categoria': 'sexta'},
            {'codigo_dane': '41668', 'nombre': 'San Agustín', 'categoria': 'sexta'},
            {'codigo_dane': '41676', 'nombre': 'Santa María', 'categoria': 'sexta'},
            {'codigo_dane': '41770', 'nombre': 'Suaza', 'categoria': 'sexta'},
            {'codigo_dane': '41791', 'nombre': 'Tarqui', 'categoria': 'sexta'},
            {'codigo_dane': '41797', 'nombre': 'Tesalia', 'categoria': 'sexta'},
            {'codigo_dane': '41799', 'nombre': 'Tello', 'categoria': 'sexta'},
            {'codigo_dane': '41801', 'nombre': 'Teruel', 'categoria': 'sexta'},
            {'codigo_dane': '41807', 'nombre': 'Timaná', 'categoria': 'sexta'},
            {'codigo_dane': '41872', 'nombre': 'Villavieja', 'categoria': 'sexta'},
            {'codigo_dane': '41885', 'nombre': 'Yaguará', 'categoria': 'sexta'},
        ],
    }
    
    # Procesar lote 4
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
    
    print(f"\n📊 RESUMEN LOTE 4:")
    print(f"  - Municipios procesados: {len([m for dept_muns in municipios_data.values() for m in dept_muns])}")
    print(f"  - Municipios creados: {total_municipios_creados}")
    print(f"  - Municipios existentes: {total_municipios_existentes}")
    print(f"  - Total en base de datos: {Municipio.objects.count()}")
    
    return total_municipios_creados

if __name__ == "__main__":
    cargar_municipios_lote4()
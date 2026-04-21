#!/usr/bin/env python3
"""
Script para cargar municipios de Colombia - LOTE 5
(La Guajira, Magdalena, Meta, Nariño)
"""

import os
# import django

# Configurar Django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev_sqlite')
# django.setup()

from apps.security_probabilistic.models import Departamento, Municipio

def cargar_municipios_lote5():
    """Carga municipios del lote 5"""
    
    print("🇨🇴 Cargando municipios - LOTE 5...")
    
    # Obtener departamentos existentes
    departamentos = {dept.codigo_dane: dept for dept in Departamento.objects.all()}
    
    # Datos del lote 5
    municipios_data = {
        
        # LA GUAJIRA (44) - 15 municipios
        '44': [
            {'codigo_dane': '44001', 'nombre': 'Riohacha', 'categoria': 'segunda', 'poblacion': 278746},
            {'codigo_dane': '44035', 'nombre': 'Albania', 'categoria': 'sexta'},
            {'codigo_dane': '44078', 'nombre': 'Barrancas', 'categoria': 'sexta'},
            {'codigo_dane': '44090', 'nombre': 'Dibulla', 'categoria': 'sexta'},
            {'codigo_dane': '44098', 'nombre': 'Distracción', 'categoria': 'sexta'},
            {'codigo_dane': '44110', 'nombre': 'El Molino', 'categoria': 'sexta'},
            {'codigo_dane': '44279', 'nombre': 'Fonseca', 'categoria': 'quinta'},
            {'codigo_dane': '44378', 'nombre': 'Hatonuevo', 'categoria': 'sexta'},
            {'codigo_dane': '44420', 'nombre': 'La Jagua del Pilar', 'categoria': 'sexta'},
            {'codigo_dane': '44430', 'nombre': 'Maicao', 'categoria': 'cuarta'},
            {'codigo_dane': '44560', 'nombre': 'Manaure', 'categoria': 'sexta'},
            {'codigo_dane': '44650', 'nombre': 'San Juan del Cesar', 'categoria': 'sexta'},
            {'codigo_dane': '44847', 'nombre': 'Uribia', 'categoria': 'sexta'},
            {'codigo_dane': '44855', 'nombre': 'Urumita', 'categoria': 'sexta'},
            {'codigo_dane': '44874', 'nombre': 'Villanueva', 'categoria': 'sexta'},
        ],
        
        # MAGDALENA (47) - 30 municipios
        '47': [
            {'codigo_dane': '47001', 'nombre': 'Santa Marta', 'categoria': 'primera', 'poblacion': 515462},
            {'codigo_dane': '47030', 'nombre': 'Algarrobo', 'categoria': 'sexta'},
            {'codigo_dane': '47053', 'nombre': 'Aracataca', 'categoria': 'sexta'},
            {'codigo_dane': '47058', 'nombre': 'Ariguaní', 'categoria': 'sexta'},
            {'codigo_dane': '47161', 'nombre': 'Cerro San Antonio', 'categoria': 'sexta'},
            {'codigo_dane': '47170', 'nombre': 'Chibolo', 'categoria': 'sexta'},
            {'codigo_dane': '47189', 'nombre': 'Ciénaga', 'categoria': 'cuarta'},
            {'codigo_dane': '47205', 'nombre': 'Concordia', 'categoria': 'sexta'},
            {'codigo_dane': '47245', 'nombre': 'El Banco', 'categoria': 'quinta'},
            {'codigo_dane': '47258', 'nombre': 'El Piñón', 'categoria': 'sexta'},
            {'codigo_dane': '47268', 'nombre': 'El Retén', 'categoria': 'sexta'},
            {'codigo_dane': '47288', 'nombre': 'Fundación', 'categoria': 'quinta'},
            {'codigo_dane': '47318', 'nombre': 'Guamal', 'categoria': 'sexta'},
            {'codigo_dane': '47460', 'nombre': 'Nueva Granada', 'categoria': 'sexta'},
            {'codigo_dane': '47541', 'nombre': 'Pedraza', 'categoria': 'sexta'},
            {'codigo_dane': '47545', 'nombre': 'Pijiño del Carmen', 'categoria': 'sexta'},
            {'codigo_dane': '47551', 'nombre': 'Pivijay', 'categoria': 'quinta'},
            {'codigo_dane': '47555', 'nombre': 'Plato', 'categoria': 'quinta'},
            {'codigo_dane': '47570', 'nombre': 'Puebloviejo', 'categoria': 'sexta'},
            {'codigo_dane': '47605', 'nombre': 'Remolino', 'categoria': 'sexta'},
            {'codigo_dane': '47660', 'nombre': 'Sabanas de San Ángel', 'categoria': 'sexta'},
            {'codigo_dane': '47675', 'nombre': 'Salamina', 'categoria': 'sexta'},
            {'codigo_dane': '47692', 'nombre': 'San Sebastián de Buenavista', 'categoria': 'sexta'},
            {'codigo_dane': '47703', 'nombre': 'San Zenón', 'categoria': 'sexta'},
            {'codigo_dane': '47707', 'nombre': 'Santa Ana', 'categoria': 'sexta'},
            {'codigo_dane': '47720', 'nombre': 'Santa Bárbara de Pinto', 'categoria': 'sexta'},
            {'codigo_dane': '47745', 'nombre': 'Sitionuevo', 'categoria': 'sexta'},
            {'codigo_dane': '47798', 'nombre': 'Tenerife', 'categoria': 'sexta'},
            {'codigo_dane': '47960', 'nombre': 'Zapayán', 'categoria': 'sexta'},
            {'codigo_dane': '47980', 'nombre': 'Zona Bananera', 'categoria': 'quinta'},
        ],
        
        # META (50) - 29 municipios
        '50': [
            {'codigo_dane': '50001', 'nombre': 'Villavicencio', 'categoria': 'primera', 'poblacion': 531275},
            {'codigo_dane': '50006', 'nombre': 'Acacías', 'categoria': 'cuarta'},
            {'codigo_dane': '50110', 'nombre': 'Barranca de Upía', 'categoria': 'sexta'},
            {'codigo_dane': '50124', 'nombre': 'Cabuyaro', 'categoria': 'sexta'},
            {'codigo_dane': '50150', 'nombre': 'Castilla la Nueva', 'categoria': 'sexta'},
            {'codigo_dane': '50223', 'nombre': 'Cubarral', 'categoria': 'sexta'},
            {'codigo_dane': '50226', 'nombre': 'Cumaral', 'categoria': 'quinta'},
            {'codigo_dane': '50245', 'nombre': 'El Calvario', 'categoria': 'sexta'},
            {'codigo_dane': '50251', 'nombre': 'El Castillo', 'categoria': 'sexta'},
            {'codigo_dane': '50270', 'nombre': 'El Dorado', 'categoria': 'sexta'},
            {'codigo_dane': '50287', 'nombre': 'Fuente de Oro', 'categoria': 'sexta'},
            {'codigo_dane': '50313', 'nombre': 'Granada', 'categoria': 'quinta'},
            {'codigo_dane': '50318', 'nombre': 'Guamal', 'categoria': 'sexta'},
            {'codigo_dane': '50325', 'nombre': 'Mapiripán', 'categoria': 'sexta'},
            {'codigo_dane': '50330', 'nombre': 'Mesetas', 'categoria': 'sexta'},
            {'codigo_dane': '50350', 'nombre': 'La Macarena', 'categoria': 'sexta'},
            {'codigo_dane': '50370', 'nombre': 'Uribe', 'categoria': 'sexta'},
            {'codigo_dane': '50400', 'nombre': 'Lejanías', 'categoria': 'sexta'},
            {'codigo_dane': '50450', 'nombre': 'Puerto Concordia', 'categoria': 'sexta'},
            {'codigo_dane': '50568', 'nombre': 'Puerto Gaitán', 'categoria': 'quinta'},
            {'codigo_dane': '50573', 'nombre': 'Puerto López', 'categoria': 'quinta'},
            {'codigo_dane': '50577', 'nombre': 'Puerto Lleras', 'categoria': 'sexta'},
            {'codigo_dane': '50590', 'nombre': 'Puerto Rico', 'categoria': 'sexta'},
            {'codigo_dane': '50606', 'nombre': 'Restrepo', 'categoria': 'quinta'},
            {'codigo_dane': '50680', 'nombre': 'San Carlos de Guaroa', 'categoria': 'sexta'},
            {'codigo_dane': '50683', 'nombre': 'San Juan de Arama', 'categoria': 'sexta'},
            {'codigo_dane': '50686', 'nombre': 'San Juanito', 'categoria': 'sexta'},
            {'codigo_dane': '50689', 'nombre': 'San Martín', 'categoria': 'quinta'},
            {'codigo_dane': '50711', 'nombre': 'Vistahermosa', 'categoria': 'sexta'},
        ],
        
        # NARIÑO (52) - 64 municipios
        '52': [
            {'codigo_dane': '52001', 'nombre': 'Pasto', 'categoria': 'primera', 'poblacion': 392589},
            {'codigo_dane': '52019', 'nombre': 'Albán', 'categoria': 'sexta'},
            {'codigo_dane': '52022', 'nombre': 'Aldana', 'categoria': 'sexta'},
            {'codigo_dane': '52036', 'nombre': 'Ancuyá', 'categoria': 'sexta'},
            {'codigo_dane': '52051', 'nombre': 'Arboleda', 'categoria': 'sexta'},
            {'codigo_dane': '52079', 'nombre': 'Barbacoas', 'categoria': 'sexta'},
            {'codigo_dane': '52083', 'nombre': 'Belén', 'categoria': 'sexta'},
            {'codigo_dane': '52110', 'nombre': 'Buesaco', 'categoria': 'sexta'},
            {'codigo_dane': '52203', 'nombre': 'Colón', 'categoria': 'sexta'},
            {'codigo_dane': '52207', 'nombre': 'Consacá', 'categoria': 'sexta'},
            {'codigo_dane': '52210', 'nombre': 'Contadero', 'categoria': 'sexta'},
            {'codigo_dane': '52215', 'nombre': 'Córdoba', 'categoria': 'sexta'},
            {'codigo_dane': '52224', 'nombre': 'Cuaspud', 'categoria': 'sexta'},
            {'codigo_dane': '52227', 'nombre': 'Cumbal', 'categoria': 'sexta'},
            {'codigo_dane': '52233', 'nombre': 'Cumbitara', 'categoria': 'sexta'},
            {'codigo_dane': '52240', 'nombre': 'Chachagüí', 'categoria': 'sexta'},
            {'codigo_dane': '52250', 'nombre': 'El Charco', 'categoria': 'sexta'},
            {'codigo_dane': '52254', 'nombre': 'El Peñol', 'categoria': 'sexta'},
            {'codigo_dane': '52256', 'nombre': 'El Rosario', 'categoria': 'sexta'},
            {'codigo_dane': '52258', 'nombre': 'El Tablón de Gómez', 'categoria': 'sexta'},
            {'codigo_dane': '52260', 'nombre': 'El Tambo', 'categoria': 'sexta'},
            {'codigo_dane': '52287', 'nombre': 'Funes', 'categoria': 'sexta'},
            {'codigo_dane': '52317', 'nombre': 'Guachucal', 'categoria': 'sexta'},
            {'codigo_dane': '52320', 'nombre': 'Guaitarilla', 'categoria': 'sexta'},
            {'codigo_dane': '52323', 'nombre': 'Gualmatán', 'categoria': 'sexta'},
            {'codigo_dane': '52352', 'nombre': 'Iles', 'categoria': 'sexta'},
            {'codigo_dane': '52354', 'nombre': 'Imués', 'categoria': 'sexta'},
            {'codigo_dane': '52356', 'nombre': 'Ipiales', 'categoria': 'segunda'},
            {'codigo_dane': '52378', 'nombre': 'La Cruz', 'categoria': 'sexta'},
            {'codigo_dane': '52381', 'nombre': 'La Florida', 'categoria': 'sexta'},
            {'codigo_dane': '52385', 'nombre': 'La Llanada', 'categoria': 'sexta'},
            {'codigo_dane': '52390', 'nombre': 'La Tola', 'categoria': 'sexta'},
            {'codigo_dane': '52399', 'nombre': 'La Unión', 'categoria': 'sexta'},
            {'codigo_dane': '52405', 'nombre': 'Leiva', 'categoria': 'sexta'},
            {'codigo_dane': '52411', 'nombre': 'Linares', 'categoria': 'sexta'},
            {'codigo_dane': '52418', 'nombre': 'Los Andes', 'categoria': 'sexta'},
            {'codigo_dane': '52427', 'nombre': 'Magüí', 'categoria': 'sexta'},
            {'codigo_dane': '52435', 'nombre': 'Mallama', 'categoria': 'sexta'},
            {'codigo_dane': '52473', 'nombre': 'Mosquera', 'categoria': 'sexta'},
            {'codigo_dane': '52480', 'nombre': 'Nariño', 'categoria': 'sexta'},
            {'codigo_dane': '52490', 'nombre': 'Olaya Herrera', 'categoria': 'sexta'},
            {'codigo_dane': '52506', 'nombre': 'Ospina', 'categoria': 'sexta'},
            {'codigo_dane': '52520', 'nombre': 'Francisco Pizarro', 'categoria': 'sexta'},
            {'codigo_dane': '52540', 'nombre': 'Policarpa', 'categoria': 'sexta'},
            {'codigo_dane': '52560', 'nombre': 'Potosí', 'categoria': 'sexta'},
            {'codigo_dane': '52565', 'nombre': 'Providencia', 'categoria': 'sexta'},
            {'codigo_dane': '52573', 'nombre': 'Puerres', 'categoria': 'sexta'},
            {'codigo_dane': '52585', 'nombre': 'Pupiales', 'categoria': 'sexta'},
            {'codigo_dane': '52612', 'nombre': 'Ricaurte', 'categoria': 'sexta'},
            {'codigo_dane': '52621', 'nombre': 'Roberto Payán', 'categoria': 'sexta'},
            {'codigo_dane': '52678', 'nombre': 'Samaniego', 'categoria': 'sexta'},
            {'codigo_dane': '52683', 'nombre': 'Sandoná', 'categoria': 'sexta'},
            {'codigo_dane': '52685', 'nombre': 'San Bernardo', 'categoria': 'sexta'},
            {'codigo_dane': '52687', 'nombre': 'San Lorenzo', 'categoria': 'sexta'},
            {'codigo_dane': '52693', 'nombre': 'San Pablo', 'categoria': 'sexta'},
            {'codigo_dane': '52694', 'nombre': 'San Pedro de Cartago', 'categoria': 'sexta'},
            {'codigo_dane': '52696', 'nombre': 'Santa Bárbara', 'categoria': 'sexta'},
            {'codigo_dane': '52699', 'nombre': 'Santacruz', 'categoria': 'sexta'},
            {'codigo_dane': '52720', 'nombre': 'Sapuyes', 'categoria': 'sexta'},
            {'codigo_dane': '52786', 'nombre': 'Taminango', 'categoria': 'sexta'},
            {'codigo_dane': '52788', 'nombre': 'Tangua', 'categoria': 'sexta'},
            {'codigo_dane': '52835', 'nombre': 'San Andrés de Tumaco', 'categoria': 'segunda'},
            {'codigo_dane': '52838', 'nombre': 'Túquerres', 'categoria': 'quinta'},
            {'codigo_dane': '52885', 'nombre': 'Yacuanquer', 'categoria': 'sexta'},
        ],
    }
    
    # Procesar lote 5
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
    
    print(f"\n📊 RESUMEN LOTE 5:")
    print(f"  - Municipios procesados: {len([m for dept_muns in municipios_data.values() for m in dept_muns])}")
    print(f"  - Municipios creados: {total_municipios_creados}")
    print(f"  - Municipios existentes: {total_municipios_existentes}")
    print(f"  - Total en base de datos: {Municipio.objects.count()}")
    
    return total_municipios_creados

if __name__ == "__main__":
    cargar_municipios_lote5()
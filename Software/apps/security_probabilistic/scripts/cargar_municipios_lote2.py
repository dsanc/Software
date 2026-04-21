#!/usr/bin/env python3
"""
Script para cargar municipios de Colombia - LOTE 2
(Boyacá, Caldas, Caquetá, Casanare, Cauca)
"""

import os
# import django

# Configurar Django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev_sqlite')
# django.setup()

from apps.security_probabilistic.models import Departamento, Municipio

def cargar_municipios_lote2():
    """Carga municipios del lote 2"""
    
    print("🇨🇴 Cargando municipios - LOTE 2...")
    
    # Obtener departamentos existentes
    departamentos = {dept.codigo_dane: dept for dept in Departamento.objects.all()}
    
    # Datos del lote 2
    municipios_data = {
        
        # BOYACÁ (15) - 123 municipios
        '15': [
            {'codigo_dane': '15001', 'nombre': 'Tunja', 'categoria': 'segunda', 'poblacion': 203251},
            {'codigo_dane': '15022', 'nombre': 'Almeida', 'categoria': 'sexta'},
            {'codigo_dane': '15047', 'nombre': 'Aquitania', 'categoria': 'sexta'},
            {'codigo_dane': '15051', 'nombre': 'Arcabuco', 'categoria': 'sexta'},
            {'codigo_dane': '15087', 'nombre': 'Belén', 'categoria': 'sexta'},
            {'codigo_dane': '15090', 'nombre': 'Berbeo', 'categoria': 'sexta'},
            {'codigo_dane': '15092', 'nombre': 'Betéitiva', 'categoria': 'sexta'},
            {'codigo_dane': '15097', 'nombre': 'Boavita', 'categoria': 'sexta'},
            {'codigo_dane': '15104', 'nombre': 'Boyacá', 'categoria': 'sexta'},
            {'codigo_dane': '15106', 'nombre': 'Briceño', 'categoria': 'sexta'},
            {'codigo_dane': '15109', 'nombre': 'Buenavista', 'categoria': 'sexta'},
            {'codigo_dane': '15114', 'nombre': 'Busbanzá', 'categoria': 'sexta'},
            {'codigo_dane': '15131', 'nombre': 'Caldas', 'categoria': 'sexta'},
            {'codigo_dane': '15135', 'nombre': 'Campohermoso', 'categoria': 'sexta'},
            {'codigo_dane': '15162', 'nombre': 'Cerinza', 'categoria': 'sexta'},
            {'codigo_dane': '15172', 'nombre': 'Chinavita', 'categoria': 'sexta'},
            {'codigo_dane': '15176', 'nombre': 'Chiquinquirá', 'categoria': 'quinta'},
            {'codigo_dane': '15180', 'nombre': 'Chiscas', 'categoria': 'sexta'},
            {'codigo_dane': '15183', 'nombre': 'Chita', 'categoria': 'sexta'},
            {'codigo_dane': '15185', 'nombre': 'Chitaraque', 'categoria': 'sexta'},
            {'codigo_dane': '15187', 'nombre': 'Chivatá', 'categoria': 'sexta'},
            {'codigo_dane': '15189', 'nombre': 'Ciénega', 'categoria': 'sexta'},
            {'codigo_dane': '15204', 'nombre': 'Cómbita', 'categoria': 'sexta'},
            {'codigo_dane': '15212', 'nombre': 'Coper', 'categoria': 'sexta'},
            {'codigo_dane': '15215', 'nombre': 'Corrales', 'categoria': 'sexta'},
            {'codigo_dane': '15218', 'nombre': 'Covarachía', 'categoria': 'sexta'},
            {'codigo_dane': '15223', 'nombre': 'Cubará', 'categoria': 'sexta'},
            {'codigo_dane': '15224', 'nombre': 'Cucaita', 'categoria': 'sexta'},
            {'codigo_dane': '15226', 'nombre': 'Cuítiva', 'categoria': 'sexta'},
            {'codigo_dane': '15232', 'nombre': 'Chíquiza', 'categoria': 'sexta'},
            {'codigo_dane': '15236', 'nombre': 'Chivor', 'categoria': 'sexta'},
            {'codigo_dane': '15238', 'nombre': 'Duitama', 'categoria': 'segunda'},
            {'codigo_dane': '15244', 'nombre': 'El Cocuy', 'categoria': 'sexta'},
            {'codigo_dane': '15248', 'nombre': 'El Espino', 'categoria': 'sexta'},
            {'codigo_dane': '15272', 'nombre': 'Firavitoba', 'categoria': 'sexta'},
            {'codigo_dane': '15276', 'nombre': 'Floresta', 'categoria': 'sexta'},
            {'codigo_dane': '15293', 'nombre': 'Gachantivá', 'categoria': 'sexta'},
            {'codigo_dane': '15296', 'nombre': 'Gameza', 'categoria': 'sexta'},
            {'codigo_dane': '15299', 'nombre': 'Garagoa', 'categoria': 'sexta'},
            {'codigo_dane': '15317', 'nombre': 'Guacamayas', 'categoria': 'sexta'},
            {'codigo_dane': '15322', 'nombre': 'Guateque', 'categoria': 'sexta'},
            {'codigo_dane': '15325', 'nombre': 'Guayatá', 'categoria': 'sexta'},
            {'codigo_dane': '15332', 'nombre': 'Güicán de la Sierra', 'categoria': 'sexta'},
            {'codigo_dane': '15362', 'nombre': 'Iza', 'categoria': 'sexta'},
            {'codigo_dane': '15367', 'nombre': 'Jenesano', 'categoria': 'sexta'},
            {'codigo_dane': '15368', 'nombre': 'Jericó', 'categoria': 'sexta'},
            {'codigo_dane': '15377', 'nombre': 'Labranzagrande', 'categoria': 'sexta'},
            {'codigo_dane': '15380', 'nombre': 'La Capilla', 'categoria': 'sexta'},
            {'codigo_dane': '15401', 'nombre': 'La Victoria', 'categoria': 'sexta'},
            {'codigo_dane': '15403', 'nombre': 'La Uvita', 'categoria': 'sexta'},
            {'codigo_dane': '15407', 'nombre': 'Villa de Leyva', 'categoria': 'sexta'},
            {'codigo_dane': '15425', 'nombre': 'Macanal', 'categoria': 'sexta'},
            {'codigo_dane': '15442', 'nombre': 'Maripí', 'categoria': 'sexta'},
            {'codigo_dane': '15455', 'nombre': 'Miraflores', 'categoria': 'sexta'},
            {'codigo_dane': '15464', 'nombre': 'Mongua', 'categoria': 'sexta'},
            {'codigo_dane': '15466', 'nombre': 'Monguí', 'categoria': 'sexta'},
            {'codigo_dane': '15469', 'nombre': 'Moniquirá', 'categoria': 'sexta'},
            {'codigo_dane': '15476', 'nombre': 'Motavita', 'categoria': 'sexta'},
            {'codigo_dane': '15480', 'nombre': 'Muzo', 'categoria': 'sexta'},
            {'codigo_dane': '15491', 'nombre': 'Nobsa', 'categoria': 'sexta'},
            {'codigo_dane': '15494', 'nombre': 'Nuevo Colón', 'categoria': 'sexta'},
            {'codigo_dane': '15500', 'nombre': 'Oicatá', 'categoria': 'sexta'},
            {'codigo_dane': '15507', 'nombre': 'Otanche', 'categoria': 'sexta'},
            {'codigo_dane': '15511', 'nombre': 'Pachavita', 'categoria': 'sexta'},
            {'codigo_dane': '15514', 'nombre': 'Páez', 'categoria': 'sexta'},
            {'codigo_dane': '15516', 'nombre': 'Paipa', 'categoria': 'quinta'},
            {'codigo_dane': '15518', 'nombre': 'Pajarito', 'categoria': 'sexta'},
            {'codigo_dane': '15522', 'nombre': 'Panqueba', 'categoria': 'sexta'},
            {'codigo_dane': '15531', 'nombre': 'Pauna', 'categoria': 'sexta'},
            {'codigo_dane': '15533', 'nombre': 'Paya', 'categoria': 'sexta'},
            {'codigo_dane': '15537', 'nombre': 'Paz de Río', 'categoria': 'sexta'},
            {'codigo_dane': '15542', 'nombre': 'Pesca', 'categoria': 'sexta'},
            {'codigo_dane': '15550', 'nombre': 'Pisba', 'categoria': 'sexta'},
            {'codigo_dane': '15572', 'nombre': 'Puerto Boyacá', 'categoria': 'quinta'},
            {'codigo_dane': '15580', 'nombre': 'Quípama', 'categoria': 'sexta'},
            {'codigo_dane': '15599', 'nombre': 'Ramiriquí', 'categoria': 'sexta'},
            {'codigo_dane': '15600', 'nombre': 'Ráquira', 'categoria': 'sexta'},
            {'codigo_dane': '15621', 'nombre': 'Rondón', 'categoria': 'sexta'},
            {'codigo_dane': '15632', 'nombre': 'Saboyá', 'categoria': 'sexta'},
            {'codigo_dane': '15638', 'nombre': 'Sáchica', 'categoria': 'sexta'},
            {'codigo_dane': '15646', 'nombre': 'Samacá', 'categoria': 'sexta'},
            {'codigo_dane': '15660', 'nombre': 'San Eduardo', 'categoria': 'sexta'},
            {'codigo_dane': '15664', 'nombre': 'San José de Pare', 'categoria': 'sexta'},
            {'codigo_dane': '15667', 'nombre': 'San Luis de Gaceno', 'categoria': 'sexta'},
            {'codigo_dane': '15673', 'nombre': 'San Mateo', 'categoria': 'sexta'},
            {'codigo_dane': '15676', 'nombre': 'San Miguel de Sema', 'categoria': 'sexta'},
            {'codigo_dane': '15681', 'nombre': 'San Pablo de Borbur', 'categoria': 'sexta'},
            {'codigo_dane': '15686', 'nombre': 'Santana', 'categoria': 'sexta'},
            {'codigo_dane': '15690', 'nombre': 'Santa María', 'categoria': 'sexta'},
            {'codigo_dane': '15693', 'nombre': 'Santa Rosa de Viterbo', 'categoria': 'sexta'},
            {'codigo_dane': '15696', 'nombre': 'Santa Sofía', 'categoria': 'sexta'},
            {'codigo_dane': '15720', 'nombre': 'Sativanorte', 'categoria': 'sexta'},
            {'codigo_dane': '15723', 'nombre': 'Sativasur', 'categoria': 'sexta'},
            {'codigo_dane': '15740', 'nombre': 'Siachoque', 'categoria': 'sexta'},
            {'codigo_dane': '15753', 'nombre': 'Soatá', 'categoria': 'sexta'},
            {'codigo_dane': '15755', 'nombre': 'Socotá', 'categoria': 'sexta'},
            {'codigo_dane': '15757', 'nombre': 'Socha', 'categoria': 'sexta'},
            {'codigo_dane': '15759', 'nombre': 'Sogamoso', 'categoria': 'segunda'},
            {'codigo_dane': '15761', 'nombre': 'Somondoco', 'categoria': 'sexta'},
            {'codigo_dane': '15762', 'nombre': 'Sora', 'categoria': 'sexta'},
            {'codigo_dane': '15763', 'nombre': 'Sotaquirá', 'categoria': 'sexta'},
            {'codigo_dane': '15764', 'nombre': 'Soracá', 'categoria': 'sexta'},
            {'codigo_dane': '15774', 'nombre': 'Susacón', 'categoria': 'sexta'},
            {'codigo_dane': '15776', 'nombre': 'Sutamarchán', 'categoria': 'sexta'},
            {'codigo_dane': '15778', 'nombre': 'Sutatenza', 'categoria': 'sexta'},
            {'codigo_dane': '15790', 'nombre': 'Tasco', 'categoria': 'sexta'},
            {'codigo_dane': '15798', 'nombre': 'Tenza', 'categoria': 'sexta'},
            {'codigo_dane': '15804', 'nombre': 'Tibaná', 'categoria': 'sexta'},
            {'codigo_dane': '15806', 'nombre': 'Tibasosa', 'categoria': 'sexta'},
            {'codigo_dane': '15808', 'nombre': 'Tinjacá', 'categoria': 'sexta'},
            {'codigo_dane': '15810', 'nombre': 'Tipacoque', 'categoria': 'sexta'},
            {'codigo_dane': '15814', 'nombre': 'Toca', 'categoria': 'sexta'},
            {'codigo_dane': '15816', 'nombre': 'Togüí', 'categoria': 'sexta'},
            {'codigo_dane': '15820', 'nombre': 'Tópaga', 'categoria': 'sexta'},
            {'codigo_dane': '15822', 'nombre': 'Tota', 'categoria': 'sexta'},
            {'codigo_dane': '15832', 'nombre': 'Tununguá', 'categoria': 'sexta'},
            {'codigo_dane': '15835', 'nombre': 'Turmequé', 'categoria': 'sexta'},
            {'codigo_dane': '15837', 'nombre': 'Tuta', 'categoria': 'sexta'},
            {'codigo_dane': '15839', 'nombre': 'Tutazá', 'categoria': 'sexta'},
            {'codigo_dane': '15842', 'nombre': 'Umbita', 'categoria': 'sexta'},
            {'codigo_dane': '15861', 'nombre': 'Ventaquemada', 'categoria': 'sexta'},
            {'codigo_dane': '15879', 'nombre': 'Viracachá', 'categoria': 'sexta'},
            {'codigo_dane': '15897', 'nombre': 'Zetaquira', 'categoria': 'sexta'},
        ],
        
        # CALDAS (17) - 27 municipios
        '17': [
            {'codigo_dane': '17001', 'nombre': 'Manizales', 'categoria': 'primera', 'poblacion': 434403},
            {'codigo_dane': '17013', 'nombre': 'Aguadas', 'categoria': 'sexta'},
            {'codigo_dane': '17042', 'nombre': 'Anserma', 'categoria': 'quinta'},
            {'codigo_dane': '17050', 'nombre': 'Aranzazu', 'categoria': 'sexta'},
            {'codigo_dane': '17088', 'nombre': 'Belalcázar', 'categoria': 'sexta'},
            {'codigo_dane': '17174', 'nombre': 'Chinchiná', 'categoria': 'quinta'},
            {'codigo_dane': '17272', 'nombre': 'Filadelfia', 'categoria': 'sexta'},
            {'codigo_dane': '17380', 'nombre': 'La Dorada', 'categoria': 'cuarta'},
            {'codigo_dane': '17388', 'nombre': 'La Merced', 'categoria': 'sexta'},
            {'codigo_dane': '17433', 'nombre': 'Manzanares', 'categoria': 'sexta'},
            {'codigo_dane': '17442', 'nombre': 'Marmato', 'categoria': 'sexta'},
            {'codigo_dane': '17444', 'nombre': 'Marquetalia', 'categoria': 'sexta'},
            {'codigo_dane': '17446', 'nombre': 'Marulanda', 'categoria': 'sexta'},
            {'codigo_dane': '17486', 'nombre': 'Neira', 'categoria': 'sexta'},
            {'codigo_dane': '17495', 'nombre': 'Norcasia', 'categoria': 'sexta'},
            {'codigo_dane': '17513', 'nombre': 'Pácora', 'categoria': 'sexta'},
            {'codigo_dane': '17524', 'nombre': 'Palestina', 'categoria': 'sexta'},
            {'codigo_dane': '17541', 'nombre': 'Pensilvania', 'categoria': 'sexta'},
            {'codigo_dane': '17614', 'nombre': 'Riosucio', 'categoria': 'quinta'},
            {'codigo_dane': '17616', 'nombre': 'Risaralda', 'categoria': 'sexta'},
            {'codigo_dane': '17653', 'nombre': 'Salamina', 'categoria': 'sexta'},
            {'codigo_dane': '17662', 'nombre': 'Samaná', 'categoria': 'sexta'},
            {'codigo_dane': '17665', 'nombre': 'San José', 'categoria': 'sexta'},
            {'codigo_dane': '17777', 'nombre': 'Supía', 'categoria': 'sexta'},
            {'codigo_dane': '17867', 'nombre': 'Victoria', 'categoria': 'sexta'},
            {'codigo_dane': '17873', 'nombre': 'Villamaría', 'categoria': 'quinta'},
            {'codigo_dane': '17877', 'nombre': 'Viterbo', 'categoria': 'sexta'},
        ],
        
        # CAQUETÁ (18) - 16 municipios
        '18': [
            {'codigo_dane': '18001', 'nombre': 'Florencia', 'categoria': 'segunda', 'poblacion': 188365},
            {'codigo_dane': '18029', 'nombre': 'Albania', 'categoria': 'sexta'},
            {'codigo_dane': '18094', 'nombre': 'Belén de los Andaquíes', 'categoria': 'sexta'},
            {'codigo_dane': '18150', 'nombre': 'Cartagena del Chairá', 'categoria': 'sexta'},
            {'codigo_dane': '18205', 'nombre': 'Curillo', 'categoria': 'sexta'},
            {'codigo_dane': '18247', 'nombre': 'El Doncello', 'categoria': 'sexta'},
            {'codigo_dane': '18256', 'nombre': 'El Paujil', 'categoria': 'sexta'},
            {'codigo_dane': '18410', 'nombre': 'La Montañita', 'categoria': 'sexta'},
            {'codigo_dane': '18460', 'nombre': 'Milán', 'categoria': 'sexta'},
            {'codigo_dane': '18479', 'nombre': 'Morelia', 'categoria': 'sexta'},
            {'codigo_dane': '18592', 'nombre': 'Puerto Rico', 'categoria': 'sexta'},
            {'codigo_dane': '18610', 'nombre': 'San José del Fragua', 'categoria': 'sexta'},
            {'codigo_dane': '18753', 'nombre': 'San Vicente del Caguán', 'categoria': 'quinta'},
            {'codigo_dane': '18756', 'nombre': 'Solano', 'categoria': 'sexta'},
            {'codigo_dane': '18785', 'nombre': 'Solita', 'categoria': 'sexta'},
            {'codigo_dane': '18860', 'nombre': 'Valparaíso', 'categoria': 'sexta'},
        ],
        
        # CASANARE (85) - 19 municipios
        '85': [
            {'codigo_dane': '85001', 'nombre': 'Yopal', 'categoria': 'segunda', 'poblacion': 147699},
            {'codigo_dane': '85010', 'nombre': 'Aguazul', 'categoria': 'quinta'},
            {'codigo_dane': '85015', 'nombre': 'Chámeza', 'categoria': 'sexta'},
            {'codigo_dane': '85125', 'nombre': 'Hato Corozal', 'categoria': 'sexta'},
            {'codigo_dane': '85136', 'nombre': 'La Salina', 'categoria': 'sexta'},
            {'codigo_dane': '85139', 'nombre': 'Maní', 'categoria': 'sexta'},
            {'codigo_dane': '85162', 'nombre': 'Monterrey', 'categoria': 'sexta'},
            {'codigo_dane': '85225', 'nombre': 'Nunchía', 'categoria': 'sexta'},
            {'codigo_dane': '85230', 'nombre': 'Orocué', 'categoria': 'sexta'},
            {'codigo_dane': '85250', 'nombre': 'Paz de Ariporo', 'categoria': 'quinta'},
            {'codigo_dane': '85263', 'nombre': 'Pore', 'categoria': 'sexta'},
            {'codigo_dane': '85279', 'nombre': 'Recetor', 'categoria': 'sexta'},
            {'codigo_dane': '85300', 'nombre': 'Sabanalarga', 'categoria': 'sexta'},
            {'codigo_dane': '85315', 'nombre': 'Sácama', 'categoria': 'sexta'},
            {'codigo_dane': '85325', 'nombre': 'San Luis de Palenque', 'categoria': 'sexta'},
            {'codigo_dane': '85400', 'nombre': 'Támara', 'categoria': 'sexta'},
            {'codigo_dane': '85410', 'nombre': 'Tauramena', 'categoria': 'quinta'},
            {'codigo_dane': '85430', 'nombre': 'Trinidad', 'categoria': 'quinta'},
            {'codigo_dane': '85440', 'nombre': 'Villanueva', 'categoria': 'quinta'},
        ],
        
        # CAUCA (19) - 42 municipios
        '19': [
            {'codigo_dane': '19001', 'nombre': 'Popayán', 'categoria': 'segunda', 'poblacion': 318059},
            {'codigo_dane': '19022', 'nombre': 'Almaguer', 'categoria': 'sexta'},
            {'codigo_dane': '19050', 'nombre': 'Argelia', 'categoria': 'sexta'},
            {'codigo_dane': '19075', 'nombre': 'Balboa', 'categoria': 'sexta'},
            {'codigo_dane': '19100', 'nombre': 'Bolívar', 'categoria': 'sexta'},
            {'codigo_dane': '19110', 'nombre': 'Buenos Aires', 'categoria': 'sexta'},
            {'codigo_dane': '19130', 'nombre': 'Cajibío', 'categoria': 'sexta'},
            {'codigo_dane': '19137', 'nombre': 'Caldono', 'categoria': 'sexta'},
            {'codigo_dane': '19142', 'nombre': 'Caloto', 'categoria': 'sexta'},
            {'codigo_dane': '19212', 'nombre': 'Corinto', 'categoria': 'sexta'},
            {'codigo_dane': '19256', 'nombre': 'El Tambo', 'categoria': 'sexta'},
            {'codigo_dane': '19290', 'nombre': 'Florencia', 'categoria': 'sexta'},
            {'codigo_dane': '19300', 'nombre': 'Guachené', 'categoria': 'sexta'},
            {'codigo_dane': '19318', 'nombre': 'Guapi', 'categoria': 'sexta'},
            {'codigo_dane': '19355', 'nombre': 'Inzá', 'categoria': 'sexta'},
            {'codigo_dane': '19364', 'nombre': 'Jambaló', 'categoria': 'sexta'},
            {'codigo_dane': '19392', 'nombre': 'La Sierra', 'categoria': 'sexta'},
            {'codigo_dane': '19397', 'nombre': 'La Vega', 'categoria': 'sexta'},
            {'codigo_dane': '19418', 'nombre': 'López de Micay', 'categoria': 'sexta'},
            {'codigo_dane': '19450', 'nombre': 'Mercaderes', 'categoria': 'sexta'},
            {'codigo_dane': '19455', 'nombre': 'Miranda', 'categoria': 'sexta'},
            {'codigo_dane': '19473', 'nombre': 'Morales', 'categoria': 'sexta'},
            {'codigo_dane': '19513', 'nombre': 'Padilla', 'categoria': 'sexta'},
            {'codigo_dane': '19517', 'nombre': 'Páez', 'categoria': 'sexta'},
            {'codigo_dane': '19532', 'nombre': 'Patía', 'categoria': 'sexta'},
            {'codigo_dane': '19533', 'nombre': 'Piamonte', 'categoria': 'sexta'},
            {'codigo_dane': '19548', 'nombre': 'Piendamó - Tunía', 'categoria': 'sexta'},
            {'codigo_dane': '19573', 'nombre': 'Puerto Tejada', 'categoria': 'quinta'},
            {'codigo_dane': '19585', 'nombre': 'Puracé', 'categoria': 'sexta'},
            {'codigo_dane': '19622', 'nombre': 'Rosas', 'categoria': 'sexta'},
            {'codigo_dane': '19693', 'nombre': 'San Sebastián', 'categoria': 'sexta'},
            {'codigo_dane': '19698', 'nombre': 'Santander de Quilichao', 'categoria': 'quinta'},
            {'codigo_dane': '19701', 'nombre': 'Santa Rosa', 'categoria': 'sexta'},
            {'codigo_dane': '19743', 'nombre': 'Silvia', 'categoria': 'sexta'},
            {'codigo_dane': '19760', 'nombre': 'Sotará', 'categoria': 'sexta'},
            {'codigo_dane': '19780', 'nombre': 'Suárez', 'categoria': 'sexta'},
            {'codigo_dane': '19785', 'nombre': 'Sucre', 'categoria': 'sexta'},
            {'codigo_dane': '19807', 'nombre': 'Timbío', 'categoria': 'sexta'},
            {'codigo_dane': '19809', 'nombre': 'Timbiquí', 'categoria': 'sexta'},
            {'codigo_dane': '19821', 'nombre': 'Toribío', 'categoria': 'sexta'},
            {'codigo_dane': '19824', 'nombre': 'Totoró', 'categoria': 'sexta'},
            {'codigo_dane': '19845', 'nombre': 'Villa Rica', 'categoria': 'sexta'},
        ],
    }
    
    # Procesar lote 2
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
    
    print(f"\n📊 RESUMEN LOTE 2:")
    print(f"  - Municipios procesados: {len([m for dept_muns in municipios_data.values() for m in dept_muns])}")
    print(f"  - Municipios creados: {total_municipios_creados}")
    print(f"  - Municipios existentes: {total_municipios_existentes}")
    print(f"  - Total en base de datos: {Municipio.objects.count()}")
    
    return total_municipios_creados

if __name__ == "__main__":
    cargar_municipios_lote2()
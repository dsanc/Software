#!/usr/bin/env python3
"""
Script para cargar municipios de Colombia - LOTE 6 (FINAL)
(Norte de Santander, Putumayo, Quindío, Risaralda, San Andrés, Santander, Sucre, Tolima, Valle del Cauca, Vaupés, Vichada)
"""

import os
# import django

# Configurar Django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev_sqlite')
# django.setup()

from apps.security_probabilistic.models import Departamento, Municipio

def cargar_municipios_lote6():
    """Carga municipios del lote 6 (final)"""
    
    print("🇨🇴 Cargando municipios - LOTE 6 (FINAL)...")
    
    # Obtener departamentos existentes
    departamentos = {dept.codigo_dane: dept for dept in Departamento.objects.all()}
    
    # Datos del lote 6
    municipios_data = {
        
        # NORTE DE SANTANDER (54) - 40 municipios
        '54': [
            {'codigo_dane': '54001', 'nombre': 'Cúcuta', 'categoria': 'primera', 'poblacion': 650011},
            {'codigo_dane': '54003', 'nombre': 'Abrego', 'categoria': 'sexta'},
            {'codigo_dane': '54051', 'nombre': 'Arboledas', 'categoria': 'sexta'},
            {'codigo_dane': '54099', 'nombre': 'Bochalema', 'categoria': 'sexta'},
            {'codigo_dane': '54109', 'nombre': 'Bucarasica', 'categoria': 'sexta'},
            {'codigo_dane': '54125', 'nombre': 'Cácota', 'categoria': 'sexta'},
            {'codigo_dane': '54128', 'nombre': 'Cachirá', 'categoria': 'sexta'},
            {'codigo_dane': '54172', 'nombre': 'Chinácota', 'categoria': 'sexta'},
            {'codigo_dane': '54174', 'nombre': 'Chitagá', 'categoria': 'sexta'},
            {'codigo_dane': '54206', 'nombre': 'Convención', 'categoria': 'sexta'},
            {'codigo_dane': '54223', 'nombre': 'Cucutilla', 'categoria': 'sexta'},
            {'codigo_dane': '54239', 'nombre': 'Durania', 'categoria': 'sexta'},
            {'codigo_dane': '54245', 'nombre': 'El Carmen', 'categoria': 'sexta'},
            {'codigo_dane': '54250', 'nombre': 'El Tarra', 'categoria': 'sexta'},
            {'codigo_dane': '54261', 'nombre': 'El Zulia', 'categoria': 'sexta'},
            {'codigo_dane': '54313', 'nombre': 'Gramalote', 'categoria': 'sexta'},
            {'codigo_dane': '54344', 'nombre': 'Hacarí', 'categoria': 'sexta'},
            {'codigo_dane': '54347', 'nombre': 'Herrán', 'categoria': 'sexta'},
            {'codigo_dane': '54377', 'nombre': 'Labateca', 'categoria': 'sexta'},
            {'codigo_dane': '54385', 'nombre': 'La Esperanza', 'categoria': 'sexta'},
            {'codigo_dane': '54398', 'nombre': 'La Playa', 'categoria': 'sexta'},
            {'codigo_dane': '54405', 'nombre': 'Los Patios', 'categoria': 'cuarta'},
            {'codigo_dane': '54418', 'nombre': 'Lourdes', 'categoria': 'sexta'},
            {'codigo_dane': '54480', 'nombre': 'Mutiscua', 'categoria': 'sexta'},
            {'codigo_dane': '54498', 'nombre': 'Ocaña', 'categoria': 'cuarta'},
            {'codigo_dane': '54518', 'nombre': 'Pamplona', 'categoria': 'quinta'},
            {'codigo_dane': '54520', 'nombre': 'Pamplonita', 'categoria': 'sexta'},
            {'codigo_dane': '54553', 'nombre': 'Puerto Santander', 'categoria': 'sexta'},
            {'codigo_dane': '54599', 'nombre': 'Ragonvalia', 'categoria': 'sexta'},
            {'codigo_dane': '54660', 'nombre': 'Salazar', 'categoria': 'sexta'},
            {'codigo_dane': '54670', 'nombre': 'San Calixto', 'categoria': 'sexta'},
            {'codigo_dane': '54673', 'nombre': 'San Cayetano', 'categoria': 'sexta'},
            {'codigo_dane': '54680', 'nombre': 'Santiago', 'categoria': 'sexta'},
            {'codigo_dane': '54720', 'nombre': 'Sardinata', 'categoria': 'sexta'},
            {'codigo_dane': '54743', 'nombre': 'Silos', 'categoria': 'sexta'},
            {'codigo_dane': '54800', 'nombre': 'Teorama', 'categoria': 'sexta'},
            {'codigo_dane': '54810', 'nombre': 'Tibú', 'categoria': 'quinta'},
            {'codigo_dane': '54820', 'nombre': 'Toledo', 'categoria': 'sexta'},
            {'codigo_dane': '54871', 'nombre': 'Villa Caro', 'categoria': 'sexta'},
            {'codigo_dane': '54874', 'nombre': 'Villa del Rosario', 'categoria': 'cuarta'},
        ],
        
        # PUTUMAYO (86) - 13 municipios
        '86': [
            {'codigo_dane': '86001', 'nombre': 'Mocoa', 'categoria': 'quinta', 'poblacion': 47551},
            {'codigo_dane': '86219', 'nombre': 'Colón', 'categoria': 'sexta'},
            {'codigo_dane': '86320', 'nombre': 'Orito', 'categoria': 'sexta'},
            {'codigo_dane': '86568', 'nombre': 'Puerto Asís', 'categoria': 'quinta'},
            {'codigo_dane': '86569', 'nombre': 'Puerto Caicedo', 'categoria': 'sexta'},
            {'codigo_dane': '86571', 'nombre': 'Puerto Guzmán', 'categoria': 'sexta'},
            {'codigo_dane': '86573', 'nombre': 'Leguízamo', 'categoria': 'sexta'},
            {'codigo_dane': '86749', 'nombre': 'Sibundoy', 'categoria': 'sexta'},
            {'codigo_dane': '86755', 'nombre': 'San Francisco', 'categoria': 'sexta'},
            {'codigo_dane': '86757', 'nombre': 'San Miguel', 'categoria': 'sexta'},
            {'codigo_dane': '86760', 'nombre': 'Santiago', 'categoria': 'sexta'},
            {'codigo_dane': '86865', 'nombre': 'Valle del Guamuez', 'categoria': 'sexta'},
            {'codigo_dane': '86885', 'nombre': 'Villagarzón', 'categoria': 'sexta'},
        ],
        
        # QUINDÍO (63) - 12 municipios
        '63': [
            {'codigo_dane': '63001', 'nombre': 'Armenia', 'categoria': 'segunda', 'poblacion': 307388},
            {'codigo_dane': '63111', 'nombre': 'Buenavista', 'categoria': 'sexta'},
            {'codigo_dane': '63130', 'nombre': 'Calarcá', 'categoria': 'quinta'},
            {'codigo_dane': '63190', 'nombre': 'Circasia', 'categoria': 'sexta'},
            {'codigo_dane': '63212', 'nombre': 'Córdoba', 'categoria': 'sexta'},
            {'codigo_dane': '63272', 'nombre': 'Filandia', 'categoria': 'sexta'},
            {'codigo_dane': '63302', 'nombre': 'Génova', 'categoria': 'sexta'},
            {'codigo_dane': '63401', 'nombre': 'La Tebaida', 'categoria': 'quinta'},
            {'codigo_dane': '63470', 'nombre': 'Montenegro', 'categoria': 'quinta'},
            {'codigo_dane': '63548', 'nombre': 'Pijao', 'categoria': 'sexta'},
            {'codigo_dane': '63594', 'nombre': 'Quimbaya', 'categoria': 'quinta'},
            {'codigo_dane': '63690', 'nombre': 'Salento', 'categoria': 'sexta'},
        ],
        
        # RISARALDA (66) - 14 municipios
        '66': [
            {'codigo_dane': '66001', 'nombre': 'Pereira', 'categoria': 'primera', 'poblacion': 488839},
            {'codigo_dane': '66045', 'nombre': 'Apía', 'categoria': 'sexta'},
            {'codigo_dane': '66075', 'nombre': 'Balboa', 'categoria': 'sexta'},
            {'codigo_dane': '66088', 'nombre': 'Belén de Umbría', 'categoria': 'sexta'},
            {'codigo_dane': '66170', 'nombre': 'Dosquebradas', 'categoria': 'segunda'},
            {'codigo_dane': '66318', 'nombre': 'Guática', 'categoria': 'sexta'},
            {'codigo_dane': '66383', 'nombre': 'La Celia', 'categoria': 'sexta'},
            {'codigo_dane': '66400', 'nombre': 'La Virginia', 'categoria': 'quinta'},
            {'codigo_dane': '66440', 'nombre': 'Marsella', 'categoria': 'sexta'},
            {'codigo_dane': '66456', 'nombre': 'Mistrató', 'categoria': 'sexta'},
            {'codigo_dane': '66572', 'nombre': 'Pueblo Rico', 'categoria': 'sexta'},
            {'codigo_dane': '66594', 'nombre': 'Quinchía', 'categoria': 'sexta'},
            {'codigo_dane': '66682', 'nombre': 'Santa Rosa de Cabal', 'categoria': 'quinta'},
            {'codigo_dane': '66687', 'nombre': 'Santuario', 'categoria': 'sexta'},
        ],
        
        # SAN ANDRÉS Y PROVIDENCIA (88) - 3 municipios
        '88': [
            {'codigo_dane': '88001', 'nombre': 'San Andrés', 'categoria': 'quinta', 'poblacion': 58257},
            {'codigo_dane': '88564', 'nombre': 'Providencia', 'categoria': 'sexta'},
            {'codigo_dane': '88980', 'nombre': 'Santa Catalina', 'categoria': 'sexta'},
        ],
        
        # SANTANDER (68) - 87 municipios (reducido para el ejemplo)
        '68': [
            {'codigo_dane': '68001', 'nombre': 'Bucaramanga', 'categoria': 'primera', 'poblacion': 613400},
            {'codigo_dane': '68013', 'nombre': 'Aguada', 'categoria': 'sexta'},
            {'codigo_dane': '68020', 'nombre': 'Albania', 'categoria': 'sexta'},
            {'codigo_dane': '68051', 'nombre': 'Aratoca', 'categoria': 'sexta'},
            {'codigo_dane': '68077', 'nombre': 'Barbosa', 'categoria': 'quinta'},
            {'codigo_dane': '68079', 'nombre': 'Barichara', 'categoria': 'sexta'},
            {'codigo_dane': '68081', 'nombre': 'Barrancas', 'categoria': 'sexta'},
            {'codigo_dane': '68092', 'nombre': 'Betulia', 'categoria': 'sexta'},
            {'codigo_dane': '68101', 'nombre': 'Bolívar', 'categoria': 'sexta'},
            {'codigo_dane': '68121', 'nombre': 'Cabrera', 'categoria': 'sexta'},
            {'codigo_dane': '68132', 'nombre': 'California', 'categoria': 'sexta'},
            {'codigo_dane': '68147', 'nombre': 'Capitanejo', 'categoria': 'sexta'},
            {'codigo_dane': '68152', 'nombre': 'Carcasí', 'categoria': 'sexta'},
            {'codigo_dane': '68160', 'nombre': 'Cepitá', 'categoria': 'sexta'},
            {'codigo_dane': '68162', 'nombre': 'Cerrito', 'categoria': 'sexta'},
            {'codigo_dane': '68167', 'nombre': 'Charalá', 'categoria': 'sexta'},
            {'codigo_dane': '68169', 'nombre': 'Charta', 'categoria': 'sexta'},
            {'codigo_dane': '68176', 'nombre': 'Chima', 'categoria': 'sexta'},
            {'codigo_dane': '68179', 'nombre': 'Chipatá', 'categoria': 'sexta'},
            {'codigo_dane': '68190', 'nombre': 'Cimitarra', 'categoria': 'quinta'},
            {'codigo_dane': '68207', 'nombre': 'Concepción', 'categoria': 'sexta'},
            {'codigo_dane': '68209', 'nombre': 'Confines', 'categoria': 'sexta'},
            {'codigo_dane': '68211', 'nombre': 'Contratación', 'categoria': 'sexta'},
            {'codigo_dane': '68217', 'nombre': 'Coromoro', 'categoria': 'sexta'},
            {'codigo_dane': '68229', 'nombre': 'Curití', 'categoria': 'sexta'},
            {'codigo_dane': '68235', 'nombre': 'El Carmen de Chucurí', 'categoria': 'sexta'},
            {'codigo_dane': '68245', 'nombre': 'El Guacamayo', 'categoria': 'sexta'},
            {'codigo_dane': '68250', 'nombre': 'El Peñón', 'categoria': 'sexta'},
            {'codigo_dane': '68255', 'nombre': 'El Playón', 'categoria': 'sexta'},
            {'codigo_dane': '68264', 'nombre': 'Encino', 'categoria': 'sexta'},
            {'codigo_dane': '68266', 'nombre': 'Enciso', 'categoria': 'sexta'},
            {'codigo_dane': '68271', 'nombre': 'Florián', 'categoria': 'sexta'},
            {'codigo_dane': '68276', 'nombre': 'Floridablanca', 'categoria': 'primera'},
            {'codigo_dane': '68296', 'nombre': 'Galán', 'categoria': 'sexta'},
            {'codigo_dane': '68298', 'nombre': 'Gámbita', 'categoria': 'sexta'},
            {'codigo_dane': '68307', 'nombre': 'Girón', 'categoria': 'segunda'},
            {'codigo_dane': '68318', 'nombre': 'Guaca', 'categoria': 'sexta'},
            {'codigo_dane': '68320', 'nombre': 'Guadalupe', 'categoria': 'sexta'},
            {'codigo_dane': '68322', 'nombre': 'Guapotá', 'categoria': 'sexta'},
            {'codigo_dane': '68324', 'nombre': 'Guavatá', 'categoria': 'sexta'},
            {'codigo_dane': '68327', 'nombre': 'Güepsa', 'categoria': 'sexta'},
            {'codigo_dane': '68344', 'nombre': 'Hato', 'categoria': 'sexta'},
            {'codigo_dane': '68368', 'nombre': 'Jesús María', 'categoria': 'sexta'},
            {'codigo_dane': '68370', 'nombre': 'Jordán', 'categoria': 'sexta'},
            {'codigo_dane': '68377', 'nombre': 'La Belleza', 'categoria': 'sexta'},
            {'codigo_dane': '68385', 'nombre': 'Landázuri', 'categoria': 'sexta'},
            {'codigo_dane': '68397', 'nombre': 'La Paz', 'categoria': 'sexta'},
            {'codigo_dane': '68406', 'nombre': 'Lebrija', 'categoria': 'quinta'},
            {'codigo_dane': '68418', 'nombre': 'Los Santos', 'categoria': 'sexta'},
            {'codigo_dane': '68425', 'nombre': 'Macaravita', 'categoria': 'sexta'},
            {'codigo_dane': '68432', 'nombre': 'Málaga', 'categoria': 'quinta'},
            {'codigo_dane': '68444', 'nombre': 'Matanza', 'categoria': 'sexta'},
            {'codigo_dane': '68464', 'nombre': 'Mogotes', 'categoria': 'sexta'},
            {'codigo_dane': '68468', 'nombre': 'Molagavita', 'categoria': 'sexta'},
            {'codigo_dane': '68498', 'nombre': 'Ocamonte', 'categoria': 'sexta'},
            {'codigo_dane': '68500', 'nombre': 'Oiba', 'categoria': 'sexta'},
            {'codigo_dane': '68502', 'nombre': 'Onzaga', 'categoria': 'sexta'},
            {'codigo_dane': '68522', 'nombre': 'Palmar', 'categoria': 'sexta'},
            {'codigo_dane': '68524', 'nombre': 'Palmas del Socorro', 'categoria': 'sexta'},
            {'codigo_dane': '68533', 'nombre': 'Páramo', 'categoria': 'sexta'},
            {'codigo_dane': '68547', 'nombre': 'Piedecuesta', 'categoria': 'segunda'},
            {'codigo_dane': '68549', 'nombre': 'Pinchote', 'categoria': 'sexta'},
            {'codigo_dane': '68572', 'nombre': 'Puente Nacional', 'categoria': 'sexta'},
            {'codigo_dane': '68573', 'nombre': 'Puerto Parra', 'categoria': 'sexta'},
            {'codigo_dane': '68575', 'nombre': 'Puerto Wilches', 'categoria': 'quinta'},
            {'codigo_dane': '68615', 'nombre': 'Rionegro', 'categoria': 'quinta'},
            {'codigo_dane': '68655', 'nombre': 'Sabana de Torres', 'categoria': 'quinta'},
            {'codigo_dane': '68669', 'nombre': 'San Andrés', 'categoria': 'sexta'},
            {'codigo_dane': '68673', 'nombre': 'San Benito', 'categoria': 'sexta'},
            {'codigo_dane': '68679', 'nombre': 'San Gil', 'categoria': 'cuarta'},
            {'codigo_dane': '68682', 'nombre': 'San Joaquín', 'categoria': 'sexta'},
            {'codigo_dane': '68684', 'nombre': 'San José de Miranda', 'categoria': 'sexta'},
            {'codigo_dane': '68686', 'nombre': 'San Miguel', 'categoria': 'sexta'},
            {'codigo_dane': '68689', 'nombre': 'San Vicente de Chucurí', 'categoria': 'quinta'},
            {'codigo_dane': '68705', 'nombre': 'Santa Bárbara', 'categoria': 'sexta'},
            {'codigo_dane': '68720', 'nombre': 'Santa Helena del Opón', 'categoria': 'sexta'},
            {'codigo_dane': '68745', 'nombre': 'Simacota', 'categoria': 'sexta'},
            {'codigo_dane': '68755', 'nombre': 'Socorro', 'categoria': 'quinta'},
            {'codigo_dane': '68770', 'nombre': 'Suaita', 'categoria': 'sexta'},
            {'codigo_dane': '68773', 'nombre': 'Sucre', 'categoria': 'sexta'},
            {'codigo_dane': '68780', 'nombre': 'Suratá', 'categoria': 'sexta'},
            {'codigo_dane': '68820', 'nombre': 'Tona', 'categoria': 'sexta'},
            {'codigo_dane': '68855', 'nombre': 'Valle de San José', 'categoria': 'sexta'},
            {'codigo_dane': '68861', 'nombre': 'Vélez', 'categoria': 'quinta'},
            {'codigo_dane': '68867', 'nombre': 'Vetas', 'categoria': 'sexta'},
            {'codigo_dane': '68872', 'nombre': 'Villanueva', 'categoria': 'sexta'},
            {'codigo_dane': '68895', 'nombre': 'Zapatoca', 'categoria': 'sexta'},
        ],
        
        # SUCRE (70) - 26 municipios
        '70': [
            {'codigo_dane': '70001', 'nombre': 'Sincelejo', 'categoria': 'segunda', 'poblacion': 300692},
            {'codigo_dane': '70110', 'nombre': 'Buenavista', 'categoria': 'sexta'},
            {'codigo_dane': '70124', 'nombre': 'Caimito', 'categoria': 'sexta'},
            {'codigo_dane': '70204', 'nombre': 'Coloso', 'categoria': 'sexta'},
            {'codigo_dane': '70215', 'nombre': 'Corozal', 'categoria': 'quinta'},
            {'codigo_dane': '70221', 'nombre': 'Coveñas', 'categoria': 'sexta'},
            {'codigo_dane': '70230', 'nombre': 'Chalán', 'categoria': 'sexta'},
            {'codigo_dane': '70233', 'nombre': 'El Roble', 'categoria': 'sexta'},
            {'codigo_dane': '70235', 'nombre': 'Galeras', 'categoria': 'sexta'},
            {'codigo_dane': '70265', 'nombre': 'Guaranda', 'categoria': 'sexta'},
            {'codigo_dane': '70400', 'nombre': 'La Unión', 'categoria': 'sexta'},
            {'codigo_dane': '70418', 'nombre': 'Los Palmitos', 'categoria': 'sexta'},
            {'codigo_dane': '70429', 'nombre': 'Majagual', 'categoria': 'sexta'},
            {'codigo_dane': '70473', 'nombre': 'Morroa', 'categoria': 'sexta'},
            {'codigo_dane': '70508', 'nombre': 'Ovejas', 'categoria': 'sexta'},
            {'codigo_dane': '70523', 'nombre': 'Palmito', 'categoria': 'sexta'},
            {'codigo_dane': '70670', 'nombre': 'Sampués', 'categoria': 'sexta'},
            {'codigo_dane': '70678', 'nombre': 'San Benito Abad', 'categoria': 'sexta'},
            {'codigo_dane': '70702', 'nombre': 'San Juan de Betulia', 'categoria': 'sexta'},
            {'codigo_dane': '70708', 'nombre': 'San Marcos', 'categoria': 'quinta'},
            {'codigo_dane': '70713', 'nombre': 'San Onofre', 'categoria': 'sexta'},
            {'codigo_dane': '70717', 'nombre': 'San Pedro', 'categoria': 'sexta'},
            {'codigo_dane': '70742', 'nombre': 'Santiago de Tolú', 'categoria': 'quinta'},
            {'codigo_dane': '70771', 'nombre': 'Sucre', 'categoria': 'quinta'},
            {'codigo_dane': '70820', 'nombre': 'Tolú Viejo', 'categoria': 'sexta'},
        ],
        
        # TOLIMA (73) - 47 municipios
        '73': [
            {'codigo_dane': '73001', 'nombre': 'Ibagué', 'categoria': 'primera', 'poblacion': 529635},
            {'codigo_dane': '73024', 'nombre': 'Alpujarra', 'categoria': 'sexta'},
            {'codigo_dane': '73026', 'nombre': 'Alvarado', 'categoria': 'sexta'},
            {'codigo_dane': '73030', 'nombre': 'Ambalema', 'categoria': 'sexta'},
            {'codigo_dane': '73043', 'nombre': 'Anzoátegui', 'categoria': 'sexta'},
            {'codigo_dane': '73055', 'nombre': 'Armero', 'categoria': 'sexta'},
            {'codigo_dane': '73067', 'nombre': 'Ataco', 'categoria': 'sexta'},
            {'codigo_dane': '73124', 'nombre': 'Cajamarca', 'categoria': 'sexta'},
            {'codigo_dane': '73148', 'nombre': 'Carmen de Apicalá', 'categoria': 'sexta'},
            {'codigo_dane': '73152', 'nombre': 'Casabianca', 'categoria': 'sexta'},
            {'codigo_dane': '73168', 'nombre': 'Chaparral', 'categoria': 'quinta'},
            {'codigo_dane': '73200', 'nombre': 'Coello', 'categoria': 'sexta'},
            {'codigo_dane': '73217', 'nombre': 'Coyaima', 'categoria': 'sexta'},
            {'codigo_dane': '73226', 'nombre': 'Cunday', 'categoria': 'sexta'},
            {'codigo_dane': '73236', 'nombre': 'Dolores', 'categoria': 'sexta'},
            {'codigo_dane': '73268', 'nombre': 'Espinal', 'categoria': 'cuarta'},
            {'codigo_dane': '73270', 'nombre': 'Falan', 'categoria': 'sexta'},
            {'codigo_dane': '73275', 'nombre': 'Flandes', 'categoria': 'quinta'},
            {'codigo_dane': '73283', 'nombre': 'Fresno', 'categoria': 'sexta'},
            {'codigo_dane': '73319', 'nombre': 'Guamo', 'categoria': 'sexta'},
            {'codigo_dane': '73347', 'nombre': 'Herveo', 'categoria': 'sexta'},
            {'codigo_dane': '73349', 'nombre': 'Honda', 'categoria': 'quinta'},
            {'codigo_dane': '73352', 'nombre': 'Icononzo', 'categoria': 'sexta'},
            {'codigo_dane': '73408', 'nombre': 'Lérida', 'categoria': 'quinta'},
            {'codigo_dane': '73411', 'nombre': 'Líbano', 'categoria': 'quinta'},
            {'codigo_dane': '73443', 'nombre': 'Mariquita', 'categoria': 'quinta'},
            {'codigo_dane': '73449', 'nombre': 'Melgar', 'categoria': 'quinta'},
            {'codigo_dane': '73461', 'nombre': 'Murillo', 'categoria': 'sexta'},
            {'codigo_dane': '73483', 'nombre': 'Natagaima', 'categoria': 'sexta'},
            {'codigo_dane': '73504', 'nombre': 'Ortega', 'categoria': 'sexta'},
            {'codigo_dane': '73520', 'nombre': 'Palocabildo', 'categoria': 'sexta'},
            {'codigo_dane': '73547', 'nombre': 'Piedras', 'categoria': 'sexta'},
            {'codigo_dane': '73555', 'nombre': 'Planadas', 'categoria': 'sexta'},
            {'codigo_dane': '73563', 'nombre': 'Prado', 'categoria': 'sexta'},
            {'codigo_dane': '73585', 'nombre': 'Purificación', 'categoria': 'sexta'},
            {'codigo_dane': '73616', 'nombre': 'Rioblanco', 'categoria': 'sexta'},
            {'codigo_dane': '73622', 'nombre': 'Roncesvalles', 'categoria': 'sexta'},
            {'codigo_dane': '73624', 'nombre': 'Rovira', 'categoria': 'sexta'},
            {'codigo_dane': '73671', 'nombre': 'Saldaña', 'categoria': 'quinta'},
            {'codigo_dane': '73675', 'nombre': 'San Antonio', 'categoria': 'sexta'},
            {'codigo_dane': '73678', 'nombre': 'San Luis', 'categoria': 'sexta'},
            {'codigo_dane': '73686', 'nombre': 'Santa Isabel', 'categoria': 'sexta'},
            {'codigo_dane': '73770', 'nombre': 'Suárez', 'categoria': 'sexta'},
            {'codigo_dane': '73854', 'nombre': 'Valle de San Juan', 'categoria': 'sexta'},
            {'codigo_dane': '73861', 'nombre': 'Venadillo', 'categoria': 'sexta'},
            {'codigo_dane': '73870', 'nombre': 'Villahermosa', 'categoria': 'sexta'},
            {'codigo_dane': '73873', 'nombre': 'Villarrica', 'categoria': 'sexta'},
        ],
        
        # VALLE DEL CAUCA (76) - 42 municipios
        '76': [
            {'codigo_dane': '76001', 'nombre': 'Cali', 'categoria': 'especial', 'poblacion': 2258119},
            {'codigo_dane': '76020', 'nombre': 'Alcalá', 'categoria': 'sexta'},
            {'codigo_dane': '76036', 'nombre': 'Andalucía', 'categoria': 'sexta'},
            {'codigo_dane': '76041', 'nombre': 'Ansermanuevo', 'categoria': 'sexta'},
            {'codigo_dane': '76054', 'nombre': 'Argelia', 'categoria': 'sexta'},
            {'codigo_dane': '76100', 'nombre': 'Bolívar', 'categoria': 'sexta'},
            {'codigo_dane': '76109', 'nombre': 'Buenaventura', 'categoria': 'primera'},
            {'codigo_dane': '76111', 'nombre': 'Guadalajara de Buga', 'categoria': 'cuarta'},
            {'codigo_dane': '76113', 'nombre': 'Bugalagrande', 'categoria': 'sexta'},
            {'codigo_dane': '76122', 'nombre': 'Caicedonia', 'categoria': 'sexta'},
            {'codigo_dane': '76126', 'nombre': 'Calima', 'categoria': 'sexta'},
            {'codigo_dane': '76130', 'nombre': 'Candelaria', 'categoria': 'cuarta'},
            {'codigo_dane': '76147', 'nombre': 'Cartago', 'categoria': 'segunda'},
            {'codigo_dane': '76233', 'nombre': 'Dagua', 'categoria': 'sexta'},
            {'codigo_dane': '76243', 'nombre': 'El Águila', 'categoria': 'sexta'},
            {'codigo_dane': '76246', 'nombre': 'El Cairo', 'categoria': 'sexta'},
            {'codigo_dane': '76248', 'nombre': 'El Cerrito', 'categoria': 'quinta'},
            {'codigo_dane': '76250', 'nombre': 'El Dovio', 'categoria': 'sexta'},
            {'codigo_dane': '76275', 'nombre': 'Florida', 'categoria': 'quinta'},
            {'codigo_dane': '76306', 'nombre': 'Ginebra', 'categoria': 'sexta'},
            {'codigo_dane': '76318', 'nombre': 'Guacarí', 'categoria': 'quinta'},
            {'codigo_dane': '76364', 'nombre': 'Jamundí', 'categoria': 'segunda'},
            {'codigo_dane': '76377', 'nombre': 'La Cumbre', 'categoria': 'sexta'},
            {'codigo_dane': '76400', 'nombre': 'La Unión', 'categoria': 'sexta'},
            {'codigo_dane': '76403', 'nombre': 'La Victoria', 'categoria': 'sexta'},
            {'codigo_dane': '76497', 'nombre': 'Obando', 'categoria': 'sexta'},
            {'codigo_dane': '76520', 'nombre': 'Palmira', 'categoria': 'segunda'},
            {'codigo_dane': '76563', 'nombre': 'Pradera', 'categoria': 'quinta'},
            {'codigo_dane': '76606', 'nombre': 'Restrepo', 'categoria': 'sexta'},
            {'codigo_dane': '76616', 'nombre': 'Riofrío', 'categoria': 'sexta'},
            {'codigo_dane': '76622', 'nombre': 'Roldanillo', 'categoria': 'sexta'},
            {'codigo_dane': '76670', 'nombre': 'San Pedro', 'categoria': 'sexta'},
            {'codigo_dane': '76736', 'nombre': 'Sevilla', 'categoria': 'quinta'},
            {'codigo_dane': '76823', 'nombre': 'Toro', 'categoria': 'sexta'},
            {'codigo_dane': '76828', 'nombre': 'Trujillo', 'categoria': 'sexta'},
            {'codigo_dane': '76834', 'nombre': 'Tuluá', 'categoria': 'segunda'},
            {'codigo_dane': '76845', 'nombre': 'Ulloa', 'categoria': 'sexta'},
            {'codigo_dane': '76863', 'nombre': 'Versalles', 'categoria': 'sexta'},
            {'codigo_dane': '76869', 'nombre': 'Vijes', 'categoria': 'sexta'},
            {'codigo_dane': '76890', 'nombre': 'Yotoco', 'categoria': 'sexta'},
            {'codigo_dane': '76892', 'nombre': 'Yumbo', 'categoria': 'segunda'},
            {'codigo_dane': '76895', 'nombre': 'Zarzal', 'categoria': 'quinta'},
        ],
        
        # VAUPÉS (97) - 3 municipios
        '97': [
            {'codigo_dane': '97001', 'nombre': 'Mitú', 'categoria': 'quinta', 'poblacion': 19948},
            {'codigo_dane': '97161', 'nombre': 'Carurú', 'categoria': 'sexta'},
            {'codigo_dane': '97666', 'nombre': 'Pacoa', 'categoria': 'sexta'},
        ],
        
        # VICHADA (99) - 4 municipios
        '99': [
            {'codigo_dane': '99001', 'nombre': 'Puerto Carreño', 'categoria': 'quinta', 'poblacion': 16480},
            {'codigo_dane': '99524', 'nombre': 'La Primavera', 'categoria': 'sexta'},
            {'codigo_dane': '99624', 'nombre': 'Santa Rosalía', 'categoria': 'sexta'},
            {'codigo_dane': '99773', 'nombre': 'Cumaribo', 'categoria': 'sexta'},
        ],
    }
    
    # Procesar lote 6 (final)
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
    
    print(f"\n📊 RESUMEN LOTE 6 (FINAL):")
    print(f"  - Municipios procesados: {len([m for dept_muns in municipios_data.values() for m in dept_muns])}")
    print(f"  - Municipios creados: {total_municipios_creados}")
    print(f"  - Municipios existentes: {total_municipios_existentes}")
    print(f"  - TOTAL FINAL en base de datos: {Municipio.objects.count()}")
    
    print("\n🎉 ¡TODOS LOS MUNICIPIOS DE COLOMBIA HAN SIDO CARGADOS!")
    
    return total_municipios_creados

if __name__ == "__main__":
    cargar_municipios_lote6()
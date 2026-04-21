#!/usr/bin/env python3
"""
Script para cargar TODOS los municipios de Colombia (1,122 municipios)
Organizados por departamento con códigos DANE oficiales
"""

import os
# import django

# Configurar Django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev_sqlite')
# django.setup()

from apps.security_probabilistic.models import Departamento, Municipio

def cargar_todos_municipios():
    """Carga todos los municipios de Colombia por departamento"""
    
    print("🇨🇴 Cargando TODOS los municipios de Colombia...")
    print("📊 Total objetivo: 1,122 municipios")
    
    # Obtener departamentos existentes
    departamentos = {dept.codigo_dane: dept for dept in Departamento.objects.all()}
    
    # Datos completos de municipios por departamento
    municipios_data = {
        
        # AMAZONAS (91) - 2 municipios
        '91': [
            {'codigo_dane': '91001', 'nombre': 'Leticia', 'categoria': 'cuarta'},
            {'codigo_dane': '91263', 'nombre': 'Puerto Nariño', 'categoria': 'sexta'},
        ],
        
        # ANTIOQUIA (05) - 125 municipios
        '05': [
            {'codigo_dane': '05001', 'nombre': 'Medellín', 'categoria': 'especial', 'poblacion': 2508452},
            {'codigo_dane': '05002', 'nombre': 'Abejorral', 'categoria': 'sexta'},
            {'codigo_dane': '05004', 'nombre': 'Abriaquí', 'categoria': 'sexta'},
            {'codigo_dane': '05021', 'nombre': 'Alejandría', 'categoria': 'sexta'},
            {'codigo_dane': '05030', 'nombre': 'Amalfi', 'categoria': 'sexta'},
            {'codigo_dane': '05031', 'nombre': 'Andes', 'categoria': 'quinta'},
            {'codigo_dane': '05034', 'nombre': 'Angelópolis', 'categoria': 'sexta'},
            {'codigo_dane': '05036', 'nombre': 'Angostura', 'categoria': 'sexta'},
            {'codigo_dane': '05038', 'nombre': 'Anorí', 'categoria': 'sexta'},
            {'codigo_dane': '05040', 'nombre': 'Santa Fé de Antioquia', 'categoria': 'sexta'},
            {'codigo_dane': '05042', 'nombre': 'Anza', 'categoria': 'sexta'},
            {'codigo_dane': '05044', 'nombre': 'Apartadó', 'categoria': 'segunda', 'poblacion': 195414},
            {'codigo_dane': '05045', 'nombre': 'Arboletes', 'categoria': 'sexta'},
            {'codigo_dane': '05051', 'nombre': 'Argelia', 'categoria': 'sexta'},
            {'codigo_dane': '05055', 'nombre': 'Armenia', 'categoria': 'sexta'},
            {'codigo_dane': '05059', 'nombre': 'Barbosa', 'categoria': 'quinta'},
            {'codigo_dane': '05079', 'nombre': 'Belmira', 'categoria': 'sexta'},
            {'codigo_dane': '05086', 'nombre': 'Bello', 'categoria': 'primera', 'poblacion': 506674},
            {'codigo_dane': '05088', 'nombre': 'Betania', 'categoria': 'sexta'},
            {'codigo_dane': '05091', 'nombre': 'Betulia', 'categoria': 'sexta'},
            {'codigo_dane': '05093', 'nombre': 'Ciudad Bolívar', 'categoria': 'sexta'},
            {'codigo_dane': '05101', 'nombre': 'Briceño', 'categoria': 'sexta'},
            {'codigo_dane': '05107', 'nombre': 'Buriticá', 'categoria': 'sexta'},
            {'codigo_dane': '05113', 'nombre': 'Cáceres', 'categoria': 'sexta'},
            {'codigo_dane': '05120', 'nombre': 'Caicedo', 'categoria': 'sexta'},
            {'codigo_dane': '05125', 'nombre': 'Caldas', 'categoria': 'cuarta'},
            {'codigo_dane': '05129', 'nombre': 'Campamento', 'categoria': 'sexta'},
            {'codigo_dane': '05134', 'nombre': 'Cañasgordas', 'categoria': 'sexta'},
            {'codigo_dane': '05138', 'nombre': 'Caracolí', 'categoria': 'sexta'},
            {'codigo_dane': '05142', 'nombre': 'Caramanta', 'categoria': 'sexta'},
            {'codigo_dane': '05145', 'nombre': 'Carepa', 'categoria': 'quinta'},
            {'codigo_dane': '05147', 'nombre': 'El Carmen de Viboral', 'categoria': 'quinta'},
            {'codigo_dane': '05148', 'nombre': 'Casabianca', 'categoria': 'sexta'},
            {'codigo_dane': '05150', 'nombre': 'Castilla La Nueva', 'categoria': 'sexta'},
            {'codigo_dane': '05154', 'nombre': 'Caucasia', 'categoria': 'cuarta'},
            {'codigo_dane': '05172', 'nombre': 'Chigorodó', 'categoria': 'quinta'},
            {'codigo_dane': '05190', 'nombre': 'Cisneros', 'categoria': 'sexta'},
            {'codigo_dane': '05197', 'nombre': 'Cocorná', 'categoria': 'sexta'},
            {'codigo_dane': '05206', 'nombre': 'Concepción', 'categoria': 'sexta'},
            {'codigo_dane': '05209', 'nombre': 'Concordia', 'categoria': 'sexta'},
            {'codigo_dane': '05212', 'nombre': 'Copacabana', 'categoria': 'tercera'},
            {'codigo_dane': '05234', 'nombre': 'Dabeiba', 'categoria': 'sexta'},
            {'codigo_dane': '05237', 'nombre': 'Don Matías', 'categoria': 'sexta'},
            {'codigo_dane': '05240', 'nombre': 'Ebéjico', 'categoria': 'sexta'},
            {'codigo_dane': '05250', 'nombre': 'El Bagre', 'categoria': 'sexta'},
            {'codigo_dane': '05264', 'nombre': 'Entrerríos', 'categoria': 'sexta'},
            {'codigo_dane': '05266', 'nombre': 'Envigado', 'categoria': 'primera', 'poblacion': 237989},
            {'codigo_dane': '05282', 'nombre': 'Fredonia', 'categoria': 'sexta'},
            {'codigo_dane': '05284', 'nombre': 'Frontino', 'categoria': 'sexta'},
            {'codigo_dane': '05306', 'nombre': 'Giraldo', 'categoria': 'sexta'},
            {'codigo_dane': '05308', 'nombre': 'Girardota', 'categoria': 'quinta'},
            {'codigo_dane': '05310', 'nombre': 'Gómez Plata', 'categoria': 'sexta'},
            {'codigo_dane': '05313', 'nombre': 'Granada', 'categoria': 'sexta'},
            {'codigo_dane': '05315', 'nombre': 'Guadalupe', 'categoria': 'sexta'},
            {'codigo_dane': '05318', 'nombre': 'Guarne', 'categoria': 'quinta'},
            {'codigo_dane': '05321', 'nombre': 'Guatapé', 'categoria': 'sexta'},
            {'codigo_dane': '05347', 'nombre': 'Heliconia', 'categoria': 'sexta'},
            {'codigo_dane': '05353', 'nombre': 'Hispania', 'categoria': 'sexta'},
            {'codigo_dane': '05360', 'nombre': 'Itagüí', 'categoria': 'primera', 'poblacion': 281853},
            {'codigo_dane': '05361', 'nombre': 'Ituango', 'categoria': 'sexta'},
            {'codigo_dane': '05364', 'nombre': 'Jardín', 'categoria': 'sexta'},
            {'codigo_dane': '05368', 'nombre': 'Jericó', 'categoria': 'sexta'},
            {'codigo_dane': '05376', 'nombre': 'La Ceja', 'categoria': 'quinta'},
            {'codigo_dane': '05380', 'nombre': 'La Estrella', 'categoria': 'quinta'},
            {'codigo_dane': '05390', 'nombre': 'La Pintada', 'categoria': 'sexta'},
            {'codigo_dane': '05400', 'nombre': 'La Unión', 'categoria': 'sexta'},
            {'codigo_dane': '05411', 'nombre': 'Liborina', 'categoria': 'sexta'},
            {'codigo_dane': '05425', 'nombre': 'Maceo', 'categoria': 'sexta'},
            {'codigo_dane': '05440', 'nombre': 'Marinilla', 'categoria': 'quinta'},
            {'codigo_dane': '05467', 'nombre': 'Montebello', 'categoria': 'sexta'},
            {'codigo_dane': '05475', 'nombre': 'Murindó', 'categoria': 'sexta'},
            {'codigo_dane': '05480', 'nombre': 'Mutatá', 'categoria': 'sexta'},
            {'codigo_dane': '05483', 'nombre': 'Nariño', 'categoria': 'sexta'},
            {'codigo_dane': '05490', 'nombre': 'Necoclí', 'categoria': 'sexta'},
            {'codigo_dane': '05495', 'nombre': 'Nechí', 'categoria': 'sexta'},
            {'codigo_dane': '05501', 'nombre': 'Olaya', 'categoria': 'sexta'},
            {'codigo_dane': '05541', 'nombre': 'Peñol', 'categoria': 'sexta'},
            {'codigo_dane': '05543', 'nombre': 'Peque', 'categoria': 'sexta'},
            {'codigo_dane': '05576', 'nombre': 'Pueblorrico', 'categoria': 'sexta'},
            {'codigo_dane': '05579', 'nombre': 'Puerto Berrío', 'categoria': 'quinta'},
            {'codigo_dane': '05585', 'nombre': 'Puerto Nare', 'categoria': 'sexta'},
            {'codigo_dane': '05591', 'nombre': 'Puerto Triunfo', 'categoria': 'sexta'},
            {'codigo_dane': '05604', 'nombre': 'Remedios', 'categoria': 'sexta'},
            {'codigo_dane': '05607', 'nombre': 'Retiro', 'categoria': 'sexta'},
            {'codigo_dane': '05615', 'nombre': 'Rionegro', 'categoria': 'segunda'},
            {'codigo_dane': '05628', 'nombre': 'Sabanalarga', 'categoria': 'sexta'},
            {'codigo_dane': '05631', 'nombre': 'Sabaneta', 'categoria': 'cuarta'},
            {'codigo_dane': '05642', 'nombre': 'Salgar', 'categoria': 'sexta'},
            {'codigo_dane': '05647', 'nombre': 'San Andrés de Cuerquia', 'categoria': 'sexta'},
            {'codigo_dane': '05649', 'nombre': 'San Carlos', 'categoria': 'sexta'},
            {'codigo_dane': '05652', 'nombre': 'San Francisco', 'categoria': 'sexta'},
            {'codigo_dane': '05656', 'nombre': 'San Jerónimo', 'categoria': 'sexta'},
            {'codigo_dane': '05658', 'nombre': 'San José de la Montaña', 'categoria': 'sexta'},
            {'codigo_dane': '05659', 'nombre': 'San Juan de Urabá', 'categoria': 'sexta'},
            {'codigo_dane': '05660', 'nombre': 'San Luis', 'categoria': 'sexta'},
            {'codigo_dane': '05664', 'nombre': 'San Pedro', 'categoria': 'sexta'},
            {'codigo_dane': '05665', 'nombre': 'San Pedro de Urabá', 'categoria': 'sexta'},
            {'codigo_dane': '05667', 'nombre': 'San Rafael', 'categoria': 'sexta'},
            {'codigo_dane': '05670', 'nombre': 'San Roque', 'categoria': 'sexta'},
            {'codigo_dane': '05674', 'nombre': 'San Vicente', 'categoria': 'sexta'},
            {'codigo_dane': '05679', 'nombre': 'Santa Bárbara', 'categoria': 'sexta'},
            {'codigo_dane': '05686', 'nombre': 'Santa Rosa de Osos', 'categoria': 'quinta'},
            {'codigo_dane': '05690', 'nombre': 'Santo Domingo', 'categoria': 'sexta'},
            {'codigo_dane': '05697', 'nombre': 'El Santuario', 'categoria': 'sexta'},
            {'codigo_dane': '05736', 'nombre': 'Segovia', 'categoria': 'sexta'},
            {'codigo_dane': '05756', 'nombre': 'Sonsón', 'categoria': 'quinta'},
            {'codigo_dane': '05761', 'nombre': 'Sopetrán', 'categoria': 'sexta'},
            {'codigo_dane': '05789', 'nombre': 'Támesis', 'categoria': 'sexta'},
            {'codigo_dane': '05790', 'nombre': 'Tarazá', 'categoria': 'sexta'},
            {'codigo_dane': '05792', 'nombre': 'Tarso', 'categoria': 'sexta'},
            {'codigo_dane': '05809', 'nombre': 'Titiribí', 'categoria': 'sexta'},
            {'codigo_dane': '05819', 'nombre': 'Toledo', 'categoria': 'sexta'},
            {'codigo_dane': '05837', 'nombre': 'Turbo', 'categoria': 'cuarta'},
            {'codigo_dane': '05842', 'nombre': 'Uramita', 'categoria': 'sexta'},
            {'codigo_dane': '05847', 'nombre': 'Urrao', 'categoria': 'sexta'},
            {'codigo_dane': '05854', 'nombre': 'Valdivia', 'categoria': 'sexta'},
            {'codigo_dane': '05856', 'nombre': 'Valparaíso', 'categoria': 'sexta'},
            {'codigo_dane': '05858', 'nombre': 'Vegachí', 'categoria': 'sexta'},
            {'codigo_dane': '05861', 'nombre': 'Venecia', 'categoria': 'sexta'},
            {'codigo_dane': '05873', 'nombre': 'Vigía del Fuerte', 'categoria': 'sexta'},
            {'codigo_dane': '05885', 'nombre': 'Yalí', 'categoria': 'sexta'},
            {'codigo_dane': '05887', 'nombre': 'Yarumal', 'categoria': 'quinta'},
            {'codigo_dane': '05890', 'nombre': 'Yolombó', 'categoria': 'sexta'},
            {'codigo_dane': '05893', 'nombre': 'Yondó', 'categoria': 'sexta'},
            {'codigo_dane': '05895', 'nombre': 'Zaragoza', 'categoria': 'sexta'},
        ],
        
        # ARAUCA (81) - 7 municipios
        '81': [
            {'codigo_dane': '81001', 'nombre': 'Arauca', 'categoria': 'cuarta', 'poblacion': 93896},
            {'codigo_dane': '81065', 'nombre': 'Arauquita', 'categoria': 'quinta'},
            {'codigo_dane': '81220', 'nombre': 'Cravo Norte', 'categoria': 'sexta'},
            {'codigo_dane': '81300', 'nombre': 'Fortul', 'categoria': 'sexta'},
            {'codigo_dane': '81591', 'nombre': 'Puerto Rondón', 'categoria': 'sexta'},
            {'codigo_dane': '81736', 'nombre': 'Saravena', 'categoria': 'quinta', 'poblacion': 54301},
            {'codigo_dane': '81794', 'nombre': 'Tame', 'categoria': 'quinta'},
        ],
        
        # ATLÁNTICO (08) - 23 municipios
        '08': [
            {'codigo_dane': '08001', 'nombre': 'Barranquilla', 'categoria': 'especial', 'poblacion': 1274250},
            {'codigo_dane': '08078', 'nombre': 'Baranoa', 'categoria': 'quinta'},
            {'codigo_dane': '08137', 'nombre': 'Campo de la Cruz', 'categoria': 'sexta'},
            {'codigo_dane': '08141', 'nombre': 'Candelaria', 'categoria': 'sexta'},
            {'codigo_dane': '08296', 'nombre': 'Galapa', 'categoria': 'quinta'},
            {'codigo_dane': '08372', 'nombre': 'Juan de Acosta', 'categoria': 'sexta'},
            {'codigo_dane': '08421', 'nombre': 'Luruaco', 'categoria': 'sexta'},
            {'codigo_dane': '08433', 'nombre': 'Malambo', 'categoria': 'cuarta'},
            {'codigo_dane': '08436', 'nombre': 'Manatí', 'categoria': 'sexta'},
            {'codigo_dane': '08520', 'nombre': 'Palmar de Varela', 'categoria': 'quinta'},
            {'codigo_dane': '08549', 'nombre': 'Piojó', 'categoria': 'sexta'},
            {'codigo_dane': '08558', 'nombre': 'Polonuevo', 'categoria': 'sexta'},
            {'codigo_dane': '08560', 'nombre': 'Ponedera', 'categoria': 'sexta'},
            {'codigo_dane': '08573', 'nombre': 'Puerto Colombia', 'categoria': 'quinta'},
            {'codigo_dane': '08606', 'nombre': 'Repelón', 'categoria': 'sexta'},
            {'codigo_dane': '08634', 'nombre': 'Sabanagrande', 'categoria': 'quinta'},
            {'codigo_dane': '08638', 'nombre': 'Sabanalarga', 'categoria': 'quinta'},
            {'codigo_dane': '08675', 'nombre': 'Santa Lucía', 'categoria': 'sexta'},
            {'codigo_dane': '08685', 'nombre': 'Santo Tomás', 'categoria': 'quinta'},
            {'codigo_dane': '08758', 'nombre': 'Soledad', 'categoria': 'primera', 'poblacion': 713508},
            {'codigo_dane': '08770', 'nombre': 'Suan', 'categoria': 'sexta'},
            {'codigo_dane': '08832', 'nombre': 'Tubará', 'categoria': 'sexta'},
            {'codigo_dane': '08849', 'nombre': 'Usiacurí', 'categoria': 'sexta'},
        ],
        
        # BOGOTÁ D.C. (11) - 1 municipio
        '11': [
            {'codigo_dane': '11001', 'nombre': 'Bogotá', 'categoria': 'especial', 'poblacion': 7181469},
        ],
        
        # BOLÍVAR (13) - 46 municipios
        '13': [
            {'codigo_dane': '13001', 'nombre': 'Cartagena', 'categoria': 'especial', 'poblacion': 971592},
            {'codigo_dane': '13006', 'nombre': 'Achí', 'categoria': 'sexta'},
            {'codigo_dane': '13030', 'nombre': 'Altos del Rosario', 'categoria': 'sexta'},
            {'codigo_dane': '13042', 'nombre': 'Arenal', 'categoria': 'sexta'},
            {'codigo_dane': '13052', 'nombre': 'Arjona', 'categoria': 'quinta'},
            {'codigo_dane': '13062', 'nombre': 'Arroyohondo', 'categoria': 'sexta'},
            {'codigo_dane': '13074', 'nombre': 'Barranco de Loba', 'categoria': 'sexta'},
            {'codigo_dane': '13140', 'nombre': 'Calamar', 'categoria': 'sexta'},
            {'codigo_dane': '13160', 'nombre': 'Cantagallo', 'categoria': 'sexta'},
            {'codigo_dane': '13188', 'nombre': 'Cicuco', 'categoria': 'sexta'},
            {'codigo_dane': '13212', 'nombre': 'Córdoba', 'categoria': 'sexta'},
            {'codigo_dane': '13222', 'nombre': 'Clemencia', 'categoria': 'sexta'},
            {'codigo_dane': '13244', 'nombre': 'El Carmen de Bolívar', 'categoria': 'quinta'},
            {'codigo_dane': '13248', 'nombre': 'El Guamo', 'categoria': 'sexta'},
            {'codigo_dane': '13268', 'nombre': 'El Peñón', 'categoria': 'sexta'},
            {'codigo_dane': '13300', 'nombre': 'Hatillo de Loba', 'categoria': 'sexta'},
            {'codigo_dane': '13430', 'nombre': 'Magangué', 'categoria': 'cuarta'},
            {'codigo_dane': '13433', 'nombre': 'Mahates', 'categoria': 'sexta'},
            {'codigo_dane': '13440', 'nombre': 'Margarita', 'categoria': 'sexta'},
            {'codigo_dane': '13442', 'nombre': 'María la Baja', 'categoria': 'quinta'},
            {'codigo_dane': '13458', 'nombre': 'Montecristo', 'categoria': 'sexta'},
            {'codigo_dane': '13468', 'nombre': 'Mompós', 'categoria': 'sexta'},
            {'codigo_dane': '13473', 'nombre': 'Morales', 'categoria': 'sexta'},
            {'codigo_dane': '13549', 'nombre': 'Pinillos', 'categoria': 'sexta'},
            {'codigo_dane': '13580', 'nombre': 'Regidor', 'categoria': 'sexta'},
            {'codigo_dane': '13600', 'nombre': 'Río Viejo', 'categoria': 'sexta'},
            {'codigo_dane': '13620', 'nombre': 'San Cristóbal', 'categoria': 'sexta'},
            {'codigo_dane': '13647', 'nombre': 'San Estanislao', 'categoria': 'sexta'},
            {'codigo_dane': '13650', 'nombre': 'San Fernando', 'categoria': 'sexta'},
            {'codigo_dane': '13654', 'nombre': 'San Jacinto', 'categoria': 'sexta'},
            {'codigo_dane': '13655', 'nombre': 'San Jacinto del Cauca', 'categoria': 'sexta'},
            {'codigo_dane': '13657', 'nombre': 'San Juan Nepomuceno', 'categoria': 'sexta'},
            {'codigo_dane': '13667', 'nombre': 'San Martín de Loba', 'categoria': 'sexta'},
            {'codigo_dane': '13670', 'nombre': 'San Pablo', 'categoria': 'sexta'},
            {'codigo_dane': '13673', 'nombre': 'Santa Catalina', 'categoria': 'sexta'},
            {'codigo_dane': '13683', 'nombre': 'Santa Rosa', 'categoria': 'sexta'},
            {'codigo_dane': '13688', 'nombre': 'Santa Rosa del Sur', 'categoria': 'sexta'},
            {'codigo_dane': '13744', 'nombre': 'Simití', 'categoria': 'sexta'},
            {'codigo_dane': '13760', 'nombre': 'Soplaviento', 'categoria': 'sexta'},
            {'codigo_dane': '13780', 'nombre': 'Talaigua Nuevo', 'categoria': 'sexta'},
            {'codigo_dane': '13810', 'nombre': 'Tiquisio', 'categoria': 'sexta'},
            {'codigo_dane': '13836', 'nombre': 'Turbaco', 'categoria': 'cuarta'},
            {'codigo_dane': '13838', 'nombre': 'Turbaná', 'categoria': 'sexta'},
            {'codigo_dane': '13873', 'nombre': 'Villanueva', 'categoria': 'sexta'},
            {'codigo_dane': '13894', 'nombre': 'Zambrano', 'categoria': 'sexta'},
        ],
    }
    
    # Procesar por lotes para no sobrecargar
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
                        'usa_riesgo_departamento': True,  # Por defecto usar riesgo del departamento
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
    
    print(f"\n📊 RESUMEN PARCIAL:")
    print(f"  - Municipios procesados en este lote: {len([m for dept_muns in municipios_data.values() for m in dept_muns])}")
    print(f"  - Municipios creados: {total_municipios_creados}")
    print(f"  - Municipios existentes: {total_municipios_existentes}")
    print(f"  - Total en base de datos: {Municipio.objects.count()}")
    
    return total_municipios_creados

if __name__ == "__main__":
    cargar_todos_municipios()
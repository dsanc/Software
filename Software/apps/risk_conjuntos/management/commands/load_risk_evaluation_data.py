"""
Comando para cargar datos iniciales del sistema de evaluación de riesgos
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.risk_conjuntos.models import (
    TipoRiesgo, EscenarioRiesgo, CalificacionOpcion, PreguntaEvaluacion
)


class Command(BaseCommand):
    help = 'Carga datos iniciales del sistema de evaluación de riesgos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando carga de datos iniciales...'))
        
        try:
            with transaction.atomic():
                # Cargar opciones de calificación
                self.cargar_calificaciones()
                
                # Cargar tipos de riesgos
                self.cargar_tipos_riesgos()
                
                # Cargar escenarios
                self.cargar_escenarios()
                
                # Cargar preguntas de ejemplo
                self.cargar_preguntas_ejemplo()
                
            self.stdout.write(
                self.style.SUCCESS('✓ Datos iniciales cargados exitosamente!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error al cargar datos: {str(e)}')
            )

    def cargar_calificaciones(self):
        """Carga las opciones de calificación"""
        opciones = [
            {'codigo': 'ausente', 'nombre': 'Ausente', 'valor': 0.005, 'orden': 1},
            {'codigo': 'deficiente', 'nombre': 'Deficiente', 'valor': 0.1, 'orden': 2},
            {'codigo': 'vulnerable', 'nombre': 'Vulnerable', 'valor': 0.25, 'orden': 3},
            {'codigo': 'adecuado', 'nombre': 'Adecuado', 'valor': 0.6, 'orden': 4},
            {'codigo': 'eficaz', 'nombre': 'Eficaz', 'valor': 0.9, 'orden': 5},
        ]
        
        for opcion in opciones:
            CalificacionOpcion.objects.get_or_create(
                codigo=opcion['codigo'],
                defaults=opcion
            )
        
        self.stdout.write('  ✓ Opciones de calificación cargadas')

    def cargar_tipos_riesgos(self):
        """Carga los tipos de riesgos"""
        tipos = [
            {'codigo': 'intrusion_general', 'nombre': 'Intrusión General', 'orden': 1},
            {'codigo': 'conspiracion_intrusion', 'nombre': 'Conspiración Para Intrusión', 'orden': 2},
            {'codigo': 'intrusion_unidad', 'nombre': 'Intrusión Unidad Residencial', 'orden': 3},
            {'codigo': 'robo_vehiculos', 'nombre': 'Robo De Vehículos', 'orden': 4},
            {'codigo': 'robo_bicicletas', 'nombre': 'Robo De Bicicletas', 'orden': 5},
            {'codigo': 'dano_areas_comunes', 'nombre': 'Daño En Áreas Comunes', 'orden': 6},
            {'codigo': 'conflictos_parqueos', 'nombre': 'Conflictos Por Mal Uso De Parqueos', 'orden': 7},
            {'codigo': 'sustraccion_bienes', 'nombre': 'Sustracción De Bienes De Apartamentos', 'orden': 8},
            {'codigo': 'secuestro', 'nombre': 'Secuestro', 'orden': 9},
        ]
        
        for tipo in tipos:
            TipoRiesgo.objects.get_or_create(
                codigo=tipo['codigo'],
                defaults=tipo
            )
        
        self.stdout.write('  ✓ Tipos de riesgos cargados')

    def cargar_escenarios(self):
        """Carga los escenarios de riesgo"""
        # Mapeo de escenarios por tipo de riesgo
        escenarios_data = {
            'intrusion_general': [
                {'codigo': 'traspasando_cerramiento', 'nombre': 'Traspasando El Cerramiento Perimetral', 'orden': 1},
                {'codigo': 'debilidad_procedimiento', 'nombre': 'Por Debilidad Del Procedimiento De Ingreso', 'orden': 2},
                {'codigo': 'distraccion_vigilante', 'nombre': 'Distracción Al Vigilante', 'orden': 3},
                {'codigo': 'simultaneamente_autorizada', 'nombre': 'Pasando Simultáneamente Con Una Persona Autorizada', 'orden': 4},
                {'codigo': 'autorizacion_irresponsable', 'nombre': 'Autorización Irresponsable', 'orden': 5},
            ],
            'conspiracion_intrusion': [
                {'codigo': 'neutralizando_seguridad', 'nombre': 'Neutralizando Al Personal De Seguridad', 'orden': 1},
                {'codigo': 'coaccionando_residente', 'nombre': 'Coaccionando A Residente O Persona Autorizada', 'orden': 2},
                {'codigo': 'ingenieria_social', 'nombre': 'Por Ingeniería Social', 'orden': 3},
                {'codigo': 'sobrepasando_controles', 'nombre': 'Sobrepasando Los Controles De Acceso', 'orden': 4},
                {'codigo': 'suplantacion', 'nombre': 'Suplantación', 'orden': 5},
            ],
            'intrusion_unidad': [
                {'codigo': 'residente', 'nombre': 'Residente', 'orden': 1},
                {'codigo': 'empleado_interno', 'nombre': 'Empleado Interno O Prestador De Servicios', 'orden': 2},
                {'codigo': 'violando_puerta_principal', 'nombre': 'Violando La Seguridad De La Puerta Principal', 'orden': 3},
                {'codigo': 'acceso_ventanas_balcones', 'nombre': 'Por Acceso Por Ventanas O Balcones', 'orden': 4},
                {'codigo': 'ventosa_ruptura_paredes', 'nombre': 'Por ventosa o ruptura de paredes', 'orden': 5},
                {'codigo': 'acceso_violento_persona', 'nombre': 'Por Acceso Violento A Persona Que Abre La Puerta', 'orden': 6},
                {'codigo': 'suplantacion_residente', 'nombre': 'Por Suplantación Del Residente', 'orden': 7},
                {'codigo': 'sometimiento_residente', 'nombre': 'Por Sometimiento Del Residente', 'orden': 8},
            ],
            'robo_vehiculos': [
                {'codigo': 'salida_violenta', 'nombre': 'Por Salida Violenta', 'orden': 1},
                {'codigo': 'autorizacion_forzada', 'nombre': 'Por Autorización Forzada', 'orden': 2},
                {'codigo': 'acceso_simplificado', 'nombre': 'Acceso Simplificado A Las Mismas', 'orden': 3},
                {'codigo': 'salida_normal', 'nombre': 'Por Salida Normal', 'orden': 4},
            ],
            'robo_bicicletas': [
                {'codigo': 'autorizacion_suplantada', 'nombre': 'Por Autorización Suplantada', 'orden': 1},
                {'codigo': 'accion_interna', 'nombre': 'Por Acción Interna', 'orden': 2},
            ],
            'dano_areas_comunes': [
                {'codigo': 'accion_interna', 'nombre': 'Por Acción Interna', 'orden': 1},
            ],
            'conflictos_parqueos': [
                {'codigo': 'permisividad_parqueos_asignados', 'nombre': 'Permisividad En El Uso De Parqueos Asignados', 'orden': 1},
                {'codigo': 'permisividad_administracion_parqueaderos', 'nombre': 'Permisividad En La Administración De Pos Parqueaderos De Parte De Seguridad', 'orden': 2},
            ],
            'sustraccion_bienes': [
                {'codigo': 'retiro_porterias', 'nombre': 'Retiro Por Porterías', 'orden': 1},
                {'codigo': 'retiro_area_perimetral', 'nombre': 'Retiro Por El Área Perimetral', 'orden': 2},
            ],
            'secuestro': [
                {'codigo': 'salida_forzada_escoltas', 'nombre': 'Salida Forzada Suplantando A Escoltas', 'orden': 1},
                {'codigo': 'salida_forzada_familiaridad', 'nombre': 'Salida Forzada Sometido Por Una Persona Que Le Obliga A Comportarse Con Familiaridad', 'orden': 2},
                {'codigo': 'suplantando_servicios_medicos', 'nombre': 'Suplantando Servicios Médicos', 'orden': 3},
            ],
        }
        
        for tipo_codigo, escenarios in escenarios_data.items():
            try:
                tipo_riesgo = TipoRiesgo.objects.get(codigo=tipo_codigo)
                for escenario in escenarios:
                    EscenarioRiesgo.objects.get_or_create(
                        codigo=escenario['codigo'],
                        defaults={
                            'tipo_riesgo': tipo_riesgo,
                            'nombre': escenario['nombre'],
                            'orden': escenario['orden']
                        }
                    )
            except TipoRiesgo.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Tipo de riesgo no encontrado: {tipo_codigo}')
                )
        
        self.stdout.write('  ✓ Escenarios de riesgo cargados')

    def cargar_preguntas_ejemplo(self):
        """Carga preguntas de ejemplo para algunos escenarios"""
        preguntas_ejemplo = [
            {
                'escenario_codigo': 'traspasando_cerramiento',
                'preguntas': [
                    '¿Existe un cerramiento perimetral completo y en buen estado?',
                    '¿El cerramiento tiene la altura adecuada (mínimo 2.5 metros)?',
                    '¿Existen elementos de seguridad adicionales en el cerramiento (púas, alambre de púas, etc.)?',
                    '¿Se realiza mantenimiento regular del cerramiento perimetral?',
                ]
            },
            {
                'escenario_codigo': 'debilidad_procedimiento',
                'preguntas': [
                    '¿Existe un procedimiento escrito y claro para el ingreso de visitantes?',
                    '¿El personal de seguridad está capacitado en los procedimientos de ingreso?',
                    '¿Se verifica la identidad de todas las personas que ingresan?',
                    '¿Se lleva un registro de ingresos y salidas?',
                ]
            },
            {
                'escenario_codigo': 'violando_puerta_principal',
                'preguntas': [
                    '¿Las puertas de las unidades residenciales tienen cerraduras de seguridad?',
                    '¿Existen mirillas o sistemas de video portero en las puertas?',
                    '¿Las puertas están reforzadas y son resistentes?',
                    '¿Se han instalado sistemas de alarma en las unidades?',
                ]
            },
        ]
        
        for item in preguntas_ejemplo:
            try:
                escenario = EscenarioRiesgo.objects.get(codigo=item['escenario_codigo'])
                for i, pregunta_texto in enumerate(item['preguntas'], 1):
                    PreguntaEvaluacion.objects.get_or_create(
                        escenario=escenario,
                        texto_pregunta=pregunta_texto,
                        defaults={'orden': i}
                    )
            except EscenarioRiesgo.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Escenario no encontrado: {item["escenario_codigo"]}')
                )
        
        self.stdout.write('  ✓ Preguntas de ejemplo cargadas')
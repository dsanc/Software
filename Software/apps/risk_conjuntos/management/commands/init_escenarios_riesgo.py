from django.core.management.base import BaseCommand
from django.db import transaction
from apps.risk_conjuntos.models import TipoRiesgo, EscenarioRiesgo, PreguntaEvaluacion


class Command(BaseCommand):
    help = 'Inicializa los escenarios de riesgo, los relaciona con sus tipos de riesgo y crea las preguntas asociadas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué cambios se harían sin ejecutarlos',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reasignar escenarios existentes a nuevos tipos de riesgo si es necesario',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Simulando cambios...'))
        
        self.stdout.write(self.style.SUCCESS('Inicializando escenarios de riesgo...'))

        # Mapeo de tipos de riesgo -> escenarios con sus preguntas
        mapping = {
            'intrusion_general': {
                'traspasando_cerramiento': [
                    'El cerramiento perimetral dispone de una altura adecuada y una barrera física que retarde o dificulte efectivamente el acceso no autorizado',
                    'El cerramiento perimetral está dispuesto a lo largo de la instalación sin contar con puntos críticos',
                    'El cerramiento perimetral dispone de un sistema de detección perimetral efectivo para generar alertas y direcciona el punto exacto de la intrusión',
                    'El conjunto residencial tiene un sistema de recorridas perimetrales permanentes y suficiente que permite mantener al 100% controlado el perímetro por el campo visual de las personas de seguridad',
                    'Las áreas adyacentes al conjunto residencial, muestra o da una imagen de que su cerramiento perimetral es seguro, lo cual disuade efectivamente',
                    'Se dispone de un sistema efectivo de observación permanente del perímetro con baja probabilidad de fallo',
                    'La iluminación protectiva es adecuada para disuadir al delincuente y para facilitar la ventaja de observación al vigilante',
                ],
                'debilidad_procedimiento': [
                    'Se cuenta con un procedimiento de ingreso adecuado para evitar que personas puedan acceder valiéndose de las debilidades del procedimiento',
                    'El procedimiento de ingreso de personas involucra factores para que sean identificados positivamente los invitados, visitantes o contratistas que ingresan al conjunto residencial',
                    'El procedimiento de ingreso es bien aplicado por los residentes y no facilitan ingresos irresponsables de personas que no sean adecuadamente identificadas',
                    'El procedimiento de ingreso deja la evidencia inalterable de quien da la aprobación para el ingreso',
                    'El procedimiento de ingreso deja el registro adecuadamente de quien ingresó evitando o minimizando la suplantación',
                ],
                'distraccion_vigilante': [
                    'El vigilante está adecuadamente resguardado y dada su condición de hermeticidad es dificil que alguien pueda generarle una distracción que implique una intrusión',
                    'El puesto cumple con un modo de seguridad en el que un vigilante supervisa el ingreso sin tener participación en la autorización o no de la forma de acceso',
                ],
                'simultaneamente_autorizada': [
                    'El sistema de seguridad es adecuado dado que posee un diseño adecuado para garantizar el paso individual de cada residente evitando que pasen dos personas juntas',
                    'El sistema de seguridad permite identificar positivamente y efectivamente a las personas que acceden al interior de la unidad residencial',
                ],
                'autorizacion_irresponsable': [
                    'El procedimiento para validación de ingresos obliga a que la persona que autoriza, tenga plena certeza de quien está aspirando a seguir sea la persona que espera',
                    'El procedimiento para validación de ingresos permite dejar la evidencia o registro inalterable de la autorización',
                ],
                'neutralizando_seguridad': [
                    'El vigilante está adecuadamente resguardado ante personas que puedan acceder y neutralizarlo contando con un diseño que lo proteja de armas de fuego',
                    'El área de servicio del vigilante impide que este deba exponerse para atender al personal que llega a las instalaciones para ser atendidos',
                    'Todos los puestos de seguridad tienen la posibilidad de resguardarse ante una situación de posible amenaza',
                    'Se evita el ingreso de personas como domiciliarios que puedan quedar en contacto directo con el personal de seguridad',
                ],
                'coaccionando_residente': [
                    'Se tiene un procedimiento para validar que las autorizaciones de ingreso no sean hechas de manera irresponsable o coaccionadas',
                    'El sistema de seguridad permite dejar evidencia de quien autoriza el ingreso',
                    'Se tiene un procedimiento o mecanismo para advertir cuando un residente se encuentra bajo amenaza o intimidación',
                ],
                'ingenieria_social': [
                    'Se dispone de capacitaciones o mecanismos de alerta periódica para los residentes en donde se promuevan técnicas de prevención de llamada millonaria o advertencias sobre la ingeniería social',
                    'El personal de seguridad antes de dar acceso a personas desconocidas tiene dentro de su procedimiento algún mecanismo para identificar si el acceso podría estar viciado de algún tipo de acceso de ingeniería social',
                ],
                'sobrepasando_controles': [
                    'El sistema de control de acceso es suficiente para dificultar el paso abusivo por los bretes, torniquetes o demás sistemas de cierre',
                    'El sistema de control de accesos permite detectar cualquier intento de paso abusivo, alertando al personal de seguridad sobre este',
                ],
                'suplantacion': [
                    'Se tienen procedimientos o mecanismos para prevenir de que no ingresen personas con bajo nivel de confiabilidad como arrendatarios temporales, alquileres por plataformas de renta corta, entre otros?',
                    'Se tiene algún sistema para validar de que los arrendatarios de periodos cortos, sean adecuadamente seleccionados o validados en su confiabilidad',
                ],
            },
            'conspiracion_intrusion': {
                'residente': [
                    'Se tienen mecanismos para validar la confiabilidad de los residentes que permita identificar posibles conductas sospechosas',
                    'Se tienen sistemas para dejar el registro de las autorizaciones dadas por los residentes',
                ],
                'empleado_interno': [
                    'Se tienen mecanismos para validar la confiabilidad de los empleados y contratistas que pueden requerir ingresos de terceras personas',
                    'Se tienen sistemas para dejar el registro de las autorizaciones dadas por los empleados y contratistas autorizados',
                    'Se dispone de un procedimiento adecuado para determinar los casos en los que empleados y contratistas pueden requerir un ingreso de una persona y los mecanismos de validación con los que cuenta el vigilante',
                ],
            },
            'intrusion_unidad': {
                'violando_puerta_principal': [
                    'Se dispone de un estándar adecuado de seguridad en las puertas principales de reforzamiento estructural, cerraduras de seguridad y anclaje de los marcos',
                    'Se prohibe rotundamente que el personal de seguridad reciba llaves de los apartamentos que van a estar sus propietarios por fuera',
                    'Se dispone de un sistema de detección de violación de los sistemas de seguridad de la puerta principal, que genere una alarma oportunamente, permitiendo una respuesta efectiva',
                ],
                'ingenieria_social': [
                    'Se disponen de capacitaciones adecuadas para el personal de residentes y de personal de servicio sensibilizando frente a modus operandi como el de la llamada millonaria',
                    'Se dispone de algún sistema de notificación a los residentes en donde estos puedan consultar posibles personas que manifiestan la necesidad de entrar a sus domicilios',
                ],
                'acceso_ventanas_balcones': [
                    'Se dispone de un sistema de seguridad en las unidades residenciales que permitan hacer un monitoreo y detección de cualquier posible intrusión en balcones o ventanas',
                    'Se dispone de un sistema de retardo estándar que permita resistir intentos de intrusión por los balcones o ventanas vulnerables',
                ],
                'ventosa_ruptura_paredes': [
                    'Se dispone de un sistema de recorridos que permita identificar cualquier ingreso no autorizado por el rompimiento de la estructura externa de la unidad residencial en un tiempo adecuado',
                    'Se disponen de mapas de riesgo en donde se identifiquen unidades residenciales que colindan con otras y que se encuentren en poder de personas con estatus temporal en dicha residencia',
                ],
                'acceso_violento_persona': [
                    'Se disponen de mecanismos de comunicación que permitan atender a una persona externa, sin necesidad de aperturar la puerta de la unidad residencial',
                ],
            },
            'robo_vehiculos': {
                'suplantacion_residente': [
                    'Se disponen de mecanismos de identificación positiva y efectiva del propietario cuando sale con el vehículo',
                    'El sistema de identificación del propietario que retira el vehículo se mantiene aún en condiciones de vigilantes nuevos',
                ],
                'sometimiento_residente': [
                    'El sistema de salida vehicular da las facilidades al personal de seguridad de saber que el propietario sale bajo amenaza armada',
                ],
                'salida_violenta': [
                    'El sistema de salida vehicular es rígido para disuadir o reducir la probabilidad de una salida vehicular violenta',
                ],
                'autorizacion_forzada': [
                    'El sistema de seguridad permite identificar cuando un propietario está dando un aval para salida de una persona en un vehículo bajo coacción',
                ],
            },
            'robo_bicicletas': {
                'acceso_simplificado': [
                    'Se dispone de un sistema de acceso a las bicicletas controlado por mecanismos de retardo de dificil violación en tiempos cortos y requiriendo herramientas especializadas.',
                ],
                'salida_normal': [
                    'El sistema de seguridad está diseñado de manera tal que evita que una persona retire una bicicleta que no es de su propiedad',
                ],
                'salida_violenta': [
                    'El sistema de seguridad evita que una persona sustraiga una bicicleta amenazando con arma de fuego a las personas de seguridad',
                ],
                'autorizacion_suplantada': [
                    'El sistema de seguridad evita que una persona pueda suplantar al dueño de la bicicleta para facilitar la salida de esta',
                ],
            },
            'dano_areas_comunes': {
                'accion_interna': [
                    'El sistema de seguridad permite mantener la grabación y evidencia de las áreas comunes identificando la totalidad de la estructura para su aseguramiento',
                    'El sistema de seguridad, su presencia y ubicación permite con efectividad identificar en la mayoría de los casos cualquier daño o afectación gracias a su ubicación que permite controlar todas las áreas del complejo en tiempo real',
                ],
            },
            'conflictos_parqueos': {
                'permisividad_parqueos_asignados': [
                    'Se carece de una base de datos para el uso de los parqueaderos, en donde se tenga el registro claro del usuario, datos del vehículo, número de residencia y dato de contacto',
                    'Se disponen de procedimientos adecuados para el uso de los parqueaderos, evitando que visitantes usen espacios asignados a residentes',
                    'El personal de seguridad tiene dedicación exclusiva para el control de los parqueaderos, sin funciones adicionales que le restrinjan de la prestación de este servicio',
                ],
                'permisividad_administracion_parqueaderos': [
                    'El personal de seguridad debe ejercer un control claro de los vehículos que ingresan y pernoctan y no tiene autorizado recibir dinero por concepto del uso de parqueaderos',
                ],
            },
            'sustraccion_bienes': {
                'retiro_porterias': [
                    'Se disponen de mecanismos efectivos para identificar bienes que están saliendo visuales por porterías (peatonal y vehicular)',
                    'Se disponen de mecanismos para autorizar la salida de los elementos por las porterías que sea de obligatorio cumplimiento para los propietarios',
                ],
                'retiro_area_perimetral': [
                    'Los mecanismos de retardo son adecuados para dificultar la sustracción de elementos que ameriten ser cargados o transportados visiblemente',
                    'Los mecanismos de detección son adecuados para identificar la sustracción de elementos por el cerramiento perimetral',
                ],
            },
            'secuestro': {
                'salida_forzada_escoltas': [
                    'Se disponen de mecanismos de identificación positiva para el personal de escoltas, debiendo permanecer en un área específica que no involucren tener acceso a las unidades residenciales',
                    'Se disponen de mecanismos de salida de escoltas y sus protegidos, que faciliten la revisión visual del estado interior del vehículo al personal de seguridad para validar su identidad positivamente',
                ],
                'salida_forzada_familiaridad': [
                    'Se dispone de un código de conducta o de generación de alerta para cuando un residente salga acompañado o ingrese que pueda referir algún tipo de amenaza que lo somete',
                ],
                'suplantando_servicios_medicos': [
                    'Se dispone de un procedimiento para validar el ingreso y salida de una ambulancia, confirmando con alguien del núcleo familiar, la veracidad de la situación que se presenta.',
                ],
            },
            # Agregar otros tipos de riesgo y sus escenarios con preguntas
        }

        created_total = 0
        updated_total = 0
        preguntas_created = 0
        preguntas_updated = 0

        with transaction.atomic():
            for tipo_codigo, escenarios_data in mapping.items():
                try:
                    tipo = TipoRiesgo.objects.get(codigo=tipo_codigo)
                except TipoRiesgo.DoesNotExist:
                    # Crear TipoRiesgo si no existe
                    if not dry_run:
                        tipo = TipoRiesgo.objects.create(codigo=tipo_codigo, nombre=tipo_codigo.replace('_', ' ').title())
                    self.stdout.write(self.style.SUCCESS(f'  • TipoRiesgo {"creado" if not dry_run else "sería creado"}: {tipo_codigo}'))

                orden_escenario = 1
                for esc_codigo, preguntas_list in escenarios_data.items():
                    # Obtener etiqueta (nombre) desde las choices de EscenarioRiesgo
                    label = None
                    for code, name in EscenarioRiesgo.ESCENARIOS_CHOICES:
                        if code == esc_codigo:
                            label = name
                            break

                    nombre = label or esc_codigo.replace('_', ' ').title()

                    # Verificar si ya existe el escenario para este tipo de riesgo
                    escenario_obj = None
                    try:
                        escenario_existente = EscenarioRiesgo.objects.get(tipo_riesgo=tipo, codigo=esc_codigo)
                        
                        # El escenario ya existe para este tipo de riesgo, solo actualizar otros campos
                        if not dry_run:
                            escenario_existente.nombre = nombre
                            escenario_existente.orden = orden_escenario
                            escenario_existente.activo = True
                            escenario_existente.save()
                            escenario_obj = escenario_existente
                        updated_total += 1
                        self.stdout.write(self.style.NOTICE(
                            f'  • Escenario {"actualizado" if not dry_run else "sería actualizado"}: {tipo_codigo} -> {nombre}'
                        ))

                    except EscenarioRiesgo.DoesNotExist:
                        # El escenario no existe para este tipo de riesgo, crearlo
                        if not dry_run:
                            escenario_obj = EscenarioRiesgo.objects.create(
                                tipo_riesgo=tipo,
                                codigo=esc_codigo,
                                nombre=nombre,
                                descripcion='',
                                orden=orden_escenario,
                                activo=True
                            )
                        created_total += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✓ Escenario {"creado" if not dry_run else "sería creado"}: {tipo_codigo} -> {nombre}'
                        ))

                    # Crear preguntas para este escenario
                    if escenario_obj or dry_run:
                        orden_pregunta = 1
                        for texto_pregunta in preguntas_list:
                            if not dry_run and escenario_obj:
                                pregunta_obj, pregunta_created = PreguntaEvaluacion.objects.get_or_create(
                                    escenario=escenario_obj,
                                    texto_pregunta=texto_pregunta,
                                    defaults={
                                        'orden': orden_pregunta,
                                        'obligatoria': True,
                                        'activa': True,
                                        'ayuda': '',
                                    }
                                )
                                if pregunta_created:
                                    preguntas_created += 1
                                    self.stdout.write(self.style.SUCCESS(
                                        f'    ✓ Pregunta creada: {texto_pregunta[:50]}...'
                                    ))
                                else:
                                    preguntas_updated += 1
                                    self.stdout.write(self.style.NOTICE(
                                        f'    • Pregunta existente: {texto_pregunta[:50]}...'
                                    ))
                            else:
                                preguntas_created += 1
                                self.stdout.write(self.style.SUCCESS(
                                    f'    ✓ Pregunta {"creada" if not dry_run else "sería creada"}: {texto_pregunta[:50]}...'
                                ))
                            
                            orden_pregunta += 1

                    orden_escenario += 1

        action_text = "realizadas" if not dry_run else "que se realizarían"
        self.stdout.write(self.style.SUCCESS(
            f'✓ Operaciones {action_text}:'
        ))
        self.stdout.write(f'  Escenarios - Creados: {created_total}, Actualizados: {updated_total}')
        self.stdout.write(f'  Preguntas - Creadas: {preguntas_created}, Existentes: {preguntas_updated}')

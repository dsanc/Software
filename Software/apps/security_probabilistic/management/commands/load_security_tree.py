from django.core.management.base import BaseCommand
from django.db import transaction
from apps.security_probabilistic.models import ArbolDecision, Pregunta, OpcionRespuesta

class Command(BaseCommand):
    help = 'Carga el árbol de decisión de Evaluación de Seguridad'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando carga del árbol de decisión...')

        try:
            with transaction.atomic():
                # 1. Crear o actualizar el árbol
                arbol, created = ArbolDecision.objects.get_or_create(
                    nombre='Evaluación de Seguridad',
                    defaults={
                        'descripcion': 'Evaluación probabilística de riesgo basada en patrones de desplazamiento y actividades laborales.',
                        'activo': True
                    }
                )
                
                if not created:
                    self.stdout.write('El árbol ya existe. Actualizando estructura...')
                    # Opcional: Limpiar estructura existente si se desea reiniciar
                    # arbol.preguntas.all().delete()
                
                # Diccionario para almacenar referencias a las preguntas creadas
                preguntas_map = {}

                # 2. Definir las preguntas (sin enlaces aún)
                datos_preguntas = [
                    {
                        'id_ref': 6,
                        'texto': '¿Existe evidencia del desarrollo de ataques en el lugar de actividad política principal?',
                        'orden': 1,
                        'es_inicial': True
                    },
                    {
                        'id_ref': 7,
                        'texto': '¿La persona se desplaza a zonas críticas o con riesgo mayor?',
                        'orden': 2,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 8,
                        'texto': '¿Con qué frecuencia se desplaza a estos lugares?',
                        'orden': 3,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 9,
                        'texto': '¿Con qué frecuencia se desplaza por carretera a estos lugares?',
                        'orden': 4,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 10,
                        'texto': '¿Desarrolla actividades políticas que contrarían ideológicamente a alguno de los actores armados?',
                        'orden': 5,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 11,
                        'texto': 'Si se efectuara un ataque en su contra, ¿se beneficiaría algún sector político?',
                        'orden': 6,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 12,
                        'texto': '¿Desarrolla activismo político directo contra grupos al margen de la ley?',
                        'orden': 7,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 13,
                        'texto': '¿Ha recibido amenazas o tiene evidencias de actividades de seguimiento para atentar en su contra?',
                        'orden': 8,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 14,
                        'texto': '¿Tiene usted evidencia, información que pueda comprometer políticamente a otras personas en escándalos públicos o procesos penales?',
                        'orden': 9,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 15,
                        'texto': '¿Desarrolla activismo político por cualquier medio de comunicación masivo que condene hechos o acciones políticas de terceros?',
                        'orden': 10,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 16,
                        'texto': '¿Sus contra partes políticas incitan al odio públicamente derivado de actividades políticas o de antecedentes familiares?',
                        'orden': 11,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 17,
                        'texto': '¿Tiene un capital político importante que pueda hacer temer a sus contra partes políticas o grupos al margen posible logro de su cargo esperado?',
                        'orden': 12,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 18,
                        'texto': '¿Su discurso político va en contra de la delincuencia común?',
                        'orden': 13,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 19,
                        'texto': '¿Desarrolla actividades políticas que le impliquen exposición en espacios públicos?',
                        'orden': 14,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 20,
                        'texto': '¿Existe forma de conocer sus rutinas públicas con anticipación o publica información de su ubicación en redes?',
                        'orden': 15,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 21,
                        'texto': '¿Frecuenta sitios con aglomeración pública no controlada?',
                        'orden': 16,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 22,
                        'texto': '¿Su lugar de domicilio tiene medidas extraordinarias de seguridad?',
                        'orden': 17,
                        'es_inicial': False
                    },
                    {
                        'id_ref': 23,
                        'texto': '¿Existen personas de su colectividad política o semejante que podría implicar un mayor valor de impacto que el suyo?',
                        'orden': 18,
                        'es_inicial': False
                    },
                ]

                # Crear preguntas
                for p_data in datos_preguntas:
                    pregunta, _ = Pregunta.objects.update_or_create(
                        arbol=arbol,
                        texto=p_data['texto'],
                        defaults={
                            'orden': p_data['orden'],
                            'es_pregunta_inicial': p_data['es_inicial']
                        }
                    )
                    preguntas_map[p_data['id_ref']] = pregunta

                # 3. Definir opciones y flujo
                # Formato: (id_pregunta_origen, texto_opcion, id_pregunta_destino_o_None, valor_ponderado, orden, es_final)
                flujo = [
                    (6, 'SI', 7,  1.000, 1, False), (6, 'NO', 7,  0.000, 2, False),
                    (7, 'SI', 8,  1.000, 1, False), (7, 'NO', 10, 0.000, 2, False),
                    (8, 'Menos de 3 meses', 9, 0.250, 1, False),
                    (8, 'De 4 a 10 meses',  9, 0.500, 2, False),
                    (8, 'Mas de 10 meses',  9, 0.750, 3, False),
                    (8, 'NO',               9, 0.000, 4, False),
                    (9, 'Menos de 3 meses', 10, 0.250, 1, False),
                    (9, 'De 4 a 10 meses',  10, 0.500, 2, False),
                    (9, 'Mas de 10 meses',  10, 0.750, 3, False),
                    (9, 'NO',               10, 0.000, 4, False),
                    (10, 'SI', 11, 1.000, 1, False), (10, 'NO', 18, 0.000, 2, False),
                    (11, 'SI', 12, 1.000, 1, False), (11, 'NO', 18, 0.000, 2, False),
                    (12, 'SI', 13, 1.000, 1, False), (12, 'NO', 13, 0.000, 2, False),
                    (13, 'SI', 14, 1.000, 1, False), (13, 'NO', 14, 0.000, 2, False),
                    (14, 'SI', 15, 1.000, 1, False), (14, 'NO', 15, 0.000, 2, False),
                    (15, 'SI', 16, 1.000, 1, False), (15, 'NO', 16, 0.000, 2, False),
                    (16, 'SI', 17, 1.000, 1, False), (16, 'NO', 17, 0.000, 2, False),
                    (17, 'SI', 18, 1.000, 1, False), (17, 'NO', 18, 0.000, 2, False),
                    (18, 'SI', 19, 1.000, 1, False), (18, 'NO', 19, 0.000, 2, False),
                    (19, 'SI', 20, 1.000, 1, False), (19, 'NO', 20, 0.000, 2, False),
                    (20, 'SI', 21, 1.000, 1, False), (20, 'NO', 21, 0.000, 2, False),
                    (21, 'SI', 22, 1.000, 1, False), (21, 'NO', 22, 0.000, 2, False),
                    (22, 'SI', 23, 1.000, 1, False), (22, 'NO', 23, 0.000, 2, False),
                    (23, 'SI', None, 1.000, 1, True), (23, 'NO', None, 0.000, 2, True),
                ]

                # Crear opciones y conectar
                for id_origen, texto, id_destino, valor, orden, es_final in flujo:
                    pregunta_origen = preguntas_map.get(id_origen)
                    pregunta_destino = preguntas_map.get(id_destino) if id_destino else None

                    if pregunta_origen:
                        OpcionRespuesta.objects.update_or_create(
                            pregunta=pregunta_origen,
                            texto=texto,
                            defaults={
                                'pregunta_siguiente': pregunta_destino,
                                'valor_ponderado': valor,
                                'orden': orden,
                                'es_respuesta_final': es_final,
                            }
                        )

            self.stdout.write(self.style.SUCCESS('Árbol de decisión cargado exitosamente'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cargando árbol: {str(e)}'))

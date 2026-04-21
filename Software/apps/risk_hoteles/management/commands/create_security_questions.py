"""
Comando para poblar preguntas de seguridad para cada categoría del módulo de hoteles
"""
from django.core.management.base import BaseCommand
from apps.risk_hoteles.models import SecurityCategory, SecurityQuestion


class Command(BaseCommand):
    help = 'Crea las preguntas de seguridad para cada categoría del módulo de hoteles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando preguntas de seguridad para hoteles...'))
        
        # Limpiar preguntas existentes
        existing_count = SecurityQuestion.objects.count()
        if existing_count > 0:
            SecurityQuestion.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Se eliminaron {existing_count} preguntas existentes.'))
        
        # Definir preguntas por categoría
        questions_data = {
            'gestion_organizacion': [
                {
                    'question_text': 'La organización hotelera debe tener una Política de Seguridad o documento que evidencie el compromiso, respaldo y seguimiento de la alta dirección en el fortalecimiento continuo de la seguridad, que conlleve y ejecute acciones concretas y evidenciables en el desarrollo de la seguridad de la organización.',
                    'help_text': 'Verificar la existencia de una política formal documentada con respaldo directivo visible.',
                    'weight': 1.5,
                    'order': 1
                },
                {
                    'question_text': 'El hotel dispone (y se evidencia) un plan para el desarrollo de la cultura organizacional que promueva valores que fortalezcan la seguridad a través de la integridad de los empleados y la participación permanente en apoyar la seguridad. El plan cumple con aspectos como: valores, ética, compromiso con la seguridad del hotel y reporte de situaciones relevantes que puedan afectar la seguridad.',
                    'help_text': 'Evaluar la existencia de un plan cultural que incluya valores, ética y compromiso con la seguridad.',
                    'weight': 1.4,
                    'order': 2
                },
                {
                    'question_text': 'Se evidencia el compromiso de la organización en la participación de comités para la gestión del riesgo que contenga aspectos como: determinación y valoración de los niveles de riesgo, implementación y seguimiento a los controles de los riesgos que deben ser intervenidos y argumentación de los criterios de aceptabilidad de riesgos en niveles altos y auditorías al sistema de gestión de riesgos.',
                    'help_text': 'Confirmar la existencia y funcionamiento de comités de gestión de riesgos con responsabilidades claras.',
                    'weight': 1.5,
                    'order': 3
                },
                {
                    'question_text': 'La organización dispone dentro de su estructura la existencia de un cargo responsable de la mitigación de los riesgos y gestión de la seguridad como principal responsabilidad dentro de su cargo.',
                    'help_text': 'Verificar que existe un cargo específico responsable de la gestión de seguridad.',
                    'weight': 1.5,
                    'order': 4
                },
                {
                    'question_text': 'Las funciones, responsabilidades y nivel de autoridad delegado al responsable de la seguridad son suficientes para tomar las decisiones que permitan el control de la operación de la seguridad.',
                    'help_text': 'Evaluar si el responsable de seguridad tiene autoridad suficiente para tomar decisiones efectivas.',
                    'weight': 1.4,
                    'order': 5
                },
                {
                    'question_text': 'La persona de seguridad dispone de la formación o experiencia necesaria para el desarrollo y cumplimiento de las actividades propias de gestión de los riesgos e implementación de los diferentes controles para minimizar la probabilidad o consecuencia de estos.',
                    'help_text': 'Confirmar que el personal de seguridad tiene la formación y experiencia adecuada.',
                    'weight': 1.3,
                    'order': 6
                },
                {
                    'question_text': 'La empresa hotelera dispone de un plan de seguridad coherente con la situación de los riesgos de la organización, en el cual se define la hoja de ruta de seguridad en el mediano y corto plazo, con la posibilidad de medir todo su desarrollo y cumplimiento.',
                    'help_text': 'Verificar la existencia de un plan de seguridad con metas medibles y cronograma definido.',
                    'weight': 1.4,
                    'order': 7
                },
                {
                    'question_text': 'Se tiene un manual de seguridad en el cual se encuentran todos los documentos base para determinar el funcionamiento de la seguridad, en el cual se definen tipos de actividades, responsables, documentación y funcionamiento de recursos, tecnología y medios físicos para desarrollar capacidades que permitan la mitigación de los riesgos.',
                    'help_text': 'Confirmar la existencia de un manual completo que documente todos los aspectos de seguridad.',
                    'weight': 1.3,
                    'order': 8
                },
                {
                    'question_text': 'La organización desarrolla análisis de riesgos y estructura sus mecanismos de mitigación coherente con la evaluación de los riesgos. Se evidencia que la implementación de los controles sea coherente con la medición del riesgo.',
                    'help_text': 'Evaluar la coherencia entre el análisis de riesgos y los controles implementados.',
                    'weight': 1.5,
                    'order': 9
                },
                {
                    'question_text': 'El análisis de los riesgos considera las amenazas de la organización y que estas sean coherentes con la realidad del entorno.',
                    'help_text': 'Verificar que el análisis de riesgos refleje las amenazas reales del entorno.',
                    'weight': 1.3,
                    'order': 10
                },
                {
                    'question_text': 'Se tienen identificadas claramente las vulnerabilidades de la organización y se promueve por la reducción o eliminación de estas vulnerabilidades en la seguridad o las debilidades en los procesos.',
                    'help_text': 'Confirmar la identificación y gestión de vulnerabilidades organizacionales.',
                    'weight': 1.4,
                    'order': 11
                },
                {
                    'question_text': 'Se dispone de la elección de los activos clave de negocio para desarrollar el análisis de los riesgos de manera que se logre identificar y valorar los principales riesgos de la organización.',
                    'help_text': 'Evaluar la identificación correcta de activos críticos para el análisis de riesgos.',
                    'weight': 1.3,
                    'order': 12
                },
                {
                    'question_text': 'Se dispone de una formulación clara dentro del manual de seguridad para la conservación de los controles en seguridad física que promuevan el retardo y la detección.',
                    'help_text': 'Verificar que el manual incluye controles de seguridad física con principios de retardo y detección.',
                    'weight': 1.2,
                    'order': 13
                },
                {
                    'question_text': 'El manual de seguridad dispone de la formulación clara del esquema de seguridad de vigilantes, siendo este coherente con los riesgos de la organización y desempeñando actividades que promuevan la reducción del mismo.',
                    'help_text': 'Confirmar que existe un esquema claro para el personal de vigilancia.',
                    'weight': 1.3,
                    'order': 14
                },
                {
                    'question_text': 'La organización además debe disponer dentro del manual de seguridad de las funciones y procedimientos asociados con cada uno de los puestos de vigilancia, los niveles de supervisión y gerencial que tengan relacionamiento con la seguridad hotelera corporativa.',
                    'help_text': 'Evaluar la documentación de funciones y procedimientos para todos los niveles de vigilancia.',
                    'weight': 1.2,
                    'order': 15
                },
                {
                    'question_text': 'El esquema o dispositivo de seguridad de los vigilantes deberá contar con las acreditaciones legales para el funcionamiento y deberá ser sensible a los cambios de riesgos de la organización para ajustar los horarios.',
                    'help_text': 'Verificar que el personal de vigilancia cumple requisitos legales y es adaptable a cambios.',
                    'weight': 1.2,
                    'order': 16
                },
                {
                    'question_text': 'El manual de seguridad dispone del funcionamiento y configuración de los sistemas de seguridad electrónica que reduzcan entre otros: la pérdida de la información que requiere ser controlada, la ubicación de los dispositivos del sistema de seguridad electrónica, la designación de perfiles de usuario coherentes con la dinámica del riesgo de la organización y la eliminación de usuarios que estén caducados o no apliquen.',
                    'help_text': 'Confirmar la documentación completa de sistemas electrónicos y gestión de usuarios.',
                    'weight': 1.3,
                    'order': 17
                },
                {
                    'question_text': 'El manual de seguridad se actualiza y se mejora conforme con los resultados de los análisis de los riesgos implementando mejores medidas para el logro de la mitigación de los riesgos.',
                    'help_text': 'Evaluar si el manual se actualiza regularmente basado en análisis de riesgos.',
                    'weight': 1.2,
                    'order': 18
                },
                {
                    'question_text': 'La organización dispone dentro del Plan de seguridad con los mecanismos coherentes para evaluar la gestión desarrollada e índices que midan las situaciones de incidentes que se presentan.',
                    'help_text': 'Verificar la existencia de mecanismos de evaluación y medición de incidentes.',
                    'weight': 1.3,
                    'order': 19
                },
                {
                    'question_text': 'Las decisiones gerenciales deben tomarse específicamente analizando la consecuencia de estas en los riesgos de seguridad. Las decisiones no deberán incrementar los niveles de riesgos en la seguridad a niveles que no deban ser asumidos ni aceptados por la organización.',
                    'help_text': 'Confirmar que las decisiones gerenciales consideran el impacto en los riesgos de seguridad.',
                    'weight': 1.4,
                    'order': 20
                },
                {
                    'question_text': 'La organización tiene un plan de capacitación en seguridad coherente con las necesidades en materia de seguridad hotelera que se cumple y sea adecuado según el contexto y los cargos.',
                    'help_text': 'Evaluar la existencia y adecuación del plan de capacitación en seguridad.',
                    'weight': 1.3,
                    'order': 21
                },
                {
                    'question_text': 'La persona responsable de la capacitación promueve que quienes ejecutan el plan de capacitación tengan las competencias adecuadas para que esta genere el incremento de las competencias en seguridad.',
                    'help_text': 'Verificar que los capacitadores tienen las competencias necesarias.',
                    'weight': 1.2,
                    'order': 22
                },
                {
                    'question_text': 'El proceso de seguridad evidencia la planificación de actividades que promueva la mitigación del riesgo y los mecanismos de control y seguimiento de dichas actividades.',
                    'help_text': 'Confirmar la planificación y seguimiento de actividades de mitigación de riesgos.',
                    'weight': 1.3,
                    'order': 23
                },
                {
                    'question_text': 'El responsable de la seguridad tiene la facultad de poder ingresar en casos excepcionales a cualquier área de la instalación hotelera, dejando evidencia del cumplimiento del procedimiento dispuesto para tal fin.',
                    'help_text': 'Evaluar si el responsable de seguridad tiene acceso completo con procedimientos claros.',
                    'weight': 1.2,
                    'order': 24
                },
                {
                    'question_text': 'El responsable de la seguridad hotelera tiene identificado y gestiona permanentemente el cumplimiento de los requisitos normativos que le aplican a su proceso.',
                    'help_text': 'Verificar la gestión del cumplimiento normativo en seguridad.',
                    'weight': 1.2,
                    'order': 25
                },
                {
                    'question_text': 'Se tienen indicadores de gestión que promuevan la medición efectiva de los resultados del objetivo del proceso.',
                    'help_text': 'Confirmar la existencia de indicadores de gestión para medir resultados.',
                    'weight': 1.2,
                    'order': 26
                },
                {
                    'question_text': 'Se tienen índices para medir la frecuencia en relación con las actividades clave del hotel para conocer el comportamiento de los riesgos inherentes y la capacidad del sistema de seguridad para mitigarlos.',
                    'help_text': 'Evaluar la existencia de índices de frecuencia para actividades clave.',
                    'weight': 1.2,
                    'order': 27
                },
                {
                    'question_text': 'El proceso de seguridad cuenta con los recursos necesarios para la operación de acuerdo con sus necesidades frente a la mitigación de los riesgos, sus escenarios y las áreas hoteleras en dónde podría presentarse.',
                    'help_text': 'Verificar la suficiencia de recursos para la operación de seguridad.',
                    'weight': 1.3,
                    'order': 28
                },
                {
                    'question_text': 'Se evidencia el adecuado funcionamiento y mantenimiento de los recursos técnicos y tecnológicos destinados a la seguridad de la organización hotelera.',
                    'help_text': 'Confirmar el mantenimiento adecuado de recursos técnicos y tecnológicos.',
                    'weight': 1.2,
                    'order': 29
                },
                {
                    'question_text': 'Se promueve el uso de las auditorías al proceso de seguridad con el fin de mejorar continuamente y adoptar los cambios necesarios en el tiempo establecido.',
                    'help_text': 'Evaluar la implementación de auditorías para mejora continua.',
                    'weight': 1.2,
                    'order': 30
                },
                {
                    'question_text': 'La organización hotelera identifica los cargos que podrían impactar en la seguridad y promueve las pruebas necesarias para evaluar la confiabilidad de las personas que los desempeñan.',
                    'help_text': 'Verificar la identificación de cargos críticos y evaluación de confiabilidad.',
                    'weight': 1.3,
                    'order': 31
                },
                {
                    'question_text': 'Se dispone de la estructura y fundamentación evidenciable de un subproceso de investigación, el cual sea acorde con las dinámicas propias de la frecuencia de los eventos y los resultados permiten la toma de decisiones efectivas para el cierre de los casos y la mejora continua de los eventos que dieron origen a los riesgos materializados objeto de la investigación.',
                    'help_text': 'Confirmar la existencia de un subproceso formal de investigación de incidentes.',
                    'weight': 1.3,
                    'order': 32
                },
                {
                    'question_text': 'El proceso de seguridad dispone de un procedimiento documentado y socializado con los responsables del desarrollo de eventos dentro de la organización hotelera, el cuál incluya entre otros la claridad de conocer las personas que ingresarán, las condiciones de seguridad requeridas por el hotel y en los casos que el análisis de los riesgos indique, la consideración de controles de seguridad.',
                    'help_text': 'Evaluar los procedimientos documentados para gestión de eventos.',
                    'weight': 1.2,
                    'order': 33
                },
                {
                    'question_text': 'El proceso de seguridad se integra adecuadamente en los riesgos de la operación de los demás procesos mediante el análisis de los riesgos por procesos organizacionales.',
                    'help_text': 'Verificar la integración del proceso de seguridad con otros procesos organizacionales.',
                    'weight': 1.3,
                    'order': 34
                },
                {
                    'question_text': 'El proceso de seguridad dispone de un adecuado cumplimiento de los controles propuestos para cada uno de los procesos y se han documentado adecuadamente de manera tal que se pueda evidenciar los responsables y los registros de estos.',
                    'help_text': 'Confirmar la documentación y cumplimiento de controles por proceso.',
                    'weight': 1.2,
                    'order': 35
                },
                {
                    'question_text': 'Se conocen las áreas críticas de la organización, se tienen documentadas y se han definidos estas conforme a criterios claros con el fin de implementar medidas de seguridad coherentes.',
                    'help_text': 'Evaluar la identificación y documentación de áreas críticas.',
                    'weight': 1.3,
                    'order': 36
                },
                {
                    'question_text': 'Se identifica la participación del proceso de seguridad en las emergencias y se tienen consideradas las contingencias derivadas de los riesgos de seguridad.',
                    'help_text': 'Verificar la participación de seguridad en gestión de emergencias.',
                    'weight': 1.3,
                    'order': 37
                },
                {
                    'question_text': 'El proceso de seguridad tiene clasificada la información considerada como sensible y se aplican procedimientos claros para salvaguardarla de divulgación, pérdida o modificación.',
                    'help_text': 'Confirmar la clasificación y protección de información sensible.',
                    'weight': 1.3,
                    'order': 38
                },
                {
                    'question_text': 'La organización dispone de pruebas periódicas para validar el cumplimiento de las medidas de seguridad y efectividad de los controles adoptados conforme a los riesgos de la instalación hotelera.',
                    'help_text': 'Evaluar la implementación de pruebas periódicas de seguridad.',
                    'weight': 1.2,
                    'order': 39
                },
                {
                    'question_text': 'Se actualiza la situación de riesgos conforme a la dinámica local y nacional diaria, con el fin de mantener la capacidad preventiva y de respuesta a incidentes de origen humano e intencional.',
                    'help_text': 'Verificar la actualización continua de la situación de riesgos.',
                    'weight': 1.2,
                    'order': 40
                },
                {
                    'question_text': 'Se tiene el personal de monitoreo que cumpla las funciones de observa áreas críticas y exigir al personal de operación de seguridad el cumplimiento de las medidas propias para la mitigación del riesgo.',
                    'help_text': 'Confirmar la existencia de personal de monitoreo de áreas críticas.',
                    'weight': 1.2,
                    'order': 41
                },
                {
                    'question_text': 'Se promueven las medidas para evitar la rotación del personal de seguridad y se fomenta el incremento de las competencias de estos en referencia a las funciones que desarrollan.',
                    'help_text': 'Evaluar las medidas de retención y desarrollo del personal de seguridad.',
                    'weight': 1.1,
                    'order': 42
                },
                {
                    'question_text': 'El líder de seguridad dispone de acceso a la información relevante para cumplir con identificación de situaciones de inseguridad, riesgos y otros datos que estén contenidos en los sistemas de información operativa de la organización para poder prevenir e investigar cualquier tipo de situación.',
                    'help_text': 'Verificar el acceso del líder de seguridad a información relevante.',
                    'weight': 1.3,
                    'order': 43
                },
                {
                    'question_text': 'La organización evidencia con claridad los niveles de uso de la fuerza que podría usar el personal de seguridad ante diferentes circunstancias.',
                    'help_text': 'Confirmar la claridad en los protocolos de uso de la fuerza.',
                    'weight': 1.2,
                    'order': 44
                },
                {
                    'question_text': 'El líder de seguridad dispone de la autorización para acceder a cualquier área del hotel considerando el procedimiento para estos y sus excepciones.',
                    'help_text': 'Evaluar la autorización de acceso del líder de seguridad.',
                    'weight': 1.2,
                    'order': 45
                },
                {
                    'question_text': 'Se dispone de un contrato con un proveedor externo para la prestación de servicios de vigilancia y es adecuado para las necesidades de seguridad del hotel y se evidencian los pagos claros al personal de seguridad.',
                    'help_text': 'Verificar la adecuación de contratos con proveedores de vigilancia.',
                    'weight': 1.1,
                    'order': 46
                },
                {
                    'question_text': 'Se dispone de un claro flujo de información y comunicación de las incidencias operativas diarias que requieran la implementación de oportunidades de mejora, así como las disposiciones que deban ser transmitidas al personal de seguridad para su cumplimiento.',
                    'help_text': 'Confirmar la existencia de flujos claros de comunicación operativa.',
                    'weight': 1.2,
                    'order': 47
                },
                {
                    'question_text': 'El sistema de comunicaciones cubre la totalidad de las áreas de la instalación hotelera, sin generar quebrantos o fallos en las comunicaciones operativas.',
                    'help_text': 'Evaluar la cobertura completa del sistema de comunicaciones.',
                    'weight': 1.2,
                    'order': 48
                },
                {
                    'question_text': 'Se dispone de las estrategias para fomentar el uso de las cajillas de seguridad de las habitaciones.',
                    'help_text': 'Verificar las estrategias para promover el uso de cajas de seguridad.',
                    'weight': 1.0,
                    'order': 49
                },
                {
                    'question_text': 'La organización hotelera dispone de adecuado enlace con empresas de transporte privado para ser referidos, salvaguardando la integridad del huésped y exigiendo tarifas acordes con los precios del mercado.',
                    'help_text': 'Confirmar enlaces adecuados con empresas de transporte.',
                    'weight': 1.0,
                    'order': 50
                },
                {
                    'question_text': 'La organización hotelera tiene un adecuado procedimiento para el manejo de elementos perdidos y encontrados "Lost & Found" que permita salvaguardar la propiedad del cliente.',
                    'help_text': 'Evaluar el procedimiento de objetos perdidos y encontrados.',
                    'weight': 1.0,
                    'order': 51
                },
                {
                    'question_text': 'El procedimiento de "Lost & Found" promueve el realizar devolución a los propietarios de sus elementos.',
                    'help_text': 'Verificar que el procedimiento promueva la devolución activa.',
                    'weight': 1.0,
                    'order': 52
                },
                {
                    'question_text': 'Se dispone de un procedimiento para administrar las llaves del hotel que permita mantener controlado el acceso a cada dependencia y los préstamos de llaves cuando sea necesario.',
                    'help_text': 'Confirmar la existencia de procedimientos de control de llaves.',
                    'weight': 1.2,
                    'order': 53
                }
            ],
            'seguridad_externa': [
                {
                    'question_text': 'La organización hotelera tiene identificados las áreas críticas del entorno que podrían llegar a afectar la seguridad de sus instalaciones?',
                    'help_text': 'Evaluar si se han identificado y documentado las áreas del entorno que representan riesgos para la seguridad.',
                    'weight': 1.4,
                    'order': 1
                },
                {
                    'question_text': 'La organización hotelera tiene establecido con las demás organizaciones del entorno la colaboración y la comunicación permanente para anticiparse a posibles amenazas que sean detectadas?',
                    'help_text': 'Verificar la existencia de redes de colaboración con organizaciones vecinas para detección temprana de amenazas.',
                    'weight': 1.3,
                    'order': 2
                },
                {
                    'question_text': 'La organización hotelera dispone de controles para evitar que en el área cercana a sus instalaciones se desarrollen condiciones ambientales inadecuadas que puedan generar tendencias al delito. (Esto se hace a través del mantenimiento de áreas, evitar basuras o espacios deteriorados visualmente)',
                    'help_text': 'Confirmar la implementación de controles ambientales que reduzcan factores criminógenos en el entorno.',
                    'weight': 1.2,
                    'order': 3
                },
                {
                    'question_text': 'La organización hotelera, evidencia la realización de actividades de implementación de mecanismos de mitigación de amenazas en su interacción con autoridades o actuaciones en alianza con otras organizaciones para mejorar el perfil de riesgo de la zona.',
                    'help_text': 'Evaluar las actividades de mitigación realizadas en coordinación con autoridades y otras organizaciones.',
                    'weight': 1.3,
                    'order': 4
                },
                {
                    'question_text': 'La iluminación es adecuada para generar un efecto disuasivo en el entorno inmediato?',
                    'help_text': 'Verificar que la iluminación exterior cumpla función disuasiva contra actividades delictivas.',
                    'weight': 1.2,
                    'order': 5
                },
                {
                    'question_text': 'El entorno permite por su diseño generar un efecto de vigilancia natural, que disuada a los delincuentes en esta área?',
                    'help_text': 'Confirmar que el diseño del entorno facilite la vigilancia natural y visibilidad.',
                    'weight': 1.1,
                    'order': 6
                },
                {
                    'question_text': 'El área externa dispone de un control perimetral y de accesos previo al de la instalación hotelera?',
                    'help_text': 'Evaluar la existencia de controles de seguridad en el perímetro externo antes del acceso principal.',
                    'weight': 1.3,
                    'order': 7
                },
                {
                    'question_text': 'Se disponen de iniciativas permanentes para detectar amenazas en tiempo real en el perímetro externo de la instalación hotelera.',
                    'help_text': 'Verificar la implementación de sistemas de detección temprana de amenazas en el perímetro externo.',
                    'weight': 1.4,
                    'order': 8
                }
            ],
            'seguridad_perimetral': [
                {
                    'question_text': 'La organización hotelera, dispone de un cerramiento o barrera perimetral que genere un efecto disuasivo de retardo efectivo que solo pueda ser sobrepasado con ayuda de elementos o equipos para afectarlo. Se debe considerar que dicho cerramiento perimetral debe ser constante con los mismos atributos en los 360° del cerramiento.',
                    'help_text': 'Evaluar la calidad, continuidad y efectividad del cerramiento perimetral completo.',
                    'weight': 1.5,
                    'order': 1
                },
                {
                    'question_text': 'La instalación hotelera, está ubicada dentro de alguna instalación, que funcione como un filtro efectivo a la seguridad hotelera inicial.',
                    'help_text': 'Verificar si existe una barrera de seguridad externa adicional que proteja la instalación.',
                    'weight': 1.2,
                    'order': 2
                },
                {
                    'question_text': 'La articulación del cerramiento perimetral con los puntos de control de acceso, están debidamente diseñados de manera tal que no exista un área intermedia entre estos que facilite la intrusión.',
                    'help_text': 'Confirmar que no existen espacios vulnerables entre el cerramiento y los puntos de acceso.',
                    'weight': 1.4,
                    'order': 3
                },
                {
                    'question_text': 'Se disponen de los elementos de detección efectivos en el cerramiento perimetral, de manera tal que permitan generar un mecanismo de respuesta oportuno.',
                    'help_text': 'Evaluar la presencia y efectividad de sistemas de detección perimetral.',
                    'weight': 1.4,
                    'order': 4
                },
                {
                    'question_text': 'El sistema de detección es constante y permanente a lo largo del cerramiento perimetral de manera tal que no sea vulnerado en los puntos deficientes.',
                    'help_text': 'Verificar la continuidad y cobertura completa del sistema de detección.',
                    'weight': 1.3,
                    'order': 5
                },
                {
                    'question_text': 'El sistema de detección perimetral indica con precisión el punto de intento de intrusión o sabotaje, con el fin de permitir una alarma clara y generar la reacción del personal de seguridad.',
                    'help_text': 'Confirmar la precisión y claridad del sistema de alertas de detección.',
                    'weight': 1.3,
                    'order': 6
                },
                {
                    'question_text': 'Se dispone de un sistema de seguridad de guardias o vigilantes que tengan presencia exclusiva para el cerramiento perimetral y disponen de un diseño adecuado de las funciones de puesto para mitigar el riesgo.',
                    'help_text': 'Evaluar la dedicación y preparación del personal de seguridad perimetral.',
                    'weight': 1.2,
                    'order': 7
                },
                {
                    'question_text': 'En las áreas con salida al mar se dispone de presencia permanente de un método de control efectivo para evitar que la intrusión se de por esta área.',
                    'help_text': 'Verificar controles específicos para accesos marítimos cuando aplique.',
                    'weight': 1.3,
                    'order': 8
                },
                {
                    'question_text': 'La organización hotelera dispone de un mecanismo para verificar permanentemente el estado de la estructura perimetral y se soluciona adecuadamente los hallazgos o afectaciones.',
                    'help_text': 'Confirmar la existencia de mantenimiento preventivo y correctivo del perímetro.',
                    'weight': 1.2,
                    'order': 9
                },
                {
                    'question_text': 'Se promueve la iluminación a lo largo del cerramiento perimetral para facilitar la labor de visibilidad en la detección de conductas sospechosas externamente.',
                    'help_text': 'Evaluar la cobertura y efectividad de la iluminación perimetral.',
                    'weight': 1.1,
                    'order': 10
                }
            ],
            'seguridad_internas': [
                {
                    'question_text': 'Las áreas internas cuentan con la iluminación adecuada para facilitar la labor de los recorredores de seguridad o la vigilancia natural efectiva a lo largo de la instalación hotelera, incluyendo áreas de empleados (y zonas de playa si las tiene) bajo el control hotelero.',
                    'help_text': 'Evaluar la cobertura e intensidad de iluminación en todas las áreas internas incluyendo zonas de empleados.',
                    'weight': 1.3,
                    'order': 1
                },
                {
                    'question_text': 'La organización hotelera dispone en su interior de unas áreas limpias de obstáculos vegetales o de ambientes que faciliten el ocultamiento delictivo (elementos dispuestos en el piso o acumulación de activos) que promuevan el interés delincuencial en ingresar a la instalación hotelera.',
                    'help_text': 'Verificar que las áreas estén libres de elementos que faciliten actividades delictivas u ocultamiento.',
                    'weight': 1.2,
                    'order': 2
                },
                {
                    'question_text': 'Se dispone de los mecanismos efectivos en las áreas internas para disuadir e identificar fácilmente cualquier tránsito sospechoso en los diferentes ambientes públicos del hotel.',
                    'help_text': 'Confirmar la existencia de sistemas para detectar comportamientos sospechosos en áreas públicas.',
                    'weight': 1.4,
                    'order': 3
                },
                {
                    'question_text': 'Se dispone de un mecanismo de identificación efectivo y positivo que promueva la rápida actuación del personal de seguridad para decidir la intervención frente a una persona sospechosa en su área de responsabilidad.',
                    'help_text': 'Evaluar los procedimientos de identificación y respuesta ante personas sospechosas.',
                    'weight': 1.4,
                    'order': 4
                },
                {
                    'question_text': 'El personal de seguridad de áreas internas (no accesos) dispone de las funciones de puesto ajustadas para mitigar los riesgos de seguridad.',
                    'help_text': 'Verificar que el personal tenga funciones claramente definidas para áreas internas.',
                    'weight': 1.3,
                    'order': 5
                },
                {
                    'question_text': 'Se disponen de controles en profundidad que limita a personas no identificadas transitar por áreas internas.',
                    'help_text': 'Confirmar la existencia de múltiples niveles de control para personas no autorizadas.',
                    'weight': 1.4,
                    'order': 6
                },
                {
                    'question_text': 'La organización hotelera, identifica los puntos críticos de las áreas internas y en consecuencia, maximizará las actividades de control sobre estos puntos. Se debe tener adecuada justificación de los factores que inciden en la criticidad de las diferentes áreas. Normalmente se determinan tres niveles de criticidad: baja, media y alta.',
                    'help_text': 'Evaluar la clasificación de criticidad y control diferenciado de áreas internas.',
                    'weight': 1.5,
                    'order': 7
                },
                {
                    'question_text': 'Existen mecanismos variables de reforzamiento de la seguridad en áreas internas, según la ocupación del hotel.',
                    'help_text': 'Verificar la adaptación de medidas de seguridad según el nivel de ocupación.',
                    'weight': 1.2,
                    'order': 8
                },
                {
                    'question_text': 'Se asegura por parte de la organización hotelera que sólo las personas que están facultadas podrán acceder a las zonas restringidas que están en las áreas internas.',
                    'help_text': 'Confirmar el control de acceso a zonas restringidas dentro de áreas internas.',
                    'weight': 1.4,
                    'order': 9
                },
                {
                    'question_text': 'En caso de que las áreas internas sean compartidas con otras organizaciones, se tendrán claros acuerdos de vigilancia, interacción y comunicación entre los responsables de la seguridad en los niveles directivos, de coordinación y de vigilancia.',
                    'help_text': 'Evaluar los acuerdos de seguridad con otras organizaciones en espacios compartidos.',
                    'weight': 1.3,
                    'order': 10
                },
                {
                    'question_text': 'En las áreas internas para el uso y disfrute de actividades de los huéspedes se dispone de las medidas de seguridad para detectar conductas agresivas o mal intencionadas.',
                    'help_text': 'Verificar la detección de comportamientos agresivos en áreas de huéspedes.',
                    'weight': 1.3,
                    'order': 11
                },
                {
                    'question_text': 'Se dispone de algún mecanismo efectivo para la protección de niños en las áreas públicas que sea efectivo en la prevención de situaciones de abuso infantil.',
                    'help_text': 'Confirmar la existencia de protocolos específicos para protección de menores.',
                    'weight': 1.5,
                    'order': 12
                },
                {
                    'question_text': 'Se tiene una trazabilidad y control en tiempo real para visitantes, contratistas o proveedores que transitan por las áreas internas para evitar que estos interactúen en las áreas internas de los huéspedes.',
                    'help_text': 'Evaluar el control y seguimiento de personas externas en áreas internas.',
                    'weight': 1.4,
                    'order': 13
                },
                {
                    'question_text': 'Se tienen mecanismos de control de uso acceso y trazabilidad en las zonas deportivas con apertura y posibles usos no permitidos de externos, evitando personas no autorizadas.',
                    'help_text': 'Verificar el control de acceso a instalaciones deportivas.',
                    'weight': 1.3,
                    'order': 14
                },
                {
                    'question_text': 'Se dispone de mecanismos de control para menores de edad que asisten a eventos o zonas deportivas en áreas internas públicas.',
                    'help_text': 'Confirmar los controles específicos para menores en eventos y actividades deportivas.',
                    'weight': 1.4,
                    'order': 15
                },
                {
                    'question_text': 'Se tiene un mecanismos de control efectivo para el tránsito de personas que son críticas por el porte de armas o elementos que puedan ser peligrosos como transportadoras de valores, escoltas y otras que deban tener tránsito controlado y restringido.',
                    'help_text': 'Evaluar el control especial para personas que portan armas o elementos peligrosos.',
                    'weight': 1.5,
                    'order': 16
                },
                {
                    'question_text': 'La organización hotelera dispone de sistemas de alerta efectivos, y accesibles en todas las áreas internas, con el fin de reportar situaciones de riesgo.',
                    'help_text': 'Verificar la cobertura y efectividad de sistemas de alerta en áreas internas.',
                    'weight': 1.4,
                    'order': 17
                },
                {
                    'question_text': 'El sistema de comunicaciones del esquema de seguridad tiene la cobertura al 100% total de los predios del hotel, permitiendo que ningún reporte será desestimado por falta de cobertura.',
                    'help_text': 'Confirmar la cobertura completa del sistema de comunicaciones de seguridad.',
                    'weight': 1.5,
                    'order': 18
                },
                {
                    'question_text': 'En el área de gimnasio se disponen controles de accesos, mecanismos de monitoreo, y trazabilidad en la detección de incidentes o conductas inapropiadas en tiempo real.',
                    'help_text': 'Evaluar los controles específicos de seguridad en áreas de gimnasio.',
                    'weight': 1.2,
                    'order': 19
                },
                {
                    'question_text': 'La(s) zona(s) de piscinas o zonas húmedas, se tienen controles efectivos para prevenir e identificar accidentes o conductas peligrosas para las personas en dichas zonas.',
                    'help_text': 'Verificar los controles de seguridad específicos en áreas de piscinas.',
                    'weight': 1.4,
                    'order': 20
                },
                {
                    'question_text': 'La(s) zona(s) de piscinas tienen controles efectivos para cerrar y detectar el uso en los momentos de cierre, evitando el uso no autorizado y las situaciones de riesgo por ahogamiento, uso inadecuado o comportamientos desadaptados.',
                    'help_text': 'Confirmar los controles para evitar uso no autorizado de piscinas fuera de horario.',
                    'weight': 1.3,
                    'order': 21
                }
            ],
            'controles_accesos': [
                {
                    'question_text': 'Se dispone de un control de acceso que permita la identificación positiva de los huéspedes que ingresan al hotel que sea efectivo para minimizar las suplantaciones o ingresos fraudulentos.',
                    'help_text': 'Evaluar la efectividad del sistema de identificación para prevenir accesos fraudulentos.',
                    'weight': 1.5,
                    'order': 1
                },
                {
                    'question_text': 'Se dispone de un control de acceso primario asociado a un anillo o capa externa que tenga extendido el control primario de las personas que ingresan a la instalación, validando la reserva de las personas que ingresan.',
                    'help_text': 'Verificar la existencia de controles de acceso en capas externas con validación de reservas.',
                    'weight': 1.4,
                    'order': 2
                },
                {
                    'question_text': 'El mecanismo de identificación es fiable de no ser suplantado, copiado o adulterado y deja la evidencia y trazabilidad del proceso de manera clara que pueda ser consultada.',
                    'help_text': 'Confirmar la confiabilidad y trazabilidad del sistema de identificación.',
                    'weight': 1.5,
                    'order': 3
                },
                {
                    'question_text': 'El mecanismo ofrece validación clara y oportuna con el proceso hotelero interesado para evitar autorizaciones irresponsables que conlleven accesos a la instalación hotelera.',
                    'help_text': 'Evaluar la integración del control de acceso con los procesos hoteleros.',
                    'weight': 1.3,
                    'order': 4
                },
                {
                    'question_text': 'El control de acceso dispone de los procedimientos o medidas para la mitigación de los riesgos de ingreso de materiales peligrosos a la instalación hotelera como identificación de estos que deben ser notificados, aquellos que no puedan ingresar y los mecanismos para mantener el control constante de estos dentro de la instalación cuando fuesen autorizados. Dada la criticidad de este, debe quedar evidencia del cumplimiento.',
                    'help_text': 'Verificar los controles para materiales peligrosos y su documentación.',
                    'weight': 1.5,
                    'order': 5
                },
                {
                    'question_text': 'El sistema de validación del control de acceso perimetral (en caso de tenerlo); una vez una persona ha ingresado, se restringe de poder ingresar otra persona con la misma identificación.',
                    'help_text': 'Confirmar que el sistema previene el uso simultáneo de credenciales.',
                    'weight': 1.4,
                    'order': 6
                },
                {
                    'question_text': 'Se dispone del personal o infraestructura física necesaria para evitar el ingreso abusivo o violento a la instalación hotelera o los mecanismos de respuesta efectivos que permitan una neutralización.',
                    'help_text': 'Evaluar las medidas físicas y de personal para prevenir ingresos forzados.',
                    'weight': 1.4,
                    'order': 7
                },
                {
                    'question_text': 'La empresa hotelera deberá contar con el personal de seguridad suficiente para cubrir los accesos de manera tal que se garantice el control las veinticuatro (24) horas en la instalación y que cubran procesos simultáneos de entrada peatonal y vehicular si fuese el caso.',
                    'help_text': 'Verificar la cobertura 24/7 del personal de seguridad en accesos.',
                    'weight': 1.4,
                    'order': 8
                },
                {
                    'question_text': 'Los controles de acceso cuentan dentro de su infraestructura con un adecuado diseño de bretes para evitar el paso no autorizado en los puntos donde se une con el cerramiento u otras áreas que estén colindantes (incluso para los ingresos vehiculares).',
                    'help_text': 'Confirmar el diseño físico que previene accesos no autorizados.',
                    'weight': 1.3,
                    'order': 9
                },
                {
                    'question_text': 'Los protocolos de seguridad de la entrada consideran claramente cada uno de los tipos de usuarios que pueden tener una instalación hotelera: Huéspedes, empleados, contratistas, autoridades, visitantes, especificando los mecanismos de identificación y validación.',
                    'help_text': 'Evaluar la diferenciación de protocolos según tipo de usuario.',
                    'weight': 1.3,
                    'order': 10
                },
                {
                    'question_text': 'Las funciones del personal de seguridad que controla los accesos, se encuentran documentadas en los puestos, son consultadas y divulgadas con el fin de lograr el aseguramiento en el cumplimiento de estas medidas y se dispone de las versiones vigentes en el puesto de control de acceso.',
                    'help_text': 'Verificar la documentación y divulgación de funciones del personal de acceso.',
                    'weight': 1.2,
                    'order': 11
                },
                {
                    'question_text': 'Se dispone de las funciones y procedimientos para el personal de los accesos que se alineen con los planes de emergencias, para proceder a facilitar las salidas de las personas en dichos casos explicando claramente las actividades para tal fin.',
                    'help_text': 'Confirmar la integración de procedimientos de acceso con planes de emergencia.',
                    'weight': 1.4,
                    'order': 12
                },
                {
                    'question_text': 'La organización hotelera define los eventos que ameriten el control y prevención para el ingreso de armas por los accesos de huéspedes y la permanencia de estos controles en los accesos de los empleados de la organización.',
                    'help_text': 'Evaluar las políticas específicas para control de armas.',
                    'weight': 1.5,
                    'order': 13
                },
                {
                    'question_text': 'Se dispone de los mecanismos efectivos para la restricción del ingreso de armas de fuego a la instalación y se puede dar cuenta del cumplimiento de estos tanto en la detección, como en la restricción.',
                    'help_text': 'Verificar los sistemas de detección y restricción de armas de fuego.',
                    'weight': 1.5,
                    'order': 14
                },
                {
                    'question_text': 'Se tiene un mecanismo para que las personas que pueden acceder por temporalidad sea de fácil consulta y restrinja una vez vencida la autorización.',
                    'help_text': 'Confirmar el control de accesos temporales y su vencimiento automático.',
                    'weight': 1.3,
                    'order': 15
                },
                {
                    'question_text': 'Para el procedimiento de egreso, se desarrolla adecuadamente para evitar la sustracción de bienes y elementos de los huéspedes, del hotel o que no sean de quien los retira.',
                    'help_text': 'Evaluar los controles de egreso para prevenir sustracciones.',
                    'weight': 1.3,
                    'order': 16
                },
                {
                    'question_text': 'El diseño del sistema de control de acceso permite mantener un control de prevención de accesos fraudulentos que sean avalados por la persona de seguridad a la instalación hotelera.',
                    'help_text': 'Verificar que el sistema facilite la validación por personal de seguridad.',
                    'weight': 1.4,
                    'order': 17
                },
                {
                    'question_text': 'El sistema de control de acceso permite tener el adecuado control de los vehículos que ingresan y salen de la instalación hotelera, mitigando el riesgo de salida no controlada de un vehículo y dejando la trazabilidad de la información.',
                    'help_text': 'Confirmar el control y trazabilidad de acceso vehicular.',
                    'weight': 1.4,
                    'order': 18
                },
                {
                    'question_text': 'El sistema de control de acceso, faculta al personal de seguridad a hacer una revisión del personal de empleados generando disuasión y generando una cultura de no retirar elementos de los huéspedes o del hotel.',
                    'help_text': 'Evaluar las facultades de revisión del personal para prevenir hurtos.',
                    'weight': 1.2,
                    'order': 19
                },
                {
                    'question_text': 'Se dispone del mecanismo de retiro del sistema de identificación de los huéspedes de check out que permita auditar las salidas y controlar que puedan permanecer más del tiempo establecido (solo cuando aplique) de manera que se controle adecuadamente la salida de personas y el check out del sistema.',
                    'help_text': 'Verificar el control de identificaciones durante el check-out.',
                    'weight': 1.3,
                    'order': 20
                },
                {
                    'question_text': 'Se tiene algún sistema efectivo de control frente al préstamo o reclamación fraudulenta de pérdida del distintivo para el ingreso al hotel o el uso de los privilegios del hotel, penalizando la pérdida de este.',
                    'help_text': 'Confirmar los controles contra uso fraudulento de distintivos de acceso.',
                    'weight': 1.3,
                    'order': 21
                }
            ],
            'seguridad_habitaciones': [
                {
                    'question_text': 'El acceso a las áreas de alojamiento o espacios dedicados al hospedaje, cuentan con un control de acceso que permita el paso exclusivo a los huéspedes, minimizando efectivamente el riesgo de intrusión a estas.',
                    'help_text': 'Evaluar la efectividad del control de acceso exclusivo para huéspedes en áreas de alojamiento.',
                    'weight': 1.5,
                    'order': 1
                },
                {
                    'question_text': 'El acceso por sistemas de elevadores es efectivo para evitar que una persona externa pueda ingresar a partir del uso por parte de personas que si disponen del mecanismo para el ingreso a las zonas de alojamiento.',
                    'help_text': 'Verificar los controles de seguridad en elevadores para prevenir accesos no autorizados.',
                    'weight': 1.4,
                    'order': 2
                },
                {
                    'question_text': 'La organización hotelera, deja la evidencia fílmica, documental o digital de las personas que acceden a las áreas de habitaciones.',
                    'help_text': 'Confirmar la existencia de registro audiovisual o digital de accesos a habitaciones.',
                    'weight': 1.3,
                    'order': 3
                },
                {
                    'question_text': 'La organización hotelera tiene un sistema efectivo de detección del ingreso de una persona que no cumple con los criterios de huésped en los espacios o instalaciones dedicados al hospedaje de clientes.',
                    'help_text': 'Evaluar los sistemas de detección de personas no autorizadas en áreas de hospedaje.',
                    'weight': 1.4,
                    'order': 4
                },
                {
                    'question_text': 'La estructura de las habitaciones es de material rígido como bloque, ladrillo o concreto (u otros, que eviten ruptura rápida para hacer intrusiones.',
                    'help_text': 'Verificar que la construcción de habitaciones utilice materiales resistentes a intrusiones.',
                    'weight': 1.3,
                    'order': 5
                },
                {
                    'question_text': 'Las puertas de las habitaciones deberán contar con refuerzo en el marco, ser maciza por dentro, tener mirilla y la chapa deberá garantizar el registro de la apertura y dificultad de clonación o decodificación de los dispositivos de apertura.',
                    'help_text': 'Confirmar las especificaciones de seguridad de puertas de habitaciones.',
                    'weight': 1.5,
                    'order': 6
                },
                {
                    'question_text': 'Las ventanas de las habitaciones hoteleras deberán tener mecanismos de apertura limitada para evitar la intrusión desde la parte externa. En el caso de que la habitación tenga balcón exterior y puertas corredizas, deberá contar como mínimo con sistema de CCTV orientado y visible en el cubrimiento de esta área así como la posibilidad de identificar por parte de los encargados de monitoreo las puertas que han sido dejadas abiertas (esto aplica prioritariamente a los pisos bajos (primero y segundo) o a los pisos que tengan mecanismos de acceso laterales a las terrazas).',
                    'help_text': 'Evaluar las medidas de seguridad en ventanas y balcones de habitaciones.',
                    'weight': 1.4,
                    'order': 7
                },
                {
                    'question_text': 'La habitación del hotel debe disponer de cajilla de seguridad gratuita, anclada a la pared adecuadamente y su mecanismo de apertura por parte de la administración, no debe ser genéricamente comercial, sino exclusivo de las cajillas de seguridad de la instalación hotelera.',
                    'help_text': 'Verificar la disponibilidad y especificaciones de cajas fuertes en habitaciones.',
                    'weight': 1.3,
                    'order': 8
                },
                {
                    'question_text': 'La cajilla de seguridad de la instalación hotelera deberá tener las dimensiones mínimas que permitan guardar los elementos habituales de valor: laptop de 15.6 pulgadas, y en consecuencia elementos de menor tamaño.',
                    'help_text': 'Confirmar que las cajas fuertes tengan capacidad adecuada para elementos de valor.',
                    'weight': 1.2,
                    'order': 9
                },
                {
                    'question_text': 'El sistema de seguridad de las puertas de la habitación deberá generar una alarma controlada para evidenciar las puertas que han sido deficientemente cerradas y poder generar mecanismos prioritarios de control del riesgo.',
                    'help_text': 'Evaluar los sistemas de alerta para puertas mal cerradas.',
                    'weight': 1.3,
                    'order': 10
                },
                {
                    'question_text': 'Se dispone de una revisión estándar en el día para validar por lo menos cada cuatro horas el área de las habitaciones, realizando por lo menos: 1. Identificación de personas sospechosas 2. Identificación y reporte de habitaciones mal cerradas 3. Presencia en puntos críticos 4. Actividad de disuasión. Toda novedad deberá quedar registrada y contar con el debido seguimiento y acción tomada al respecto.',
                    'help_text': 'Verificar la implementación de rondas de seguridad cada 4 horas en área de habitaciones.',
                    'weight': 1.4,
                    'order': 11
                },
                {
                    'question_text': 'La organización hotelera debe efectuar una revisión de la habitación una vez finalizado el hospedaje del huésped (check out) que valide los elementos olvidados, los faltantes y los consumos de las habitaciones.',
                    'help_text': 'Confirmar los procedimientos de revisión post check-out.',
                    'weight': 1.2,
                    'order': 12
                },
                {
                    'question_text': 'En caso de que la habitación de la instalación hotelera tenga acceso compartido con la habitación contigua, la organización hotelera deberá tener un mecanismo fiable del control del cierre de esta y las evidencias de la aprobación de la apertura en los casos que sean definidos por los huéspedes.',
                    'help_text': 'Evaluar los controles para habitaciones con accesos compartidos.',
                    'weight': 1.4,
                    'order': 13
                },
                {
                    'question_text': 'La empresa hotelera deberá definir claramente el procedimiento para el encargado o los encargados de seguridad regulando el ingreso a la habitación ocupada y las excepciones que le habilitarían la realización de esta actividad, siendo solamente en los casos que se consideren críticos para la seguridad o la salud del huésped.',
                    'help_text': 'Verificar los protocolos para ingreso de seguridad a habitaciones ocupadas.',
                    'weight': 1.5,
                    'order': 14
                },
                {
                    'question_text': 'La organización hotelera dispone de un control efectivo para la seguridad de las habitaciones que tenga la posibilidad de identificar con alto grado de fiabilidad presencia de personas sospechosas o no autorizadas en las zonas de habitaciones.',
                    'help_text': 'Confirmar los sistemas de detección de personas no autorizadas en zonas de habitaciones.',
                    'weight': 1.4,
                    'order': 15
                },
                {
                    'question_text': 'La organización hotelera garantiza que el personal de seguridad destinado para las recorridas de las habitaciones cuenta con el entrenamiento necesario en: detección de conductas sospechosas, uso de niveles de la fuerza, plan de atención de emergencias y procedimientos de ingreso a las habitaciones, como mínimo una vez al año.',
                    'help_text': 'Evaluar la capacitación anual del personal de seguridad para área de habitaciones.',
                    'weight': 1.3,
                    'order': 16
                },
                {
                    'question_text': 'La organización hotelera, mantendrá actualizada la identificación de las zonas críticas y habitaciones con mayor nivel de concentración del riesgo, contando con los mecanismos necesarios para su efectiva mitigación y trazabilidad.',
                    'help_text': 'Verificar la identificación y control de zonas críticas en área de habitaciones.',
                    'weight': 1.4,
                    'order': 17
                },
                {
                    'question_text': 'La organización hotelera cuenta con un procedimiento de seguridad para controlar el acceso de personas no registradas y de dudosa vinculación con el huésped con el fin de evitar el sometimiento o afectación de este.',
                    'help_text': 'Confirmar los procedimientos para controlar acceso de personas no registradas.',
                    'weight': 1.4,
                    'order': 18
                },
                {
                    'question_text': 'La organización hotelera mantiene el registro detallado y vigente de las pérdidas en habitaciones y de las acciones de mejoramiento implementadas en virtud de las investigaciones realizadas.',
                    'help_text': 'Evaluar el registro y seguimiento de incidentes en habitaciones.',
                    'weight': 1.3,
                    'order': 19
                },
                {
                    'question_text': 'La organización hotelera, dispone de detectores de humo y mecanismos efectivos para prevenir el incendio en las habitaciones.',
                    'help_text': 'Verificar los sistemas de detección y prevención de incendios en habitaciones.',
                    'weight': 1.5,
                    'order': 20
                },
                {
                    'question_text': 'La organización hotelera dispone de medidas de mitigación del riesgo de incendio en las habitaciones a partir del control de los equipos de las fuentes de calor con elementos sustitutos o algún otro tipo de seguimiento o trazabilidad.',
                    'help_text': 'Confirmar las medidas de control de fuentes de calor para prevenir incendios.',
                    'weight': 1.4,
                    'order': 21
                },
                {
                    'question_text': 'El proceso de aseo a las habitaciones dispone de un procedimiento para que durante el aseo no ingrese una persona desconocida o suplantando a un huésped y que restrinja el criterio de la persona encargada del aseo o del minibar, manteniendo efectivo el procedimiento.',
                    'help_text': 'Evaluar los controles de seguridad durante el proceso de limpieza de habitaciones.',
                    'weight': 1.3,
                    'order': 22
                },
                {
                    'question_text': 'Se tiene, dispone y cumple el procedimiento de acceso a las habitaciones por parte de los diferentes tipos de empleados facultados para acceder a estas cuando están ocupadas y discriminando los motivos que generan esta habilitación.',
                    'help_text': 'Verificar los protocolos de acceso de empleados a habitaciones ocupadas.',
                    'weight': 1.4,
                    'order': 23
                },
                {
                    'question_text': 'Se maneja un sistema de lost & found efectivo que busque almacenar los elementos y valores dejados por los huéspedes así como un sistema de estímulos a los empleados que reporten todos los elementos de valor olvidados.',
                    'help_text': 'Confirmar la efectividad del sistema de objetos perdidos y estímulos al personal.',
                    'weight': 1.2,
                    'order': 24
                },
                {
                    'question_text': 'Se dispone de manera visible los números de emergencia que el huésped debe usar en caso de una emergencia.',
                    'help_text': 'Evaluar la visibilidad de información de emergencia en habitaciones.',
                    'weight': 1.3,
                    'order': 25
                },
                {
                    'question_text': 'Se tiene el plano de evacuación del hotel y es fácilmente entendible por el huésped, así como visible para los puntos de mayor observación cuando este se encuentra en la habitación.',
                    'help_text': 'Verificar la disponibilidad y claridad de planos de evacuación en habitaciones.',
                    'weight': 1.4,
                    'order': 26
                },
                {
                    'question_text': 'Se dispone de un área exclusiva para permitir el ingreso de huéspedes que requieren protección ejecutiva o que por su nivel de riesgo deben mantener unas condiciones de seguridad especiales.',
                    'help_text': 'Confirmar la existencia de áreas especiales para huéspedes de alto riesgo.',
                    'weight': 1.3,
                    'order': 27
                },
                {
                    'question_text': 'El personal de seguridad, así como el personal de servicio en las habitaciones reportar las habitaciones que sean encontradas abiertas, dejando el registro de la novedad, verificando la posible hora de salida del huésped y los registros de cámaras para evidenciar posibles intrusiones, siendo en cualquier caso obligatorio revisar que el huésped no se encuentre en la misma, así como la normalidad al interior de la misma y darle un correcto cierre.',
                    'help_text': 'Evaluar los protocolos para habitaciones encontradas abiertas.',
                    'weight': 1.4,
                    'order': 28
                },
                {
                    'question_text': 'El sistema de seguridad de la organización hotelera permite restringir el acceso a la habitación una vez se finaliza su tiempo de permanencia en el hotel.',
                    'help_text': 'Verificar la restricción automática de acceso post check-out.',
                    'weight': 1.3,
                    'order': 29
                },
                {
                    'question_text': 'El sistema de ingreso a la habitación es adecuado para evitar la pérdida de este y mantiene la confidencialidad del sistema al cual tiene la viabilidad de aperturar.',
                    'help_text': 'Confirmar la seguridad y confidencialidad del sistema de acceso a habitaciones.',
                    'weight': 1.4,
                    'order': 30
                }
            ],
            'seguridad_activos': [
                {
                    'question_text': 'Sistema Hidráulico: La Organización hotelera debe tener un mecanismo de cierre adecuado para la seguridad de los tanques de agua.',
                    'help_text': 'Evaluar los sistemas de cierre y seguridad de tanques de agua del hotel.',
                    'weight': 1.5,
                    'order': 1
                },
                {
                    'question_text': 'Sistema Hidráulico: La Organización hotelera debe tener una estructura rígida 360° que evite zonas de intrusión no controladas.',
                    'help_text': 'Verificar la protección perimetral completa de sistemas hidráulicos.',
                    'weight': 1.4,
                    'order': 2
                },
                {
                    'question_text': 'Sistema Hidráulico: La Organización hotelera debe tener un mecanismo de detección de la apertura o cierres erróneos de los tanques de agua.',
                    'help_text': 'Confirmar sistemas de detección para apertura/cierre de tanques de agua.',
                    'weight': 1.4,
                    'order': 3
                },
                {
                    'question_text': 'Sistema Hidráulico: La Organización hotelera debe disponer de un sistema de detección de movimiento al interior del recinto donde están los tanques.',
                    'help_text': 'Evaluar sistemas de detección de movimiento en áreas de tanques.',
                    'weight': 1.3,
                    'order': 4
                },
                {
                    'question_text': 'Sistema Hidráulico: La Organización hotelera debe disponer de un sistema de monitoreo al ingreso del sistema hidráulico y al interior del área de los tanques.',
                    'help_text': 'Verificar sistemas de monitoreo de acceso a sistemas hidráulicos.',
                    'weight': 1.3,
                    'order': 5
                },
                {
                    'question_text': 'Sistema Hidráulico: La Organización hotelera debe disponer de un sistema de monitoreo de alarmas en donde se evidencien las pruebas periódicas de su óptimo funcionamiento.',
                    'help_text': 'Confirmar monitoreo de alarmas y pruebas de funcionamiento del sistema hidráulico.',
                    'weight': 1.2,
                    'order': 6
                },
                {
                    'question_text': 'Sistema Hidráulico: La Organización hotelera debe disponer de un adecuado manejo de las llaves de los tanques de agua.',
                    'help_text': 'Evaluar el control y manejo de llaves de acceso a tanques.',
                    'weight': 1.3,
                    'order': 7
                },
                {
                    'question_text': 'Sistema Hidráulico: La Organización hotelera debe disponer de un procedimiento y la evidencia del cumplimiento del control restringido y las aperturas realizadas, identificando preventivamente la persona antes de que la apertura se realice.',
                    'help_text': 'Verificar procedimientos de control y evidencia de accesos a sistemas hidráulicos.',
                    'weight': 1.4,
                    'order': 8
                },
                {
                    'question_text': 'Sistema Hidráulico: La Organización hotelera debe disponer de un adecuado mecanismo de respuesta frente a cualquier intrusión en los tanques de agua, al igual que evidencia de las pruebas realizadas.',
                    'help_text': 'Confirmar mecanismos de respuesta ante intrusiones en tanques de agua.',
                    'weight': 1.4,
                    'order': 9
                },
                {
                    'question_text': 'Sistema Hidráulico: La Organización tiene señal preventiva refiriendo al ingreso restringido a los tanques de agua.',
                    'help_text': 'Evaluar señalización preventiva para acceso restringido a tanques.',
                    'weight': 1.1,
                    'order': 10
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización hotelera debe tener un mecanismo de cierre adecuado para la seguridad de las subestaciones eléctricas, plantas de respaldo y Tanques de combustible.',
                    'help_text': 'Verificar sistemas de cierre para infraestructura eléctrica crítica.',
                    'weight': 1.5,
                    'order': 11
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización hotelera debe tener una estructura rígida 360° que evite zonas de intrusión no controladas.',
                    'help_text': 'Confirmar protección perimetral completa de sistemas eléctricos.',
                    'weight': 1.4,
                    'order': 12
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización hotelera debe tener un mecanismo de detección de la apertura o cierres erróneos de activos clave como: subestaciones, plantas de respaldo y combustible.',
                    'help_text': 'Evaluar detección de apertura/cierre en sistemas eléctricos críticos.',
                    'weight': 1.4,
                    'order': 13
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización hotelera debe disponer de un sistema de detección de movimiento al interior del recinto donde están activos clave como: subestaciones, plantas de respaldo y combustible.',
                    'help_text': 'Verificar detección de movimiento en áreas de sistemas eléctricos.',
                    'weight': 1.3,
                    'order': 14
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización hotelera debe disponer de un sistema de monitoreo al ingreso las subestaciones, plantas de energía de respaldo y área de almacenamiento de combustibles.',
                    'help_text': 'Confirmar monitoreo de acceso a infraestructura eléctrica crítica.',
                    'weight': 1.3,
                    'order': 15
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización hotelera debe disponer de un sistema de monitoreo de alarmas en donde se evidencien las pruebas periódicas de su óptimo funcionamiento.',
                    'help_text': 'Evaluar monitoreo de alarmas y pruebas de sistemas eléctricos.',
                    'weight': 1.2,
                    'order': 16
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización hotelera debe disponer de un adecuado manejo de las llaves de las zonas donde se resguardan las subestaciones, las plantas de energía de respaldo y el combustible.',
                    'help_text': 'Verificar control de llaves para acceso a sistemas eléctricos.',
                    'weight': 1.3,
                    'order': 17
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización hotelera debe disponer de un procedimiento y la evidencia del cumplimiento del control restringido y las aperturas realizadas, identificando preventivamente la persona antes de que la apertura se realice.',
                    'help_text': 'Confirmar procedimientos de control y evidencia para sistemas eléctricos.',
                    'weight': 1.4,
                    'order': 18
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización hotelera debe disponer de un adecuado mecanismo de respuesta frente a cualquier intrusión en los sistemas de subestaciones, plantas generadoras y tanques de combustible.',
                    'help_text': 'Evaluar mecanismos de respuesta ante intrusiones en sistemas eléctricos.',
                    'weight': 1.4,
                    'order': 19
                },
                {
                    'question_text': 'Sistema Eléctrico: La Organización tiene señalización preventiva refiriendo al ingreso restringido a los tanques de agua.',
                    'help_text': 'Verificar señalización preventiva para sistemas eléctricos.',
                    'weight': 1.1,
                    'order': 20
                },
                {
                    'question_text': 'Se dispone de un procedimiento que establezca los cargos y las personas que pueden ingresar a los activos clave de la organización.',
                    'help_text': 'Confirmar definición de roles y accesos a activos críticos.',
                    'weight': 1.3,
                    'order': 21
                },
                {
                    'question_text': 'Servidores e información: La Organización hotelera debe tener un mecanismo de cierre adecuado para la seguridad de los servidores y lugares donde se tenga información clave del negocio.',
                    'help_text': 'Evaluar seguridad física de servidores e información crítica.',
                    'weight': 1.5,
                    'order': 22
                },
                {
                    'question_text': 'Servidores e información: La Organización hotelera debe tener una estructura rígida 360° que evite zonas de intrusión a los lugares donde se almacena la información clave del negocio.',
                    'help_text': 'Verificar protección perimetral de centros de datos.',
                    'weight': 1.4,
                    'order': 23
                },
                {
                    'question_text': 'Servidores e información: La Organización hotelera debe tener un mecanismo de detección de la apertura o cierres erróneos de los lugares donde se encuentra almacenada la información clave de negocio y servidores.',
                    'help_text': 'Confirmar detección de accesos a centros de información.',
                    'weight': 1.4,
                    'order': 24
                },
                {
                    'question_text': 'Servidores e información: La Organización hotelera debe disponer de un sistema de detección de movimiento al interior del recinto donde están activos clave como: servidores información.',
                    'help_text': 'Evaluar detección de movimiento en áreas de servidores.',
                    'weight': 1.3,
                    'order': 25
                },
                {
                    'question_text': 'Servidores e información: La Organización hotelera debe disponer de un sistema de monitoreo al ingreso los lugares en donde se almacene activos clave como servidores e información.',
                    'help_text': 'Verificar monitoreo de acceso a centros de información.',
                    'weight': 1.3,
                    'order': 26
                },
                {
                    'question_text': 'Servidores e información: La Organización hotelera debe disponer de un sistema de monitoreo de alarmas en donde se evidencien las pruebas periódicas de su óptimo funcionamiento, relacionados con los servidores y áreas sensibles de almacenamiento de información.',
                    'help_text': 'Confirmar monitoreo de alarmas para sistemas de información.',
                    'weight': 1.2,
                    'order': 27
                },
                {
                    'question_text': 'Servidores e información: La Organización hotelera debe disponer de un adecuado manejo de las llaves de las zonas donde se resguardan los servidores y áreas sensibles de manejo de información.',
                    'help_text': 'Evaluar control de llaves para acceso a servidores.',
                    'weight': 1.3,
                    'order': 28
                },
                {
                    'question_text': 'Servidores e información: La Organización hotelera debe disponer de un procedimiento y la evidencia del cumplimiento del control restringido y las aperturas realizadas, identificando preventivamente la persona antes de que la apertura se realice.',
                    'help_text': 'Verificar procedimientos de control para acceso a información crítica.',
                    'weight': 1.4,
                    'order': 29
                },
                {
                    'question_text': 'Servidores e información: La Organización hotelera debe disponer de un adecuado mecanismo de respuesta frente a cualquier intrusión en los servidores y áreas de almacenamiento de información sensible.',
                    'help_text': 'Confirmar mecanismos de respuesta ante intrusiones en sistemas de información.',
                    'weight': 1.4,
                    'order': 30
                },
                {
                    'question_text': 'Servidores e información: La Organización tiene señalización preventiva refiriendo al ingreso restringido al área de los servidores y lugar con información sensible.',
                    'help_text': 'Evaluar señalización preventiva para centros de datos.',
                    'weight': 1.1,
                    'order': 31
                },
                {
                    'question_text': 'Propiedad del huésped: La organización hotelera, procura un adecuado cuidado de los activos clave propiedad de los huéspedes que sean dejados en custodia a través de un área específica para el almacenamiento e identificación de estos.',
                    'help_text': 'Verificar sistemas de custodia para pertenencias de huéspedes.',
                    'weight': 1.3,
                    'order': 32
                },
                {
                    'question_text': 'Propiedad del huésped: La organización hotelera, dispone de un procedimiento para la recepción, almacenamiento, custodia y entrega de la propiedad del huésped a su titular.',
                    'help_text': 'Confirmar procedimientos para manejo de propiedad de huéspedes.',
                    'weight': 1.3,
                    'order': 33
                },
                {
                    'question_text': 'Propiedad del cliente: La organización hotelera dispone de un procedimiento para identificación, recepción, almacenamiento seguro, custodia y entrega de los elementos de los asistentes a eventos que requieran este servicio (solo en los casos que este servicio sea prestado por el hotel).',
                    'help_text': 'Evaluar procedimientos para custodia de pertenencias en eventos.',
                    'weight': 1.2,
                    'order': 34
                },
                {
                    'question_text': 'La organización hotelera, cuenta con un procedimiento seguro para mantener el control y evitar pérdidas de los equipajes del huésped cuando este no pueda hacer el check in.',
                    'help_text': 'Verificar control de equipajes cuando no se puede realizar check-in inmediato.',
                    'weight': 1.3,
                    'order': 35
                }
            ],
            'seguridad_parqueo': [
                {
                    'question_text': 'El área de parqueo para huéspedes que van a realizar el check in dispone de un control de los vehículos, para evitar que sean sustraídos los elementos cuando este queda solo.',
                    'help_text': 'Evaluar los controles de seguridad para vehículos durante el proceso de check-in.',
                    'weight': 1.4,
                    'order': 1
                },
                {
                    'question_text': 'La organización hotelera cuenta con sistemas de grabación de CCTV en el área total de parqueaderos que permita evidenciar y consultar cualquier reclamación de un huésped sobre el estado de su vehículo o sobre dudas que surjan de elementos que no se encuentran.',
                    'help_text': 'Verificar la cobertura completa de CCTV en áreas de parqueadero para evidencia y reclamos.',
                    'weight': 1.5,
                    'order': 2
                },
                {
                    'question_text': 'La organización hotelera cuenta con un área de parqueo que esté aislada efectivamente del entorno público y por tanto que no sea susceptible de que las amenazas accedan fácilmente a esta zona.',
                    'help_text': 'Confirmar el aislamiento efectivo del parqueadero respecto a áreas públicas.',
                    'weight': 1.4,
                    'order': 3
                },
                {
                    'question_text': 'El área de parqueo cuenta con la iluminación necesaria para facilitar la ubicación de los vehículos y mejorar el desempeño del sistema de CCTV.',
                    'help_text': 'Evaluar la adecuación de la iluminación para seguridad y efectividad del CCTV.',
                    'weight': 1.3,
                    'order': 4
                },
                {
                    'question_text': 'La organización hotelera cuenta con un sistema de seguridad en el parqueadero ajustado al riesgo residual esperado, por lo cual las amenazas, las vulnerabilidades y los residuos deben estar adecuadamente calculados.',
                    'help_text': 'Verificar que el sistema de seguridad esté basado en análisis de riesgo apropiado.',
                    'weight': 1.4,
                    'order': 5
                },
                {
                    'question_text': 'La organización hotelera, garantiza el adecuado registro de la información relacionada con el titular del vehículo, el vehículo y la relación con la habitación.',
                    'help_text': 'Confirmar el registro completo de información vehículo-propietario-habitación.',
                    'weight': 1.3,
                    'order': 6
                },
                {
                    'question_text': 'En caso de contar con servicio de Valet Parking, la organización hotelera garantiza el adecuado manejo, identificación, clasificación, almacenamiento, trazabilidad y entrega de las llaves al propietario evidenciado mediante un procedimiento y los registros del cumplimiento de este.',
                    'help_text': 'Evaluar los procedimientos completos de valet parking cuando aplique.',
                    'weight': 1.4,
                    'order': 7
                },
                {
                    'question_text': 'El personal de valet parking o parqueadero, registra si al momento del recibido del vehículo existe alguna anomalía con su estado o estructura que deba ser registrado y notificado al responsable de este por parte del hotel.',
                    'help_text': 'Verificar el registro de condiciones previas del vehículo al recibirlo.',
                    'weight': 1.3,
                    'order': 8
                },
                {
                    'question_text': 'El sistema de seguridad del parqueadero cuenta con un sistema de validación y reconocimiento positivo de quien retira el vehículo este debidamente autorizado para esto.',
                    'help_text': 'Confirmar sistemas de validación de identidad para retiro de vehículos.',
                    'weight': 1.5,
                    'order': 9
                },
                {
                    'question_text': 'La organización hotelera controla adecuadamente los parqueaderos asignados comparando la cantidad de vehículos reales en este.',
                    'help_text': 'Evaluar el control de ocupación real vs. asignada en parqueaderos.',
                    'weight': 1.2,
                    'order': 10
                },
                {
                    'question_text': 'Los vehículos autorizados de huéspedes en el parqueadero son adecuadamente identificados y controlados con procedimientos que se evidencien su cumplimiento.',
                    'help_text': 'Verificar la identificación y control de vehículos autorizados con evidencia documental.',
                    'weight': 1.3,
                    'order': 11
                },
                {
                    'question_text': 'La organización hotelera dispone de un seguro con el fin de cubrir los daños o pérdidas ocurridos a los vehículos por terceras personas o por los empleados a cargo de los vehículos del parqueadero.',
                    'help_text': 'Confirmar la existencia de cobertura de seguro para vehículos en custodia.',
                    'weight': 1.3,
                    'order': 12
                }
            ],
            'gestion_humana': [
                {
                    'question_text': 'La organización hotelera realiza la verificación de la confiabilidad de los candidatos a desempeñarse en cargos críticos (entendidos estos como aquellos que tengan relación directa con el cliente, su propiedad o con el manejo de los activos críticos de la empresa) para validar su lealtad con la ética, transparencia y honestidad.',
                    'help_text': 'Evaluar los procesos de verificación de confiabilidad para cargos críticos.',
                    'weight': 1.5,
                    'order': 1
                },
                {
                    'question_text': 'La organización hotelera efectúa verificación de la confiabilidad de los empleados, cuando se presume de la ejecución de conductas desviadas en contra de la propiedad del huésped, de los empleados o del hotel.',
                    'help_text': 'Verificar los procedimientos de investigación ante presuntas conductas inadecuadas.',
                    'weight': 1.4,
                    'order': 2
                },
                {
                    'question_text': 'La organización hotelera evalúa periódicamente los cargos que por su nivel de criticidad o (acceso a áreas relacionadas con el huésped, acceso y toma de decisiones sobre alojamiento, alimentos y bebidas, información y sistemas de gestión hotelera) deberán ser considerados para la realización de pruebas de confiabilidad.',
                    'help_text': 'Confirmar la evaluación periódica de criticidad de cargos para pruebas de confiabilidad.',
                    'weight': 1.4,
                    'order': 3
                },
                {
                    'question_text': 'Se dispone y se cumple un procedimiento efectivo para informar cuando un empleado o colaborador, deja de laborar en la organización y se eliminan oportunamente los privilegios de acceso al hotel, recursos informáticos y otros sistemas que sean relevantes para el hotel.',
                    'help_text': 'Evaluar los procedimientos de revocación de accesos al terminar la relación laboral.',
                    'weight': 1.5,
                    'order': 4
                },
                {
                    'question_text': 'Se promueven desde recursos humanos iniciativas para el fomento de cultura y compromiso con la seguridad, ética y transparencia de los empleados y colaboradores.',
                    'help_text': 'Verificar las iniciativas de cultura organizacional en seguridad y ética.',
                    'weight': 1.3,
                    'order': 5
                },
                {
                    'question_text': 'Se disponen de planes de capacitación efectivos para la divulgación y compromiso con las medidas de seguridad en cada uno de los procesos del hotel.',
                    'help_text': 'Confirmar la existencia de planes estructurados de capacitación en seguridad.',
                    'weight': 1.4,
                    'order': 6
                },
                {
                    'question_text': 'Desde la gerencia de recursos humanos se promueve la implementación y cumplimiento de funciones y responsabilidades relacionadas con la seguridad en cada uno de los puestos de trabajo con el fin de lograr el compromiso y reportes de situaciones de inseguridad.',
                    'help_text': 'Evaluar la integración de responsabilidades de seguridad en las descripciones de cargo.',
                    'weight': 1.3,
                    'order': 7
                }
            ],
            'seguridad_eventos': [
                {
                    'question_text': 'La organización hotelera notifica al departamento de seguridad de todo evento que se vaya a realizar, con el fin de valorar el riesgo asociado al mismo y en caso de requerir medidas para el tratamiento y control del riesgo, se informa oportunamente al cliente.',
                    'help_text': 'Evaluar el proceso de notificación temprana a seguridad para valoración de riesgos de eventos.',
                    'weight': 1.4,
                    'order': 1
                },
                {
                    'question_text': 'La organización hotelera garantiza que todo evento que se vaya a realizar (excepto los eventos internos del hotel), se deberá verificar la reputación del cliente persona o empresa, para minimizar el riesgo de lavado de activos o financiación del terrorismo.',
                    'help_text': 'Verificar los procesos de due diligence para prevenir lavado de activos y financiación del terrorismo.',
                    'weight': 1.5,
                    'order': 2
                },
                {
                    'question_text': 'El proceso de eventos define antes de la firma del contrato del evento el perfil de riesgo del mismo con el fin de determinar cualquier requerimiento de medidas de seguridad o controles del riesgo para prevenir la afectación a la integridad de las personas o de la instalación hotelera.',
                    'help_text': 'Confirmar la definición previa del perfil de riesgo antes de la contratación del evento.',
                    'weight': 1.5,
                    'order': 3
                },
                {
                    'question_text': 'La organización hotelera promueve buenas prácticas para que las personas contratadas de manera temporal para la prestación del servicio, hayan superado un debido proceso de verificación de su confiabilidad.',
                    'help_text': 'Evaluar los procesos de verificación de confiabilidad para personal temporal de eventos.',
                    'weight': 1.3,
                    'order': 4
                },
                {
                    'question_text': 'El proceso, área o departamento encargado de los eventos remite oportunamente al proceso de seguridad relacionando al personal que colaborará en el evento, así como los asistentes del mismo, incluyendo la información particular, que permita establecer la identificación positiva al momento de ingresar en el horario previo a la prestación del servicio.',
                    'help_text': 'Verificar la entrega oportuna de información de personal y asistentes para identificación positiva.',
                    'weight': 1.4,
                    'order': 5
                },
                {
                    'question_text': 'El proceso de seguridad dispone de la matriz de riesgos que defina claramente los controles necesarios para los riesgos del evento y los puestos de vigilancia solicitados tengan como soporte los posibles escenarios de riesgos que se deseen mitigar. Por lo tanto, los servicios requeridos deberán tener debidamente definidas las funciones y controles que estos efectuarán. El riesgo residual de esta matriz deberá garantizar la aceptabilidad del riesgo.',
                    'help_text': 'Confirmar la existencia de matriz de riesgos específica para eventos con controles definidos.',
                    'weight': 1.5,
                    'order': 6
                },
                {
                    'question_text': 'La organización hotelera notifica la prohibición del ingreso de cualquier tipo de arma a la instalación hotelera, con excepción de las personalidades que ostentan un nivel de riesgo muy alto, habilitando solo cuando el nivel de riesgo residual, así lo evidencie.',
                    'help_text': 'Evaluar las políticas de control de armas en eventos y excepciones para personalidades de alto riesgo.',
                    'weight': 1.5,
                    'order': 7
                },
                {
                    'question_text': 'La organización hotelera dispone de un procedimiento y la evidencia de su aplicación para reportar a las autoridades posibles situaciones que puedan generar una amenaza para la seguridad del hotel antes de que el evento pueda salirse de control.',
                    'help_text': 'Verificar procedimientos de reporte temprano a autoridades ante amenazas potenciales.',
                    'weight': 1.4,
                    'order': 8
                },
                {
                    'question_text': 'Los equipos que sean ingresados por el organizador del evento, sus contratistas, los equipos de propiedad del hotel o de los asistentes, son debidamente identificados y registrados por las personas de seguridad que según el caso realicen los controles de acceso debidos, con el fin de prevenir el hurto o sustracción de los mismos.',
                    'help_text': 'Confirmar el registro y control de todos los equipos ingresados para eventos.',
                    'weight': 1.3,
                    'order': 9
                },
                {
                    'question_text': 'La organización hotelera deberá disponer de un procedimiento para el registro de los equipos y elementos que hacen parte del evento y que no son provistos por el hotel. El procedimiento debe incluir el registro del equipo y las personas que lo ingresan y lo retiran.',
                    'help_text': 'Evaluar procedimientos específicos para registro de equipos externos al hotel.',
                    'weight': 1.3,
                    'order': 10
                },
                {
                    'question_text': 'La organización hotelera dispone de un procedimiento para el manejo de los elementos "Lost & Found" del evento, en el cual se estipule la gestión de la devolución a su propietario y el adecuado almacenamiento y seguridad de estos.',
                    'help_text': 'Verificar procedimientos específicos de objetos perdidos para eventos.',
                    'weight': 1.2,
                    'order': 11
                },
                {
                    'question_text': 'La organización hotelera procura por mantener un equipamiento necesario para dar cobertura de video vigilancia y almacenamiento de la información de las imágenes de las áreas de los eventos con calidad de video y velocidad, hasta por al menos 3 meses.',
                    'help_text': 'Confirmar la capacidad de videovigilancia y almacenamiento para áreas de eventos.',
                    'weight': 1.4,
                    'order': 12
                },
                {
                    'question_text': 'La organización hotelera, dispone de mecanismos efectivos para el cobro de los eventos, y considerando un mecanismo para la prevención del fraude en el medio de pago de los eventos.',
                    'help_text': 'Evaluar mecanismos de cobro y prevención de fraudes en pagos de eventos.',
                    'weight': 1.3,
                    'order': 13
                },
                {
                    'question_text': 'La organización hotelera deberá disponer de mecanismos para evitar la recepción de pagos de dinero en efectivo conforme la política de prevención de lavado de activos y la financiación del terrorismo.',
                    'help_text': 'Verificar políticas para evitar pagos en efectivo según normativas LAFT.',
                    'weight': 1.4,
                    'order': 14
                },
                {
                    'question_text': 'La organización hotelera se compromete a mantener un claro control de las bebidas requeridas por el cliente para el evento así como la alimentación, previniendo la conducta abusiva del personal sobre estos recursos.',
                    'help_text': 'Confirmar controles sobre bebidas y alimentación para prevenir abuso del personal.',
                    'weight': 1.2,
                    'order': 15
                },
                {
                    'question_text': 'La organización hotelera, garantizar las comunicaciones entre las personas que atienden logísticamente el evento y el personal de seguridad a cargo de este.',
                    'help_text': 'Evaluar la efectividad de comunicaciones entre logística de eventos y seguridad.',
                    'weight': 1.3,
                    'order': 16
                },
                {
                    'question_text': 'La organización hotelera implementa un procedimiento para el manejo de asistentes a eventos con actitud agresiva, con el fin de evitar acciones que empeoren las circunstancias. Este procedimiento es divulgado y conservados los registros o evidencias de que el personal de seguridad y de evento que participa del evento lo conoce adecuadamente.',
                    'help_text': 'Verificar procedimientos para manejo de asistentes agresivos y su divulgación al personal.',
                    'weight': 1.4,
                    'order': 17
                }
            ],
            'seguridad_ayb': [
                {
                    'question_text': 'Se disponen de los mecanismos necesarios para controlar la fuga de víveres o alimentos preparados para usos distintos a los requeridos por el hotel.',
                    'help_text': 'Evaluar los controles para prevenir el uso indebido de alimentos y víveres.',
                    'weight': 1.4,
                    'order': 1
                },
                {
                    'question_text': 'Se disponen de análisis de riesgos y los controles adecuados en los lugares donde se prestan servicios de catering con el fin de evitar que la propiedad del huésped se vea afectada.',
                    'help_text': 'Verificar análisis de riesgos específicos para servicios de catering que protejan la propiedad del huésped.',
                    'weight': 1.3,
                    'order': 2
                },
                {
                    'question_text': 'La organización hotelera dispone de un control adecuado y efectivo para mitigar la fuga o baja de víveres, desde el momento que estos ingresan a la instalación, hasta que son destinados a su preparación.',
                    'help_text': 'Confirmar el control integral de víveres desde ingreso hasta preparación.',
                    'weight': 1.4,
                    'order': 3
                },
                {
                    'question_text': 'Se disponen de las medidas de control para evitar la salida de víveres o alimentos y bebidas del hotel en los accesos, exigiendo algún documento o evidencia debidamente diligenciada para tal fin, solo cuando sea autorizado.',
                    'help_text': 'Evaluar controles de egreso para alimentos y bebidas con documentación apropiada.',
                    'weight': 1.3,
                    'order': 4
                },
                {
                    'question_text': 'Se disponen de mecanismos de seguridad para evitar el acceso de personas no autorizadas a los alimentos antes o durante su preparación.',
                    'help_text': 'Verificar controles de acceso para proteger alimentos durante almacenamiento y preparación.',
                    'weight': 1.4,
                    'order': 5
                },
                {
                    'question_text': 'Se disponen de los mecanismos de seguridad necesarios para mitigar el riesgo de clonación o uso abusivo de la tarjeta de crédito (Esto incluye la captura de los datos de esta).',
                    'help_text': 'Confirmar medidas de seguridad contra fraude con tarjetas de crédito en A&B.',
                    'weight': 1.5,
                    'order': 6
                },
                {
                    'question_text': 'La organización hotelera tiene un mecanismo para asegurar que los envases de productos alimenticios no sean reusados para envasar sustancias no alimenticias que puedan afectar la salud de las personas, así como evitar la reutilización de estos para la fuga o uso para fingir consumos de inventarios no efectuados.',
                    'help_text': 'Evaluar controles sobre reutilización de envases para prevenir riesgos sanitarios y fraudes.',
                    'weight': 1.3,
                    'order': 7
                },
                {
                    'question_text': 'La organización hotelera dispone de los mecanismos para prevenir la manipulación del sistema de ventas de alimentos, por parte del cajero para evitar devoluciones ficticias de productos vendidos.',
                    'help_text': 'Verificar controles anti-fraude en sistemas de ventas para prevenir devoluciones ficticias.',
                    'weight': 1.4,
                    'order': 8
                }
            ],
            'seguridad_reservas': [
                {
                    'question_text': 'La organización hotelera tiene la posibilidad de determinar los perfiles de riesgo de los huéspedes a partir de las reservas y se hacen actividades para mitigar el riesgo en el hotel?',
                    'help_text': 'Evaluar si existe un sistema de evaluación de riesgo de huéspedes basado en patrones de reserva, historial y otras variables para implementar medidas preventivas.',
                    'weight': 1.5,
                    'order': 1
                },
                {
                    'question_text': 'La organización hotelera restringe solo a los cargos necesarios, la información de las reservas y registros de consulta de estas, dejando el registro y trazabilidad de los registros de acceso.',
                    'help_text': 'Verificar que existe control de acceso por roles a la información de reservas y que se mantiene trazabilidad de quién accede a qué información.',
                    'weight': 1.5,
                    'order': 2
                },
                {
                    'question_text': 'Se disponen de los mecanismos de seguridad adecuados para la asignación de usuarios de acceso a la información del huésped, de las reservas y consumos, incluyendo la actualización de los privilegios y eliminación de usuarios.',
                    'help_text': 'Evaluar la gestión del ciclo de vida de usuarios del sistema, incluyendo alta, modificación de permisos y baja de usuarios.',
                    'weight': 1.4,
                    'order': 3
                },
                {
                    'question_text': 'La organización hotelera dispone de algún mecanismo para controlar el riesgo de que se hospeden personas bajo la modalidad walk in',
                    'help_text': 'Verificar procedimientos especiales para huéspedes walk-in, incluyendo verificación de identidad y evaluación de riesgo adicional.',
                    'weight': 1.4,
                    'order': 4
                },
                {
                    'question_text': 'La organización hotelera dispone de los controles claros y efectivos para mitigar el riesgo de hurto de equipajes de los huéspedes durante el check in y el check out',
                    'help_text': 'Evaluar protocolos para manejo seguro de equipajes durante procesos de registro y salida, incluyendo custodia y responsabilidades.',
                    'weight': 1.4,
                    'order': 5
                },
                {
                    'question_text': 'El personal que labora en la recepción tienen asignadas funciones de seguridad, incluyendo procedimientos para emitir facturas, reasignar llaves de habitaciones, suministrar información confidencial del huésped, asegurar equipajes de huéspedes que han realizado check out y se dejan las evidencias y se auditan estas actividades realizadas.',
                    'help_text': 'Verificar que el personal de recepción cuenta con procedimientos documentados para funciones sensibles y que estas actividades son auditables.',
                    'weight': 1.5,
                    'order': 6
                },
                {
                    'question_text': 'La organización hotelera dispone de los mecanismos y recursos necesarios para almacenar con seguridad los equipajes y elementos lost and found de los huéspedes, una vez estos han realizado el check out',
                    'help_text': 'Evaluar instalaciones y procedimientos para almacenamiento seguro de pertenencias de huéspedes post-checkout.',
                    'weight': 1.3,
                    'order': 7
                },
                {
                    'question_text': 'Se dispone de un mecanismo adecuado para evitar el acceso de la información confidencial de los métodos de pago digitales de los huéspedes del hotel que han registrado estos',
                    'help_text': 'Verificar protección de datos de métodos de pago, cumplimiento PCI-DSS y protocolos de manejo de información financiera sensible.',
                    'weight': 1.5,
                    'order': 8
                },
                {
                    'question_text': 'Se dispone de un mecanismo para el registro, identificación y seguimiento de las acompañantes ocasionales de los huéspedes desde el ingreso hasta su salida velando por mantener la seguridad del huésped',
                    'help_text': 'Evaluar procedimientos para control y seguimiento de visitantes ocasionales de huéspedes registrados.',
                    'weight': 1.4,
                    'order': 9
                },
                {
                    'question_text': 'La organización hotelera dispone de los mecanismos adecuados para que el otorgamiento de tarifas preferenciales sean habilitados por las personas que tienen delegación y autoridad para esto, dejando la evidencia de estas decisiones y la posibilidad de auditarlas cuando sea el caso.',
                    'help_text': 'Verificar que existe control de autorización para descuentos y tarifas especiales, con trazabilidad y capacidad de auditoría.',
                    'weight': 1.4,
                    'order': 10
                },
                {
                    'question_text': 'La organización hotelera dispone de los mecanismos para salvaguardar la información fílmica y de registros de los eventos sucedidos en la recepción como mínimo tres meses',
                    'help_text': 'Evaluar sistemas de grabación y almacenamiento de video en áreas de recepción con retención mínima de 3 meses.',
                    'weight': 1.4,
                    'order': 11
                },
                {
                    'question_text': 'La empresa hotelera deberá garantizar que los contratistas o personas que prestan el servicio de transporte están debidamente verificados en su confiabilidad y que sus vehículos gozan de un buen estado de funcionamiento.',
                    'help_text': 'Verificar procesos de verificación y validación de proveedores de transporte, incluyendo antecedentes y estado de vehículos.',
                    'weight': 1.4,
                    'order': 12
                },
                {
                    'question_text': 'La organización hotelera dispone de los mecanismos necesarios para salvaguardar el dinero en efectivo y otros elementos, equipos que puedan ser susceptibles de ser usados ilícitamente, afectados o intercambiados.',
                    'help_text': 'Evaluar protocolos de seguridad para manejo de efectivo y elementos de valor en recepción, incluyendo cajas fuertes y procedimientos de custodia.',
                    'weight': 1.5,
                    'order': 13
                }
            ],
            'seguridad_compras': [
                {
                    'question_text': 'La organización hotelera mantiene una actividad regulatoria y de seguimiento al proceso de compras, en donde se deje evidencia de los controles aplicables a los requerimientos de compras, una selección objetiva de los productos que sea verificable periódicamente y unas medidas coherentes para evitar riesgos de corrupción',
                    'help_text': 'Evaluar la existencia de un marco regulatorio interno para compras con controles documentados, procesos transparentes de selección y medidas anticorrupción.',
                    'weight': 1.5,
                    'order': 1
                },
                {
                    'question_text': 'El proceso de compras valida la trayectoria, reputación, sistemas de lavado de activos y financiación del terrorismo, y calidad de los productos de los proveedores, más que la cercanía con los miembros de la organización.',
                    'help_text': 'Verificar que la selección de proveedores se basa en criterios objetivos profesionales y cumplimiento legal, no en relaciones personales.',
                    'weight': 1.5,
                    'order': 2
                },
                {
                    'question_text': 'Se tienen mecanismos de seguridad para validar el ingreso de los elementos comprados a la empresa y un control redundante de ingreso al almacén.',
                    'help_text': 'Evaluar procedimientos de verificación en recepción de mercancías con doble control para asegurar conformidad con órdenes de compra.',
                    'weight': 1.4,
                    'order': 3
                },
                {
                    'question_text': 'La organización hotelera dispone de un control para identificar la compra de elementos, materiales, equipos o servicios que pudieran representar un riesgo para la organización hotelera',
                    'help_text': 'Verificar sistema de clasificación y evaluación de riesgos asociados a productos/servicios antes de su adquisición.',
                    'weight': 1.4,
                    'order': 4
                },
                {
                    'question_text': 'La organización hotelera realiza auditorías periódicas al proceso de compras y de almacén con el fin de validar el ingreso y salida de los elementos, conforme con los documentos que respaldan sus movimientos',
                    'help_text': 'Evaluar frecuencia y efectividad de auditorías internas para verificar integridad de procesos y concordancia documental.',
                    'weight': 1.4,
                    'order': 5
                },
                {
                    'question_text': 'La organización hotelera dispone de un control efectivo para el recibo, almacenamiento en el recinto de almacén seguro y los controles de ingreso para minimizar las mermas y pérdidas de los activos.',
                    'help_text': 'Verificar protocolos de almacenamiento seguro, control de acceso a bodegas y medidas para prevenir pérdidas.',
                    'weight': 1.4,
                    'order': 6
                },
                {
                    'question_text': 'La organización hotelera dispone de un mecanismo claro para notificar a los proveedores la persona, los documentos y demás requerimientos necesarios para formalizar una compra y evitar que personas ajenas no autorizadas realicen requerimientos a nombre de la organización.',
                    'help_text': 'Evaluar comunicación formal de autorizaciones y procedimientos a proveedores para prevenir fraudes por suplantación.',
                    'weight': 1.3,
                    'order': 7
                }
            ],
            'gestion_emergencias': [
                {
                    'question_text': 'La organización tiene identificados los riesgos que podrían generar emergencias y tiene determinados los planes específicos de contingencias frente a este tipo de situaciones, generando respuestas coherentes para la organización. Entre estos podrían estar: fuego, alarma de fuego, amenaza de bomba, explosión, amenaza de agentes químicos o biológicos (y los demás que la organización posea dependiendo de su contexto)',
                    'help_text': 'Evaluar la identificación comprehensiva de riesgos y la existencia de planes específicos de contingencia para cada tipo de emergencia potencial.',
                    'weight': 1.5,
                    'order': 1
                },
                {
                    'question_text': 'La organización hotelera cuenta con la planificación de las actividades para evacuar personas basado en un documento, plan, procedimiento u otro que sea adecuado para la organización y que el personal lo cumpla a cabalidad',
                    'help_text': 'Verificar la existencia de documentación formal de evacuación y el cumplimiento efectivo por parte del personal.',
                    'weight': 1.5,
                    'order': 2
                },
                {
                    'question_text': 'La organización dispone de mecanismos para la identificación, el monitoreo, mitigación y la supervisión de las áreas con mayor probabilidad de riesgo de incendio como: caldera, cocina, habitaciones, parqueaderos, tanques de combustible y otras que conlleven alto riesgo de incendio o explosión.',
                    'help_text': 'Evaluar sistemas de monitoreo continuo y medidas preventivas en áreas de alto riesgo de incendio.',
                    'weight': 1.5,
                    'order': 3
                },
                {
                    'question_text': 'La organización hotelera tiene establecido un aforo máximo, así como la estimación de la cantidad de personas en un momento dado, con el fin de estimar y planificar los tiempos de la evacuación',
                    'help_text': 'Verificar control de aforo y cálculos de tiempo de evacuación basados en ocupación real.',
                    'weight': 1.4,
                    'order': 4
                },
                {
                    'question_text': 'La organización hotelera deberá contar con un grupo de brigadistas de emergencias, como mínimo un 10% de los empleados o colaboradores que presten servicios en el hotel, con una capacitación evidenciada para la promoción de las competencias',
                    'help_text': 'Evaluar la conformación, porcentaje y capacitación del grupo de brigadistas de emergencia.',
                    'weight': 1.5,
                    'order': 5
                },
                {
                    'question_text': 'La organización hotelera gestiona que por cada turno de servicio, se encuentren disponibles una cantidad de brigadistas adecuada para atender una emergencia',
                    'help_text': 'Verificar la disponibilidad constante de brigadistas capacitados en todos los turnos operativos.',
                    'weight': 1.4,
                    'order': 6
                },
                {
                    'question_text': 'La organización hotelera dispone de iluminación de emergencia en los pasillos y en las salidas, que oriente eficazmente a los huéspedes y empleados a los puntos de encuentro',
                    'help_text': 'Evaluar la cobertura y funcionalidad del sistema de iluminación de emergencia.',
                    'weight': 1.4,
                    'order': 7
                },
                {
                    'question_text': 'La organización hotelera, dispone de los mecanismos efectivos para facilitar al huésped la información necesaria sobre los procedimientos de actuación en caso de emergencia y evacuación.',
                    'help_text': 'Verificar los medios de comunicación e información sobre procedimientos de emergencia para huéspedes.',
                    'weight': 1.4,
                    'order': 8
                },
                {
                    'question_text': 'Se dispone de la planificación y ejecución de las actividades necesarias para la mitigación de las diferentes emergencias que podrían darse en la instalación hotelera',
                    'help_text': 'Evaluar planes específicos de mitigación para diferentes tipos de emergencias identificadas.',
                    'weight': 1.4,
                    'order': 9
                },
                {
                    'question_text': 'Se deberá tener la implementación de un sistema de detección de incendios mediante un panel de control direccionable que abarque las habitaciones, pasillos, cocinas, calderas, zonas de almacenamiento y las áreas que involucren una medida de riesgo considerable.',
                    'help_text': 'Verificar la cobertura completa y funcionalidad del sistema de detección de incendios direccionable.',
                    'weight': 1.5,
                    'order': 10
                },
                {
                    'question_text': 'La organización hotelera efectúa simulacros de manejo de emergencias y evacuación como mínimo una vez cada 4 meses, dejando las memorias de esta y el mejoramiento de los mismos basados en las oportunidades de mejora detectadas',
                    'help_text': 'Evaluar frecuencia, documentación y mejora continua de los simulacros de emergencia.',
                    'weight': 1.4,
                    'order': 11
                },
                {
                    'question_text': 'La organización hotelera dispone de un sistema que permita generar de manera coherente, oportuna y moderada la notificación de una alarma ante una situación de emergencias tanto de manera audible como visual.',
                    'help_text': 'Verificar la efectividad del sistema de alarmas audibles y visuales.',
                    'weight': 1.4,
                    'order': 12
                },
                {
                    'question_text': 'La organización hotelera dispone de los mecanismos de comunicación interna efectivos y con un adecuado alcance para garantizar un oportuno e ininterrumpido flujo de información en emergencias',
                    'help_text': 'Evaluar sistemas de comunicación interna durante emergencias con cobertura total.',
                    'weight': 1.4,
                    'order': 13
                },
                {
                    'question_text': 'La organización hotelera dispone de un mecanismo de notificación de autoridades externas y tiene implementado un sistema de comando de incidentes que promueva la adecuada interacción, mando y coordinación para mitigar la emergencia',
                    'help_text': 'Verificar protocolos de notificación externa y sistema de comando de incidentes.',
                    'weight': 1.5,
                    'order': 14
                },
                {
                    'question_text': 'La organización hotelera cuenta con un servicio médico 24 horas que pueda apoyar ante cualquier afectación repentina del estado de la salud de un huésped o cualquier accidente que ocurra en la instalación, contando con los adecuados medios para la atención primaria de estos.',
                    'help_text': 'Evaluar disponibilidad continua de servicios médicos de emergencia y recursos de atención primaria.',
                    'weight': 1.4,
                    'order': 15
                },
                {
                    'question_text': 'La organización hotelera identifica la situación de las amenazas del país y le da relevancia a aquellas situaciones potenciales que pudiesen ocurrir según la dinámica conflictiva del país como: secuestros, toma de rehenes, asesinatos, asonadas y asaltos',
                    'help_text': 'Verificar análisis de amenazas específicas del contexto nacional y medidas preventivas correspondientes.',
                    'weight': 1.4,
                    'order': 16
                },
                {
                    'question_text': 'La organización hotelera dispone de los mecanismos de identificación, prevención e intervención a los riesgos derivados de la amenaza humana de manera planificada, implementada y registrada.',
                    'help_text': 'Evaluar protocolos documentados para amenazas de origen humano con evidencia de implementación.',
                    'weight': 1.4,
                    'order': 17
                },
                {
                    'question_text': 'La organización hotelera identifica en las actividades no rutinarias y rutinarias las posibilidades de generación de emergencias, incluyendo trabajos de contratistas externos, nuevos productos, eventos especiales, entre otros que pudieran generar situaciones de emergencia y desarrolla, planes específicos de prevención de los riesgos que pudieran derivar en emergencias',
                    'help_text': 'Verificar identificación proactiva de riesgos en actividades especiales y desarrollo de planes preventivos específicos.',
                    'weight': 1.4,
                    'order': 18
                },
                {
                    'question_text': 'La organización hotelera dispone de las vías de evacuación señalizadas, habilitadas, no obstruidas y con flujo directo a los puntos de encuentro definidos por la organización hotelera',
                    'help_text': 'Evaluar señalización, estado y accesibilidad de las rutas de evacuación.',
                    'weight': 1.5,
                    'order': 19
                },
                {
                    'question_text': 'La organización hotelera dispone de los puntos de encuentro necesarios para satisfacer el aforo máximo estipulado, con el fin de lograr el resguardo de las personas de manera segura, considerando que podría uno o dos puntos de encuentro ser inhabilitados por la cercanía a la misma emergencia, requiriendo la acomodación en los puntos de encuentro restantes',
                    'help_text': 'Verificar capacidad y distribución de puntos de encuentro con redundancia para emergencias.',
                    'weight': 1.4,
                    'order': 20
                },
                {
                    'question_text': 'La organización hotelera dispone de mecanismos efectivos y evidenciados para mitigar la posibilidad de que las vías de evacuación sean bloqueadas, obstruidas o alteradas, sin previo aviso o autorización.',
                    'help_text': 'Evaluar medidas de protección y control para mantener despejadas las rutas de evacuación.',
                    'weight': 1.4,
                    'order': 21
                },
                {
                    'question_text': 'La organización hotelera dispone de los mecanismos de extinción de incendios adecuados para ser operados las 24 horas del día, con el cubrimiento necesario para todos los lugares (incluyendo habitaciones, áreas de eventos, cocinas, calderas y todas las áreas) de manera oportuna para evitar la expansión del incendio',
                    'help_text': 'Verificar cobertura completa y disponibilidad continua de sistemas de extinción de incendios.',
                    'weight': 1.5,
                    'order': 22
                },
                {
                    'question_text': 'La organización hotelera dispone de zonas de refugio adecuadas para albergar a los empleados, huéspedes en caso de emergencias naturales como ciclones, terremotos, colapsamiento de estructuras e inundaciones',
                    'help_text': 'Evaluar zonas de refugio para emergencias naturales con capacidad adecuada.',
                    'weight': 1.4,
                    'order': 23
                },
                {
                    'question_text': 'Los sistemas de extinción manuales se encuentran a lo largo y ancho de la instalación hotelera, siendo coherentes los agentes de extinción con los materiales combustibles del entorno. Se asegura el óptimo funcionamiento y vigencia de estos',
                    'help_text': 'Verificar distribución, adecuación y mantenimiento de extintores manuales.',
                    'weight': 1.4,
                    'order': 24
                },
                {
                    'question_text': 'Se dispone de una estructura jerárquica y funcional para operar en caso de emergencias, la cual conozca y efectúe sus roles dentro del desempeño de la planificación como de la participación en la dirección de una emergencia',
                    'help_text': 'Evaluar organización jerárquica de respuesta a emergencias con roles claramente definidos.',
                    'weight': 1.4,
                    'order': 25
                },
                {
                    'question_text': 'Se dispone de un área adecuada y la promoción de la operatividad de un Centro de Operaciones para el direccionamiento de la emergencia',
                    'help_text': 'Verificar existencia y funcionalidad de centro de operaciones de emergencia.',
                    'weight': 1.3,
                    'order': 26
                }
            ]
        }
        
        # Contadores para estadísticas
        created_count = 0
        error_count = 0
        
        # Crear preguntas para cada categoría
        for category_code, questions in questions_data.items():
            try:
                # Obtener la categoría
                category = SecurityCategory.objects.get(code=category_code)
                self.stdout.write(f'\nProcesando categoría: {category.name}')
                
                # Crear preguntas para esta categoría
                for question_data in questions:
                    question = SecurityQuestion.objects.create(
                        category=category,
                        question_text=question_data['question_text'],
                        help_text=question_data['help_text'],
                        weight=question_data['weight'],
                        order=question_data['order'],
                        is_required=True,
                        is_active=True
                    )
                    created_count += 1
                    self.stdout.write(f'  ✓ Pregunta {question_data["order"]}: {question_data["question_text"][:60]}...')
                    
            except SecurityCategory.DoesNotExist:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'ERROR: Categoría con código "{category_code}" no encontrada')
                )
                continue
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'ERROR creando preguntas para {category_code}: {str(e)}')
                )
                continue
        
        # Resumen final
        total_questions = SecurityQuestion.objects.count()
        total_categories = SecurityCategory.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Proceso completado!\n'
                f'📊 Estadísticas:\n'
                f'   • Preguntas creadas: {created_count}\n'
                f'   • Errores: {error_count}\n'
                f'   • Total preguntas en sistema: {total_questions}\n'
                f'   • Categorías procesadas: {total_categories}\n'
                f'   • Promedio preguntas por categoría: {total_questions/total_categories:.1f}\n'
                f'\n✅ Sistema de preguntas de seguridad configurado correctamente!'
            )
        )
        
        # Mostrar resumen por categoría
        self.stdout.write('\n📋 Resumen por categoría:')
        categories = SecurityCategory.objects.all().order_by('order')
        for category in categories:
            question_count = category.questions.count()
            self.stdout.write(f'   • {category.name}: {question_count} preguntas')
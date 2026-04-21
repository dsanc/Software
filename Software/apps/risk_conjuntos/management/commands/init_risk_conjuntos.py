from django.core.management.base import BaseCommand
from apps.risk_conjuntos.models import TipoConjunto, CategoriaSeguridad, PreguntaSeguridad


class Command(BaseCommand):
    help = 'Inicializa datos básicos para el módulo Risk Conjuntos'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Inicializando datos para Risk Conjuntos...'))
        
        # Crear tipos de conjuntos
        self.create_tipos_conjunto()
        
        # Crear categorías de seguridad
        self.create_categorias_seguridad()
        
        # Crear preguntas de seguridad
        self.create_preguntas_seguridad()
        
        self.stdout.write(self.style.SUCCESS('✓ Datos inicializados correctamente'))
    
    def create_tipos_conjunto(self):
        """Crear tipos de conjuntos predefinidos"""
        tipos = [
            {
                'nombre': 'conjunto_cerrado',
                'descripcion': 'Conjunto residencial cerrado con control de acceso',
                'icono': 'fas fa-home',
                'color': '#2ecc71'
            },
            {
                'nombre': 'urbanizacion',
                'descripcion': 'Urbanización con múltiples sectores',
                'icono': 'fas fa-city',
                'color': '#3498db'
            },
            {
                'nombre': 'condominio',
                'descripcion': 'Condominio residencial',
                'icono': 'fas fa-building',
                'color': '#9b59b6'
            },
            {
                'nombre': 'cluster',
                'descripcion': 'Cluster o agrupación de casas',
                'icono': 'fas fa-home',
                'color': '#e67e22'
            },
            {
                'nombre': 'edificio',
                'descripcion': 'Edificio residencial',
                'icono': 'fas fa-building',
                'color': '#34495e'
            },
            {
                'nombre': 'torres',
                'descripcion': 'Torres residenciales',
                'icono': 'fas fa-building',
                'color': '#e74c3c'
            }
        ]
        
        for tipo_data in tipos:
            tipo, created = TipoConjunto.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(f'✓ Tipo de conjunto creado: {tipo.get_nombre_display()}')
    
    def create_categorias_seguridad(self):
        """Crear categorías de seguridad específicas para conjuntos"""
        categorias = [
            {
                'codigo': 'acceso_control',
                'nombre': 'Control de Acceso',
                'descripcion': 'Sistemas de control y restricción de acceso al conjunto',
                'icono': 'fas fa-key',
                'orden': 1,
                'peso': 1.5
            },
            {
                'codigo': 'seguridad_perimetral',
                'nombre': 'Seguridad Perimetral',
                'descripcion': 'Cercas, muros, barreras y delimitación del perímetro',
                'icono': 'fas fa-shield-alt',
                'orden': 2,
                'peso': 1.3
            },
            {
                'codigo': 'vigilancia_porteria',
                'nombre': 'Vigilancia y Portería',
                'descripcion': 'Personal de seguridad y sistemas de vigilancia',
                'icono': 'fas fa-user-shield',
                'orden': 3,
                'peso': 1.4
            },
            {
                'codigo': 'circuito_cerrado',
                'nombre': 'Circuito Cerrado de TV',
                'descripcion': 'Sistemas de videovigilancia y monitoreo',
                'icono': 'fas fa-video',
                'orden': 4,
                'peso': 1.2
            },
            {
                'codigo': 'iluminacion',
                'nombre': 'Iluminación y Visibilidad',
                'descripcion': 'Sistemas de iluminación en áreas comunes y exteriores',
                'icono': 'fas fa-lightbulb',
                'orden': 5,
                'peso': 1.0
            },
            {
                'codigo': 'emergencias',
                'nombre': 'Gestión de Emergencias',
                'descripcion': 'Planes y equipos para manejo de emergencias',
                'icono': 'fas fa-ambulance',
                'orden': 6,
                'peso': 1.3
            },
            {
                'codigo': 'areas_comunes',
                'nombre': 'Seguridad en Áreas Comunes',
                'descripcion': 'Seguridad en piscinas, salones, parques y zonas recreativas',
                'icono': 'fas fa-swimming-pool',
                'orden': 7,
                'peso': 1.1
            },
            {
                'codigo': 'visitantes',
                'nombre': 'Control de Visitantes',
                'descripcion': 'Procedimientos para registro y control de visitantes',
                'icono': 'fas fa-user-friends',
                'orden': 8,
                'peso': 1.2
            },
            {
                'codigo': 'administracion',
                'nombre': 'Administración y Gobernanza',
                'descripcion': 'Gestión administrativa de la seguridad del conjunto',
                'icono': 'fas fa-users-cog',
                'orden': 9,
                'peso': 1.1
            }
        ]
        
        for cat_data in categorias:
            categoria, created = CategoriaSeguridad.objects.get_or_create(
                codigo=cat_data['codigo'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'✓ Categoría creada: {categoria.nombre}')
    
    def create_preguntas_seguridad(self):
        """Crear preguntas de seguridad por categoría"""
        
        # Control de Acceso
        acceso_control = CategoriaSeguridad.objects.get(codigo='acceso_control')
        preguntas_acceso = [
            {
                'texto_pregunta': '¿El conjunto cuenta con control de acceso vehicular las 24 horas?',
                'ayuda': 'Evalúe si existe control permanente para el ingreso de vehículos',
                'tipo_respuesta': 'rating',
                'orden': 1,
                'peso': 1.5
            },
            {
                'texto_pregunta': '¿Existe control de acceso peatonal independiente del vehicular?',
                'ayuda': 'Verifique si hay portones o accesos específicos para peatones',
                'tipo_respuesta': 'rating',
                'orden': 2,
                'peso': 1.2
            },
            {
                'texto_pregunta': '¿Se utilizan sistemas tecnológicos para el control de acceso (tarjetas, códigos, biometría)?',
                'ayuda': 'Evalúe la presencia de tecnología moderna en el control de acceso',
                'tipo_respuesta': 'rating',
                'orden': 3,
                'peso': 1.3
            },
            {
                'texto_pregunta': '¿Los residentes cuentan con identificación para acceso al conjunto?',
                'ayuda': 'Verifique si existe un sistema de identificación para residentes',
                'tipo_respuesta': 'rating',
                'orden': 4,
                'peso': 1.1
            }
        ]
        
        for pregunta_data in preguntas_acceso:
            pregunta, created = PreguntaSeguridad.objects.get_or_create(
                categoria=acceso_control,
                texto_pregunta=pregunta_data['texto_pregunta'],
                defaults=pregunta_data
            )
            if created:
                self.stdout.write(f'  ✓ Pregunta creada: {pregunta.texto_pregunta[:50]}...')
        
        # Seguridad Perimetral
        seg_perimetral = CategoriaSeguridad.objects.get(codigo='seguridad_perimetral')
        preguntas_perimetral = [
            {
                'texto_pregunta': '¿El conjunto cuenta con cerramiento perimetral completo?',
                'ayuda': 'Evalúe si todo el perímetro está debidamente cerrado',
                'tipo_respuesta': 'rating',
                'orden': 1,
                'peso': 1.4
            },
            {
                'texto_pregunta': '¿La altura del cerramiento es adecuada para disuadir intrusiones?',
                'ayuda': 'Considere si la altura es suficiente (generalmente mínimo 2.5m)',
                'tipo_respuesta': 'rating',
                'orden': 2,
                'peso': 1.2
            },
            {
                'texto_pregunta': '¿El cerramiento cuenta con elementos de seguridad adicionales (alambre de púas, cercas eléctricas)?',
                'ayuda': 'Verifique la presencia de elementos disuasivos en la parte superior',
                'tipo_respuesta': 'rating',
                'orden': 3,
                'peso': 1.1
            },
            {
                'texto_pregunta': '¿Se realizan inspecciones periódicas del estado del cerramiento?',
                'ayuda': 'Evalúe si existe mantenimiento y revisión regular del perímetro',
                'tipo_respuesta': 'rating',
                'orden': 4,
                'peso': 1.0
            }
        ]
        
        for pregunta_data in preguntas_perimetral:
            pregunta, created = PreguntaSeguridad.objects.get_or_create(
                categoria=seg_perimetral,
                texto_pregunta=pregunta_data['texto_pregunta'],
                defaults=pregunta_data
            )
            if created:
                self.stdout.write(f'  ✓ Pregunta creada: {pregunta.texto_pregunta[:50]}...')
        
        # Vigilancia y Portería
        vigilancia = CategoriaSeguridad.objects.get(codigo='vigilancia_porteria')
        preguntas_vigilancia = [
            {
                'texto_pregunta': '¿El conjunto cuenta con vigilancia las 24 horas del día?',
                'ayuda': 'Evalúe la cobertura temporal del servicio de vigilancia',
                'tipo_respuesta': 'rating',
                'orden': 1,
                'peso': 1.5
            },
            {
                'texto_pregunta': '¿El personal de vigilancia cuenta con formación en seguridad?',
                'ayuda': 'Verifique si los vigilantes tienen capacitación formal',
                'tipo_respuesta': 'rating',
                'orden': 2,
                'peso': 1.3
            },
            {
                'texto_pregunta': '¿Existe una garita o caseta de vigilancia en condiciones adecuadas?',
                'ayuda': 'Evalúe las condiciones físicas del puesto de vigilancia',
                'tipo_respuesta': 'rating',
                'orden': 3,
                'peso': 1.1
            },
            {
                'texto_pregunta': '¿Se llevan registros de novedades y eventos de seguridad?',
                'ayuda': 'Verifique si existe documentación de incidentes y actividades',
                'tipo_respuesta': 'rating',
                'orden': 4,
                'peso': 1.2
            }
        ]
        
        for pregunta_data in preguntas_vigilancia:
            pregunta, created = PreguntaSeguridad.objects.get_or_create(
                categoria=vigilancia,
                texto_pregunta=pregunta_data['texto_pregunta'],
                defaults=pregunta_data
            )
            if created:
                self.stdout.write(f'  ✓ Pregunta creada: {pregunta.texto_pregunta[:50]}...')
        
        # Circuito Cerrado de TV
        cctv = CategoriaSeguridad.objects.get(codigo='circuito_cerrado')
        preguntas_cctv = [
            {
                'texto_pregunta': '¿El conjunto cuenta con cámaras de seguridad en áreas estratégicas?',
                'ayuda': 'Evalúe la presencia de videovigilancia en puntos clave',
                'tipo_respuesta': 'rating',
                'orden': 1,
                'peso': 1.3
            },
            {
                'texto_pregunta': '¿Las cámaras cubren todos los accesos al conjunto?',
                'ayuda': 'Verifique que todos los puntos de entrada estén monitoreados',
                'tipo_respuesta': 'rating',
                'orden': 2,
                'peso': 1.4
            },
            {
                'texto_pregunta': '¿El sistema de CCTV permite grabación y almacenamiento de imágenes?',
                'ayuda': 'Evalúe si las grabaciones se conservan por tiempo adecuado',
                'tipo_respuesta': 'rating',
                'orden': 3,
                'peso': 1.2
            },
            {
                'texto_pregunta': '¿Las cámaras están en funcionamiento y buenas condiciones?',
                'ayuda': 'Verifique el estado operativo del sistema de videovigilancia',
                'tipo_respuesta': 'rating',
                'orden': 4,
                'peso': 1.1
            }
        ]
        
        for pregunta_data in preguntas_cctv:
            pregunta, created = PreguntaSeguridad.objects.get_or_create(
                categoria=cctv,
                texto_pregunta=pregunta_data['texto_pregunta'],
                defaults=pregunta_data
            )
            if created:
                self.stdout.write(f'  ✓ Pregunta creada: {pregunta.texto_pregunta[:50]}...')
        
        # Iluminación
        iluminacion = CategoriaSeguridad.objects.get(codigo='iluminacion')
        preguntas_iluminacion = [
            {
                'texto_pregunta': '¿Las áreas comunes cuentan con iluminación nocturna adecuada?',
                'ayuda': 'Evalúe si la iluminación permite visibilidad durante la noche',
                'tipo_respuesta': 'rating',
                'orden': 1,
                'peso': 1.2
            },
            {
                'texto_pregunta': '¿Los accesos y portones están bien iluminados?',
                'ayuda': 'Verifique que los puntos de entrada tengan buena visibilidad',
                'tipo_respuesta': 'rating',
                'orden': 2,
                'peso': 1.3
            },
            {
                'texto_pregunta': '¿Existen sistemas de iluminación de emergencia?',
                'ayuda': 'Evalúe la presencia de respaldo eléctrico para iluminación',
                'tipo_respuesta': 'rating',
                'orden': 3,
                'peso': 1.1
            }
        ]
        
        for pregunta_data in preguntas_iluminacion:
            pregunta, created = PreguntaSeguridad.objects.get_or_create(
                categoria=iluminacion,
                texto_pregunta=pregunta_data['texto_pregunta'],
                defaults=pregunta_data
            )
            if created:
                self.stdout.write(f'  ✓ Pregunta creada: {pregunta.texto_pregunta[:50]}...')
        
        # Gestión de Emergencias
        emergencias = CategoriaSeguridad.objects.get(codigo='emergencias')
        preguntas_emergencias = [
            {
                'texto_pregunta': '¿Existe un plan de emergencias documentado y socializado?',
                'ayuda': 'Evalúe si hay procedimientos claros para diferentes emergencias',
                'tipo_respuesta': 'rating',
                'orden': 1,
                'peso': 1.4
            },
            {
                'texto_pregunta': '¿El conjunto cuenta con equipos de primeros auxilios?',
                'ayuda': 'Verifique la disponibilidad de botiquines y equipos médicos básicos',
                'tipo_respuesta': 'rating',
                'orden': 2,
                'peso': 1.2
            },
            {
                'texto_pregunta': '¿Hay extintores y sistemas contra incendios instalados?',
                'ayuda': 'Evalúe los sistemas de prevención y control de incendios',
                'tipo_respuesta': 'rating',
                'orden': 3,
                'peso': 1.3
            },
            {
                'texto_pregunta': '¿Se realizan simulacros de emergencia periódicamente?',
                'ayuda': 'Verifique si se practican los procedimientos de emergencia',
                'tipo_respuesta': 'rating',
                'orden': 4,
                'peso': 1.1
            }
        ]
        
        for pregunta_data in preguntas_emergencias:
            pregunta, created = PreguntaSeguridad.objects.get_or_create(
                categoria=emergencias,
                texto_pregunta=pregunta_data['texto_pregunta'],
                defaults=pregunta_data
            )
            if created:
                self.stdout.write(f'  ✓ Pregunta creada: {pregunta.texto_pregunta[:50]}...')
        
        # Control de Visitantes
        visitantes = CategoriaSeguridad.objects.get(codigo='visitantes')
        preguntas_visitantes = [
            {
                'texto_pregunta': '¿Existe un procedimiento establecido para el ingreso de visitantes?',
                'ayuda': 'Evalúe si hay protocolos claros para visitantes',
                'tipo_respuesta': 'rating',
                'orden': 1,
                'peso': 1.3
            },
            {
                'texto_pregunta': '¿Se lleva registro de todos los visitantes que ingresan?',
                'ayuda': 'Verifique si se documenta la entrada y salida de visitantes',
                'tipo_respuesta': 'rating',
                'orden': 2,
                'peso': 1.2
            },
            {
                'texto_pregunta': '¿Los visitantes deben ser autorizados por los residentes?',
                'ayuda': 'Evalúe si existe confirmación previa antes del ingreso',
                'tipo_respuesta': 'rating',
                'orden': 3,
                'peso': 1.1
            }
        ]
        
        for pregunta_data in preguntas_visitantes:
            pregunta, created = PreguntaSeguridad.objects.get_or_create(
                categoria=visitantes,
                texto_pregunta=pregunta_data['texto_pregunta'],
                defaults=pregunta_data
            )
            if created:
                self.stdout.write(f'  ✓ Pregunta creada: {pregunta.texto_pregunta[:50]}...')
"""
Comando para crear y configurar todos los escenarios de riesgo relacionados correctamente
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.risk_conjuntos.models import TipoRiesgo, EscenarioRiesgo


class Command(BaseCommand):
    help = 'Crea y configura todos los escenarios de riesgo relacionados correctamente con cada tipo de riesgo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recreación de escenarios existentes'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se crearía sin hacer cambios reales'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🏗️  Configurando escenarios de riesgo...'))
        
        # Definir la estructura completa de riesgos y sus escenarios
        estructura_riesgos = {
            'intrusion_general': {
                'nombre': 'Intrusión General',
                'descripcion': 'Riesgos relacionados con intrusiones generales al conjunto residencial',
                'escenarios': [
                    {
                        'codigo': 'traspasando_cerramiento',
                        'nombre': 'Traspasando El Cerramiento Perimetral',
                        'descripcion': 'Intrusion saltando, rompiendo o atravesando el cerramiento perimetral',
                        'orden': 1
                    },
                    {
                        'codigo': 'debilidad_procedimiento',
                        'nombre': 'Por Debilidad Del Procedimiento De Ingreso',
                        'descripcion': 'Intrusion aprovechando debilidades en los procedimientos de control de acceso',
                        'orden': 2
                    }
                ]
            },
            'conspiracion_intrusion': {
                'nombre': 'Conspiración Para Intrusión',
                'descripcion': 'Riesgos relacionados con intrusiones planificadas con ayuda interna o externa',
                'escenarios': [
                    {
                        'codigo': 'distraccion_vigilante',
                        'nombre': 'Distracción Al Vigilante',
                        'descripcion': 'Intrusion mediante distracción del personal de seguridad',
                        'orden': 1
                    },
                    {
                        'codigo': 'simultaneamente_autorizada',
                        'nombre': 'Pasando Simultáneamente Con Una Persona Autorizada',
                        'descripcion': 'Intrusion aprovechando el ingreso de personas autorizadas',
                        'orden': 2
                    }
                ]
            },
            'intrusion_unidad': {
                'nombre': 'Intrusión Unidad Residencial',
                'descripcion': 'Riesgos específicos de intrusión a unidades residenciales individuales',
                'escenarios': [
                    {
                        'codigo': 'violando_puerta_principal',
                        'nombre': 'Violando La Seguridad De La Puerta Principal',
                        'descripcion': 'Intrusión forzando la puerta principal de la unidad residencial',
                        'orden': 1
                    },
                    {
                        'codigo': 'acceso_ventanas_balcones',
                        'nombre': 'Por Acceso Por Ventanas O Balcones',
                        'descripcion': 'Intrusión a través de ventanas, balcones o terrazas',
                        'orden': 2
                    }
                ]
            },
            'robo_vehiculos': {
                'nombre': 'Robo De Vehículos',
                'descripcion': 'Riesgos relacionados con el robo de vehículos en el conjunto',
                'escenarios': [
                    {
                        'codigo': 'acceso_simplificado',
                        'nombre': 'Acceso Simplificado A Las Mismas',
                        'descripcion': 'Robo aprovechando facilidades de acceso a los vehículos',
                        'orden': 1
                    },
                    {
                        'codigo': 'salida_normal',
                        'nombre': 'Por Salida Normal',
                        'descripcion': 'Robo con salida normal del conjunto sin levantar sospechas',
                        'orden': 2
                    }
                ]
            },
            'robo_bicicletas': {
                'nombre': 'Robo De Bicicletas',
                'descripcion': 'Riesgos específicos del robo de bicicletas y elementos similares',
                'escenarios': [
                    {
                        'codigo': 'retiro_porterias',
                        'nombre': 'Retiro Por Porterías',
                        'descripcion': 'Robo de bicicletas sacándolas por la portería principal',
                        'orden': 1
                    },
                    {
                        'codigo': 'retiro_area_perimetral',
                        'nombre': 'Retiro Por El Área Perimetral',
                        'descripcion': 'Robo sacando bicicletas por áreas perimetrales menos vigiladas',
                        'orden': 2
                    }
                ]
            },
            'dano_areas_comunes': {
                'nombre': 'Daño En Áreas Comunes',
                'descripcion': 'Riesgos de vandalismo y daños en espacios compartidos del conjunto',
                'escenarios': [
                    {
                        'codigo': 'autorizacion_suplantada',
                        'nombre': 'Por Autorización Suplantada',
                        'descripcion': 'Daños causados por personas que ingresan suplantando autorización',
                        'orden': 1
                    },
                    {
                        'codigo': 'accion_interna',
                        'nombre': 'Por Acción Interna',
                        'descripcion': 'Daños causados por residentes o personas con acceso legítimo',
                        'orden': 2
                    }
                ]
            },
            'conflictos_parqueos': {
                'nombre': 'Conflictos Por Mal Uso De Parqueos',
                'descripcion': 'Riesgos derivados del uso inadecuado de espacios de parqueo',
                'escenarios': [
                    {
                        'codigo': 'permisividad_parqueos_asignados',
                        'nombre': 'Permisividad En El Uso De Parqueos Asignados',
                        'descripcion': 'Conflictos por uso indebido de parqueaderos asignados',
                        'orden': 1
                    },
                    {
                        'codigo': 'permisividad_administracion_parqueaderos',
                        'nombre': 'Permisividad En La Administración De Parqueaderos De Seguridad',
                        'descripcion': 'Problemas por gestión inadecuada de parqueaderos por parte de seguridad',
                        'orden': 2
                    }
                ]
            },
            'sustraccion_bienes': {
                'nombre': 'Sustracción De Bienes De Apartamentos',
                'descripcion': 'Riesgos de robo de objetos y bienes dentro de las unidades residenciales',
                'escenarios': [
                    {
                        'codigo': 'autorizacion_irresponsable',
                        'nombre': 'Autorización Irresponsable',
                        'descripcion': 'Robos facilitados por autorizaciones de acceso irresponsables',
                        'orden': 1
                    },
                    {
                        'codigo': 'ingenieria_social',
                        'nombre': 'Por Ingeniería Social',
                        'descripcion': 'Robos usando técnicas de manipulación psicológica',
                        'orden': 2
                    }
                ]
            },
            'secuestro': {
                'nombre': 'Secuestro',
                'descripcion': 'Riesgos relacionados con secuestros de residentes o visitantes',
                'escenarios': [
                    {
                        'codigo': 'salida_forzada_escoltas',
                        'nombre': 'Salida Forzada Suplantando A Escoltas',
                        'descripcion': 'Secuestro haciéndose pasar por escoltas o personal de seguridad',
                        'orden': 1
                    },
                    {
                        'codigo': 'suplantando_servicios_medicos',
                        'nombre': 'Suplantando Servicios Médicos',
                        'descripcion': 'Secuestro suplantando personal médico o de emergencias',
                        'orden': 2
                    }
                ]
            }
        }
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🧪 MODO DRY-RUN: Mostrando lo que se crearía...'))
        
        creados = 0
        actualizados = 0
        errores = 0
        
        try:
            with transaction.atomic():
                for codigo_riesgo, datos_riesgo in estructura_riesgos.items():
                    self.stdout.write(f'\\n🎯 Procesando riesgo: {datos_riesgo["nombre"]}')
                    
                    # Crear o actualizar tipo de riesgo
                    try:
                        tipo_riesgo, created = TipoRiesgo.objects.get_or_create(
                            codigo=codigo_riesgo,
                            defaults={
                                'nombre': datos_riesgo['nombre'],
                                'descripcion': datos_riesgo['descripcion'],
                                'orden': list(estructura_riesgos.keys()).index(codigo_riesgo) + 1,
                                'activo': True
                            }
                        )
                        
                        if created:
                            self.stdout.write(f'  ✅ Tipo de riesgo creado: {tipo_riesgo.nombre}')
                        elif options['force']:
                            tipo_riesgo.nombre = datos_riesgo['nombre']
                            tipo_riesgo.descripcion = datos_riesgo['descripcion']
                            tipo_riesgo.save()
                            self.stdout.write(f'  🔄 Tipo de riesgo actualizado: {tipo_riesgo.nombre}')
                        else:
                            self.stdout.write(f'  ⚪ Tipo de riesgo ya existe: {tipo_riesgo.nombre}')
                        
                        # Procesar escenarios de este riesgo
                        for datos_escenario in datos_riesgo['escenarios']:
                            try:
                                if not options['dry_run']:
                                    escenario, created = EscenarioRiesgo.objects.get_or_create(
                                        codigo=datos_escenario['codigo'],
                                        defaults={
                                            'tipo_riesgo': tipo_riesgo,
                                            'nombre': datos_escenario['nombre'],
                                            'descripcion': datos_escenario['descripcion'],
                                            'orden': datos_escenario['orden'],
                                            'activo': True
                                        }
                                    )
                                    
                                    if created:
                                        self.stdout.write(f'    ✅ Escenario creado: {escenario.nombre}')
                                        creados += 1
                                    elif options['force']:
                                        escenario.tipo_riesgo = tipo_riesgo
                                        escenario.nombre = datos_escenario['nombre']
                                        escenario.descripcion = datos_escenario['descripcion']
                                        escenario.orden = datos_escenario['orden']
                                        escenario.save()
                                        self.stdout.write(f'    🔄 Escenario actualizado: {escenario.nombre}')
                                        actualizados += 1
                                    else:
                                        self.stdout.write(f'    ⚪ Escenario ya existe: {escenario.nombre}')
                                else:
                                    # Dry run - solo mostrar
                                    existe = EscenarioRiesgo.objects.filter(codigo=datos_escenario['codigo']).exists()
                                    if existe and not options['force']:
                                        self.stdout.write(f'    ⚪ [DRY-RUN] Escenario ya existe: {datos_escenario["nombre"]}')
                                    else:
                                        action = "actualizaría" if existe else "crearía"
                                        self.stdout.write(f'    🧪 [DRY-RUN] Se {action}: {datos_escenario["nombre"]}')
                                        creados += 1
                                        
                            except Exception as e:
                                errores += 1
                                self.stdout.write(
                                    self.style.ERROR(f'    ❌ Error creando escenario {datos_escenario["codigo"]}: {str(e)}')
                                )
                        
                    except Exception as e:
                        errores += 1
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Error procesando riesgo {codigo_riesgo}: {str(e)}')
                        )
                
                if options['dry_run']:
                    # En dry-run, hacer rollback de la transacción
                    raise Exception("Dry run - rollback intencional")
                    
        except Exception as e:
            if not options['dry_run']:
                self.stdout.write(self.style.ERROR(f'❌ Error en transacción: {str(e)}'))
                return
        
        # Resumen final
        self.stdout.write('\\n' + '='*60)
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('🧪 SIMULACIÓN COMPLETADA'))
        else:
            self.stdout.write(self.style.SUCCESS('🎉 CONFIGURACIÓN COMPLETADA'))
        
        self.stdout.write(f'  • Escenarios creados: {creados}')
        self.stdout.write(f'  • Escenarios actualizados: {actualizados}')
        self.stdout.write(f'  • Errores: {errores}')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('  ⚠️  Ejecutar sin --dry-run para aplicar cambios'))
        
        # Mostrar estadísticas finales
        if not options['dry_run']:
            total_tipos = TipoRiesgo.objects.filter(activo=True).count()
            total_escenarios = EscenarioRiesgo.objects.filter(activo=True).count()
            
            self.stdout.write(f'\\n📊 ESTADÍSTICAS FINALES:')
            self.stdout.write(f'  • Total tipos de riesgo activos: {total_tipos}')
            self.stdout.write(f'  • Total escenarios activos: {total_escenarios}')
            self.stdout.write(f'  • Promedio escenarios por riesgo: {total_escenarios/total_tipos:.1f}')
            
            # Verificar estructura de 2 escenarios por riesgo
            riesgos_completos = 0
            for riesgo in TipoRiesgo.objects.filter(activo=True):
                escenarios_count = riesgo.escenarios.filter(activo=True).count()
                if escenarios_count == 2:
                    riesgos_completos += 1
                elif escenarios_count != 2:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  {riesgo.nombre} tiene {escenarios_count} escenarios (esperado: 2)')
                    )
            
            self.stdout.write(f'  • Riesgos con 2 escenarios: {riesgos_completos}/{total_tipos}')
            
            if riesgos_completos == total_tipos:
                self.stdout.write(self.style.SUCCESS('  ✅ Todos los riesgos tienen exactamente 2 escenarios'))
            
        self.stdout.write('\\n🚀 ¡Listo para usar en evaluaciones!')
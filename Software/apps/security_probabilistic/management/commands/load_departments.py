from django.core.management.base import BaseCommand
from django.db import transaction
from apps.security_probabilistic.models import Departamento


DEPARTAMENTOS_COLOMBIA = [
    # (codigo_dane, nombre, region, nivel_riesgo, factor_riesgo)
    ('05', 'Antioquia',              'andina',    'alto',     0.650),
    ('08', 'Atlántico',              'caribe',    'medio',    0.400),
    ('11', 'Bogotá D.C.',            'andina',    'alto',     0.600),
    ('13', 'Bolívar',                'caribe',    'alto',     0.650),
    ('15', 'Boyacá',                 'andina',    'bajo',     0.250),
    ('17', 'Caldas',                 'andina',    'medio',    0.400),
    ('18', 'Caquetá',                'amazonia',  'muy_alto', 0.850),
    ('19', 'Cauca',                  'pacifica',  'muy_alto', 0.820),
    ('20', 'Cesar',                  'caribe',    'alto',     0.680),
    ('23', 'Córdoba',                'caribe',    'alto',     0.700),
    ('25', 'Cundinamarca',           'andina',    'medio',    0.450),
    ('27', 'Chocó',                  'pacifica',  'critico',  0.950),
    ('41', 'Huila',                  'andina',    'medio',    0.500),
    ('44', 'La Guajira',             'caribe',    'alto',     0.700),
    ('47', 'Magdalena',              'caribe',    'alto',     0.650),
    ('50', 'Meta',                   'orinoquia', 'alto',     0.700),
    ('52', 'Nariño',                 'pacifica',  'muy_alto', 0.800),
    ('54', 'Norte de Santander',     'andina',    'muy_alto', 0.820),
    ('63', 'Quindío',                'andina',    'bajo',     0.250),
    ('66', 'Risaralda',              'andina',    'medio',    0.400),
    ('68', 'Santander',              'andina',    'medio',    0.450),
    ('70', 'Sucre',                  'caribe',    'alto',     0.650),
    ('73', 'Tolima',                 'andina',    'alto',     0.650),
    ('76', 'Valle del Cauca',        'pacifica',  'alto',     0.650),
    ('81', 'Arauca',                 'orinoquia', 'critico',  0.900),
    ('85', 'Casanare',               'orinoquia', 'medio',    0.500),
    ('86', 'Putumayo',               'amazonia',  'muy_alto', 0.850),
    ('88', 'San Andrés y Providencia','insular',  'bajo',     0.200),
    ('91', 'Amazonas',               'amazonia',  'medio',    0.500),
    ('94', 'Guainía',                'amazonia',  'alto',     0.700),
    ('95', 'Guaviare',               'amazonia',  'muy_alto', 0.820),
    ('97', 'Vaupés',                 'amazonia',  'alto',     0.680),
    ('99', 'Vichada',                'orinoquia', 'alto',     0.680),
]


class Command(BaseCommand):
    help = 'Carga los 33 departamentos de Colombia con sus niveles de riesgo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Actualiza los factores de riesgo aunque el departamento ya exista',
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)
        creados = 0
        actualizados = 0
        sin_cambios = 0

        self.stdout.write('Cargando departamentos de Colombia...')

        with transaction.atomic():
            for codigo, nombre, region, nivel_riesgo, factor_riesgo in DEPARTAMENTOS_COLOMBIA:
                dept, created = Departamento.objects.get_or_create(
                    codigo_dane=codigo,
                    defaults={
                        'nombre': nombre,
                        'region': region,
                        'nivel_riesgo': nivel_riesgo,
                        'factor_riesgo': factor_riesgo,
                        'activo': True,
                    }
                )

                if created:
                    creados += 1
                    self.stdout.write(f'  [+] {nombre} ({codigo})')
                elif reset:
                    dept.nombre = nombre
                    dept.region = region
                    dept.nivel_riesgo = nivel_riesgo
                    dept.factor_riesgo = factor_riesgo
                    dept.save()
                    actualizados += 1
                    self.stdout.write(f'  [~] {nombre} ({codigo}) actualizado')
                else:
                    sin_cambios += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDepartamentos: {creados} creados, {actualizados} actualizados, {sin_cambios} sin cambios.'
        ))

from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.management import call_command
import sys
from apps.security_probabilistic.scripts.cargar_municipios_lote1 import cargar_todos_municipios as cargar_lote1
from apps.security_probabilistic.scripts.cargar_municipios_lote2 import cargar_municipios_lote2
from apps.security_probabilistic.scripts.cargar_municipios_lote3 import cargar_municipios_lote3
from apps.security_probabilistic.scripts.cargar_municipios_lote4 import cargar_municipios_lote4
from apps.security_probabilistic.scripts.cargar_municipios_lote5 import cargar_municipios_lote5
from apps.security_probabilistic.scripts.cargar_municipios_lote6 import cargar_municipios_lote6

LOTES = [
    ('Lote 1', cargar_lote1),
    ('Lote 2', cargar_municipios_lote2),
    ('Lote 3', cargar_municipios_lote3),
    ('Lote 4', cargar_municipios_lote4),
    ('Lote 5', cargar_municipios_lote5),
    ('Lote 6', cargar_municipios_lote6),
]


class Command(BaseCommand):
    help = 'Carga los 33 departamentos y todos los municipios de Colombia'

    def handle(self, *args, **options):
        # Forzar UTF-8 en stdout para que los print() con emojis de los scripts no fallen
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')

        self.stdout.write(self.style.SUCCESS('=== Iniciando carga de ubicaciones ==='))

        # Paso 1: cargar departamentos (prerequisito para municipios)
        self.stdout.write('\nPaso 1: Cargando departamentos...')
        call_command('load_departments')

        # Paso 2: cargar municipios por lotes
        self.stdout.write('\nPaso 2: Cargando municipios por lotes...')
        errores = []

        for nombre_lote, funcion_lote in LOTES:
            self.stdout.write(f'  Procesando {nombre_lote}...')
            try:
                with transaction.atomic():
                    creados = funcion_lote()
                self.stdout.write(self.style.SUCCESS(f'  {nombre_lote} completado ({creados} creados)'))
            except Exception as e:
                errores.append((nombre_lote, str(e)))
                self.stdout.write(self.style.ERROR(f'  {nombre_lote} falló: {e}'))

        if errores:
            self.stdout.write(self.style.ERROR(
                f'\nCarga finalizada con {len(errores)} error(es):'
            ))
            for lote, err in errores:
                self.stdout.write(self.style.ERROR(f'  - {lote}: {err}'))
        else:
            self.stdout.write(self.style.SUCCESS('\nTodos los lotes cargados correctamente.'))

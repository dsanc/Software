from django.core.management.base import BaseCommand
from apps.security_probabilistic.scripts.cargar_municipios_lote1 import cargar_todos_municipios as cargar_lote1
from apps.security_probabilistic.scripts.cargar_municipios_lote2 import cargar_municipios_lote2
from apps.security_probabilistic.scripts.cargar_municipios_lote3 import cargar_municipios_lote3
from apps.security_probabilistic.scripts.cargar_municipios_lote4 import cargar_municipios_lote4
from apps.security_probabilistic.scripts.cargar_municipios_lote5 import cargar_municipios_lote5
from apps.security_probabilistic.scripts.cargar_municipios_lote6 import cargar_municipios_lote6

class Command(BaseCommand):
    help = 'Carga todos los municipios de Colombia desde los scripts por lotes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando carga de municipios...'))
        
        try:
            self.stdout.write('Procesando Lote 1...')
            cargar_lote1()
            self.stdout.write(self.style.SUCCESS('Lote 1 cargado exitosamente'))
            
            self.stdout.write('Procesando Lote 2...')
            cargar_municipios_lote2()
            self.stdout.write(self.style.SUCCESS('Lote 2 cargado exitosamente'))
            
            self.stdout.write('Procesando Lote 3...')
            cargar_municipios_lote3()
            self.stdout.write(self.style.SUCCESS('Lote 3 cargado exitosamente'))
            
            self.stdout.write('Procesando Lote 4...')
            cargar_municipios_lote4()
            self.stdout.write(self.style.SUCCESS('Lote 4 cargado exitosamente'))
            
            self.stdout.write('Procesando Lote 5...')
            cargar_municipios_lote5()
            self.stdout.write(self.style.SUCCESS('Lote 5 cargado exitosamente'))
            
            self.stdout.write('Procesando Lote 6...')
            cargar_municipios_lote6()
            self.stdout.write(self.style.SUCCESS('Lote 6 cargado exitosamente'))
            
            self.stdout.write(self.style.SUCCESS('Todos los municipios han sido cargados correctamente'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cargando municipios: {str(e)}'))

"""
Django management command para cargar municipios de Colombia
Reemplaza los scripts individuales en la raíz del proyecto
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.security_probabilistic.models import Departamento, Municipio


class Command(BaseCommand):
    help = 'Carga todos los municipios de Colombia organizados por departamento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lote',
            type=int,
            choices=[1, 2, 3, 4, 5, 6],
            help='Cargar un lote específico de municipios'
        )
        parser.add_argument(
            '--todos',
            action='store_true',
            help='Cargar todos los municipios (todos los lotes)'
        )

    def handle(self, *args, **options):
        if options['todos']:
            self.cargar_todos_municipios()
        elif options['lote']:
            self.cargar_lote_especifico(options['lote'])
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Especifica --lote [1-6] o --todos'
                )
            )

    @transaction.atomic
    def cargar_todos_municipios(self):
        """Carga todos los municipios de Colombia"""
        self.stdout.write("🇨🇴 Cargando TODOS los municipios de Colombia...")
        self.stdout.write("📊 Total objetivo: 1,122 municipios")
        
        # Consolidar lógica de todos los scripts aquí
        for lote in range(1, 7):
            self.cargar_lote_especifico(lote)
            
        total_municipios = Municipio.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Carga completada: {total_municipios} municipios'
            )
        )

    def cargar_lote_especifico(self, lote):
        """Carga un lote específico de municipios"""
        self.stdout.write(f"📦 Cargando lote {lote}...")
        
        # TODO: Implementar lógica específica por lote
        # Consolidar el código de cargar_municipios_lote{X}.py
        
        pass
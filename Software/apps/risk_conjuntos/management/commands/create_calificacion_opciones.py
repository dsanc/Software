"""
Comando para crear/actualizar las opciones de calificación del sistema de evaluación de riesgos.
Escala: ausente → deficiente → vulnerable → adecuado → eficaz
"""
from django.core.management.base import BaseCommand
from apps.risk_conjuntos.models import CalificacionOpcion


class Command(BaseCommand):
    help = 'Crea las opciones de calificación (escala ausente-eficaz) para las evaluaciones de riesgo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Elimina las opciones existentes antes de crear nuevas',
        )

    def handle(self, *args, **options):
        if options['clean']:
            count = CalificacionOpcion.objects.count()
            CalificacionOpcion.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Se eliminaron {count} opciones existentes.'))

        opciones = [
            {'codigo': 'ausente',    'nombre': 'Ausente',    'valor': 0.005, 'orden': 1},
            {'codigo': 'deficiente', 'nombre': 'Deficiente', 'valor': 0.1,   'orden': 2},
            {'codigo': 'vulnerable', 'nombre': 'Vulnerable', 'valor': 0.25,  'orden': 3},
            {'codigo': 'adecuado',   'nombre': 'Adecuado',   'valor': 0.6,   'orden': 4},
            {'codigo': 'eficaz',     'nombre': 'Eficaz',     'valor': 0.9,   'orden': 5},
        ]

        creadas = 0
        actualizadas = 0

        for data in opciones:
            obj, created = CalificacionOpcion.objects.update_or_create(
                codigo=data['codigo'],
                defaults={
                    'nombre': data['nombre'],
                    'valor':  data['valor'],
                    'orden':  data['orden'],
                    'activa': True,
                }
            )
            if created:
                creadas += 1
                self.stdout.write(self.style.SUCCESS(f'  [+] Creada: {obj.codigo} - {obj.nombre} ({obj.valor})'))
            else:
                actualizadas += 1
                self.stdout.write(f'  [~] Actualizada: {obj.codigo} - {obj.nombre} ({obj.valor})')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Proceso completado: {creadas} creadas, {actualizadas} actualizadas. '
            f'Total: {CalificacionOpcion.objects.filter(activa=True).count()} opciones activas.'
        ))

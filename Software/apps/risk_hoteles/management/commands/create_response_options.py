"""
Comando para crear/actualizar las opciones de respuesta del sistema de evaluaciones.
Gestiona la escala de calificación 0-5 más la opción 'No Aplica' (-1).

Uso:
    python manage.py create_response_options
"""
from django.core.management.base import BaseCommand
from apps.risk_hoteles.models import ResponseOption


class Command(BaseCommand):
    help = 'Crea/actualiza las opciones de respuesta para las evaluaciones de seguridad'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Configurando opciones de respuesta...'))

        options_data = [
            {
                'value': -1,
                'label': 'No Aplica',
                'description': (
                    'No aplica - Por el tipo de organización hotelera, por la dinámica operativa, '
                    'por ubicación o servicio, el criterio no aplica para este establecimiento.'
                ),
                'order': 0,
            },
            {
                'value': 0,
                'label': 'Expuesto',
                'description': (
                    'Expuesto - Se carece de dicho control. El hotel no cuenta con ninguna medida, '
                    'procedimiento o recurso que mitigue el riesgo evaluado. Existe exposición total.'
                ),
                'order': 1,
            },
            {
                'value': 1,
                'label': 'Vulnerable',
                'description': (
                    'Vulnerable - El control que se tiene es totalmente vulnerable dado que no cumple '
                    'con ningún nivel de efectividad y podría ser superado, quebrantado u omitido dado '
                    'que no genera ningún tipo de incidencia en la mitigación del riesgo o en el '
                    'cumplimiento cabal del requisito.'
                ),
                'order': 2,
            },
            {
                'value': 2,
                'label': 'Insuficiente',
                'description': (
                    'Insuficiente - El control puede funcionar en ocasiones o incidir positivamente '
                    'en algunos casos pero no en todos. Esto implica que el control no es efectivo '
                    'para la mayoría de los casos y su fallo es recurrente.'
                ),
                'order': 3,
            },
            {
                'value': 3,
                'label': 'Estándar',
                'description': (
                    'Estándar - El control que se tiene funciona de manera regular la mayoría de las '
                    'veces. Este podría fallar en ocasiones determinadas, ocurrentes pero no recurrentes. '
                    'Se considera que el control es efectivo pero en algunos casos presenta variabilidad '
                    'en su funcionamiento.'
                ),
                'order': 4,
            },
            {
                'value': 4,
                'label': 'Adecuado',
                'description': (
                    'Adecuado - El control que se tiene funciona adecuadamente la mayoría de las veces. '
                    'Este podría fallar excepcionalmente. Se considera que el control es efectivo '
                    'cumpliendo confiablemente con el requisito.'
                ),
                'order': 5,
            },
            {
                'value': 5,
                'label': 'Excelente',
                'description': (
                    'Excelente - El control que se tiene funciona con un nivel superior, dado que tiene '
                    'mecanismos redundantes y cuenta con diseño a prueba de fallos. Se considera que el '
                    'control es efectivo, cumple a un nivel más alto que garantiza su constante '
                    'confiabilidad y no se conocen fallos de este.'
                ),
                'order': 6,
            },
        ]

        created_count = 0
        updated_count = 0

        for opt in options_data:
            obj, created = ResponseOption.objects.update_or_create(
                value=opt['value'],
                defaults={
                    'label': opt['label'],
                    'description': opt['description'],
                    'order': opt['order'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Creada: [{opt["value"]:+d}] {opt["label"]}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'  ↻ Actualizada: [{opt["value"]:+d}] {opt["label"]}'))

        total = ResponseOption.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Opciones de respuesta configuradas!\n'
                f'   • Creadas: {created_count}\n'
                f'   • Actualizadas: {updated_count}\n'
                f'   • Total en sistema: {total}'
            )
        )

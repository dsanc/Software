"""
Comando para poblar una evaluación de seguridad completa con respuestas de demostración.

Genera SecurityResponse para cada pregunta de las 14 categorías y recalcula
SecurityCategoryScore, activando todas las secciones del panel hotel_detail.

Uso:
    python manage.py populate_demo_assessment
    python manage.py populate_demo_assessment --hotel-id <uuid>
    python manage.py populate_demo_assessment --assessment-id <uuid>
    python manage.py populate_demo_assessment --recalculate-only
    python manage.py populate_demo_assessment --clear
"""
import random
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = 'Pobla una evaluación con respuestas de demostración y recalcula los scores por categoría'

    # Perfil de calificaciones por categoría (peso probabilístico: rating → probabilidad)
    # Simula un hotel de nivel medio con algunas fortalezas y debilidades reales
    CATEGORY_PROFILES = {
        'gestion_organizacion':   [0, 1, 2, 2, 3, 3, 3, 2, 1, 0],   # Deficiente
        'seguridad_externa':      [0, 1, 1, 2, 2, 3, 3, 4, 3, 2],   # Regular
        'seguridad_perimetral':   [0, 1, 2, 2, 3, 3, 4, 4, 3, 2],   # Regular
        'seguridad_internas':     [1, 2, 2, 3, 3, 3, 4, 4, 3, 2],   # Moderado
        'controles_accesos':      [0, 1, 1, 2, 2, 2, 3, 3, 2, 1],   # Bajo
        'seguridad_habitaciones': [1, 1, 2, 2, 3, 3, 3, 4, 3, 2],   # Moderado
        'seguridad_activos':      [0, 1, 1, 1, 2, 2, 3, 3, 2, 1],   # Bajo
        'seguridad_parqueo':      [1, 2, 2, 3, 3, 3, 4, 4, 3, 3],   # Regular
        'gestion_humana':         [0, 1, 1, 2, 2, 2, 3, 3, 2, 1],   # Bajo
        'seguridad_eventos':      [1, 2, 2, 3, 3, 4, 4, 3, 3, 2],   # Moderado
        'seguridad_ayb':          [1, 2, 2, 2, 3, 3, 3, 4, 3, 2],   # Moderado
        'seguridad_reservas':     [0, 1, 1, 2, 2, 3, 3, 3, 2, 1],   # Bajo
        'seguridad_compras':      [1, 2, 2, 3, 3, 3, 4, 4, 3, 2],   # Regular
        'gestion_emergencias':    [0, 0, 1, 1, 2, 2, 2, 3, 2, 1],   # Crítico
    }

    COMMENTS_POOL = {
        0: [
            'No se evidencia ningún control implementado.',
            'Se carece completamente de este elemento.',
            'No existe documentación ni procedimiento al respecto.',
        ],
        1: [
            'El control existe pero es completamente ineficaz en la práctica.',
            'Se observa un intento de implementación pero sin efectividad real.',
            'Control muy básico, fácilmente superable.',
        ],
        2: [
            'El control funciona esporádicamente, con fallas frecuentes.',
            'Se aplica en algunos casos pero no de manera sistemática.',
            'Implementación parcial con vacíos significativos.',
        ],
        3: [
            'Control funcional la mayoría del tiempo con fallas ocasionales.',
            'Cumple el estándar mínimo esperado.',
            'Requiere mejoras puntuales para ser más confiable.',
        ],
        4: [
            'Control bien implementado y confiable.',
            'Cumple adecuadamente con el requisito evaluado.',
            'Solo presenta fallas excepcionales.',
        ],
        5: [
            'Control con nivel superior, mecanismos redundantes implementados.',
            'Diseño a prueba de fallos, sin incidentes conocidos.',
            'Ejemplo de buena práctica en gestión de seguridad.',
        ],
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel-id',
            type=str,
            help='UUID del hotel. Si se omite, usa el primero disponible.',
        )
        parser.add_argument(
            '--assessment-id',
            type=str,
            help='UUID de la evaluación existente a poblar. Si se omite, usa la primera.',
        )
        parser.add_argument(
            '--recalculate-only',
            action='store_true',
            help='Solo recalcula SecurityCategoryScore sin modificar las respuestas.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todas las respuestas demo antes de generar nuevas.',
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=42,
            help='Semilla para reproducibilidad (default: 42)',
        )

    def handle(self, *args, **options):
        from apps.risk_hoteles.models import (
            Hotel, SecurityAssessment, SecurityCategory,
            SecurityQuestion, SecurityResponse, SecurityCategoryScore,
        )

        random.seed(options['seed'])

        # ── 1. Obtener / validar evaluación ──────────────────────────────────
        assessment = self._get_assessment(options, SecurityAssessment, Hotel)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🏨 Hotel: {assessment.hotel.name}\n'
                f'📋 Evaluación: {assessment.id}\n'
                f'📅 Fecha: {assessment.assessment_date.strftime("%Y-%m-%d")}\n'
                f'📊 Estado actual: {assessment.status}\n'
            )
        )

        # ── 2. Asegurar categorías seleccionadas ─────────────────────────────
        all_categories = SecurityCategory.objects.filter(is_active=True).order_by('order')
        if all_categories.count() == 0:
            raise CommandError(
                'No hay SecurityCategory en la BD. '
                'Ejecuta primero: python manage.py create_security_categories'
            )

        current_cats = assessment.selected_categories.count()
        if current_cats == 0:
            assessment.selected_categories.set(all_categories)
            self.stdout.write(
                self.style.WARNING(
                    f'  → Se asignaron {all_categories.count()} categorías a la evaluación.'
                )
            )
        else:
            self.stdout.write(f'  → Categorías ya asignadas: {current_cats}')

        # ── 3. Solo recalcular si se pide ────────────────────────────────────
        if options['recalculate_only']:
            self._recalculate_scores(assessment)
            return

        # ── 4. Limpiar respuestas si se pide ────────────────────────────────
        if options['clear']:
            deleted, _ = SecurityResponse.objects.filter(assessment=assessment).delete()
            self.stdout.write(self.style.WARNING(f'  → {deleted} respuestas eliminadas.'))

        # ── 5. Generar respuestas ────────────────────────────────────────────
        self.stdout.write('\n📝 Generando respuestas por categoría...')
        total_created = 0
        total_skipped = 0

        for category in all_categories:
            questions = SecurityQuestion.objects.filter(
                category=category,
                is_active=True,
            ).order_by('order')

            if not questions.exists():
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Sin preguntas: {category.name}')
                )
                continue

            profile = self.CATEGORY_PROFILES.get(category.code, [1, 2, 3, 3, 4, 3, 2, 2, 1, 1])
            cat_created = 0
            cat_skipped = 0

            for question in questions:
                # No sobrescribir respuestas existentes (salvo --clear)
                if SecurityResponse.objects.filter(
                    assessment=assessment, question=question
                ).exists():
                    cat_skipped += 1
                    continue

                rating = random.choice(profile)
                comment = random.choice(self.COMMENTS_POOL[rating])

                SecurityResponse.objects.create(
                    assessment=assessment,
                    question=question,
                    rating=rating,
                    not_applicable=False,
                    comments=comment,
                )
                cat_created += 1

            total_created += cat_created
            total_skipped += cat_skipped

            avg_profile = sum(profile) / len(profile)
            self.stdout.write(
                f'  ✓ {category.name:<45} '
                f'{questions.count():>3} preguntas  '
                f'creadas:{cat_created:>3}  '
                f'omitidas:{cat_skipped:>3}  '
                f'(perfil ~{avg_profile:.1f}/5)'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n  Total respuestas creadas : {total_created}\n'
                f'  Total respuestas omitidas: {total_skipped}'
            )
        )

        # ── 6. Recalcular scores ─────────────────────────────────────────────
        self._recalculate_scores(assessment)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_assessment(self, options, SecurityAssessment, Hotel):
        if options.get('assessment_id'):
            try:
                return SecurityAssessment.objects.get(id=options['assessment_id'])
            except SecurityAssessment.DoesNotExist:
                raise CommandError(f'Evaluación no encontrada: {options["assessment_id"]}')

        if options.get('hotel_id'):
            try:
                hotel = Hotel.objects.get(id=options['hotel_id'])
            except Hotel.DoesNotExist:
                raise CommandError(f'Hotel no encontrado: {options["hotel_id"]}')
            assessment = SecurityAssessment.objects.filter(hotel=hotel).order_by('-assessment_date').first()
            if not assessment:
                raise CommandError(f'No hay evaluaciones para el hotel: {hotel.name}')
            return assessment

        # Usar la primera evaluación disponible
        assessment = SecurityAssessment.objects.order_by('-assessment_date').first()
        if not assessment:
            raise CommandError(
                'No hay evaluaciones en la BD. '
                'Crea una evaluación desde la interfaz web primero.'
            )
        return assessment

    def _recalculate_scores(self, assessment):
        from apps.risk_hoteles.models import SecurityCategoryScore

        self.stdout.write('\n🔢 Recalculando scores por categoría...')

        # Borrar scores previos para esta evaluación
        deleted, _ = SecurityCategoryScore.objects.filter(assessment=assessment).delete()
        if deleted:
            self.stdout.write(self.style.WARNING(f'  → {deleted} scores anteriores eliminados.'))

        # Recalcular usando el método del modelo
        assessment.save_calculated_scores()

        # Guardar overall_score y estado
        assessment.status = 'completed'
        assessment.completed_at = assessment.completed_at or timezone.now()
        assessment.save(update_fields=['overall_score', 'risk_level', 'status', 'completed_at'])

        # Mostrar resultados
        category_scores = assessment.category_scores.select_related('category').order_by(
            'category__order'
        )

        self.stdout.write(f'\n{"Categoría":<45} {"Preguntas":>9} {"Promedio":>9} {"Score%":>7}')
        self.stdout.write('─' * 75)

        for cs in category_scores:
            bar_len = int(cs.percentage / 5)  # 0–20 chars
            bar = '█' * bar_len + '░' * (20 - bar_len)
            self.stdout.write(
                f'  {cs.category.name:<43} '
                f'{cs.question_count:>9} '
                f'{cs.average_score:>9.2f} '
                f'{cs.percentage:>6.1f}%  {bar}'
            )

        overall_pct = assessment.calculate_overall_score()
        self.stdout.write('─' * 75)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n  📊 Overall score  : {assessment.overall_score:.2f} / 5.00\n'
                f'  📊 Overall %      : {overall_pct:.1f}%\n'
                f'  🚦 Nivel de riesgo: {assessment.get_risk_level_display() if assessment.risk_level else "N/D"}\n'
                f'  📁 Scores guardados: {category_scores.count()}\n'
                f'\n✅ Evaluación lista. Recarga hotel_detail en el navegador para ver los análisis.'
            )
        )

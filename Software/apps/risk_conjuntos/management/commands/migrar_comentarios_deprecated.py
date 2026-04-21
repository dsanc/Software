"""
Comando para migrar comentarios deprecated de RespuestaPregunta a ComentarioRiesgo
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.risk_conjuntos.models import RespuestaPregunta, ComentarioRiesgo


class Command(BaseCommand):
    help = 'Migra comentarios deprecated de RespuestaPregunta a ComentarioRiesgo'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo prueba sin hacer cambios',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO PRUEBA - No se harán cambios'))
        
        # Obtener todas las respuestas con comentarios
        respuestas_con_comentarios = RespuestaPregunta.objects.filter(
            comentarios__isnull=False
        ).exclude(comentarios='').select_related(
            'evaluacion', 'pregunta__escenario__tipo_riesgo'
        )
        
        total_respuestas = respuestas_con_comentarios.count()
        
        if total_respuestas == 0:
            self.stdout.write(self.style.SUCCESS('No hay comentarios para migrar'))
            return
        
        self.stdout.write(f'Encontradas {total_respuestas} respuestas con comentarios')
        
        migrados = 0
        errores = 0
        
        with transaction.atomic():
            for respuesta in respuestas_con_comentarios:
                try:
                    # Buscar o crear ComentarioRiesgo para esta evaluación y tipo de riesgo
                    tipo_riesgo = respuesta.pregunta.escenario.tipo_riesgo
                    evaluacion = respuesta.evaluacion
                    
                    comentario_riesgo, created = ComentarioRiesgo.objects.get_or_create(
                        evaluacion=evaluacion,
                        tipo_riesgo=tipo_riesgo,
                        defaults={'comentario': ''}
                    )
                    
                    # Agregar el comentario de la respuesta al comentario general del riesgo
                    comentario_existente = comentario_riesgo.comentario.strip()
                    comentario_nuevo = respuesta.comentarios.strip()
                    
                    if comentario_existente:
                        # Si ya hay un comentario, agregarlo con separador
                        comentario_final = f"{comentario_existente}\n\n--- Pregunta: {respuesta.pregunta.texto_pregunta[:100]}... ---\n{comentario_nuevo}"
                    else:
                        # Si no hay comentario previo, usar directamente el nuevo
                        comentario_final = f"--- Pregunta: {respuesta.pregunta.texto_pregunta[:100]}... ---\n{comentario_nuevo}"
                    
                    if not dry_run:
                        comentario_riesgo.comentario = comentario_final
                        comentario_riesgo.save()
                        
                        # Limpiar el comentario deprecated (opcional, comentado para seguridad)
                        # respuesta.comentarios = ''
                        # respuesta.save(update_fields=['comentarios'])
                    
                    migrados += 1
                    
                    if created:
                        self.stdout.write(f'✓ Creado nuevo ComentarioRiesgo para {tipo_riesgo.nombre}')
                    else:
                        self.stdout.write(f'✓ Actualizado ComentarioRiesgo existente para {tipo_riesgo.nombre}')
                    
                except Exception as e:
                    errores += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error migrando respuesta {respuesta.id}: {str(e)}')
                    )
        
        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Migración completada:')
        self.stdout.write(f'- Comentarios migrados: {migrados}')
        self.stdout.write(f'- Errores: {errores}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO PRUEBA - Ejecutar sin --dry-run para aplicar cambios'))
        else:
            self.stdout.write(self.style.SUCCESS('Migración aplicada exitosamente'))
            self.stdout.write(
                self.style.WARNING(
                    'NOTA: Los comentarios en RespuestaPregunta no se eliminaron por seguridad.\n'
                    'Ejecutar manualmente después de verificar la migración.'
                )
            )
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Limpia avatares de usuarios que apuntan a archivos inexistentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué avatares se limpiarían sin hacer cambios',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Limpiar avatar solo de un usuario específico',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        username = options.get('username')
        
        if username:
            users = User.objects.filter(username=username)
            if not users.exists():
                self.stdout.write(
                    self.style.ERROR(f'Usuario "{username}" no encontrado')
                )
                return
        else:
            users = User.objects.exclude(avatar='')
        
        cleaned_count = 0
        total_count = users.count()
        
        self.stdout.write(f'Revisando {total_count} usuarios con avatares...')
        
        for user in users:
            if user.avatar:
                # Verificar si el archivo existe
                if not default_storage.exists(user.avatar.name):
                    if dry_run:
                        self.stdout.write(
                            f'[DRY RUN] Limpiaría avatar inválido del usuario: {user.username} ({user.avatar.name})'
                        )
                    else:
                        old_avatar = user.avatar.name
                        user.avatar = None
                        user.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Avatar limpiado para {user.username} (era: {old_avatar})'
                            )
                        )
                    cleaned_count += 1
                else:
                    self.stdout.write(f'✓ Avatar OK para {user.username}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Se limpiarían {cleaned_count} avatares de {total_count} usuarios'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Limpiados {cleaned_count} avatares de {total_count} usuarios'
                )
            )
            
        if cleaned_count == 0:
            self.stdout.write(
                self.style.SUCCESS('🎉 Todos los avatares están en perfecto estado!')
            )
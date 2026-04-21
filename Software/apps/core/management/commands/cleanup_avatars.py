"""
Django management command para limpiar avatares huérfanos
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings


class Command(BaseCommand):
    help = 'Limpia avatares de usuarios que ya no existen en el sistema de archivos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué avatares se limpiarían sin modificar la base de datos'
        )

    def handle(self, *args, **options):
        User = get_user_model()
        dry_run = options['dry_run']
        
        users_with_avatars = User.objects.exclude(avatar='').exclude(avatar__isnull=True)
        cleaned_count = 0
        
        self.stdout.write(f"🔍 Verificando {users_with_avatars.count()} usuarios con avatares...")
        
        for user in users_with_avatars:
            avatar_path = user.avatar.path if hasattr(user.avatar, 'path') else None
            
            # Verificar si el archivo existe
            file_exists = False
            if avatar_path:
                try:
                    file_exists = os.path.exists(avatar_path)
                except:
                    file_exists = False
            
            if not file_exists:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"LIMPIARÍA: {user.email} - Avatar: {user.avatar}"
                        )
                    )
                else:
                    # Limpiar el avatar de la base de datos
                    user.avatar.delete(save=False)  # No eliminar archivo (ya no existe)
                    user.avatar = None
                    user.save()
                    cleaned_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Limpiado: {user.email}"
                        )
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Se limpiarían {cleaned_count} avatares huérfanos"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"🧹 Limpieza completada: {cleaned_count} avatares huérfanos eliminados"
                )
            )
            
        # Mostrar estadísticas finales
        remaining_users = User.objects.exclude(avatar='').exclude(avatar__isnull=True).count()
        self.stdout.write(f"📊 Usuarios con avatares válidos: {remaining_users}")
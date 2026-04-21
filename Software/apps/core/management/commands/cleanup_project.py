"""
Django management command para limpiar archivos temporales y de desarrollo
"""
import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Limpia archivos temporales, de testing y desarrollo del proyecto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué archivos se eliminarían sin borrar realmente'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar eliminación sin confirmación'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Directorio raíz del proyecto
        project_root = Path(settings.BASE_DIR)
        
        # Lista de archivos y patrones a limpiar
        files_to_clean = [
            # Archivos temporales específicos
            'check_brackets.py',
            'css-test.html',
            'accessibility_summary.js',
            
            # Scripts que deberían ser comandos Django
            'cargar_municipios_lote1.py',
            'cargar_municipios_lote2.py',
            'cargar_municipios_lote3.py',
            'cargar_municipios_lote4.py',
            'cargar_municipios_lote5.py',
            'cargar_municipios_lote6.py',
        ]
        
        # Directorios temporales
        dirs_to_clean = [
            '__pycache__',
            '.pytest_cache',
            'htmlcov',
            '.coverage',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.Python',
            'env',
            'pip-log.txt',
            'pip-delete-this-directory.txt',
            '.tox',
            '.cache',
            'nosetests.xml',
            'coverage.xml',
            '*.cover',
            '*.log',
            '.git/*',
            '.mypy_cache',
            '.pytest_cache',
            '.hypothesis',
        ]
        
        cleaned_files = []
        
        # Limpiar archivos específicos
        for filename in files_to_clean:
            file_path = project_root / filename
            if file_path.exists():
                if dry_run:
                    self.stdout.write(f"ELIMINARÍA: {file_path}")
                else:
                    if force or self.confirm_deletion(file_path):
                        file_path.unlink()
                        cleaned_files.append(str(file_path))
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Eliminado: {file_path}")
                        )
        
        # Limpiar directorios __pycache__
        for root, dirs, files in os.walk(project_root):
            if '__pycache__' in dirs:
                pycache_path = Path(root) / '__pycache__'
                if dry_run:
                    self.stdout.write(f"ELIMINARÍA DIRECTORIO: {pycache_path}")
                else:
                    shutil.rmtree(pycache_path)
                    cleaned_files.append(str(pycache_path))
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Eliminado directorio: {pycache_path}")
                    )
        
        # Limpiar archivos .pyc
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.pyc'):
                    pyc_path = Path(root) / file
                    if dry_run:
                        self.stdout.write(f"ELIMINARÍA: {pyc_path}")
                    else:
                        pyc_path.unlink()
                        cleaned_files.append(str(pyc_path))
        
        # Resumen
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Se eliminarían {len(cleaned_files)} archivos/directorios"
                )
            )
            self.stdout.write("Ejecuta sin --dry-run para hacer la limpieza real")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"🧹 Limpieza completada: {len(cleaned_files)} archivos/directorios eliminados"
                )
            )
            
    def confirm_deletion(self, file_path):
        """Confirmar eliminación de archivo importante"""
        if file_path.suffix in ['.py', '.html', '.js']:
            response = input(f"¿Eliminar {file_path}? [y/N]: ")
            return response.lower() in ['y', 'yes']
        return True
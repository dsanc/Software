from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import CommandError
import getpass

User = get_user_model()


class Command(BaseCommand):
    help = 'Crear un superusuario con email'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            help='Email del superusuario',
        )
        parser.add_argument(
            '--first_name',
            help='Nombre del superusuario',
        )
        parser.add_argument(
            '--last_name',
            help='Apellido del superusuario',
        )
    
    def handle(self, *args, **options):
        email = options.get('email')
        first_name = options.get('first_name')
        last_name = options.get('last_name')
        
        if not email:
            email = input('Email: ')
        
        if not first_name:
            first_name = input('Nombre: ')
            
        if not last_name:
            last_name = input('Apellido: ')
        
        # Generar username basado en email
        username = email.split('@')[0]
        
        # Verificar si el usuario ya existe
        if User.objects.filter(email=email).exists():
            raise CommandError(f'El usuario con email {email} ya existe')
        
        # Solicitar contraseña
        password = getpass.getpass('Contraseña: ')
        password_confirm = getpass.getpass('Confirmar contraseña: ')
        
        if password != password_confirm:
            raise CommandError('Las contraseñas no coinciden')
        
        # Crear el superusuario
        user = User.objects.create_superuser(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Superusuario {user.email} creado exitosamente')
        )
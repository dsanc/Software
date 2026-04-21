"""
Comando para probar el sistema de seguridad
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models
from apps.users.services import AccountSecurityService, TwoFactorService
from apps.users.models import LoginAttempt, AccountLockout, SecurityEvent
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Comando para probar y demostrar el sistema de seguridad'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-lockout',
            action='store_true',
            help='Probar sistema de bloqueo por intentos fallidos'
        )
        parser.add_argument(
            '--test-2fa',
            action='store_true',
            help='Probar configuración básica de 2FA'
        )
        parser.add_argument(
            '--security-stats',
            action='store_true',
            help='Mostrar estadísticas de seguridad'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Limpiar datos de prueba y bloqueos expirados'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔐 Sistema de Seguridad - Django Modular')
        )
        self.stdout.write('=' * 50)

        if options['test_lockout']:
            self.test_lockout_system()

        if options['test_2fa']:
            self.test_2fa_system()

        if options['security_stats']:
            self.show_security_stats()

        if options['cleanup']:
            self.cleanup_test_data()

        if not any([options['test_lockout'], options['test_2fa'], 
                   options['security_stats'], options['cleanup']]):
            self.show_help()

    def test_lockout_system(self):
        """Probar sistema de bloqueo por intentos fallidos"""
        self.stdout.write('\n🚫 Probando Sistema de Bloqueo...')
        
        # Buscar o crear usuario de prueba
        test_user, created = User.objects.get_or_create(
            email='test@ejemplo.com',
            defaults={
                'username': 'testuser',
                'first_name': 'Usuario',
                'last_name': 'Prueba'
            }
        )
        
        if created:
            test_user.set_password('password123')
            test_user.save()
            self.stdout.write(f'✅ Usuario de prueba creado: {test_user.email}')
        else:
            self.stdout.write(f'📋 Usando usuario existente: {test_user.email}')

        # Simular intentos fallidos
        self.stdout.write('🔄 Simulando intentos de login fallidos...')
        
        for i in range(6):  # Más del límite permitido
            AccountSecurityService.record_login_attempt(
                username=test_user.email,
                ip_address='192.168.1.100',
                user_agent='Test Browser/1.0',
                success=False,
                failure_reason='Contraseña incorrecta',
                user=test_user
            )
            
            if AccountSecurityService.is_account_locked(test_user):
                lockout = AccountSecurityService.get_active_lockout(test_user)
                self.stdout.write(
                    self.style.WARNING(
                        f'🔒 Cuenta bloqueada después del intento {i+1}'
                    )
                )
                self.stdout.write(
                    f'   ⏰ Tiempo de desbloqueo: {lockout.unlock_at}'
                )
                break
            else:
                recent_failures = AccountSecurityService.get_recent_failed_attempts(test_user)
                remaining = AccountSecurityService.MAX_LOGIN_ATTEMPTS - recent_failures.count()
                self.stdout.write(
                    f'   ⚠️  Intento {i+1} fallido. Quedan {remaining} intentos.'
                )

    def test_2fa_system(self):
        """Probar configuración básica de 2FA"""
        self.stdout.write('\n🔐 Probando Sistema 2FA...')
        
        # Estadísticas de 2FA
        total_users = User.objects.count()
        users_with_2fa = User.objects.filter(two_factor_enabled=True).count()
        
        self.stdout.write(f'📊 Usuarios totales: {total_users}')
        self.stdout.write(f'🛡️  Usuarios con 2FA: {users_with_2fa}')
        
        if total_users > 0:
            percentage = (users_with_2fa / total_users) * 100
            self.stdout.write(f'📈 Adopción de 2FA: {percentage:.1f}%')
            
            if percentage < 50:
                self.stdout.write(
                    self.style.WARNING('⚠️  Baja adopción de 2FA. Considera promover su uso.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ Buena adopción de 2FA.')
                )

        # Verificar dependencias de 2FA
        try:
            import django_otp
            from django_otp.plugins.otp_totp.models import TOTPDevice
            
            self.stdout.write('✅ django-otp instalado correctamente')
            
            totp_devices = TOTPDevice.objects.filter(confirmed=True).count()
            self.stdout.write(f'📱 Dispositivos TOTP activos: {totp_devices}')
            
        except ImportError:
            self.stdout.write(
                self.style.ERROR('❌ django-otp no está instalado')
            )

    def show_security_stats(self):
        """Mostrar estadísticas de seguridad"""
        self.stdout.write('\n📊 Estadísticas de Seguridad...')
        
        # Estadísticas generales
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Intentos de login
        total_attempts = LoginAttempt.objects.count()
        failed_attempts = LoginAttempt.objects.filter(success=False).count()
        recent_attempts_24h = LoginAttempt.objects.filter(timestamp__gte=last_24h).count()
        
        self.stdout.write(f'🔑 Total intentos de login: {total_attempts}')
        self.stdout.write(f'❌ Intentos fallidos: {failed_attempts}')
        self.stdout.write(f'📅 Intentos últimas 24h: {recent_attempts_24h}')
        
        if total_attempts > 0:
            failure_rate = (failed_attempts / total_attempts) * 100
            self.stdout.write(f'📉 Tasa de fallos: {failure_rate:.1f}%')

        # Bloqueos
        active_lockouts = AccountLockout.objects.filter(is_active=True).count()
        total_lockouts = AccountLockout.objects.count()
        recent_lockouts_7d = AccountLockout.objects.filter(locked_at__gte=last_7d).count()
        
        self.stdout.write(f'\n🔒 Bloqueos activos: {active_lockouts}')
        self.stdout.write(f'🔒 Total bloqueos históricos: {total_lockouts}')
        self.stdout.write(f'📅 Bloqueos últimos 7 días: {recent_lockouts_7d}')

        # Eventos de seguridad
        critical_events = SecurityEvent.objects.filter(
            severity='critical',
            timestamp__gte=last_7d
        ).count()
        high_events = SecurityEvent.objects.filter(
            severity='high',
            timestamp__gte=last_7d
        ).count()
        
        self.stdout.write(f'\n🚨 Eventos críticos (7d): {critical_events}')
        self.stdout.write(f'⚠️  Eventos alta severidad (7d): {high_events}')

        # Top IPs con intentos fallidos
        top_ips = (LoginAttempt.objects.filter(success=False, timestamp__gte=last_7d)
                  .values('ip_address')
                  .annotate(count=models.Count('id'))
                  .order_by('-count')[:5])
        
        if top_ips:
            self.stdout.write('\n🌐 Top IPs con intentos fallidos (7d):')
            for item in top_ips:
                self.stdout.write(f'   📍 {item["ip_address"]}: {item["count"]} intentos')

    def cleanup_test_data(self):
        """Limpiar datos de prueba y bloqueos expirados"""
        self.stdout.write('\n🧹 Limpiando datos...')
        
        # Limpiar bloqueos expirados
        expired_count = AccountSecurityService.cleanup_expired_lockouts()
        self.stdout.write(f'✅ Limpiados {expired_count} bloqueos expirados')
        
        # Opcional: limpiar usuarios de prueba
        test_users = User.objects.filter(email__endswith='@ejemplo.com')
        if test_users.exists():
            count = test_users.count()
            # test_users.delete()  # Comentado por seguridad
            self.stdout.write(f'📋 Encontrados {count} usuarios de prueba (no eliminados)')
        
        # Limpiar logs antiguos (más de 30 días)
        old_date = timezone.now() - timedelta(days=30)
        old_attempts = LoginAttempt.objects.filter(timestamp__lt=old_date)
        old_events = SecurityEvent.objects.filter(timestamp__lt=old_date)
        
        attempts_count = old_attempts.count()
        events_count = old_events.count()
        
        # old_attempts.delete()  # Comentado por seguridad
        # old_events.delete()   # Comentado por seguridad
        
        self.stdout.write(f'📋 Encontrados {attempts_count} intentos antiguos (no eliminados)')
        self.stdout.write(f'📋 Encontrados {events_count} eventos antiguos (no eliminados)')
        
        self.stdout.write(
            self.style.WARNING(
                '⚠️  Eliminación real comentada por seguridad. '
                'Descomenta en el código si es necesario.'
            )
        )

    def show_help(self):
        """Mostrar ayuda del comando"""
        self.stdout.write('\n📚 Opciones disponibles:')
        self.stdout.write('   --test-lockout     Probar sistema de bloqueo')
        self.stdout.write('   --test-2fa         Verificar sistema 2FA')
        self.stdout.write('   --security-stats   Mostrar estadísticas')
        self.stdout.write('   --cleanup          Limpiar datos antiguos')
        self.stdout.write('\nEjemplo:')
        self.stdout.write('   python manage.py test_security --security-stats')
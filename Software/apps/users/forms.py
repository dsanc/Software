from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """
    Formulario de autenticación mejorado que usa email en lugar de username
    """
    username = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com',
            'autofocus': True,
            'autocomplete': 'email',
            'id': 'id_username'
        })
    )
    
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu contraseña',
            'autocomplete': 'current-password',
            'id': 'id_password'
        })
    )
    
    remember_me = forms.BooleanField(
        label='Recordarme',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_remember_me'
        })
    )
    
    error_messages = {
        'invalid_login': (
            "Las credenciales ingresadas no son correctas. "
            "Verifica tu email y contraseña."
        ),
        'inactive': "Esta cuenta está inactiva. Contacta al administrador.",
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cambiar el label del campo username a Email
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs.update({
            'placeholder': 'tu@email.com'
        })
    
    def clean_username(self):
        """Limpiar y validar el campo email"""
        username = self.cleaned_data.get('username')
        if username:
            # Convertir a minúsculas para consistencia
            username = username.lower().strip()
        return username
    
    def clean(self):
        """Validación adicional del formulario"""
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Logging para debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Intentando autenticación para: {username}")
            
            # Verificar si el usuario existe
            try:
                user_exists = User.objects.filter(email=username).exists()
                if not user_exists:
                    logger.warning(f"Usuario no existe: {username}")
                    raise forms.ValidationError(
                        "No existe una cuenta con este email."
                    )
                else:
                    user = User.objects.get(email=username)
                    if not user.is_active:
                        logger.warning(f"Usuario inactivo: {username}")
                        raise forms.ValidationError(
                            "Esta cuenta está inactiva."
                        )
            except User.DoesNotExist:
                pass  # Será manejado por el backend de autenticación
        
        return cleaned_data
        # Cambiar el label del campo username a Email
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs.update({
            'placeholder': 'tu@email.com'
        })


class UserProfileForm(forms.ModelForm):
    """
    Formulario avanzado para editar el perfil del usuario
    """
    # Campo especial para confirmar email si se cambia
    confirm_email = forms.EmailField(
        label='Confirmar correo electrónico',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu nuevo email'
        })
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'avatar', 'job_title', 'company',
            'department', 'country', 'city',
            'email_notifications', 'sms_notifications'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre',
                'autocomplete': 'given-name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu apellido',
                'autocomplete': 'family-name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com',
                'autocomplete': 'email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+52123456789',
                'autocomplete': 'tel'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png',
                'id': 'avatar-input'
            }),
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Desarrollador Senior, Gerente, etc.',
                'autocomplete': 'organization-title'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de tu empresa',
                'autocomplete': 'organization'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Departamento o área',
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'México',
                'autocomplete': 'country-name'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad de México',
                'autocomplete': 'address-level2'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'phone': 'Teléfono',
            'avatar': 'Foto de perfil',
            'job_title': 'Cargo/Puesto',
            'company': 'Empresa',
            'department': 'Departamento',
            'country': 'País',
            'city': 'Ciudad',
            'email_notifications': 'Notificaciones por email',
            'sms_notifications': 'Notificaciones por SMS',
        }
        
        help_texts = {
            'phone': 'Formato internacional recomendado: +52123456789',
            'avatar': 'Imagen cuadrada recomendada. Se redimensionará automáticamente.',
            'email_notifications': 'Recibir notificaciones importantes por correo',
            'sms_notifications': 'Recibir notificaciones urgentes por SMS',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campo de confirmación de email
        if self.instance and self.instance.pk:
            self.fields['confirm_email'].initial = self.instance.email
        
        # Agregar validadores personalizados
        from .validators import (
            validate_avatar_image, validate_phone_number
        )
        
        self.fields['avatar'].validators.append(validate_avatar_image)
        self.fields['phone'].validators.append(validate_phone_number)
        
        # Hacer campos opcionales más claros
        optional_fields = [
            'phone', 'avatar',
            'job_title', 'company', 'department', 'country', 'city'
        ]
        
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False
    
    def clean_email(self):
        """Validar email y verificar disponibilidad"""
        email = self.cleaned_data.get('email')
        confirm_email = self.cleaned_data.get('confirm_email', '')
        
        if email:
            email = email.lower().strip()
            
            # Si el email cambió, verificar que esté disponible
            if self.instance.pk and email != self.instance.email:
                if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError("Este email ya está en uso por otro usuario.")
                
                # Verificar confirmación si se proporciona
                if confirm_email and email != confirm_email:
                    raise forms.ValidationError("La confirmación del email no coincide.")
        
        return email
    
    def clean_phone(self):
        """Limpiar y validar número telefónico"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remover espacios y caracteres comunes
            phone = re.sub(r'[\s\-\(\)]', '', phone)
            
            # Agregar código de país si no está presente
            if phone and not phone.startswith('+'):
                if len(phone) == 10:  # Número mexicano sin código
                    phone = '+52' + phone
        
        return phone

    def clean(self):
        """Validación adicional del formulario completo"""
        cleaned_data = super().clean()
        
        # Validar que si se habilitan SMS, se proporcione teléfono
        sms_notifications = cleaned_data.get('sms_notifications')
        phone = cleaned_data.get('phone')
        
        if sms_notifications and not phone:
            raise forms.ValidationError(
                "Para recibir notificaciones por SMS, debes proporcionar un número de teléfono."
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardar con procesamiento adicional"""
        user = super().save(commit=False)
        
        if commit:
            # Si el email cambió, marcar como no verificado
            if self.instance.pk and 'email' in self.changed_data:
                user.email_verified = False
            
            # Si el teléfono cambió, marcar como no verificado
            if self.instance.pk and 'phone' in self.changed_data:
                user.phone_verified = False
            
            user.save()
            
            # Log el cambio de perfil
            from .security_logging import security_logger
            import logging
            
            logger = logging.getLogger('apps.users')
            logger.info(f"Perfil actualizado para usuario {user.email}. Campos modificados: {self.changed_data}")
        
        return user


class QuickProfileForm(forms.ModelForm):
    """
    Formulario simplificado para edición rápida de perfil
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu apellido'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar validador de avatar
        from .validators import validate_avatar_image
        self.fields['avatar'].validators.append(validate_avatar_image)


class AvatarUploadForm(forms.Form):
    """
    Formulario específico para subida de avatar con preview
    """
    avatar = forms.ImageField(
        label='Seleccionar imagen',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png',
            'id': 'avatar-upload-input'
        })
    )
    
    # Campos para recorte de imagen (opcional)
    crop_x = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    crop_y = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    crop_width = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    crop_height = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar validador personalizado
        from .validators import validate_avatar_image
        self.fields['avatar'].validators.append(validate_avatar_image)
    
    def clean_avatar(self):
        """Validación adicional del avatar"""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Verificar tamaño del archivo (2MB máximo)
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError("El archivo es demasiado grande. Máximo 2MB.")
        
        return avatar


# =============================================================================
# FORMULARIOS DE GESTIÓN DE CONTRASEÑAS
# =============================================================================

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulario personalizado para cambio de contraseña con validaciones mejoradas
    """
    old_password = forms.CharField(
        label='Contraseña actual',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu contraseña actual',
            'autocomplete': 'current-password',
            'autofocus': True
        })
    )
    
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nueva contraseña',
            'autocomplete': 'new-password'
        }),
        help_text=(
            "Tu contraseña debe tener al menos 8 caracteres, "
            "incluir mayúsculas, minúsculas, números y caracteres especiales."
        )
    )
    
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu nueva contraseña',
            'autocomplete': 'new-password'
        })
    )
    
    def clean_new_password1(self):
        """Validaciones personalizadas para la nueva contraseña"""
        password = self.cleaned_data.get('new_password1')
        
        if password:
            # Validar con los validadores de Django
            validate_password(password, self.user)
            
            # Validaciones adicionales personalizadas
            if len(password) < 8:
                raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
            
            if not re.search(r'[A-Z]', password):
                raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")
            
            if not re.search(r'[a-z]', password):
                raise ValidationError("La contraseña debe contener al menos una letra minúscula.")
            
            if not re.search(r'\d', password):
                raise ValidationError("La contraseña debe contener al menos un número.")
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError("La contraseña debe contener al menos un carácter especial.")
            
            # Verificar que no sea muy similar a información personal
            user = self.user
            if user:
                user_info = [
                    user.first_name.lower() if user.first_name else '',
                    user.last_name.lower() if user.last_name else '',
                    user.email.split('@')[0].lower() if user.email else '',
                ]
                
                for info in user_info:
                    if info and len(info) > 3 and info in password.lower():
                        raise ValidationError(
                            "La contraseña no puede contener información personal como tu nombre o email."
                        )
        
        return password


class CustomPasswordResetForm(PasswordResetForm):
    """
    Formulario personalizado para solicitar reset de contraseña
    """
    email = forms.EmailField(
        label='Correo electrónico',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com',
            'autocomplete': 'email',
            'autofocus': True
        })
    )
    
    def clean_email(self):
        """Validar que el email existe en el sistema"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            
            # Verificar que el usuario existe y está activo
            if not User.objects.filter(email=email, is_active=True).exists():
                raise ValidationError(
                    "No existe una cuenta activa asociada a este correo electrónico."
                )
        
        return email
    
    def get_users(self, email):
        """Obtener usuarios activos con el email dado"""
        return User.objects.filter(
            email__iexact=email,
            is_active=True
        )


class CustomSetPasswordForm(SetPasswordForm):
    """
    Formulario personalizado para establecer nueva contraseña (reset)
    """
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nueva contraseña',
            'autocomplete': 'new-password',
            'autofocus': True
        }),
        help_text=(
            "Tu contraseña debe tener al menos 8 caracteres, "
            "incluir mayúsculas, minúsculas, números y caracteres especiales."
        )
    )
    
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu nueva contraseña',
            'autocomplete': 'new-password'
        })
    )
    
    def clean_new_password1(self):
        """Validaciones personalizadas para la nueva contraseña"""
        password = self.cleaned_data.get('new_password1')
        
        if password:
            # Validar con los validadores de Django
            validate_password(password, self.user)
            
            # Validaciones adicionales personalizadas (igual que en PasswordChangeForm)
            if len(password) < 8:
                raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
            
            if not re.search(r'[A-Z]', password):
                raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")
            
            if not re.search(r'[a-z]', password):
                raise ValidationError("La contraseña debe contener al menos una letra minúscula.")
            
            if not re.search(r'\d', password):
                raise ValidationError("La contraseña debe contener al menos un número.")
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError("La contraseña debe contener al menos un carácter especial.")
            
            # Verificar que no sea muy similar a información personal
            user = self.user
            if user:
                user_info = [
                    user.first_name.lower() if user.first_name else '',
                    user.last_name.lower() if user.last_name else '',
                    user.email.split('@')[0].lower() if user.email else '',
                ]
                
                for info in user_info:
                    if info and len(info) > 3 and info in password.lower():
                        raise ValidationError(
                            "La contraseña no puede contener información personal como tu nombre o email."
                        )
        
        return password


class PasswordStrengthForm(forms.Form):
    """
    Formulario para validar la fuerza de contraseñas en tiempo real
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password-strength-input'
        })
    )
    
    @staticmethod
    def calculate_password_strength(password):
        """
        Calcula la fuerza de una contraseña
        Retorna un diccionario con score (0-100) y criterios cumplidos
        """
        if not password:
            return {'score': 0, 'criteria': {}}
        
        score = 0
        criteria = {
            'length': len(password) >= 8,
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'numbers': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
            'no_common': not password.lower() in [
                'password', '123456', 'password123', 'admin', 'letmein'
            ]
        }
        
        # Calcular score basado en criterios
        if criteria['length']:
            score += 20
        if criteria['uppercase']:
            score += 15
        if criteria['lowercase']:
            score += 15
        if criteria['numbers']:
            score += 15
        if criteria['special']:
            score += 20
        if criteria['no_common']:
            score += 15
        
        # Bonus por longitud adicional
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Penalty por patrones comunes
        if re.search(r'(.)\1{2,}', password):  # Caracteres repetidos
            score -= 10
        if re.search(r'123|abc|qwe', password.lower()):  # Secuencias
            score -= 15
        
        score = max(0, min(100, score))  # Limitar entre 0-100
        
        return {
            'score': score,
            'criteria': criteria,
            'strength': 'Muy débil' if score < 25 else
                       'Débil' if score < 50 else
                       'Media' if score < 75 else
                       'Fuerte' if score < 90 else 'Muy fuerte'
        }


class TwoFactorSetupForm(forms.Form):
    """
    Formulario para configurar autenticación de dos factores
    """
    token = forms.CharField(
        label='Código de verificación',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'maxlength': '6',
            'minlength': '6',
            'pattern': '[0-9]{6}',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'style': 'font-size: 1.5rem; letter-spacing: 0.5rem;'
        })
    )
    
    def clean_token(self):
        token = self.cleaned_data.get('token')
        if token and not token.isdigit():
            raise ValidationError('El código debe contener solo números.')
        return token


class TwoFactorVerificationForm(forms.Form):
    """
    Formulario para verificar código 2FA durante login
    """
    token = forms.CharField(
        label='Código de autenticación',
        max_length=8,  # Permite tokens de backup más largos
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'style': 'font-size: 1.5rem; letter-spacing: 0.3rem;',
            'autofocus': True
        }),
        help_text='Ingresa el código de 6 dígitos de tu aplicación autenticadora o un código de backup.'
    )
    
    def clean_token(self):
        token = self.cleaned_data.get('token')
        if not token:
            raise ValidationError('Este campo es requerido.')
        
        # Permitir códigos de 6 dígitos (TOTP) o más largos (backup)
        if len(token) < 6:
            raise ValidationError('El código debe tener al menos 6 caracteres.')
        
        return token


class TwoFactorDisableForm(forms.Form):
    """
    Formulario para deshabilitar 2FA con confirmación
    """
    password = forms.CharField(
        label='Confirma tu contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu contraseña actual',
            'autocomplete': 'current-password'
        }),
        help_text='Por seguridad, confirma tu contraseña para deshabilitar 2FA.'
    )
    
    confirm = forms.BooleanField(
        label='Confirmo que quiero deshabilitar la autenticación de dos factores',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and not self.user.check_password(password):
            raise ValidationError('Contraseña incorrecta.')
        return password
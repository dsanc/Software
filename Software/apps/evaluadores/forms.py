"""
Formularios para gestión de evaluadores
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import Evaluador

User = get_user_model()


class EvaluadorForm(forms.ModelForm):
    """
    Formulario para crear/editar evaluadores
    """
    
    # Campo para buscar usuario por email
    email_evaluador = forms.EmailField(
        label='Email del Evaluador',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'evaluador@ejemplo.com',
            'autocomplete': 'email'
        }),
        help_text='Email del usuario evaluador (se creará si no existe)'
    )
    
    # Campo para contraseña del nuevo usuario
    password_evaluador = forms.CharField(
        label='Contraseña del Evaluador',
        required=False,  # Cambiado a False, se manejará en __init__
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña segura para el evaluador'
        }),
        help_text='Contraseña para el evaluador (mínimo 8 caracteres) - Solo necesaria al crear',
        min_length=8
    )
    
    # Selección múltiple de módulos
    modulos_permitidos = forms.MultipleChoiceField(
        label='Módulos Permitidos',
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text='Selecciona los módulos a los que tendrá acceso'
    )
    
    # Fecha de expiración
    fecha_expiracion = forms.DateTimeField(
        label='Fecha de Expiración',
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        help_text='Fecha hasta la cual el evaluador tendrá acceso (opcional)'
    )
    
    class Meta:
        model = Evaluador
        fields = [
            'nombres',
            'apellidos',
            'tipo_evaluador',
            'modulos_permitidos', 
            'permisos_crud',
            'max_evaluaciones_mes',
            'puede_crear_reportes',
            'puede_editar_evaluaciones',
            'acceso_completo_dashboard',
            'fecha_expiracion',
            'notas'
        ]
        
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres del evaluador'
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Apellidos del evaluador'
            }),
            'tipo_evaluador': forms.Select(attrs={
                'class': 'form-control'
            }),
            'max_evaluaciones_mes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1000'
            }),
            'puede_crear_reportes': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'puede_editar_evaluaciones': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'acceso_completo_dashboard': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales sobre este evaluador...'
            })
        }
        
        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'tipo_evaluador': 'Tipo de Evaluador',
            'max_evaluaciones_mes': 'Máximo Evaluaciones por Mes',
            'puede_crear_reportes': 'Puede Crear Reportes',
            'puede_editar_evaluaciones': 'Puede Editar Evaluaciones',
            'acceso_completo_dashboard': 'Acceso Completo al Dashboard',
            'notas': 'Notas'
        }
        
        help_texts = {
            'nombres': 'Nombres del evaluador',
            'apellidos': 'Apellidos del evaluador',
            'tipo_evaluador': 'Define el nivel de acceso del evaluador',
            'max_evaluaciones_mes': 'Número máximo de evaluaciones que puede realizar por mes',
            'puede_crear_reportes': 'Permitir generar reportes de evaluación',
            'puede_editar_evaluaciones': 'Permitir modificar evaluaciones existentes',
            'acceso_completo_dashboard': 'Acceso total al dashboard del usuario principal',
            'notas': 'Información adicional sobre este evaluador'
        }
    
    def __init__(self, *args, **kwargs):
        self.usuario_principal = kwargs.pop('usuario_principal', None)
        super().__init__(*args, **kwargs)
        
        # Configurar opciones de módulos basado en las suscripciones del usuario principal
        if self.usuario_principal:
            modulos_choices = self._get_modulos_disponibles()
            self.fields['modulos_permitidos'].choices = modulos_choices
            
            # Configurar el campo de permisos CRUD con los módulos disponibles
            if 'permisos_crud' in self.fields:
                from .widgets import PermisosCRUDField
                self.fields['permisos_crud'] = PermisosCRUDField(
                    modulos_choices=modulos_choices,
                    required=False,
                    help_text='Configura los permisos específicos que tendrá el evaluador en cada módulo'
                )
        
        # Si estamos editando, configurar campos apropiadamente
        if self.instance.pk:
            # Email no editable
            self.fields['email_evaluador'].initial = self.instance.usuario_evaluador.email
            self.fields['email_evaluador'].widget.attrs['readonly'] = True
            self.fields['email_evaluador'].help_text = 'No se puede cambiar el usuario evaluador'
            
            # Contraseña opcional para edición
            self.fields['password_evaluador'].required = False
            self.fields['password_evaluador'].help_text = 'Dejar vacío para mantener la contraseña actual. Completar para cambiarla.'
            self.fields['password_evaluador'].widget.attrs['placeholder'] = 'Nueva contraseña (opcional)'
        else:
            # Al crear, la contraseña es requerida
            self.fields['password_evaluador'].required = True
    
    def _get_modulos_disponibles(self):
        """Obtiene los módulos disponibles basado en las suscripciones del usuario principal"""
        if not self.usuario_principal:
            return []
        
        suscripciones = self.usuario_principal.subscriptions.filter(status='active')
        modulos = [(sub.plan.module.name, sub.plan.module.display_name) for sub in suscripciones]
        
        return list(set(modulos))  # Eliminar duplicados
    
    def clean_nombres(self):
        """Validar nombres"""
        nombres = self.cleaned_data.get('nombres', '').strip()
        
        if not nombres:
            raise ValidationError('Los nombres son requeridos')
        
        if len(nombres) < 2:
            raise ValidationError('Los nombres deben tener al menos 2 caracteres')
        
        return nombres
    
    def clean_apellidos(self):
        """Validar apellidos"""
        apellidos = self.cleaned_data.get('apellidos', '').strip()
        
        if not apellidos:
            raise ValidationError('Los apellidos son requeridos')
        
        if len(apellidos) < 2:
            raise ValidationError('Los apellidos deben tener al menos 2 caracteres')
        
        return apellidos

    def clean_password_evaluador(self):
        """Validar contraseña del evaluador"""
        password = self.cleaned_data.get('password_evaluador', '').strip()
        
        # Si es un nuevo evaluador, la contraseña es requerida
        if not self.instance.pk and not password:
            raise ValidationError('La contraseña es requerida para nuevos evaluadores')
        
        # Si se proporciona contraseña, validar su longitud
        if password and len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres')
        
        return password

    def clean_email_evaluador(self):
        """Validar email del evaluador"""
        email = self.cleaned_data.get('email_evaluador')
        
        if not email:
            raise ValidationError('El email es requerido')
        
        # No puede editar el email si estamos editando
        if self.instance.pk:
            return email
        
        # No puede ser evaluador de sí mismo
        if self.usuario_principal and email == self.usuario_principal.email:
            raise ValidationError('Un usuario no puede ser evaluador de sí mismo')
        
        # Si el usuario ya existe, verificar que no sea evaluador ya
        try:
            usuario_existente = User.objects.get(email=email)
            if self.usuario_principal and Evaluador.objects.filter(
                usuario_principal=self.usuario_principal,
                usuario_evaluador=usuario_existente
            ).exists():
                raise ValidationError('Este usuario ya es tu evaluador')
        except User.DoesNotExist:
            # Usuario no existe, está bien, lo crearemos
            pass
        
        return email
    
    def clean_fecha_expiracion(self):
        """Validar fecha de expiración"""
        fecha = self.cleaned_data.get('fecha_expiracion')
        
        if fecha and fecha <= timezone.now():
            raise ValidationError('La fecha de expiración debe ser futura')
        
        return fecha
    
    def save(self, commit=True):
        """Crear evaluador y usuario si es necesario"""
        evaluador = super().save(commit=False)
        
        if not evaluador.pk:  # Nuevo evaluador
            email = self.cleaned_data.get('email_evaluador')
            password = self.cleaned_data.get('password_evaluador')
            
            # Buscar o crear el usuario evaluador
            try:
                usuario_evaluador = User.objects.get(email=email)
                # Si el usuario ya existe, actualizar su contraseña
                if password:  # Solo si se proporcionó una nueva contraseña
                    usuario_evaluador.set_password(password)
                    usuario_evaluador.save()
            except User.DoesNotExist:
                # Crear nuevo usuario
                usuario_evaluador = User.objects.create_user(
                    email=email,
                    username=email,  # Usar email como username
                    first_name=evaluador.nombres,
                    last_name=evaluador.apellidos,
                    password=password
                )
            
            # Asignar el usuario al evaluador
            evaluador.usuario_principal = self.usuario_principal
            evaluador.usuario_evaluador = usuario_evaluador
            
            # Si no se especificaron nombres/apellidos, usar los del usuario
            if not evaluador.nombres or evaluador.nombres == 'Sin especificar':
                evaluador.nombres = usuario_evaluador.first_name or 'Sin especificar'
            
            if not evaluador.apellidos or evaluador.apellidos == 'Sin especificar':
                evaluador.apellidos = usuario_evaluador.last_name or 'Sin especificar'
            
            # Ejecutar validaciones del modelo
            evaluador.clean()
        else:
            # Evaluador existente - solo actualizar contraseña si se proporciona
            password = self.cleaned_data.get('password_evaluador')
            if password:
                evaluador.usuario_evaluador.set_password(password)
                evaluador.usuario_evaluador.save()
        
        if commit:
            evaluador.save()
            # Crear suscripciones heredadas después de guardar el evaluador
            suscripciones_creadas = evaluador.crear_suscripciones_heredadas()
            if suscripciones_creadas:
                print(f"✅ Creadas {len(suscripciones_creadas)} suscripciones heredadas para {evaluador.usuario_evaluador.email}")
        
        return evaluador


class BuscarEvaluadorForm(forms.Form):
    """
    Formulario para buscar evaluadores
    """
    
    ESTADOS_CHOICES = [('', 'Todos los estados')] + Evaluador.ESTADOS
    TIPOS_CHOICES = [('', 'Todos los tipos')] + Evaluador.TIPOS_EVALUADOR
    
    busqueda = forms.CharField(
        label='Buscar',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre, email o notas...'
        }),
        help_text='Buscar por nombre, email o notas'
    )
    
    estado = forms.ChoiceField(
        label='Estado',
        choices=ESTADOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    tipo_evaluador = forms.ChoiceField(
        label='Tipo',
        choices=TIPOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    modulo = forms.CharField(
        label='Módulo',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrar por módulo...'
        })
    )
    
    activos_solo = forms.BooleanField(
        label='Solo activos',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
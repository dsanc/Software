from django import forms
from django.forms.widgets import DateInput, Textarea, Select, TextInput, CheckboxInput
from .models import PerfilSeguridad


class DateInputWidget(DateInput):
    """Widget personalizado para campos de fecha que funciona correctamente en edición"""
    input_type = 'date'
    
    def format_value(self, value):
        """Asegurar que las fechas se formateen correctamente para input type=date"""
        if value is None:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return value


class PerfilForm(forms.ModelForm):
    """Formulario personalizado para crear/editar perfiles de seguridad"""
    
    class Meta:
        model = PerfilSeguridad
        fields = [
            'nombres', 'apellidos', 'tipo_documento', 'numero_documento', 
            'fecha_nacimiento', 'genero', 'telefono_principal', 'telefono_emergencia',
            'cargo_politico', 'partido_politico', 'nivel_exposicion',
            'departamento', 'municipio', 'direccion_residencia', 'direccion_trabajo',
            'tiene_esquema_seguridad', 'nivel_esquema_seguridad', 
            'amenazas_recibidas', 'fecha_ultima_amenaza',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono', 
            'contacto_emergencia_relacion', 'observaciones'
        ]
        
        # Configurar formatos de fecha para campos DateInput
        localized_fields = ('fecha_nacimiento', 'fecha_ultima_amenaza')
        
        widgets = {
            # Campos de texto
            'nombres': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese sus nombres',
                'required': True
            }),
            'apellidos': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese sus apellidos',
                'required': True
            }),
            'numero_documento': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12345678',
                'required': True
            }),
            'telefono_principal': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: +57 300 123 4567',
                'required': True
            }),
            'telefono_emergencia': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: +57 310 987 6543'
            }),
            'partido_politico': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Partido Liberal'
            }),
            'departamento': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Antioquia',
                'required': True
            }),
            'municipio': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Medellín',
                'required': True
            }),
            'nivel_esquema_seguridad': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Nivel 2 - Medio'
            }),
            'contacto_emergencia_nombre': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: María González',
                'required': True
            }),
            'contacto_emergencia_telefono': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: +57 320 456 7890',
                'required': True
            }),
            'contacto_emergencia_relacion': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Esposa, Hermano, Amigo',
                'required': True
            }),
            
            # Campos de selección
            'tipo_documento': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'genero': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'cargo_politico': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'nivel_exposicion': Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            
            # Campos de fecha
            'fecha_nacimiento': DateInputWidget(attrs={
                'class': 'form-control',
                'required': True
            }),
            'fecha_ultima_amenaza': DateInputWidget(attrs={
                'class': 'form-control'
            }),
            
            # Campos de área de texto
            'direccion_residencia': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ej: Calle 45 # 12-34, Barrio Centro',
                'required': True
            }),
            'direccion_trabajo': Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ej: Carrera 50 # 25-60, Edificio Administrativo'
            }),
            'observaciones': Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Información adicional relevante para la evaluación de seguridad...'
            }),
            
            # Campos de checkbox
            'tiene_esquema_seguridad': CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'amenazas_recibidas': CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'tipo_documento': 'Tipo de Documento',
            'numero_documento': 'Número de Documento',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'genero': 'Género',
            'telefono_principal': 'Teléfono Principal',
            'telefono_emergencia': 'Teléfono de Emergencia',
            'cargo_politico': 'Cargo Político',
            'partido_politico': 'Partido Político',
            'nivel_exposicion': 'Nivel de Exposición',
            'departamento': 'Departamento',
            'municipio': 'Municipio',
            'direccion_residencia': 'Dirección de Residencia',
            'direccion_trabajo': 'Dirección de Trabajo',
            'tiene_esquema_seguridad': '¿Tiene Esquema de Seguridad?',
            'nivel_esquema_seguridad': 'Nivel del Esquema de Seguridad',
            'amenazas_recibidas': '¿Ha Recibido Amenazas?',
            'fecha_ultima_amenaza': 'Fecha de Última Amenaza',
            'contacto_emergencia_nombre': 'Nombre del Contacto de Emergencia',
            'contacto_emergencia_telefono': 'Teléfono del Contacto de Emergencia',
            'contacto_emergencia_relacion': 'Relación con el Contacto',
            'observaciones': 'Observaciones Adicionales',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar clases CSS adicionales a todos los campos
        for field_name, field in self.fields.items():
            # Campos requeridos
            if field.required:
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' required-field'
                else:
                    field.widget.attrs['class'] = 'required-field'
            
            # Placeholders para campos de texto sin placeholder
            if isinstance(field.widget, TextInput) and 'placeholder' not in field.widget.attrs:
                field.widget.attrs['placeholder'] = f'Ingrese {field.label.lower()}'
                
    def clean_numero_documento(self):
        numero_documento = self.cleaned_data.get('numero_documento')
        if numero_documento:
            # Remover espacios y caracteres especiales
            numero_documento = ''.join(filter(str.isdigit, numero_documento))
            if len(numero_documento) < 6:
                raise forms.ValidationError('El número de documento debe tener al menos 6 dígitos.')
        return numero_documento
    
    def clean_telefono_principal(self):
        telefono = self.cleaned_data.get('telefono_principal')
        if telefono:
            # Validación básica de teléfono
            numeros = ''.join(filter(str.isdigit, telefono))
            if len(numeros) < 10:
                raise forms.ValidationError('El teléfono debe tener al menos 10 dígitos.')
        return telefono
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            from datetime import date
            today = date.today()
            edad = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            
            if fecha_nacimiento > today:
                raise forms.ValidationError('La fecha de nacimiento no puede ser en el futuro.')
            if edad < 18:
                raise forms.ValidationError('Debe ser mayor de edad (18 años).')
            if edad > 100:
                raise forms.ValidationError('Por favor verifique la fecha de nacimiento.')
                
        return fecha_nacimiento
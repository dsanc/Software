from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import (
    Conjunto, TipoConjunto, EvaluacionSeguridad, 
    RespuestaEvaluacion, PreguntaSeguridad, ArchivoEvaluacion
)


class ConjuntoModalForm(ModelForm):
    """
    Formulario simplificado para el modal de conjuntos
    """
    
    class Meta:
        model = Conjunto
        fields = [
            'nit', 'nombre', 'tipo_conjunto', 'direccion', 'ciudad', 
            'numero_unidades', 'numero_torres',
            'administrador_nombre', 'administrador_telefono', 'administrador_email',
            'tiene_piscina', 'tiene_gimnasio', 'tiene_salon_social',
            'tiene_juegos_infantiles', 'tiene_canchas_deportivas'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar clases CSS a campos booleanos del modal
        boolean_fields = [
            'tiene_piscina', 'tiene_gimnasio', 'tiene_salon_social',
            'tiene_juegos_infantiles', 'tiene_canchas_deportivas'
        ]
        
        for field in boolean_fields:
            if field in self.fields:
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})
        
        # Hacer algunos campos opcionales en la interfaz
        if 'administrador_nombre' in self.fields:
            self.fields['administrador_nombre'].required = False
        if 'administrador_telefono' in self.fields:
            self.fields['administrador_telefono'].required = False
        if 'administrador_email' in self.fields:
            self.fields['administrador_email'].required = False


class ConjuntoForm(ModelForm):
    """
    Formulario para crear/editar conjuntos residenciales
    """
    
    class Meta:
        model = Conjunto
        fields = [
            'nit', 'nombre', 'tipo_conjunto', 'direccion', 'ciudad', 'departamento',
            'numero_unidades', 'numero_torres', 'tiene_piscina', 'tiene_gimnasio', 
            'tiene_salon_social', 'tiene_juegos_infantiles', 'tiene_canchas_deportivas',
            'administrador_nombre', 'administrador_telefono', 'administrador_email'
        ]
        
        widgets = {
            'nit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el NIT del conjunto'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre del conjunto'
            }),
            'tipo_conjunto': forms.Select(attrs={
                'class': 'form-select'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa del conjunto'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad'
            }),
            'departamento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Departamento'
            }),
            'numero_unidades': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Número de unidades'
            }),
            'numero_torres': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Número de torres (0 si no aplica)'
            }),
            'administrador_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del administrador'
            }),
            'administrador_telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto'
            }),
            'administrador_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email de contacto'
            }),
            # Checkboxes con clases Bootstrap
            'tiene_piscina': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tiene_gimnasio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tiene_salon_social': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tiene_juegos_infantiles': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tiene_canchas_deportivas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar campos opcionales
        if 'administrador_nombre' in self.fields:
            self.fields['administrador_nombre'].required = False
        if 'administrador_telefono' in self.fields:
            self.fields['administrador_telefono'].required = False
        if 'administrador_email' in self.fields:
            self.fields['administrador_email'].required = False


class EvaluacionSeguridadForm(forms.ModelForm):
    """
    Formulario para crear evaluaciones de seguridad
    """
    
    class Meta:
        model = EvaluacionSeguridad
        fields = [
            'tipo_evaluacion',
            'fecha_evaluacion', 'observaciones'
        ]
        
        widgets = {
            'tipo_evaluacion': forms.Select(attrs={'class': 'form-select'}),
            'fecha_evaluacion': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observaciones generales sobre la evaluación'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['observaciones'].required = False


class RespuestaEvaluacionForm(forms.Form):
    """
    Formulario dinámico para responder evaluaciones
    """
    
    def __init__(self, preguntas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for pregunta in preguntas:
            field_name = f'pregunta_{pregunta.id}'
            
            if pregunta.tipo_respuesta == 'rating':
                self.fields[field_name] = forms.IntegerField(
                    label=pregunta.texto_pregunta,
                    min_value=1,
                    max_value=5,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control rating-input',
                        'data-pregunta-id': pregunta.id,
                        'placeholder': '1-5'
                    }),
                    required=pregunta.obligatoria,
                    help_text=pregunta.ayuda
                )
            
            elif pregunta.tipo_respuesta == 'booleana':
                self.fields[field_name] = forms.BooleanField(
                    label=pregunta.texto_pregunta,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'form-check-input',
                        'data-pregunta-id': pregunta.id
                    }),
                    required=False,  # BooleanField siempre es opcional en Django
                    help_text=pregunta.ayuda
                )
            
            elif pregunta.tipo_respuesta == 'multiple':
                if pregunta.opciones_json:
                    choices = [(opt, opt) for opt in pregunta.opciones_json]
                    self.fields[field_name] = forms.ChoiceField(
                        label=pregunta.texto_pregunta,
                        choices=choices,
                        widget=forms.Select(attrs={
                            'class': 'form-select',
                            'data-pregunta-id': pregunta.id
                        }),
                        required=pregunta.obligatoria,
                        help_text=pregunta.ayuda
                    )
            
            elif pregunta.tipo_respuesta == 'numerica':
                self.fields[field_name] = forms.DecimalField(
                    label=pregunta.texto_pregunta,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'step': '0.01',
                        'data-pregunta-id': pregunta.id
                    }),
                    required=pregunta.obligatoria,
                    help_text=pregunta.ayuda
                )


class FiltroConjuntosForm(forms.Form):
    """
    Formulario para filtrar conjuntos en la lista
    """
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, ciudad...'
        })
    )
    
    tipo_conjunto = forms.ModelChoiceField(
        queryset=TipoConjunto.objects.all(),
        required=False,
        empty_label='Todos los tipos',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    ciudad = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad'
        })
    )
    
    nivel_riesgo = forms.ChoiceField(
        choices=[
            ('', 'Todos los niveles'),
            ('sin_evaluar', 'Sin Evaluar'),
            ('muy_bajo', 'Muy Bajo'),
            ('bajo', 'Bajo'),
            ('medio', 'Medio'),
            ('alto', 'Alto'),
            ('critico', 'Crítico')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tiene_evaluaciones = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('si', 'Con evaluaciones'),
            ('no', 'Sin evaluaciones')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ReporteComparativoForm(forms.Form):
    """
    Formulario para generar reportes comparativos
    """
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Solo mostrar conjuntos del usuario
        self.fields['conjuntos'] = forms.ModelMultipleChoiceField(
            queryset=Conjunto.objects.filter(propietario=user, activo=True),
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            label='Conjuntos a comparar'
        )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Evaluaciones desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Evaluaciones hasta'
    )
    
    incluir_graficos = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Incluir gráficos en el reporte'
    )
    
    formato_reporte = forms.ChoiceField(
        choices=[
            ('html', 'Visualización HTML'),
            ('pdf', 'Documento PDF'),
            ('excel', 'Hoja de cálculo Excel')
        ],
        initial='html',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Formato del reporte'
    )


class ComentarioRiesgoForm(forms.Form):
    """
    Formulario para el comentario general de un riesgo específico
    """
    comentario_riesgo = forms.CharField(
        label='Comentario General del Riesgo',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Escriba aquí sus observaciones generales sobre este riesgo...',
        }),
        required=False,
        help_text='Comentario opcional sobre la evaluación de este riesgo en general'
    )


class ArchivoEvaluacionForm(forms.ModelForm):
    """
    Formulario para subir archivos adjuntos a evaluaciones
    """
    class Meta:
        model = ArchivoEvaluacion
        fields = ['archivo', 'tipo_archivo', 'descripcion']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['archivo'].widget.attrs.update({
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif'
        })
        
        self.fields['tipo_archivo'].widget.attrs.update({
            'class': 'form-select'
        })
        
        self.fields['descripcion'].widget.attrs.update({
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Descripción opcional del archivo...'
        })
        
        self.fields['descripcion'].required = False
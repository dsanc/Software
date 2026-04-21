"""
Formularios para el proceso de evaluación paso a paso
"""
from django import forms
from django.forms import formset_factory
from .models import (
    TipoRiesgo, EscenarioRiesgo, PreguntaEvaluacion, 
    CalificacionOpcion, EvaluacionRiesgo, RespuestaPregunta, ArchivoEvaluacion
)


class SeleccionRiesgosForm(forms.Form):
    """
    Paso 1: Selección de tipos de riesgos a evaluar
    """
    conjunto = forms.CharField(widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener todos los tipos de riesgos activos
        tipos_riesgos = TipoRiesgo.objects.filter(activo=True).order_by('orden')
        
        for tipo in tipos_riesgos:
            self.fields[f'riesgo_{tipo.id}'] = forms.BooleanField(
                label=tipo.nombre,
                required=False,
                initial=False,
                help_text=tipo.descripcion,
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-check-input risk-checkbox',
                    'data-riesgo-id': tipo.id
                })
            )
    
    def get_riesgos_seleccionados(self):
        """Retorna los IDs de los riesgos seleccionados"""
        riesgos_seleccionados = []
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('riesgo_') and value:
                riesgo_id = field_name.replace('riesgo_', '')
                riesgos_seleccionados.append(int(riesgo_id))
        return riesgos_seleccionados


class InformacionEvaluacionForm(forms.ModelForm):
    """
    Formulario para información básica de la evaluación
    """
    class Meta:
        model = EvaluacionRiesgo
        fields = [
            'tipo_evaluacion'
        ]
        widgets = {
            'tipo_evaluacion': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class RespuestaPreguntaForm(forms.Form):
    """
    Formulario para responder una pregunta específica
    """
    pregunta_id = forms.CharField(widget=forms.HiddenInput())
    calificacion = forms.ModelChoiceField(
        queryset=CalificacionOpcion.objects.filter(activa=True).order_by('orden'),
        empty_label="Seleccione una calificación",
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, pregunta, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pregunta = pregunta
        self.fields['pregunta_id'].initial = pregunta.id
        
        # Personalizar las opciones de calificación
        choices = []
        for opcion in self.fields['calificacion'].queryset:
            choices.append((opcion.id, opcion.nombre))
        
        self.fields['calificacion'].widget.choices = choices


class EvaluacionRiesgoFormSet(forms.BaseFormSet):
    """
    FormSet para manejar múltiples preguntas de un riesgo
    """
    def __init__(self, preguntas, *args, **kwargs):
        self.preguntas = preguntas
        super().__init__(*args, **kwargs)
    
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if index < len(self.preguntas):
            kwargs['pregunta'] = self.preguntas[index]
        return kwargs


class ObservacionesRecomendacionesForm(forms.ModelForm):
    """
    Paso 3: Observaciones y recomendaciones generales
    """
    class Meta:
        model = EvaluacionRiesgo
        fields = [
            'observaciones_generales', 
            'recomendaciones_generales', 
            'conclusiones',
            'metodologia_aplicada',
            'limitaciones_evaluacion',
            'proximas_acciones'
        ]
        widgets = {
            'observaciones_generales': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observaciones generales identificadas durante la evaluación...'
            }),
            'recomendaciones_generales': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Recomendaciones principales para mejorar la seguridad...'
            }),
            'conclusiones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Conclusiones principales de la evaluación...'
            }),
            'metodologia_aplicada': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Metodología y criterios aplicados en la evaluación...'
            }),
            'limitaciones_evaluacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Limitaciones encontradas durante la evaluación...'
            }),
            'proximas_acciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Próximas acciones sugeridas y cronograma...'
            })
        }


class ArchivoEvaluacionForm(forms.ModelForm):
    """
    Formulario para subir archivos adjuntos a la evaluación
    """
    class Meta:
        model = ArchivoEvaluacion
        fields = ['tipo_archivo', 'archivo', 'descripcion']
        widgets = {
            'tipo_archivo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'archivo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción del archivo adjunto...'
            })
        }
    
    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Validar tamaño (máximo 10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Validar tipo de archivo
            extensiones_permitidas = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
            ]
            extension = '.' + archivo.name.lower().split('.')[-1]
            if extension not in extensiones_permitidas:
                raise forms.ValidationError(
                    'Formato de archivo no permitido. '
                    'Formatos aceptados: PDF, DOC, DOCX, XLS, XLSX, JPG, JPEG, PNG, GIF'
                )
        
        return archivo


class ConfirmacionEvaluacionForm(forms.Form):
    """
    Paso 4: Confirmación y finalización de la evaluación
    """
    confirmar = forms.BooleanField(
        label="Confirmo que he revisado todos los datos y deseo finalizar la evaluación",
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    enviar_notificacion = forms.BooleanField(
        label="Enviar notificación por email al administrador del conjunto",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
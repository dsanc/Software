from django import forms
from django.core.exceptions import ValidationError
from .models import ArbolDecision, EvaluacionSeguridad, Pregunta, OpcionRespuesta


class IniciarEvaluacionForm(forms.Form):
    """Formulario para iniciar una nueva evaluación"""
    
    # Información del evaluador
    evaluador_organizacion = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de la organización'
        }),
        label="Organización"
    )
    
    # Árbol de decisión
    arbol = forms.ModelChoiceField(
        queryset=ArbolDecision.objects.filter(activo=True),
        empty_label="Seleccione un tipo de evaluación",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        label="Tipo de Evaluación",
        required=False  # Se seleccionará automáticamente el primero disponible
    )
    
    def clean_arbol(self):
        arbol = self.cleaned_data.get('arbol')
        if arbol and not arbol.preguntas.filter(es_pregunta_inicial=True).exists():
            raise ValidationError("El árbol seleccionado no tiene preguntas configuradas.")
        return arbol


class ResponderPreguntaForm(forms.Form):
    """Formulario dinámico para responder preguntas"""
    
    def __init__(self, pregunta, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pregunta = pregunta
        
        opciones = pregunta.opciones.all().order_by('orden')
        choices = [(opcion.id, f"{opcion.texto} (Peso: {opcion.valor_ponderado})") for opcion in opciones]
        
        self.fields['opcion'] = forms.ChoiceField(
            choices=choices,
            widget=forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            label=pregunta.texto,
            required=True
        )
    
    def clean_opcion(self):
        opcion_id = self.cleaned_data.get('opcion')
        try:
            opcion = OpcionRespuesta.objects.get(id=opcion_id, pregunta=self.pregunta)
            return opcion
        except OpcionRespuesta.DoesNotExist:
            raise ValidationError("Opción no válida para esta pregunta.")


class FiltroEvaluacionesForm(forms.Form):
    """Formulario para filtrar evaluaciones"""
    ESTADO_CHOICES = [('', 'Todos los estados')] + EvaluacionSeguridad.ESTADO_CHOICES
    NIVEL_CHOICES = [('', 'Todos los niveles')] + EvaluacionSeguridad.NIVEL_RIESGO_CHOICES
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    nivel_riesgo = forms.ChoiceField(
        choices=NIVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError("La fecha desde no puede ser posterior a la fecha hasta.")
        
        return cleaned_data


class CrearArbolForm(forms.ModelForm):
    """Formulario para crear/editar árboles de decisión"""
    
    class Meta:
        model = ArbolDecision
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class CrearPreguntaForm(forms.ModelForm):
    """Formulario para crear/editar preguntas"""
    
    class Meta:
        model = Pregunta
        fields = ['texto', 'orden', 'es_pregunta_inicial', 'pregunta_padre']
        widgets = {
            'texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'es_pregunta_inicial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pregunta_padre': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, arbol=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if arbol:
            self.fields['pregunta_padre'].queryset = arbol.preguntas.all()
        else:
            self.fields['pregunta_padre'].queryset = Pregunta.objects.none()


class CrearOpcionForm(forms.ModelForm):
    """Formulario para crear/editar opciones de respuesta"""
    
    class Meta:
        model = OpcionRespuesta
        fields = ['texto', 'valor_ponderado', 'orden', 'pregunta_siguiente', 'es_respuesta_final']
        widgets = {
            'texto': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_ponderado': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'pregunta_siguiente': forms.Select(attrs={'class': 'form-control'}),
            'es_respuesta_final': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, arbol=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if arbol:
            self.fields['pregunta_siguiente'].queryset = arbol.preguntas.all()
        else:
            self.fields['pregunta_siguiente'].queryset = Pregunta.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        es_respuesta_final = cleaned_data.get('es_respuesta_final')
        pregunta_siguiente = cleaned_data.get('pregunta_siguiente')
        
        if es_respuesta_final and pregunta_siguiente:
            raise ValidationError("Una respuesta final no puede tener una pregunta siguiente.")
        
        if not es_respuesta_final and not pregunta_siguiente:
            raise ValidationError("Debe especificar una pregunta siguiente o marcar como respuesta final.")
        
        return cleaned_data


class CrearEvaluacionForm(forms.ModelForm):
    """Formulario para crear una nueva evaluación de seguridad"""
    
    PRIORIDAD_CHOICES = [
        ('alta', 'Alta - Requiere atención inmediata'),
        ('media', 'Media - Evaluación de rutina'),
        ('baja', 'Baja - Evaluación preventiva'),
    ]
    
    prioridad = forms.ChoiceField(
        choices=PRIORIDAD_CHOICES,
        initial='media',
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text="Nivel de prioridad para esta evaluación"
    )
    
    # Campos adicionales para selección geográfica
    departamentos_seleccionados = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text='Departamentos seleccionados para la evaluación'
    )
    
    municipios_seleccionados = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text='Municipios seleccionados para la evaluación'
    )
    
    incluir_municipio_perfil = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        help_text='Incluir automáticamente el municipio del perfil en el análisis'
    )
    
    class Meta:
        model = EvaluacionSeguridad
        fields = [
            'arbol',
            'observaciones'
        ]
        
        widgets = {
            'arbol': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ingrese observaciones iniciales, contexto especial, o información relevante para esta evaluación...'
            }),
        }
        
        help_texts = {
            'arbol': 'Seleccione el tipo de evaluación que desea realizar',
            'observaciones': 'Información adicional o contexto especial para esta evaluación'
        }
    
    def __init__(self, *args, **kwargs):
        self.perfil = kwargs.pop('perfil', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar solo árboles activos
        self.fields['arbol'].queryset = ArbolDecision.objects.filter(activo=True)
        
        # Personalizar el queryset y labels del árbol
        if self.fields['arbol'].queryset.exists():
            choices = [('', 'Seleccione un tipo de evaluación...')]
            for arbol in self.fields['arbol'].queryset:
                # Agregar información adicional en la descripción
                descripcion = f"{arbol.nombre}"
                if arbol.descripcion:
                    descripcion += f" - {arbol.descripcion[:50]}..."
                choices.append((arbol.pk, descripcion))
            
            self.fields['arbol'].choices = choices
        
        # Si no hay árboles disponibles
        if not self.fields['arbol'].queryset.exists():
            self.fields['arbol'].widget.attrs['disabled'] = True
            self.fields['arbol'].help_text = "No hay tipos de evaluación disponibles actualmente."
    
    def clean_arbol(self):
        arbol = self.cleaned_data.get('arbol')
        if not arbol:
            raise ValidationError("Debe seleccionar un tipo de evaluación.")
        
        if not arbol.activo:
            raise ValidationError("El tipo de evaluación seleccionado no está disponible.")
        
        return arbol
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar que el perfil esté activo
        if self.perfil and self.perfil.estado_perfil != 'activo':
            raise ValidationError("No se pueden crear evaluaciones para perfiles inactivos.")
        
        # Verificar si ya existe una evaluación en progreso
        if self.perfil:
            evaluacion_en_progreso = EvaluacionSeguridad.objects.filter(
                perfil=self.perfil,
                estado__in=['iniciada', 'en_progreso']
            ).exists()
            
            if evaluacion_en_progreso:
                raise ValidationError(
                    "Ya existe una evaluación en progreso para este perfil. "
                    "Complete o cancele la evaluación actual antes de crear una nueva."
                )
        
        return cleaned_data
    
    def save(self, commit=True, user=None):
        evaluacion = super().save(commit=False)
        
        if self.perfil:
            evaluacion.perfil = self.perfil
        
        # Asignar automáticamente el nombre del evaluador del usuario autenticado
        if user and user.is_authenticated:
            evaluacion.evaluador_nombre = user.get_full_name() or user.username
        
        # Establecer el estado inicial
        evaluacion.estado = 'iniciada'
        
        # Procesar datos geográficos si están presentes
        departamentos = self.cleaned_data.get('departamentos_seleccionados', '')
        municipios = self.cleaned_data.get('municipios_seleccionados', '')
        incluir_municipio_perfil = self.cleaned_data.get('incluir_municipio_perfil', True)
        
        # Agregar información geográfica a las observaciones si se proporcionó
        observaciones_adicionales = []
        
        if departamentos:
            observaciones_adicionales.append(f"Departamentos incluidos: {departamentos}")
        
        if municipios:
            observaciones_adicionales.append(f"Municipios incluidos: {municipios}")
        
        if incluir_municipio_perfil and self.perfil and hasattr(self.perfil, 'municipio'):
            observaciones_adicionales.append(f"Incluye municipio del perfil: {self.perfil.municipio}")
        
        if observaciones_adicionales:
            if evaluacion.observaciones:
                evaluacion.observaciones += "\n\n"
            else:
                evaluacion.observaciones = ""
            evaluacion.observaciones += "\n".join(observaciones_adicionales)
        
        if commit:
            evaluacion.save()
        
        return evaluacion
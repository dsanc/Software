# Formulario específico para el modal de conjuntos
from django import forms
from django.forms import ModelForm
from .models import Conjunto


class ConjuntoModalForm(ModelForm):
    """
    Formulario simplificado para el modal de conjuntos
    """
    
    class Meta:
        model = Conjunto
        fields = [
            'nit', 'nombre', 'tipo_conjunto', 'direccion', 'ciudad', 
            'departamento', 'numero_unidades', 'numero_torres',
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
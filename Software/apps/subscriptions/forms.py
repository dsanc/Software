"""
Formularios para el sistema de suscripciones y carrito de compras
"""
from django import forms
from django.core.validators import RegexValidator
from .models import Plan


class BillingForm(forms.Form):
    """Formulario para información de facturación"""
    
    name = forms.CharField(
        label='Nombre completo',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre completo',
            'required': True
        })
    )
    
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com',
            'required': True
        })
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Formato: +573001234567 o 3001234567"
    )
    
    phone = forms.CharField(
        label='Teléfono',
        validators=[phone_regex],
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+573001234567'
        })
    )
    
    address = forms.CharField(
        label='Dirección',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Calle 123 #45-67'
        })
    )
    
    city = forms.CharField(
        label='Ciudad',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bogotá'
        })
    )
    
    COUNTRY_CHOICES = [
        ('Colombia', 'Colombia'),
        ('México', 'México'),
        ('Perú', 'Perú'),
        ('Chile', 'Chile'),
        ('Argentina', 'Argentina'),
    ]
    
    country = forms.ChoiceField(
        label='País',
        choices=COUNTRY_CHOICES,
        initial='Colombia',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    accept_terms = forms.BooleanField(
        label='Acepto los términos y condiciones',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name.split()) < 2:
            raise forms.ValidationError('Por favor ingresa tu nombre completo (nombre y apellido)')
        return name


class CheckoutForm(forms.Form):
    """Formulario para el proceso de checkout"""
    
    BILLING_CYCLE_CHOICES = [
        ('yearly', 'Anual'),
    ]
    
    billing_cycle = forms.ChoiceField(
        label='Ciclo de facturación',
        choices=BILLING_CYCLE_CHOICES,
        initial='yearly',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    coupon_code = forms.CharField(
        label='Código de cupón',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código promocional (opcional)'
        })
    )


class PlanSelectionForm(forms.Form):
    """Formulario para selección de plan"""
    
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        label='Plan',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    billing_cycle = forms.ChoiceField(
        label='Período de facturación',
        choices=[('yearly', 'Anual')],
        initial='yearly',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, module=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if module:
            self.fields['plan'].queryset = Plan.objects.filter(
                module=module,
                is_active=True
            ).select_related('plan_type').order_by('order', 'monthly_price')


class CancelSubscriptionForm(forms.Form):
    """Formulario para cancelar suscripción"""
    
    CANCELLATION_REASONS = [
        ('too_expensive', 'Muy costoso'),
        ('not_using', 'No lo estoy usando'),
        ('found_alternative', 'Encontré una alternativa'),
        ('technical_issues', 'Problemas técnicos'),
        ('missing_features', 'Faltan características'),
        ('other', 'Otro'),
    ]
    
    reason = forms.ChoiceField(
        label='Razón de cancelación',
        choices=CANCELLATION_REASONS,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    feedback = forms.CharField(
        label='Comentarios adicionales (opcional)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Cuéntanos cómo podemos mejorar...'
        })
    )
    
    confirm_cancellation = forms.BooleanField(
        label='Confirmo que deseo cancelar mi suscripción',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class UpgradeForm(forms.Form):
    """Formulario para actualizar plan"""
    
    new_plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        label='Nuevo plan',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    billing_cycle = forms.ChoiceField(
        label='Período de facturación',
        choices=[('yearly', 'Anual')],
        initial='yearly',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, current_subscription=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if current_subscription:
            # Filtrar planes del mismo módulo que sean superiores al actual
            module = current_subscription.plan.module
            current_price = current_subscription.plan.monthly_price
            
            self.fields['new_plan'].queryset = Plan.objects.filter(
                module=module,
                is_active=True,
                monthly_price__gt=current_price
            ).select_related('plan_type').order_by('order', 'monthly_price')
            
            # Establecer valor inicial del ciclo de facturación
            self.fields['billing_cycle'].initial = current_subscription.billing_cycle
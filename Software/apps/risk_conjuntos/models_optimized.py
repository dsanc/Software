"""
Modelos refactorizados para optimizar la complejidad del sistema
Separación de responsabilidades para mejorar mantenimiento
"""
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class AnalisisRiesgo(models.Model):
    """
    Modelo específico para análisis de riesgo de una respuesta
    Extrae la lógica de análisis del modelo ResultadoPregunta
    """
    NIVEL_RIESGO_CHOICES = [
        ('muy_bajo', 'Muy Bajo'),
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('muy_alto', 'Muy Alto'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Valores básicos de riesgo
    valor_riesgo = models.DecimalField(
        max_digits=7, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text='Valor de riesgo calculado (0-1)'
    )
    
    porcentaje_riesgo = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Porcentaje de riesgo (0-100%)'
    )
    
    nivel_riesgo = models.CharField(
        max_length=20, 
        choices=NIVEL_RIESGO_CHOICES,
        help_text='Clasificación del nivel de riesgo'
    )
    
    # Timestamps
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Análisis de Riesgo'
        verbose_name_plural = 'Análisis de Riesgos'
        ordering = ['-fecha_calculo']
    
    def __str__(self):
        return f'Análisis: {self.nivel_riesgo} ({self.porcentaje_riesgo}%)'
    
    def save(self, *args, **kwargs):
        # Auto-calcular porcentaje de riesgo con Decimal para consistencia
        self.porcentaje_riesgo = (self.valor_riesgo * Decimal('100')).quantize(Decimal('0.01'))

        # Auto-determinar nivel de riesgo
        if self.valor_riesgo <= Decimal('0.2'):
            self.nivel_riesgo = 'muy_bajo'
        elif self.valor_riesgo <= Decimal('0.4'):
            self.nivel_riesgo = 'bajo'
        elif self.valor_riesgo <= Decimal('0.6'):
            self.nivel_riesgo = 'medio'
        elif self.valor_riesgo <= Decimal('0.8'):
            self.nivel_riesgo = 'alto'
        else:
            self.nivel_riesgo = 'muy_alto'

        super().save(*args, **kwargs)
    
    @property
    def color_nivel(self):
        """Retorna color hexadecimal según el nivel de riesgo"""
        colores = {
            'muy_bajo': '#2ecc71',   # Verde
            'bajo': '#f1c40f',       # Amarillo
            'medio': '#e67e22',      # Naranja
            'alto': '#e74c3c',       # Rojo
            'muy_alto': '#8e44ad'    # Púrpura
        }
        return colores.get(self.nivel_riesgo, '#95a5a6')
    
    @property
    def icono_nivel(self):
        """Retorna icono FontAwesome según el nivel de riesgo"""
        iconos = {
            'muy_bajo': 'fas fa-shield-alt',
            'bajo': 'fas fa-exclamation-triangle',
            'medio': 'fas fa-exclamation-circle',
            'alto': 'fas fa-fire',
            'muy_alto': 'fas fa-skull-crossbones'
        }
        return iconos.get(self.nivel_riesgo, 'fas fa-question-circle')


class PonderacionRiesgo(models.Model):
    """
    Modelo para manejar la ponderación específica de riesgos
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    peso_pregunta = models.DecimalField(
        max_digits=5, decimal_places=3,
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(5.0)],
        help_text='Peso específico de la pregunta en la evaluación'
    )
    
    valor_ponderado = models.DecimalField(
        max_digits=7, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Valor final ponderado'
    )
    
    # Metadata del cálculo
    version_algoritmo = models.CharField(
        max_length=10,
        default='1.0',
        help_text='Versión del algoritmo de cálculo utilizado'
    )
    
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ponderación de Riesgo'
        verbose_name_plural = 'Ponderaciones de Riesgo'
        ordering = ['-fecha_calculo']
    
    def __str__(self):
        return f'Ponderación: {self.peso_pregunta} → {self.valor_ponderado}'


class MetricaCalidad(models.Model):
    """
    Modelo para métricas de calidad y confiabilidad
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    confiabilidad = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=100.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Porcentaje de confiabilidad del resultado'
    )
    
    requiere_atencion = models.BooleanField(
        default=False,
        help_text='Indica si el resultado requiere atención especial'
    )
    
    # Tiempos de procesamiento
    tiempo_procesamiento_ms = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Tiempo de procesamiento en milisegundos'
    )
    
    # Metadata
    ip_procesamiento = models.GenericIPAddressField(null=True, blank=True)
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Métrica de Calidad'
        verbose_name_plural = 'Métricas de Calidad'
        ordering = ['-fecha_calculo']
    
    def __str__(self):
        return f'Calidad: {self.confiabilidad}% - {"⚠️" if self.requiere_atencion else "✅"}'


class RecomendacionSistema(models.Model):
    """
    Modelo para recomendaciones automáticas del sistema
    """
    TIPO_RECOMENDACION_CHOICES = [
        ('accion_inmediata', 'Acción Inmediata'),
        ('prioridad_alta', 'Prioridad Alta'),
        ('monitoreo', 'Monitoreo'),
        ('mantenimiento', 'Mantenimiento'),
        ('optimo', 'Óptimo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    tipo_recomendacion = models.CharField(
        max_length=20,
        choices=TIPO_RECOMENDACION_CHOICES,
        help_text='Tipo de recomendación basada en el nivel de riesgo'
    )
    
    recomendacion_automatica = models.TextField(
        help_text='Recomendación generada automáticamente por el sistema'
    )
    
    es_critica = models.BooleanField(
        default=False,
        help_text='Indica si la recomendación es crítica'
    )
    
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Recomendación del Sistema'
        verbose_name_plural = 'Recomendaciones del Sistema'
        ordering = ['-es_critica', '-fecha_generacion']
    
    def __str__(self):
        return f'{self.get_tipo_recomendacion_display()}: {self.recomendacion_automatica[:50]}...'
    
    @classmethod
    def generar_recomendacion(cls, nivel_riesgo):
        """Genera recomendación automática basada en el nivel de riesgo"""
        recomendaciones = {
            'muy_alto': {
                'tipo': 'accion_inmediata',
                'texto': 'ACCIÓN INMEDIATA REQUERIDA: Implementar medidas de seguridad urgentes.',
                'critica': True
            },
            'alto': {
                'tipo': 'prioridad_alta',
                'texto': 'PRIORIDAD ALTA: Revisar y reforzar medidas de seguridad existentes.',
                'critica': True
            },
            'medio': {
                'tipo': 'monitoreo',
                'texto': 'MONITOREO: Evaluar opciones de mejora en medidas de seguridad.',
                'critica': False
            },
            'bajo': {
                'tipo': 'mantenimiento',
                'texto': 'MANTENIMIENTO: Continuar con medidas actuales y monitoreo regular.',
                'critica': False
            },
            'muy_bajo': {
                'tipo': 'optimo',
                'texto': 'ÓPTIMO: Mantener las medidas actuales de seguridad.',
                'critica': False
            }
        }
        
        config = recomendaciones.get(nivel_riesgo, recomendaciones['medio'])
        
        return cls.objects.create(
            tipo_recomendacion=config['tipo'],
            recomendacion_automatica=config['texto'],
            es_critica=config['critica']
        )
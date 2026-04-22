from decimal import Decimal

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
import logging
import uuid

logger = logging.getLogger(__name__)

# Importar modelos base del core
from core.models import SoftDeleteModel, TimeStampedModel

User = get_user_model()

# Importar modelos optimizados
from .models_optimized import AnalisisRiesgo, PonderacionRiesgo, MetricaCalidad, RecomendacionSistema


class TipoConjunto(models.Model):
    """
    Tipos de conjuntos residenciales
    """
    TIPO_CHOICES = [
        ('conjunto_cerrado', 'Conjunto Cerrado'),
        ('urbanizacion', 'Urbanización'),
        ('condominio', 'Condominio'),
        ('cluster', 'Cluster'),
        ('edificio', 'Edificio Residencial'),
        ('torres', 'Torres Residenciales'),
    ]
    
    nombre = models.CharField(max_length=100, choices=TIPO_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=50, default='fas fa-building')
    color = models.CharField(max_length=7, default='#3498db')
    
    class Meta:
        verbose_name = 'Tipo de Conjunto'
        verbose_name_plural = 'Tipos de Conjuntos'
    
    def __str__(self):
        return self.get_nombre_display()


class Conjunto(models.Model):
    """
    Modelo principal para conjuntos residenciales
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conjuntos')
    
    # Información básica
    nit = models.CharField(
        max_length=15, 
        unique=True,
        help_text='NIT del conjunto (Ej: 800123456-7)',
        verbose_name='NIT'
    )
    nombre = models.CharField(max_length=200)
    tipo_conjunto = models.ForeignKey(TipoConjunto, on_delete=models.PROTECT)
    
    # Ubicación
    direccion = models.TextField()
    ciudad = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    
    # Características
    numero_unidades = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Número total de unidades residenciales'
    )
    numero_torres = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Número de torres o bloques'
    )
    
    # Amenidades
    tiene_piscina = models.BooleanField(default=False)
    tiene_gimnasio = models.BooleanField(default=False)
    tiene_salon_social = models.BooleanField(default=False)
    tiene_juegos_infantiles = models.BooleanField(default=False)
    tiene_canchas_deportivas = models.BooleanField(default=False)
    
    # Administración
    administrador_nombre = models.CharField(max_length=200, blank=True)
    administrador_telefono = models.CharField(
        max_length=20, blank=True,
        validators=[RegexValidator(
            regex=r'^\+?[\d\s\-\(\)]{9,20}$',
            message="Número de teléfono debe contener entre 9 y 20 caracteres (números, espacios, guiones, paréntesis permitidos)."
        )]
    )
    administrador_email = models.EmailField(blank=True)
    
    # Metadata (mantener para funcionalidad básica)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Conjunto Residencial'
        verbose_name_plural = 'Conjuntos Residenciales'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['propietario', 'activo']),
            models.Index(fields=['ciudad']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        return f'{self.nombre} ({self.ciudad})'


class CategoriaSeguridad(models.Model):
    """
    Categorías de seguridad específicas para conjuntos residenciales
    """
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, default='fas fa-shield-alt')
    orden = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)
    
    # Ponderación para el cálculo de score
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(5.0)]
    )
    
    class Meta:
        verbose_name = 'Categoría de Seguridad'
        verbose_name_plural = 'Categorías de Seguridad'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class PreguntaSeguridad(models.Model):
    """
    Preguntas específicas para evaluación de seguridad en conjuntos
    """
    categoria = models.ForeignKey(CategoriaSeguridad, on_delete=models.CASCADE, related_name='preguntas')
    texto_pregunta = models.TextField()
    ayuda = models.TextField(blank=True, help_text='Texto de ayuda para la pregunta')
    
    # Tipo de respuesta
    TIPO_RESPUESTA_CHOICES = [
        ('rating', 'Calificación (1-5)'),
        ('booleana', 'Sí/No'),
        ('multiple', 'Opción Múltiple'),
        ('numerica', 'Numérica'),
    ]
    tipo_respuesta = models.CharField(max_length=20, choices=TIPO_RESPUESTA_CHOICES, default='rating')
    
    # Para preguntas de opción múltiple
    opciones_json = models.JSONField(blank=True, null=True)
    
    # Configuración
    obligatoria = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)
    
    # Ponderación
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)]
    )
    
    class Meta:
        verbose_name = 'Pregunta de Seguridad'
        verbose_name_plural = 'Preguntas de Seguridad'
        ordering = ['categoria', 'orden', 'texto_pregunta']
    
    def __str__(self):
        return f'{self.categoria.nombre}: {self.texto_pregunta[:50]}...'


class EvaluacionSeguridad(models.Model):
    """
    Evaluación de seguridad para un conjunto residencial
    """
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('revisada', 'Revisada'),
    ]
    
    TIPO_EVALUACION_CHOICES = [
        ('inicial', 'Evaluación Inicial'),
        ('periodica', 'Evaluación Periódica'),
        ('especial', 'Evaluación Especial'),
        ('auditoria', 'Auditoría'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conjunto = models.ForeignKey(Conjunto, on_delete=models.CASCADE, related_name='evaluaciones_seguridad')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='evaluaciones_risk_conjuntos_creadas',
                                  verbose_name='Creado por')
    
    # Información de la evaluación
    tipo_evaluacion = models.CharField(max_length=20, choices=TIPO_EVALUACION_CHOICES, default='periodica')
    fecha_evaluacion = models.DateTimeField(default=timezone.now)
    
    # Control de estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    # Resultados
    score_total = models.DecimalField(
        max_digits=5, decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Observaciones generales
    observaciones = models.TextField(blank=True)
    recomendaciones = models.TextField(blank=True)
    
    # Metadata
    ip_evaluacion = models.GenericIPAddressField(null=True, blank=True)
    tiempo_evaluacion_minutos = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Evaluación de Seguridad'
        verbose_name_plural = 'Evaluaciones de Seguridad'
        ordering = ['-fecha_evaluacion']
    
    def __str__(self):
        return f'Evaluación {self.conjunto.nombre} - {self.fecha_evaluacion.strftime("%d/%m/%Y")}'
    
    def save(self, *args, **kwargs):
        if self.estado == 'completada' and not self.fecha_completado:
            self.fecha_completado = timezone.now()
            
        super().save(*args, **kwargs)
        
        # Actualizar el score del conjunto
        if self.estado == 'completada' and self.score_total:
            self.conjunto.ultimo_score_seguridad = self.score_total
            self.conjunto.fecha_ultimo_assessment = self.fecha_evaluacion
            self.conjunto.save(update_fields=['ultimo_score_seguridad', 'fecha_ultimo_assessment'])
    
    def calcular_score_total(self):
        """Calcula el score total basado en las respuestas"""
        respuestas = self.respuestas.select_related('pregunta', 'pregunta__categoria')
        
        if not respuestas.exists():
            return 0
        
        score_total = 0
        peso_total = 0
        
        for respuesta in respuestas:
            if respuesta.rating is not None:
                peso_pregunta = float(respuesta.pregunta.peso)
                peso_categoria = float(respuesta.pregunta.categoria.peso)
                
                # Score de 1-5 convertido a 0-100
                score_pregunta = ((respuesta.rating - 1) / 4) * 100
                peso_final = peso_pregunta * peso_categoria
                
                score_total += score_pregunta * peso_final
                peso_total += peso_final
        
        if peso_total > 0:
            return round(score_total / peso_total, 2)
        return 0
    
    def get_nivel_riesgo(self):
        """Determina el nivel de riesgo basado en el score total"""
        if self.score_total is None:
            return 'sin_evaluar'
        
        score = float(self.score_total)
        if score >= 90:
            return 'muy_bajo'
        elif score >= 80:
            return 'bajo'
        elif score >= 70:
            return 'medio'
        elif score >= 60:
            return 'alto'
        else:
            return 'critico'


class RespuestaEvaluacion(models.Model):
    """
    Respuestas individuales a las preguntas de evaluación
    """
    evaluacion = models.ForeignKey(EvaluacionSeguridad, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(PreguntaSeguridad, on_delete=models.CASCADE)
    
    # Respuesta (el tipo depende de la pregunta)
    rating = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    respuesta_booleana = models.BooleanField(null=True, blank=True)
    respuesta_multiple = models.CharField(max_length=200, blank=True)
    respuesta_numerica = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Comentarios adicionales
    comentarios = models.TextField(blank=True)
    
    # Metadata
    fecha_respuesta = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Respuesta de Evaluación'
        verbose_name_plural = 'Respuestas de Evaluación'
        unique_together = ['evaluacion', 'pregunta']
    
    def __str__(self):
        return f'{self.evaluacion} - {self.pregunta.texto_pregunta[:30]}...'
    
    def get_valor_respuesta(self):
        """Obtiene el valor de la respuesta según su tipo"""
        if self.rating is not None:
            return self.rating
        elif self.respuesta_booleana is not None:
            return 5 if self.respuesta_booleana else 1
        elif self.respuesta_multiple:
            return self.respuesta_multiple
        elif self.respuesta_numerica is not None:
            return self.respuesta_numerica
        return None


class ScoreCategoria(models.Model):
    """
    Score calculado por categoría para cada evaluación
    """
    evaluacion = models.ForeignKey(EvaluacionSeguridad, on_delete=models.CASCADE, related_name='scores_categoria')
    categoria = models.ForeignKey(CategoriaSeguridad, on_delete=models.CASCADE)
    
    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    numero_preguntas = models.PositiveIntegerField(default=0)
    suma_puntuaciones = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Score por Categoría'
        verbose_name_plural = 'Scores por Categoría'
        unique_together = ['evaluacion', 'categoria']
    
    def __str__(self):
        return f'{self.evaluacion} - {self.categoria.nombre}: {self.porcentaje}%'


# ============================================================================
# NUEVOS MODELOS PARA EVALUACIÓN DE RIESGOS
# ============================================================================

class TipoRiesgo(models.Model):
    """
    Tipos de riesgos de seguridad para conjuntos residenciales
    """
    RIESGOS_CHOICES = [
        ('intrusion_general', 'Intrusión General'),
        ('conspiracion_intrusion', 'Conspiración Para Intrusión'),
        ('intrusion_unidad', 'Intrusión Unidad Residencial'),
        ('robo_vehiculos', 'Robo De Vehículos'),
        ('robo_bicicletas', 'Robo De Bicicletas'),
        ('dano_areas_comunes', 'Daño En Áreas Comunes'),
        ('conflictos_parqueos', 'Conflictos Por Mal Uso De Parqueos'),
        ('sustraccion_bienes', 'Sustracción De Bienes De Apartamentos'),
        ('secuestro', 'Secuestro'),
    ]
    
    codigo = models.CharField(max_length=50, choices=RIESGOS_CHOICES, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Tipo de Riesgo'
        verbose_name_plural = 'Tipos de Riesgos'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class EscenarioRiesgo(models.Model):
    """
    Escenarios específicos relacionados con cada tipo de riesgo
    """
    ESCENARIOS_CHOICES = [
        ('traspasando_cerramiento', 'Traspasando El Cerramiento Perimetral'),
        ('debilidad_procedimiento', 'Por Debilidad Del Procedimiento De Ingreso'),
        ('distraccion_vigilante', 'Distracción Al Vigilante'),
        ('simultaneamente_autorizada', 'Pasando Simultáneamente Con Una Persona Autorizada'),
        ('autorizacion_irresponsable', 'Autorización Irresponsable'),
        ('neutralizando_seguridad', 'Neutralizando Al Personal De Seguridad'),
        ('coaccionando_residente', 'Coaccionando A Residente O Persona Autorizada'),
        ('ingenieria_social', 'Por Ingeniería Social'),
        ('sobrepasando_controles', 'Sobrepasando Los Controles De Acceso'),
        ('suplantacion', 'Suplantación'),
        ('residente', 'Residente'),
        ('empleado_interno', 'Empleado Interno O Prestador De Servicios'),
        ('violando_puerta_principal', 'Violando La Seguridad De La Puerta Principal'),
        ('acceso_ventanas_balcones', 'Por Acceso Por Ventanas O Balcones'),
        ('ventosa_ruptura_paredes', 'Por ventosa o ruptura de paredes'),
        ('acceso_violento_persona', 'Por Acceso Violento A Persona Que Abre La Puerta'),
        ('suplantacion_residente', 'Por Suplantación Del Residente'),
        ('sometimiento_residente', 'Por Sometimiento Del Residente'),
        ('salida_violenta', 'Por Salida Violenta'),
        ('autorizacion_forzada', 'Por Autorización Forzada'),
        ('acceso_simplificado', 'Acceso Simplificado A Las Mismas'),
        ('salida_normal', 'Por Salida Normal'),
        ('autorizacion_suplantada', 'Por Autorización Suplantada'),
        ('accion_interna', 'Por Acción Interna'),
        ('permisividad_parqueos_asignados', 'Permisividad En El Uso De Parqueos Asignados'),
        ('permisividad_administracion_parqueaderos', 'Permisividad En La Administración De Pos Parqueaderos De Parte De Seguridad'),
        ('retiro_porterias', 'Retiro Por Porterías'),
        ('retiro_area_perimetral', 'Retiro Por El Área Perimetral'),
        ('salida_forzada_escoltas', 'Salida Forzada Suplantando A Escoltas'),
        ('salida_forzada_familiaridad', 'Salida Forzada Sometido Por Una Persona Que Le Obliga A Comportarse Con Familiaridad'),
        ('suplantando_servicios_medicos', 'Suplantando Servicios Médicos'),
    ]
    
    tipo_riesgo = models.ForeignKey(TipoRiesgo, on_delete=models.CASCADE, related_name='escenarios')
    codigo = models.CharField(max_length=50, choices=ESCENARIOS_CHOICES)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Escenario de Riesgo'
        verbose_name_plural = 'Escenarios de Riesgo'
        ordering = ['tipo_riesgo', 'orden', 'nombre']
        unique_together = ['tipo_riesgo', 'codigo']
    
    def __str__(self):
        return f'{self.tipo_riesgo.nombre}: {self.nombre}'


class PreguntaEvaluacion(models.Model):
    """
    Preguntas específicas para cada escenario de riesgo
    """
    escenario = models.ForeignKey(EscenarioRiesgo, on_delete=models.CASCADE, related_name='preguntas')
    texto_pregunta = models.TextField()
    ayuda = models.TextField(blank=True, help_text='Texto de ayuda para la pregunta')
    orden = models.PositiveIntegerField(default=0)
    obligatoria = models.BooleanField(default=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Pregunta de Evaluación'
        verbose_name_plural = 'Preguntas de Evaluación'
        ordering = ['escenario', 'orden', 'texto_pregunta']
    
    def __str__(self):
        return f'{self.escenario.nombre}: {self.texto_pregunta[:50]}...'


class CalificacionOpcion(models.Model):
    """
    Opciones de calificación para las preguntas
    """
    OPCIONES_CHOICES = [
        ('ausente', 'Ausente'),
        ('deficiente', 'Deficiente'),
        ('vulnerable', 'Vulnerable'),
        ('adecuado', 'Adecuado'),
        ('eficaz', 'Eficaz'),
    ]
    
    codigo = models.CharField(max_length=20, choices=OPCIONES_CHOICES, unique=True)
    nombre = models.CharField(max_length=50)
    valor = models.DecimalField(max_digits=5, decimal_places=3)
    orden = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Calificación Opción'
        verbose_name_plural = 'Calificaciones Opciones'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return f'{self.nombre} ({self.valor})'


class EvaluacionRiesgo(SoftDeleteModel):
    """
    Evaluación de riesgos para un conjunto residencial
    Con soft delete habilitado para mantener historial
    """
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('revisada', 'Revisada'),
    ]
    
    TIPO_EVALUACION_CHOICES = [
        ('inicial', 'Evaluación Inicial'),
        ('periodica', 'Evaluación Periódica'),
        ('especial', 'Evaluación Especial'),
        ('auditoria', 'Auditoría'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conjunto = models.ForeignKey(Conjunto, on_delete=models.CASCADE, related_name='evaluaciones_riesgo')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='evaluaciones_riesgo_creadas',
                                  verbose_name='Creado por')
    
    # Información de la evaluación
    tipo_evaluacion = models.CharField(max_length=20, choices=TIPO_EVALUACION_CHOICES, default='periodica')
    fecha_evaluacion = models.DateTimeField(default=timezone.now)
    
    # Control de estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    # Resultados calculados
    promedio_general = models.DecimalField(
        max_digits=7, decimal_places=4, 
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    # Observaciones generales
    observaciones_generales = models.TextField(blank=True, verbose_name='Observaciones Generales')
    recomendaciones_generales = models.TextField(blank=True, verbose_name='Recomendaciones Generales')
    conclusiones = models.TextField(blank=True, verbose_name='Conclusiones')
    
    # Campos adicionales para el paso 3
    metodologia_aplicada = models.TextField(blank=True, verbose_name='Metodología Aplicada')
    limitaciones_evaluacion = models.TextField(blank=True, verbose_name='Limitaciones de la Evaluación')
    proximas_acciones = models.TextField(blank=True, verbose_name='Próximas Acciones Sugeridas')
    
    # Metadata
    ip_evaluacion = models.GenericIPAddressField(null=True, blank=True)
    tiempo_evaluacion_minutos = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Evaluación de Riesgo'
        verbose_name_plural = 'Evaluaciones de Riesgo'
        ordering = ['-fecha_evaluacion']
        indexes = [
            models.Index(fields=['conjunto', 'estado']),
            models.Index(fields=['estado', 'fecha_evaluacion']),
            models.Index(fields=['creado_por']),
            models.Index(fields=['deleted_at']),  # Índice para soft delete
        ]
    
    def __str__(self):
        return f'Evaluación Riesgo {self.conjunto.nombre} - {self.fecha_evaluacion.strftime("%d/%m/%Y")}'
    
    def save(self, *args, **kwargs):
        if self.estado == 'completada' and not self.fecha_completado:
            self.fecha_completado = timezone.now()

        super().save(*args, **kwargs)

    def calcular_promedio_general(self):
        """Calcula el promedio general de la evaluación"""
        promedios_riesgos = self.resultados_riesgo.values_list('promedio_riesgo', flat=True)
        
        if promedios_riesgos:
            promedio = sum(promedios_riesgos) / len(promedios_riesgos)
            self.promedio_general = round(Decimal(str(promedio)), 4)
            return self.promedio_general
        return Decimal('0')

    def get_nivel_riesgo(self):
        """
        Retorna el nivel de riesgo basado en el promedio general.
        Usa la misma lógica que el sistema ponderado para consistencia.
        """
        if not self.promedio_general:
            return 'sin_evaluar'
            
        # Usar el método get_promedio_porcentaje() para consistencia
        porcentaje = self.get_promedio_porcentaje()
        
        # Rangos alineados con el sistema ponderado
        if porcentaje <= 30:
            return 'bajo'
        elif porcentaje <= 60:
            return 'medio'
        else:
            return 'alto'
    
    def get_color_semaforo(self):
        """Retorna el color del semáforo según el nivel de riesgo"""
        nivel = self.get_nivel_riesgo()
        colores = {
            'bajo': '#28a745',     # Verde
            'medio': '#ffc107',    # Amarillo
            'alto': '#dc3545',     # Rojo
            'sin_evaluar': '#6c757d'  # Gris
        }
        return colores.get(nivel, '#6c757d')
    
    def get_texto_nivel_riesgo(self):
        """Retorna el texto descriptivo del nivel de riesgo (simplificado)"""
        nivel = self.get_nivel_riesgo()
        textos = {
            'bajo': 'Bajo',
            'medio': 'Moderado', 
            'alto': 'Alto',
            'sin_evaluar': 'Sin Evaluar'
        }
        return textos.get(nivel, 'Sin Evaluar')
    
    def get_descripcion_riesgo(self):
        """Retorna una descripción detallada del nivel de riesgo"""
        nivel = self.get_nivel_riesgo()
        if not self.promedio_general:
            return 'Evaluación no completada'
            
        porcentaje = float(self.promedio_general * 100)
        
        descripciones = {
            'bajo': f'Probabilidad de materialización baja ({porcentaje:.1f}%). Las medidas de seguridad son efectivas.',
            'medio': f'Probabilidad de materialización moderada ({porcentaje:.1f}%). Se requieren mejoras en seguridad.',
            'alto': f'Probabilidad de materialización alta ({porcentaje:.1f}%). Requiere atención inmediata.'
        }
        return descripciones.get(nivel, f'Nivel de riesgo: {porcentaje:.1f}%')
    
    def get_promedio_porcentaje(self):
        """Retorna el promedio general como porcentaje"""
        if not self.promedio_general:
            return 0
        return float(self.promedio_general * 100)


class ComentarioRiesgo(models.Model):
    """
    Comentarios generales por tipo de riesgo en una evaluación
    """
    evaluacion = models.ForeignKey(EvaluacionRiesgo, on_delete=models.CASCADE, related_name='comentarios_riesgo')
    tipo_riesgo = models.ForeignKey(TipoRiesgo, on_delete=models.CASCADE)
    
    # Comentario general para este riesgo
    comentario = models.TextField(
        blank=True,
        verbose_name='Comentario General del Riesgo',
        help_text='Comentario general sobre la evaluación de este tipo de riesgo'
    )
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Comentario de Riesgo'
        verbose_name_plural = 'Comentarios de Riesgos'
        unique_together = ['evaluacion', 'tipo_riesgo']
        ordering = ['tipo_riesgo__orden', 'tipo_riesgo__nombre']
    
    def __str__(self):
        return f'{self.evaluacion} - {self.tipo_riesgo.nombre}'


class ArchivoEvaluacion(models.Model):
    """
    Archivos adjuntos a una evaluación de riesgo
    """
    TIPO_ARCHIVO_CHOICES = [
        ('evidencia', 'Evidencia Fotográfica'),
        ('documento', 'Documento de Soporte'),
        ('plano', 'Plano o Esquema'),
        ('informe', 'Informe Técnico'),
        ('certificado', 'Certificado'),
        ('acta', 'Acta de Reunión'),
        ('otro', 'Otro'),
    ]
    
    evaluacion = models.ForeignKey(EvaluacionRiesgo, on_delete=models.CASCADE, related_name='archivos_adjuntos')
    tipo_archivo = models.CharField(max_length=20, choices=TIPO_ARCHIVO_CHOICES, default='evidencia')
    nombre_archivo = models.CharField(max_length=255)
    archivo = models.FileField(
        upload_to='evaluaciones/archivos/%Y/%m/%d/',
        help_text='Formatos permitidos: PDF, DOC, DOCX, XLS, XLSX, JPG, JPEG, PNG, GIF (Máx. 10MB)'
    )
    descripcion = models.TextField(blank=True, help_text='Descripción del archivo adjunto')
    
    # Metadata
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tamaño_archivo = models.PositiveIntegerField(null=True, blank=True, help_text='Tamaño en bytes')
    
    class Meta:
        verbose_name = 'Archivo de Evaluación'
        verbose_name_plural = 'Archivos de Evaluación'
        ordering = ['-fecha_subida']
    
    def __str__(self):
        return f'{self.nombre_archivo} ({self.get_tipo_archivo_display()})'
    
    def save(self, *args, **kwargs):
        if self.archivo:
            self.tamaño_archivo = self.archivo.size
            if not self.nombre_archivo:
                self.nombre_archivo = self.archivo.name
        super().save(*args, **kwargs)
    
    @property
    def es_imagen(self):
        """Determina si el archivo es una imagen"""
        extensiones_imagen = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        if self.archivo:
            extension = self.archivo.name.lower().split('.')[-1]
            return f'.{extension}' in extensiones_imagen
        return False
    
    @property
    def tamaño_legible(self):
        """Devuelve el tamaño del archivo en formato legible"""
        if not self.tamaño_archivo:
            return 'Desconocido'
        
        if self.tamaño_archivo < 1024:
            return f'{self.tamaño_archivo} B'
        elif self.tamaño_archivo < 1024 * 1024:
            return f'{self.tamaño_archivo / 1024:.1f} KB'
        elif self.tamaño_archivo < 1024 * 1024 * 1024:
            return f'{self.tamaño_archivo / (1024 * 1024):.1f} MB'
        else:
            return f'{self.tamaño_archivo / (1024 * 1024 * 1024):.1f} GB'


class ResultadoRiesgo(models.Model):
    """
    Resultado calculado para cada tipo de riesgo en una evaluación
    """
    evaluacion = models.ForeignKey(EvaluacionRiesgo, on_delete=models.CASCADE, related_name='resultados_riesgo')
    tipo_riesgo = models.ForeignKey(TipoRiesgo, on_delete=models.CASCADE)
    promedio_riesgo = models.DecimalField(
        max_digits=7, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    class Meta:
        verbose_name = 'Resultado por Riesgo'
        verbose_name_plural = 'Resultados por Riesgo'
        unique_together = ['evaluacion', 'tipo_riesgo']
    
    def __str__(self):
        return f'{self.evaluacion} - {self.tipo_riesgo.nombre}: {self.promedio_riesgo}'
    
    def get_nivel_riesgo(self):
        """Retorna el nivel de riesgo basado en el promedio del riesgo"""
        if not self.promedio_riesgo:
            return 'sin_evaluar'
            
        porcentaje = float(self.promedio_riesgo * 100)
        
        if porcentaje <= 30:
            return 'bajo'
        elif porcentaje <= 60:
            return 'medio'
        else:
            return 'alto'
    
    def get_color_semaforo(self):
        """Retorna el color del semáforo según el nivel de riesgo"""
        nivel = self.get_nivel_riesgo()
        colores = {
            'bajo': '#28a745',     # Verde
            'medio': '#ffc107',    # Amarillo
            'alto': '#dc3545',     # Rojo
            'sin_evaluar': '#6c757d'  # Gris
        }
        return colores.get(nivel, '#6c757d')
    
    def get_texto_nivel_riesgo(self):
        """Retorna el texto descriptivo del nivel de riesgo (simplificado)"""
        nivel = self.get_nivel_riesgo()
        textos = {
            'bajo': 'Bajo',
            'medio': 'Moderado', 
            'alto': 'Alto',
            'sin_evaluar': 'Sin Evaluar'
        }
        return textos.get(nivel, 'Sin Evaluar')


class ResultadoEscenario(models.Model):
    """
    Resultado calculado para cada escenario en una evaluación
    """
    evaluacion = models.ForeignKey(EvaluacionRiesgo, on_delete=models.CASCADE, related_name='resultados_escenario')
    escenario = models.ForeignKey(EscenarioRiesgo, on_delete=models.CASCADE)
    promedio_escenario = models.DecimalField(
        max_digits=7, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    class Meta:
        verbose_name = 'Resultado por Escenario'
        verbose_name_plural = 'Resultados por Escenario'
        unique_together = ['evaluacion', 'escenario']
    
    def __str__(self):
        return f'{self.evaluacion} - {self.escenario.nombre}: {self.promedio_escenario}'


class RespuestaPregunta(models.Model):
    """
    Respuesta a una pregunta específica de evaluación
    """
    evaluacion = models.ForeignKey(EvaluacionRiesgo, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(PreguntaEvaluacion, on_delete=models.CASCADE)
    calificacion = models.ForeignKey(CalificacionOpcion, on_delete=models.CASCADE)
    
    # Resultado calculado (1 - valor)
    resultado_calculado = models.DecimalField(
        max_digits=7, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    # Campo removido: comentarios - Migrado a ComentarioRiesgo
    # Los comentarios ahora se manejan a nivel de riesgo en lugar de pregunta individual
    
    # Metadata
    fecha_respuesta = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Respuesta de Pregunta'
        verbose_name_plural = 'Respuestas de Preguntas'
        unique_together = ['evaluacion', 'pregunta']
    
    def __str__(self):
        return f'{self.evaluacion} - {self.pregunta.texto_pregunta[:30]}...'
    
    def save(self, *args, **kwargs):
        # Calcular resultado: 1 - valor de calificación (usando Decimal para consistencia)
        self.resultado_calculado = Decimal('1') - self.calificacion.valor
        super().save(*args, **kwargs)


class ResultadoPregunta(models.Model):
    """
    Tabla específica para almacenar los resultados procesados de cada pregunta
    REFACTORIZADO: Usa modelos especializados para diferentes aspectos
    """
    ESTADO_RESULTADO_CHOICES = [
        ('calculado', 'Calculado'),
        ('validado', 'Validado'),
        ('revisado', 'Revisado'),
        ('aprobado', 'Aprobado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    respuesta = models.OneToOneField(
        RespuestaPregunta, 
        on_delete=models.CASCADE, 
        related_name='resultado_procesado'
    )
    
    # Relaciones con modelos especializados
    analisis_riesgo = models.OneToOneField(
        'AnalisisRiesgo',
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text='Análisis de riesgo asociado'
    )
    
    ponderacion = models.OneToOneField(
        'PonderacionRiesgo',
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text='Ponderación asociada'
    )
    
    metrica_calidad = models.OneToOneField(
        'MetricaCalidad',
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text='Métricas de calidad asociadas'
    )
    
    recomendacion = models.OneToOneField(
        'RecomendacionSistema',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text='Recomendación del sistema'
    )
    
    # Estado y validación simplificados
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_RESULTADO_CHOICES,
        default='calculado'
    )
    
    # Notas del evaluador
    notas_evaluador = models.TextField(
        blank=True,
        help_text='Notas adicionales del evaluador'
    )
    
    # Metadata básica
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Resultado de Pregunta'
        verbose_name_plural = 'Resultados de Preguntas'
        ordering = ['-fecha_calculo']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_calculo']),
        ]
    
    def __str__(self):
        return f'Resultado: {self.respuesta.pregunta.texto_pregunta[:30]}...'
    
    def crear_analisis_completo(self, valor_riesgo, peso_pregunta=1.0):
        """
        Método simplificado para crear análisis completo
        Reemplaza la lógica compleja del save() anterior
        """
        from decimal import Decimal
        from .models_optimized import AnalisisRiesgo, PonderacionRiesgo, MetricaCalidad, RecomendacionSistema
        
        # Convertir a Decimal para evitar errores de tipo
        valor_riesgo_decimal = Decimal(str(valor_riesgo))
        peso_pregunta_decimal = Decimal(str(peso_pregunta))
        
        # Crear análisis de riesgo
        if not self.analisis_riesgo:
            self.analisis_riesgo = AnalisisRiesgo.objects.create(
                valor_riesgo=valor_riesgo_decimal
            )
        
        # Crear ponderación
        if not self.ponderacion:
            self.ponderacion = PonderacionRiesgo.objects.create(
                peso_pregunta=peso_pregunta_decimal,
                valor_ponderado=valor_riesgo_decimal * peso_pregunta_decimal
            )
        
        # Crear métricas de calidad
        if not self.metrica_calidad:
            self.metrica_calidad = MetricaCalidad.objects.create(
                requiere_atencion=float(valor_riesgo_decimal) >= 0.7
            )
        
        # Crear recomendación
        if not self.recomendacion:
            self.recomendacion = RecomendacionSistema.generar_recomendacion(
                self.analisis_riesgo.nivel_riesgo
            )
        
        self.save()
    
    # Propiedades delegadas para compatibilidad
    @property
    def valor_riesgo(self):
        return self.analisis_riesgo.valor_riesgo if self.analisis_riesgo else 0
    
    @property
    def porcentaje_riesgo(self):
        return self.analisis_riesgo.porcentaje_riesgo if self.analisis_riesgo else 0
    
    @property
    def nivel_riesgo(self):
        return self.analisis_riesgo.nivel_riesgo if self.analisis_riesgo else 'sin_evaluar'
    
    @property
    def requiere_atencion(self):
        return self.metrica_calidad.requiere_atencion if self.metrica_calidad else False
    
    @property
    def color_nivel(self):
        return self.analisis_riesgo.color_nivel if self.analisis_riesgo else '#95a5a6'
    
    @property
    def icono_nivel(self):
        return self.analisis_riesgo.icono_nivel if self.analisis_riesgo else 'fas fa-question-circle'

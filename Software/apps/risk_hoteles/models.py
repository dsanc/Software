from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()

# Importar modelos de analytics
from .models_analytics import (
    AnalyticsEvent, UserSession, PageView, ClickEvent,
    ConversionGoal, Conversion, AnalyticsReport
)


class Hotel(models.Model):
    """
    Modelo para representar un hotel en el sistema de análisis de riesgo
    """
    CATEGORY_CHOICES = [
        ('1_star', '1 Estrella'),
        ('2_star', '2 Estrellas'), 
        ('3_star', '3 Estrellas'),
        ('4_star', '4 Estrellas'),
        ('5_star', '5 Estrellas'),
        ('luxury', 'Lujo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nombre del Hotel")
    address = models.TextField(verbose_name="Dirección")
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    country = models.CharField(max_length=100, verbose_name="País")
    
    # Información básica del hotel
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Categoría"
    )
    
    total_rooms = models.PositiveIntegerField(verbose_name="Total de Habitaciones")
    
    # Información de contacto
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Sitio Web")
    
    # Información del registro
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_hotels',
        verbose_name="Propietario"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_hotels',
        verbose_name="Creado por"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    def get_average_assessment_score(self):
        """
        Calcula el promedio de todas las evaluaciones completadas del hotel
        Retorna un valor entre 0 y 5, o None si no hay evaluaciones
        """
        from django.db.models import Avg
        
        completed_assessments = self.security_assessments.filter(
            status='completed',
            overall_score__isnull=False
        )
        
        if completed_assessments.exists():
            avg_score = completed_assessments.aggregate(
                avg=Avg('overall_score')
            )['avg']
            return round(avg_score, 2) if avg_score is not None else None
        
        return None
    
    def get_average_assessment_percentage(self):
        """
        Retorna el promedio de evaluaciones como porcentaje (0-100%)
        """
        avg_score = self.get_average_assessment_score()
        if avg_score is not None:
            return round((avg_score / 5.0) * 100, 1)
        return None
    
    def get_assessment_count(self):
        """
        Retorna el número total de evaluaciones completadas
        """
        return self.security_assessments.filter(
            status='completed',
            overall_score__isnull=False
        ).count()
    
    class Meta:
        verbose_name = "Hotel"
        verbose_name_plural = "Hoteles"
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} - {self.city}, {self.country}"


class RiskCategory(models.Model):
    """
    Categorías de riesgo para hoteles (incendio, robo, desastres naturales, etc.)
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        verbose_name="Peso/Importancia"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Categoría de Riesgo"
        verbose_name_plural = "Categorías de Riesgo"
        ordering = ['name']
        
    def __str__(self):
        return self.name


class SecurityCategory(models.Model):
    """
    Categorías específicas de seguridad hotelera para análisis detallado
    """
    CATEGORY_CHOICES = [
        ('gestion_organizacion', 'Gestión y Organización de la Seguridad'),
        ('seguridad_externa', 'Seguridad Externa'),
        ('seguridad_perimetral', 'Seguridad Perimetral'),
        ('seguridad_internas', 'Seguridad en Áreas Internas'),
        ('controles_accesos', 'Controles de Accesos al Hotel'),
        ('seguridad_habitaciones', 'Seguridad en Habitaciones'),
        ('seguridad_activos', 'Seguridad de Activos Críticos del Hotel'),
        ('seguridad_parqueo', 'Seguridad en Áreas de Parqueo'),
        ('gestion_humana', 'Seguridad en el Proceso de Gestión Humana'),
        ('seguridad_eventos', 'Seguridad en Eventos'),
        ('seguridad_ayb', 'Seguridad en A&B'),
        ('seguridad_reservas', 'Seguridad en Reservas'),
        ('seguridad_compras', 'Seguridad en el Proceso de Compras'),
        ('gestion_emergencias', 'Seguridad y Gestión de Emergencias'),
    ]
    
    code = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        unique=True,
        verbose_name="Código de Categoría"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    icon = models.CharField(max_length=50, default='fas fa-shield-alt', verbose_name="Ícono")
    weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(5.0)],
        verbose_name="Peso en el Análisis"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    
    class Meta:
        verbose_name = "Categoría de Seguridad"
        verbose_name_plural = "Categorías de Seguridad"
        ordering = ['order', 'name']
        
    def __str__(self):
        return self.name


class SecurityQuestion(models.Model):
    """
    Preguntas específicas para cada categoría de seguridad
    """
    category = models.ForeignKey(
        SecurityCategory,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Categoría"
    )
    
    question_text = models.TextField(verbose_name="Texto de la Pregunta")
    help_text = models.TextField(blank=True, verbose_name="Texto de Ayuda")
    
    # Configuración de la pregunta
    is_required = models.BooleanField(default=True, verbose_name="Obligatoria")
    weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)],
        verbose_name="Peso de la Pregunta"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    
    # Metadatos
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        verbose_name = "Pregunta de Seguridad"
        verbose_name_plural = "Preguntas de Seguridad"
        ordering = ['category', 'order']
        
    def __str__(self):
        return f"{self.category.name}: {self.question_text[:50]}..."


class SecurityAssessment(models.Model):
    """
    Evaluación de seguridad completa para un hotel
    """
    ASSESSMENT_TYPE_CHOICES = [
        ('inicial', 'Análisis Inicial'),
        ('periodico', 'Análisis Periódico'),
        ('especial', 'Análisis Especial'),
        ('auditoria', 'Auditoría de Riesgo'),
    ]
    
    STATUS_CHOICES = [
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('reviewed', 'Revisado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name='security_assessments',
        verbose_name="Hotel"
    )
    
    # Información básica de la evaluación
    assessment_type = models.CharField(
        max_length=20,
        choices=ASSESSMENT_TYPE_CHOICES,
        verbose_name="Tipo de Evaluación"
    )
    assessment_date = models.DateTimeField(verbose_name="Fecha de Evaluación")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Categorías incluidas en esta evaluación
    selected_categories = models.ManyToManyField(
        SecurityCategory,
        verbose_name="Categorías Seleccionadas"
    )
    
    # Estado y resultado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name="Estado"
    )
    
    overall_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name="Puntuación General"
    )
    
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('muy_bajo', 'Muy Bajo'),
            ('bajo', 'Bajo'),
            ('medio', 'Medio'),
            ('alto', 'Alto'),
            ('muy_alto', 'Muy Alto'),
        ],
        null=True,
        blank=True,
        verbose_name="Nivel de Riesgo General"
    )
    
    # Observaciones y recomendaciones
    observations = models.TextField(blank=True, verbose_name="Observaciones Generales")
    recommendations = models.TextField(blank=True, verbose_name="Recomendaciones")
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_assessments',
        verbose_name="Creado por"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Finalización")
    
    class Meta:
        verbose_name = "Evaluación de Seguridad"
        verbose_name_plural = "Evaluaciones de Seguridad"
        ordering = ['-assessment_date']
        
    def __str__(self):
        return f"Evaluación {self.hotel.name} - {self.assessment_date.strftime('%Y-%m-%d')}"
    
    def can_start_assessment(self):
        """Verifica si la evaluación puede iniciarse (desde in_progress)"""
        return self.status == 'in_progress'
    
    def can_complete_assessment(self):
        """Verifica si la evaluación puede completarse (desde in_progress)"""
        return self.status == 'in_progress'
    
    def can_review_assessment(self):
        """Verifica si la evaluación puede revisarse (desde completed)"""
        return self.status == 'completed'
    
    def start_assessment(self):
        """Inicia la evaluación (ya en in_progress por defecto)"""
        if self.can_start_assessment():
            # Ya está en progress, solo guardamos el timestamp si es necesario
            self.save(update_fields=['updated_at'])
            return True
        return False
    
    def complete_assessment(self):
        """Completa la evaluación (in_progress -> completed)"""
        if not self.can_complete_assessment():
            return False
            
        try:
            from django.utils import timezone
            import logging
            
            logger = logging.getLogger(__name__)
            
            # Calcular y guardar puntuaciones (actualiza overall_score y risk_level)
            self.save_calculated_scores()
            logger.info(f"Scores calculated for assessment {self.id}")
            
            # Actualizar estado y fecha de finalización
            self.status = 'completed'
            self.completed_at = timezone.now()
            
            # Guardar todos los cambios de una vez
            self.save()
            
            logger.info(f"Assessment {self.id} completed successfully")
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error completing assessment {self.id}: {str(e)}")
            return False
    
    def review_assessment(self):
        """Marca la evaluación como revisada (completed -> reviewed)"""
        if self.can_review_assessment():
            self.status = 'reviewed'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
    
    def get_status_display_color(self):
        """Retorna el color Bootstrap para el estado actual"""
        status_colors = {
            'in_progress': 'warning',
            'completed': 'success',
            'reviewed': 'info'
        }
        return status_colors.get(self.status, 'warning')
    
    def calculate_category_score(self, category):
        """
        Calcula el promedio de una categoría según la metodología especificada:
        1. Suma las calificaciones de todas las preguntas (excluyendo 'No Aplica')
        2. Cuenta las preguntas válidas (excluyendo 'No Aplica') 
        3. Divide suma/cantidad y luego entre 5 para obtener porcentaje
        """
        # Obtener respuestas de la categoría que NO sean 'No Aplica' y que tengan rating
        valid_responses = self.responses.filter(
            question__category=category,
            not_applicable=False,
            rating__isnull=False
        )
        
        if not valid_responses.exists():
            return {
                'score_sum': 0,
                'question_count': 0,
                'average': 0.0,
                'percentage': 0.0
            }
        
        # Paso 1: Sumar todas las calificaciones
        score_sum = sum(response.rating for response in valid_responses)
        
        # Paso 2: Contar preguntas válidas (sin 'No Aplica')
        question_count = valid_responses.count()
        
        # Paso 3: Calcular promedio y porcentaje
        average = score_sum / question_count if question_count > 0 else 0.0
        percentage = (average / 5) * 100 if average > 0 else 0.0
        
        return {
            'score_sum': score_sum,
            'question_count': question_count,
            'average': round(average, 2),
            'percentage': round(percentage, 2)
        }
    
    def get_all_category_scores(self):
        """
        Calcula los puntajes de todas las categorías de la evaluación
        """
        category_scores = {}
        
        for category in self.selected_categories.all():
            category_scores[category.code] = {
                'category_name': category.name,
                'category': category,
                **self.calculate_category_score(category)
            }
        
        return category_scores
    
    def calculate_overall_score(self):
        """
        Calcula el promedio general de todas las categorías
        Promedio de los porcentajes de categorías que tienen datos válidos
        """
        category_scores = self.get_all_category_scores()
        
        if not category_scores:
            return 0.0
        
        # Filtrar solo categorías que tienen preguntas respondidas
        valid_categories = [
            score_data for score_data in category_scores.values() 
            if score_data['question_count'] > 0
        ]
        
        if not valid_categories:
            return 0.0
        
        # Sumar todos los porcentajes de las categorías válidas
        total_percentage = sum(
            score_data['percentage'] 
            for score_data in valid_categories
        )
        
        # Calcular promedio general
        category_count = len(valid_categories)
        overall_percentage = total_percentage / category_count if category_count > 0 else 0.0
        
        return round(overall_percentage, 2)
    
    def get_category_trends(self, months_back=6, include_test_data=False):
        """
        Calcula las tendencias históricas por categoría para los últimos X meses
        """
        from datetime import datetime, timedelta
        from django.db.models import Q
        import random
        
        # Fecha límite para el análisis
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)
        
        # Obtener todas las evaluaciones del hotel en el período
        historical_assessments = SecurityAssessment.objects.filter(
            hotel=self.hotel,
            assessment_date__gte=cutoff_date
        ).order_by('assessment_date')
        
        trends = {}
        
        for category in self.selected_categories.all():
            category_history = []
            
            # Obtener datos reales
            for assessment in historical_assessments:
                category_score = assessment.calculate_category_score(category)
                if category_score['question_count'] > 0:  # Solo incluir si hay datos
                    category_history.append({
                        'date': assessment.assessment_date,
                        'score': category_score['average'],
                        'percentage': category_score['percentage']
                    })
            
            # Si hay pocos datos y se solicita, agregar datos de prueba para demostración
            if len(category_history) < 3 and include_test_data:
                base_score = category_history[0]['score'] if category_history else 2.5
                current_date = datetime.now()
                
                # Generar 4 puntos de datos históricos simulados con tendencia
                for i in range(4):
                    days_ago = (i + 1) * 30  # Una evaluación cada mes
                    trend_factor = 0.1 * i  # Tendencia gradual de mejora
                    score_variation = random.uniform(-0.2, 0.3)  # Variación natural
                    
                    simulated_score = min(5.0, max(0.0, base_score - trend_factor + score_variation))
                    simulated_date = current_date - timedelta(days=days_ago)
                    
                    category_history.insert(0, {
                        'date': simulated_date,
                        'score': round(simulated_score, 2),
                        'percentage': round((simulated_score / 5) * 100, 1)
                    })
            
            # Eliminar duplicados exactos (misma fecha y score)
            unique_history = []
            seen = set()
            for point in category_history:
                key = (point['date'].date(), point['score'])
                if key not in seen:
                    unique_history.append(point)
                    seen.add(key)
            
            category_history = unique_history
            
            # Calcular tendencia
            trend_indicator = 'stable'
            trend_change = 0.0
            historical_average = 0.0
            
            if len(category_history) >= 2:
                # Calcular promedio histórico
                historical_average = sum(point['score'] for point in category_history) / len(category_history)
                
                # Usar regresión lineal simple para calcular tendencia más precisa
                n = len(category_history)
                if n >= 3:
                    # Calcular pendiente de la línea de tendencia
                    x_values = list(range(n))
                    y_values = [point['score'] for point in category_history]
                    
                    x_mean = sum(x_values) / n
                    y_mean = sum(y_values) / n
                    
                    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
                    denominator = sum((x - x_mean) ** 2 for x in x_values)
                    
                    if denominator != 0:
                        slope = numerator / denominator
                        # Convertir pendiente a porcentaje de cambio
                        trend_change = (slope / historical_average * 100) if historical_average > 0 else 0
                    else:
                        trend_change = 0.0
                else:
                    # Para 2 puntos, comparación directa
                    most_recent_score = category_history[-1]['score']
                    previous_score = category_history[0]['score']
                    
                    if previous_score > 0:
                        trend_change = ((most_recent_score - previous_score) / previous_score * 100)
                    else:
                        trend_change = 0.0
                
                # Determinar indicador con umbrales ajustados
                if trend_change > 2:  # Mejora significativa (>2%)
                    trend_indicator = 'improving'
                elif trend_change < -2:  # Deterioro significativo (<-2%)
                    trend_indicator = 'declining'
                else:
                    trend_indicator = 'stable'
                    
            elif len(category_history) == 1:
                historical_average = category_history[0]['score']
                trend_change = 0.0
                trend_indicator = 'stable'
            
            trends[category.code] = {
                'category_name': category.name,
                'trend_indicator': trend_indicator,
                'trend_change': round(trend_change, 1),
                'historical_average': round(historical_average, 2),
                'historical_points': category_history,
                'data_points_count': len(category_history)
            }
        
        return trends
    
    def get_category_risk_level(self, category):
        """
        Determina el nivel de riesgo de una categoría basado en score actual + tendencia
        """
        current_score = self.calculate_category_score(category)
        trends = self.get_category_trends()
        
        if category.code not in trends:
            return 'unknown'
        
        trend_data = trends[category.code]
        score = current_score['percentage']
        trend = trend_data['trend_indicator']
        
        # Matriz de riesgo
        if score >= 80:
            if trend == 'declining':
                return 'medium'  # Alto score pero empeorando
            else:
                return 'low'     # Alto score y estable/mejorando
        elif score >= 60:
            if trend == 'declining':
                return 'high'    # Score medio pero empeorando
            elif trend == 'improving':
                return 'low'     # Score medio pero mejorando
            else:
                return 'medium'  # Score medio y estable
        elif score >= 40:
            if trend == 'improving':
                return 'medium'  # Score bajo pero mejorando
            else:
                return 'high'    # Score bajo y estable/empeorando
        else:
            return 'critical'    # Score muy bajo
    
    def get_detailed_scoring_report(self):
        """
        Genera un reporte detallado con todos los cálculos
        """
        report = {
            'assessment_id': str(self.id),
            'hotel_name': self.hotel.name,
            'assessment_date': self.assessment_date,
            'categories': {},
            'overall_score': 0.0
        }
        
        category_scores = self.get_all_category_scores()
        
        for category_code, score_data in category_scores.items():
            # Obtener detalles de preguntas para esta categoría
            responses = self.responses.filter(
                question__category=score_data['category']
            ).select_related('question')
            
            question_details = []
            for response in responses:
                question_details.append({
                    'question_text': response.question.question_text,
                    'rating': response.rating,
                    'not_applicable': response.not_applicable,
                    'rating_description': response.rating_description,
                    'comments': response.comments
                })
            
            report['categories'][category_code] = {
                'name': score_data['category_name'],
                'category_name': score_data['category_name'],  # Agregar para compatibilidad
                'score_sum': score_data['score_sum'],
                'question_count': score_data['question_count'],
                'average': score_data['average'],
                'percentage': score_data['percentage'],
                'questions': question_details
            }
        
        # Calcular promedio general
        report['overall_score'] = self.calculate_overall_score()
        
        return report
    
    def save_calculated_scores(self):
        """
        Guarda los puntajes calculados en el modelo y en SecurityCategoryScore
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Calcular y guardar puntajes por categoría
            category_scores = self.get_all_category_scores()
            logger.info(f"Calculated scores for {len(category_scores)} categories in assessment {self.id}")
            
            for category_code, score_data in category_scores.items():
                category = score_data['category']
                
                # Crear o actualizar puntaje de categoría
                category_score, created = SecurityCategoryScore.objects.update_or_create(
                    assessment=self,
                    category=category,
                    defaults={
                        'score_sum': score_data['score_sum'],
                        'question_count': score_data['question_count'],
                        'average_score': score_data['average'],
                        'percentage': score_data['percentage']
                    }
                )
                logger.debug(f"{'Created' if created else 'Updated'} score for category {category.name}")
            
            # Calcular promedio general
            overall_score_percentage = self.calculate_overall_score()
            
            if overall_score_percentage is None or overall_score_percentage < 0:
                logger.warning(f"Invalid overall score calculated: {overall_score_percentage}")
                overall_score_percentage = 0
            
            # Convertir porcentaje a escala 0-5 para guardar en overall_score
            self.overall_score = (overall_score_percentage / 100) * 5
            
            # Determinar nivel de riesgo basado en el porcentaje
            if overall_score_percentage >= 90:
                self.risk_level = 'muy_bajo'
            elif overall_score_percentage >= 75:
                self.risk_level = 'bajo' 
            elif overall_score_percentage >= 60:
                self.risk_level = 'medio'
            elif overall_score_percentage >= 40:
                self.risk_level = 'alto'
            else:
                self.risk_level = 'muy_alto'
            
            logger.info(f"Assessment {self.id} - Overall score: {overall_score_percentage}%, Risk level: {self.risk_level}")
            
            # No hacer save aquí para evitar conflictos con complete_assessment
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating scores for assessment {self.id}: {str(e)}")
            raise  # Re-raise para que el método complete_assessment pueda manejarlo
    
    def get_saved_category_scores(self):
        """
        Obtiene los puntajes guardados por categoría desde SecurityCategoryScore
        """
        saved_scores = {}
        category_scores = self.category_scores.select_related('category').all()
        
        for score in category_scores:
            saved_scores[score.category.code] = {
                'category_name': score.category.name,
                'score_sum': score.score_sum,
                'question_count': score.question_count,
                'average': score.average_score,
                'percentage': score.percentage,
                'calculated_at': score.calculated_at
            }
        
        return saved_scores
    
    def get_scoring_summary(self):
        """
        Retorna un resumen completo de puntuaciones (guardadas o calculadas en tiempo real)
        """
        # Intentar obtener puntajes guardados primero
        saved_scores = self.get_saved_category_scores()
        
        if saved_scores:
            return {
                'source': 'saved',
                'overall_score_percentage': self.calculate_overall_score(),  # Usar cálculo directo correcto
                'overall_score_5_scale': self.overall_score or 0,
                'risk_level': self.risk_level,
                'categories': saved_scores,
                'last_calculated': max(score['calculated_at'] for score in saved_scores.values()) if saved_scores else None
            }
        else:
            # Si no hay puntajes guardados, calcular en tiempo real
            calculated_scores = self.get_all_category_scores()
            overall_percentage = self.calculate_overall_score()
            
            return {
                'source': 'calculated',
                'overall_score_percentage': overall_percentage,
                'overall_score_5_scale': round((overall_percentage / 100) * 5, 2),
                'risk_level': None,  # No determinado aún
                'categories': calculated_scores,
                'last_calculated': timezone.now()
            }
    
    def get_category_scores(self):
        """
        Método de compatibilidad - retorna scores por categoría en formato anterior
        """
        category_scores = {}
        scoring_summary = self.get_scoring_summary()
        
        for category_code, score_data in scoring_summary['categories'].items():
            # Convertir porcentaje a escala 0-5 para compatibilidad
            if 'percentage' in score_data:
                category_scores[category_code] = (score_data['percentage'] / 100) * 5
            else:
                category_scores[category_code] = 0.0
        
        return category_scores


class SecurityCategoryScore(models.Model):
    """
    Almacena los puntajes calculados por categoría para cada evaluación
    """
    assessment = models.ForeignKey(
        SecurityAssessment,
        on_delete=models.CASCADE,
        related_name='category_scores',
        verbose_name="Evaluación"
    )
    category = models.ForeignKey(
        SecurityCategory,
        on_delete=models.CASCADE,
        verbose_name="Categoría"
    )
    
    # Resultados de cálculo según metodología
    score_sum = models.IntegerField(
        default=0,
        verbose_name="Suma de Calificaciones"
    )
    question_count = models.IntegerField(
        default=0,
        verbose_name="Cantidad de Preguntas Válidas"
    )
    average_score = models.FloatField(
        default=0.0,
        verbose_name="Promedio de Calificaciones"
    )
    percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Porcentaje Final"
    )
    
    # Metadatos
    calculated_at = models.DateTimeField(auto_now=True, verbose_name="Calculado en")
    
    class Meta:
        verbose_name = "Puntaje de Categoría"
        verbose_name_plural = "Puntajes de Categorías"
        unique_together = ['assessment', 'category']
        
    def __str__(self):
        return f"{self.assessment.hotel.name} - {self.category.name}: {self.percentage}%"


class SecurityCategoryComment(models.Model):
    """
    Comentarios generales por categoría en una evaluación de seguridad
    """
    assessment = models.ForeignKey(
        SecurityAssessment,
        on_delete=models.CASCADE,
        related_name='category_comments',
        verbose_name="Evaluación"
    )
    category = models.ForeignKey(
        SecurityCategory,
        on_delete=models.CASCADE,
        verbose_name="Categoría"
    )
    comments = models.TextField(
        blank=True,
        verbose_name="Comentarios Generales",
        help_text="Observaciones generales, evidencias, recomendaciones sobre esta categoría"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")
    
    class Meta:
        verbose_name = "Comentario de Categoría"
        verbose_name_plural = "Comentarios de Categorías"
        unique_together = ['assessment', 'category']
        
    def __str__(self):
        return f"{self.assessment.hotel.name} - {self.category.name}: {self.comments[:50]}..."


class ResponseOption(models.Model):
    """
    Opciones de respuesta configurables para las evaluaciones de seguridad.
    Corresponden a la escala de calificación 0-5.
    """
    value = models.IntegerField(
        unique=True,
        validators=[MinValueValidator(-1), MaxValueValidator(10)],
        verbose_name="Valor numérico"
    )
    label = models.CharField(max_length=100, verbose_name="Etiqueta corta")
    description = models.TextField(verbose_name="Descripción completa")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        verbose_name = "Opción de Respuesta"
        verbose_name_plural = "Opciones de Respuesta"
        ordering = ['order', 'value']

    def __str__(self):
        return f"{self.value} - {self.label}"


class SecurityResponse(models.Model):
    """
    Respuestas a las preguntas de seguridad para una evaluación específica
    """
    RATING_CHOICES = [
        (0, 'Expuesto - Se carece de dicho control'),
        (1, 'Vulnerable - Control totalmente vulnerable'),
        (2, 'Insuficiente - Control funciona ocasionalmente'),
        (3, 'Estándar - Control funciona regularmente'),
        (4, 'Adecuado - Control funciona adecuadamente'),
        (5, 'Excelente - Control con nivel superior'),
    ]
    
    assessment = models.ForeignKey(
        SecurityAssessment,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name="Evaluación"
    )
    
    question = models.ForeignKey(
        SecurityQuestion,
        on_delete=models.CASCADE,
        verbose_name="Pregunta"
    )
    
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name="Calificación"
    )
    
    not_applicable = models.BooleanField(
        default=False,
        verbose_name="No Aplica"
    )
    
    comments = models.TextField(blank=True, verbose_name="Comentarios")
    evidence = models.TextField(blank=True, verbose_name="Evidencia/Justificación")
    
    # Metadatos
    answered_at = models.DateTimeField(auto_now=True, verbose_name="Respondido en")
    
    class Meta:
        verbose_name = "Respuesta de Seguridad"
        verbose_name_plural = "Respuestas de Seguridad"
        unique_together = ['assessment', 'question']
        
    def __str__(self):
        rating_display = dict(self.RATING_CHOICES).get(self.rating, 'Sin respuesta')
        if self.not_applicable:
            rating_display = 'No Aplica'
        return f"{self.question.question_text[:30]}... - {rating_display}"
    
    @property
    def rating_description(self):
        """
        Retorna la descripción completa de la calificación.
        Busca primero en ResponseOption (DB), con fallback a valores por defecto.
        """
        if self.not_applicable:
            try:
                option = ResponseOption.objects.get(value=-1, is_active=True)
                return option.description
            except ResponseOption.DoesNotExist:
                pass
            return "No aplica - Por el tipo de organización hotelera, por la dinámica operativa, por ubicación o servicio, el criterio no aplica"

        if self.rating is None:
            return "Sin calificación"

        try:
            option = ResponseOption.objects.get(value=self.rating, is_active=True)
            return option.description
        except ResponseOption.DoesNotExist:
            pass

        # Fallback si la tabla aún no tiene datos
        fallback = {
            0: "Expuesto - Se carece de dicho control",
            1: "Vulnerable - El control que se tiene es totalmente vulnerable dado que no cumple con ningún nivel de efectividad y podría ser superado, quebrantado u omitido dado que no genera ningún tipo de incidencia en la mitigación del riesgo o en el cumplimiento cabal del requisito",
            2: "Insuficiente - El control puede funcionar en ocasiones o incidir positivamente en algunos casos pero no en todos. Esto implica que el control no es efectivo para la mayoría de los casos y su fallo es recurrente.",
            3: "Estándar - El control que se tiene funciona de manera regular la mayoría de las veces. Este podría fallar en ocasiones determinadas, ocurrentes pero no recurrentes. Se considera que el control es efectivo pero en algunos casos presenta variabilidad en su funcionamiento.",
            4: "Adecuado - El control que se tiene funciona adecuadamente la mayoría de las veces. Este podría fallar excepcionalmente. Se considera que el control es efectivo cumpliendo confiablemente con el requisito.",
            5: "Excelente - El control que se tiene funciona con un nivel superior, dado que tiene mecanismos redundantes y cuenta con diseño a prueba de fallos. Se considera que el control es efectivo cumple a un nivel más alto que garantiza su constante confiabilidad y no se conocen fallos de este."
        }
        return fallback.get(self.rating, "Sin calificación")


class AssessmentEvidence(models.Model):
    """
    Imágenes y archivos de evidencia para las evaluaciones de seguridad
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        SecurityAssessment,
        on_delete=models.CASCADE,
        related_name='evidence_images',
        verbose_name="Evaluación"
    )
    
    # Archivo de evidencia
    image = models.ImageField(
        upload_to='evaluaciones/evidencias/%Y/%m/',
        verbose_name="Imagen de Evidencia"
    )
    
    # Metadatos
    original_name = models.CharField(
        max_length=255,
        verbose_name="Nombre Original del Archivo"
    )
    file_size = models.PositiveIntegerField(
        verbose_name="Tamaño del Archivo (bytes)"
    )
    content_type = models.CharField(
        max_length=50,
        verbose_name="Tipo de Contenido"
    )
    
    # Información adicional
    description = models.TextField(
        blank=True,
        verbose_name="Descripción de la Evidencia"
    )
    
    # Timestamps
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Subida"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Subido por"
    )
    
    class Meta:
        verbose_name = "Evidencia de Evaluación"
        verbose_name_plural = "Evidencias de Evaluación"
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"Evidencia: {self.original_name} - {self.assessment}"
    
    @property
    def file_size_mb(self):
        """Retorna el tamaño del archivo en MB"""
        return round(self.file_size / 1024 / 1024, 2)
    
    @property
    def is_image(self):
        """Verifica si el archivo es una imagen"""
        return self.content_type.startswith('image/')

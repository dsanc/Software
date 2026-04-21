"""
Sistema de IA/ML para análisis predictivo de riesgos hoteleros
Genera alertas inteligentes basadas en patrones de datos y machine learning
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

from apps.risk_hoteles.models import (
    Hotel, SecurityAssessment, SecurityCategoryScore, 
    SecurityCategory
)
from apps.users.models import User


class HotelRiskAI:
    """
    Sistema de IA para análisis predictivo de riesgos hoteleros
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.risk_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.kmeans = KMeans(n_clusters=4, random_state=42)
        self.is_trained = False
        
    def prepare_training_data(self):
        """
        Prepara datos de entrenamiento desde las evaluaciones existentes
        """
        assessments = SecurityAssessment.objects.filter(
            status='completed'
        ).select_related('hotel').prefetch_related('category_scores')
        
        if not assessments.exists():
            return None, None
        
        features = []
        labels = []
        
        for assessment in assessments:
            # Características del hotel
            hotel_features = self._extract_hotel_features(assessment.hotel)
            
            # Características de la evaluación
            eval_features = self._extract_evaluation_features(assessment)
            
            # Características de categorías
            category_features = self._extract_category_features(assessment)
            
            # Combinar todas las características
            feature_vector = hotel_features + eval_features + category_features
            features.append(feature_vector)
            
            # Etiqueta de riesgo (0=bajo, 1=medio, 2=alto, 3=crítico)
            risk_label = self._calculate_risk_label(assessment)
            labels.append(risk_label)
        
        return np.array(features), np.array(labels)
    
    def _extract_hotel_features(self, hotel):
        """Extrae características del hotel"""
        # Mapear categoría a número
        category_map = {'1_star': 1, '2_star': 2, '3_star': 3, '4_star': 4, '5_star': 5, 'luxury': 6}
        category_score = category_map.get(hotel.category, 3)
        
        # Características del hotel
        features = [
            category_score,  # Categoría del hotel
            hotel.total_rooms,  # Número de habitaciones
            len(hotel.name),  # Longitud del nombre (proxy de tamaño/importancia)
        ]
        
        return features
    
    def _extract_evaluation_features(self, assessment):
        """Extrae características de la evaluación"""
        # Días desde la evaluación
        days_since = (timezone.now() - assessment.assessment_date).days
        
        # Características temporales
        features = [
            assessment.overall_score or 0,  # Puntuación general
            days_since,  # Días desde evaluación
            assessment.assessment_date.weekday(),  # Día de la semana
            assessment.assessment_date.month,  # Mes del año
        ]
        
        return features
    
    def _extract_category_features(self, assessment):
        """Extrae características de las categorías evaluadas"""
        categories = SecurityCategoryScore.objects.filter(assessment=assessment)
        
        if not categories.exists():
            return [0] * 15  # 15 características por defecto
        
        # Estadísticas de categorías
        percentages = [cat.percentage for cat in categories]
        
        features = [
            np.mean(percentages),  # Promedio
            np.std(percentages),   # Desviación estándar
            np.min(percentages),   # Mínimo
            np.max(percentages),   # Máximo
            np.median(percentages), # Mediana
            len([p for p in percentages if p < 40]),  # Categorías críticas (<40%)
            len([p for p in percentages if p < 60]),  # Categorías problemáticas (<60%)
            len([p for p in percentages if p > 80]),  # Categorías excelentes (>80%)
            len(percentages),  # Total de categorías evaluadas
        ]
        
        # Añadir las 6 categorías más importantes individualmente
        sorted_categories = sorted(categories, key=lambda x: x.percentage)
        for i in range(6):
            if i < len(sorted_categories):
                features.append(sorted_categories[i].percentage)
            else:
                features.append(70)  # Valor por defecto neutral
        
        return features
    
    def _calculate_risk_label(self, assessment):
        """Calcula etiqueta de riesgo basada en criterios múltiples"""
        score = assessment.overall_score or 0
        
        # Contar categorías problemáticas
        categories = SecurityCategoryScore.objects.filter(assessment=assessment)
        critical_categories = len([cat for cat in categories if cat.percentage < 40])
        problematic_categories = len([cat for cat in categories if cat.percentage < 60])
        
        # Algoritmo de scoring
        if score < 2.0 or critical_categories >= 3:
            return 3  # Crítico
        elif score < 3.0 or critical_categories >= 1 or problematic_categories >= 4:
            return 2  # Alto
        elif score < 4.0 or problematic_categories >= 2:
            return 1  # Medio
        else:
            return 0  # Bajo
    
    def train_models(self):
        """Entrena todos los modelos de ML"""
        logger.info("Entrenando modelos de IA...")
        
        features, labels = self.prepare_training_data()
        if features is None:
            logger.warning("No hay suficientes datos para entrenar")
            return False
        
        logger.info(f"Datos de entrenamiento: {len(features)} evaluaciones")
        
        # Normalizar características
        features_scaled = self.scaler.fit_transform(features)
        
        # Entrenar detector de anomalías
        self.isolation_forest.fit(features_scaled)
        
        # Entrenar clasificador de riesgo
        if len(set(labels)) > 1:  # Solo si hay variedad en las etiquetas
            self.risk_classifier.fit(features_scaled, labels)
        
        # Entrenar clustering
        self.kmeans.fit(features_scaled)
        
        self.is_trained = True
        logger.info("Modelos entrenados exitosamente")
        return True
    
    def predict_hotel_risk(self, hotel):
        """Predice el riesgo de un hotel específico"""
        if not self.is_trained:
            logger.info("Modelos no entrenados. Ejecutando entrenamiento...")
            if not self.train_models():
                return None
        
        # Obtener última evaluación
        latest_assessment = SecurityAssessment.objects.filter(
            hotel=hotel, status='completed'
        ).order_by('-assessment_date').first()
        
        if not latest_assessment:
            return {
                'risk_level': 'unknown',
                'confidence': 0.0,
                'anomaly_score': 0.0,
                'cluster': -1,
                'recommendations': ['Realizar evaluación inicial de seguridad']
            }
        
        # Preparar características
        hotel_features = self._extract_hotel_features(hotel)
        eval_features = self._extract_evaluation_features(latest_assessment)
        category_features = self._extract_category_features(latest_assessment)
        
        feature_vector = np.array([hotel_features + eval_features + category_features])
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predicciones
        risk_prediction = self.risk_classifier.predict(feature_vector_scaled)[0]
        risk_probability = self.risk_classifier.predict_proba(feature_vector_scaled)[0]
        anomaly_score = self.isolation_forest.decision_function(feature_vector_scaled)[0]
        cluster = self.kmeans.predict(feature_vector_scaled)[0]
        
        # Mapear nivel de riesgo
        risk_levels = ['bajo', 'medio', 'alto', 'crítico']
        risk_level = risk_levels[risk_prediction]
        confidence = max(risk_probability)
        
        return {
            'risk_level': risk_level,
            'confidence': confidence,
            'anomaly_score': anomaly_score,
            'cluster': cluster,
            'risk_probabilities': dict(zip(risk_levels, risk_probability)),
            'recommendations': self._generate_ai_recommendations(
                hotel, latest_assessment, risk_level, anomaly_score
            )
        }
    
    def _generate_ai_recommendations(self, hotel, assessment, risk_level, anomaly_score):
        """Genera recomendaciones basadas en IA"""
        recommendations = []
        
        # Análisis de categorías problemáticas
        problematic_categories = SecurityCategoryScore.objects.filter(
            assessment=assessment, percentage__lt=60
        ).order_by('percentage')
        
        if problematic_categories.exists():
            worst_category = problematic_categories.first()
            recommendations.append(
                f"Priorizar mejoras en {worst_category.category.name} "
                f"(actual: {worst_category.percentage:.1f}%)"
            )
        
        # Recomendaciones por nivel de riesgo
        if risk_level == 'crítico':
            recommendations.extend([
                "Implementar plan de acción correctiva inmediata",
                "Asignar recursos adicionales de seguridad",
                "Programar re-evaluación en 30 días"
            ])
        elif risk_level == 'alto':
            recommendations.extend([
                "Desarrollar plan de mejora estructurado",
                "Programar re-evaluación en 60 días"
            ])
        elif risk_level == 'medio':
            recommendations.append("Monitorear tendencias y programar mejoras graduales")
        
        # Recomendaciones por anomalías
        if anomaly_score < -0.3:  # Anomalía significativa
            recommendations.append(
                "Patrón atípico detectado - revisar factores externos específicos"
            )
        
        return recommendations[:5]  # Máximo 5 recomendaciones
    
    def analyze_portfolio_risks(self, user):
        """Analiza riesgos de todo el portafolio de hoteles de un usuario"""
        hotels = Hotel.objects.filter(owner=user)
        portfolio_analysis = {
            'total_hotels': hotels.count(),
            'risk_distribution': {'bajo': 0, 'medio': 0, 'alto': 0, 'crítico': 0, 'unknown': 0},
            'high_risk_hotels': [],
            'portfolio_score': 0.0,
            'recommendations': []
        }
        
        if not hotels.exists():
            return portfolio_analysis
        
        total_score = 0
        analyzed_hotels = 0
        
        for hotel in hotels:
            risk_analysis = self.predict_hotel_risk(hotel)
            if risk_analysis:
                risk_level = risk_analysis['risk_level']
                portfolio_analysis['risk_distribution'][risk_level] += 1
                
                if risk_level in ['alto', 'crítico']:
                    portfolio_analysis['high_risk_hotels'].append({
                        'hotel': hotel,
                        'risk_level': risk_level,
                        'confidence': risk_analysis['confidence'],
                        'recommendations': risk_analysis['recommendations']
                    })
                
                # Calcular score del portafolio
                if risk_level != 'unknown':
                    risk_scores = {'bajo': 4, 'medio': 3, 'alto': 2, 'crítico': 1}
                    total_score += risk_scores[risk_level]
                    analyzed_hotels += 1
        
        if analyzed_hotels > 0:
            portfolio_analysis['portfolio_score'] = total_score / analyzed_hotels
        
        # Recomendaciones del portafolio
        critical_count = portfolio_analysis['risk_distribution']['crítico']
        high_count = portfolio_analysis['risk_distribution']['alto']
        
        if critical_count > 0:
            portfolio_analysis['recommendations'].append(
                f"URGENTE: {critical_count} hotel(es) en estado crítico requieren atención inmediata"
            )
        
        if high_count > 0:
            portfolio_analysis['recommendations'].append(
                f"PRIORIDAD: {high_count} hotel(es) con riesgo alto necesitan plan de mejora"
            )
        
        if portfolio_analysis['portfolio_score'] < 2.5:
            portfolio_analysis['recommendations'].append(
                "Portafolio en riesgo general - revisar estrategia de gestión de seguridad"
            )
        
        return portfolio_analysis
    
    def generate_ml_alerts(self, user):
        """Genera alertas usando análisis de IA/ML"""
        if not self.train_models():
            return []
        
        logger.info("Generando alertas con IA/ML...")
        
        hotels = Hotel.objects.filter(owner=user)
        ml_alerts = []
        
        for hotel in hotels:
            risk_analysis = self.predict_hotel_risk(hotel)
            if not risk_analysis:
                continue
            
            risk_level = risk_analysis['risk_level']
            confidence = risk_analysis['confidence']
            anomaly_score = risk_analysis['anomaly_score']
            
            # Generar alertas basadas en IA
            alerts = self._create_ml_alerts(hotel, risk_analysis)
            ml_alerts.extend(alerts)
        
        # Análisis del portafolio
        portfolio_analysis = self.analyze_portfolio_risks(user)
        portfolio_alerts = self._create_portfolio_alerts(user, portfolio_analysis)
        ml_alerts.extend(portfolio_alerts)
        
        logger.info(f"Generadas {len(ml_alerts)} alertas con IA")
        return ml_alerts
    
    def _create_ml_alerts(self, hotel, risk_analysis):
        """Crea alertas específicas basadas en análisis ML"""
        alerts = []
        risk_level = risk_analysis['risk_level']
        confidence = risk_analysis['confidence']
        anomaly_score = risk_analysis['anomaly_score']
        
        # Alerta por nivel de riesgo predicho
        if risk_level == 'crítico' and confidence > 0.7:
            alerts.append({
                'hotel': hotel,
                'title': f'IA: Riesgo Crítico Detectado - {hotel.name}',
                'message': f'El sistema de IA ha identificado un riesgo crítico en {hotel.name} '
                          f'con {confidence*100:.1f}% de confianza. '
                          f'Recomendaciones: {"; ".join(risk_analysis["recommendations"][:3])}',
                'severity': 'critical',
                'alert_type': 'urgent_action',
                'ai_generated': True,
                'confidence_score': confidence
            })
        
        elif risk_level == 'alto' and confidence > 0.6:
            alerts.append({
                'hotel': hotel,
                'title': f'IA: Riesgo Alto Identificado - {hotel.name}',
                'message': f'Análisis predictivo indica riesgo alto en {hotel.name} '
                          f'(confianza: {confidence*100:.1f}%). '
                          f'Acción recomendada: {risk_analysis["recommendations"][0] if risk_analysis["recommendations"] else "Revisar evaluación"}',
                'severity': 'high',
                'alert_type': 'high_risk',
                'ai_generated': True,
                'confidence_score': confidence
            })
        
        # Alerta por anomalía detectada
        if anomaly_score < -0.4:  # Anomalía fuerte
            alerts.append({
                'hotel': hotel,
                'title': f'IA: Patrón Anómalo Detectado - {hotel.name}',
                'message': f'El sistema ha detectado patrones atípicos en las métricas de seguridad de {hotel.name}. '
                          f'Esto podría indicar cambios súbitos en las condiciones operativas o problemas emergentes. '
                          f'Score de anomalía: {anomaly_score:.3f}',
                'severity': 'medium',
                'alert_type': 'new_risk',
                'ai_generated': True,
                'anomaly_score': anomaly_score
            })
        
        return alerts
    
    def _create_portfolio_alerts(self, user, portfolio_analysis):
        """Crea alertas a nivel de portafolio"""
        alerts = []
        
        critical_hotels = portfolio_analysis['risk_distribution']['crítico']
        high_risk_hotels = portfolio_analysis['risk_distribution']['alto']
        portfolio_score = portfolio_analysis['portfolio_score']
        
        # Alerta de portafolio crítico
        if critical_hotels >= 2:
            alerts.append({
                'hotel': None,  # Alerta de portafolio
                'title': f'IA: Portafolio en Estado Crítico',
                'message': f'Análisis de IA detecta {critical_hotels} hoteles en estado crítico '
                          f'de {portfolio_analysis["total_hotels"]} total. '
                          f'Score del portafolio: {portfolio_score:.2f}/4.0. '
                          f'Se requiere intervención inmediata a nivel corporativo.',
                'severity': 'critical',
                'alert_type': 'urgent_action',
                'ai_generated': True,
                'portfolio_alert': True
            })
        
        # Alerta de tendencia del portafolio
        elif portfolio_score < 2.5:
            alerts.append({
                'hotel': None,
                'title': f'IA: Riesgo Sistémico en Portafolio',
                'message': f'El análisis predictivo muestra un score general bajo del portafolio '
                          f'({portfolio_score:.2f}/4.0). '
                          f'{high_risk_hotels + critical_hotels} hoteles requieren atención. '
                          f'Considerar revisión de políticas corporativas de seguridad.',
                'severity': 'high',
                'alert_type': 'threshold_exceeded',
                'ai_generated': True,
                'portfolio_alert': True
            })
        
        return alerts


# Función auxiliar para integración con el comando de gestión
def generate_ai_alerts(user):
    """
    Función principal para generar alertas con IA
    Uso: desde comandos de gestión Django
    """
    ai_system = HotelRiskAI()
    return ai_system.generate_ml_alerts(user)
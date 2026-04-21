"""
Vistas para Reporte General Avanzado con IA/ML
Sistema inteligente que analiza todas las evaluaciones de un hotel y genera insights avanzados
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min, Q
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from textblob import TextBlob
import warnings
warnings.filterwarnings('ignore')

from .models import Hotel, SecurityAssessment, SecurityCategory, SecurityCategoryScore, SecurityCategoryComment
from .ai_recommendations import HotelSecurityAIRecommendations
from .views import get_hotel_or_404

class AdvancedHotelAnalytics:
    """
    Sistema de Analytics Avanzado con Machine Learning para Análisis Hotelero
    """
    
    def __init__(self, hotel):
        self.hotel = hotel
        self.assessments = SecurityAssessment.objects.filter(
            hotel=hotel,
            status='completed',
            overall_score__isnull=False
        ).order_by('assessment_date')
        self.ai_engine = HotelSecurityAIRecommendations()
        
    def get_temporal_trends(self):
        """Análisis de tendencias temporales con predicción ML"""
        if not self.assessments.exists():
            return None
            
        # Preparar datos temporales
        data = []
        for assessment in self.assessments:
            data.append({
                'date': assessment.assessment_date,
                'overall_score': assessment.overall_score,
                'score_percentage': (assessment.overall_score / 5.0) * 100,
                'month': assessment.assessment_date.strftime('%Y-%m'),
                'day_of_year': assessment.assessment_date.timetuple().tm_yday
            })
        
        if len(data) < 2:
            return {'trend': 'insufficient_data', 'data': data}
            
        df = pd.DataFrame(data)
        
        # Análisis de tendencia con regresión lineal
        X = np.array(range(len(df))).reshape(-1, 1)
        y = df['score_percentage'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        trend_slope = model.coef_[0]
        trend_direction = 'improving' if trend_slope > 0.5 else 'declining' if trend_slope < -0.5 else 'stable'
        
        # Predicción para los próximos 3 meses
        future_points = 3
        future_X = np.array(range(len(df), len(df) + future_points)).reshape(-1, 1)
        future_predictions = model.predict(future_X)
        
        # Análisis de volatilidad
        volatility = np.std(y)
        volatility_level = 'high' if volatility > 15 else 'medium' if volatility > 8 else 'low'
        
        return {
            'trend': trend_direction,
            'slope': round(trend_slope, 2),
            'volatility': round(volatility, 2),
            'volatility_level': volatility_level,
            'current_score': round(y[-1], 1),
            'predicted_scores': [round(pred, 1) for pred in future_predictions],
            'data': data,
            'r_squared': round(model.score(X, y), 3)
        }
    
    def get_category_performance_analysis(self):
        """Análisis avanzado de rendimiento por categorías con clustering"""
        category_data = []
        
        for category in SecurityCategory.objects.filter(is_active=True):
            scores_data = SecurityCategoryScore.objects.filter(
                assessment__hotel=self.hotel,
                assessment__status='completed',
                category=category
            )
            
            if scores_data.exists():
                scores = [cs.percentage for cs in scores_data]
                avg_score = np.mean(scores)
                score_trend = self._calculate_trend(scores)
                
                # Análisis de sentimientos en comentarios
                comments_data = SecurityCategoryComment.objects.filter(
                    assessment__hotel=self.hotel,
                    assessment__status='completed',
                    category=category
                )
                comments = [cc.comments for cc in comments_data if cc.comments]
                sentiment_analysis = self._analyze_sentiment(comments)
                
                category_data.append({
                    'name': category.name,
                    'avg_score': round(avg_score, 2),
                    'avg_percentage': round(avg_score, 1),
                    'assessments_count': len(scores),
                    'trend': score_trend,
                    'volatility': round(np.std(scores), 2),
                    'best_score': round(max(scores), 2),
                    'worst_score': round(min(scores), 2),
                    'sentiment': sentiment_analysis
                })
        
        # Clustering de categorías por rendimiento
        if len(category_data) >= 3:
            features = np.array([[cat['avg_score'], cat['volatility']] for cat in category_data])
            
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            n_clusters = min(3, len(category_data))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(features_scaled)
            
            cluster_labels = ['Crítico', 'Moderado', 'Óptimo']
            for i, cat in enumerate(category_data):
                cat['cluster'] = cluster_labels[clusters[i]] if clusters[i] < len(cluster_labels) else 'Sin Clasificar'
        
        return sorted(category_data, key=lambda x: x['avg_percentage'], reverse=True)
    
    def get_anomaly_detection(self):
        """Detección de anomalías en evaluaciones usando Isolation Forest"""
        if len(self.assessments) < 5:
            return None
            
        # Preparar características para detección de anomalías
        features = []
        assessment_info = []
        
        for assessment in self.assessments:
            # Calcular características de la evaluación
            category_scores = SecurityCategoryScore.objects.filter(assessment=assessment)
            if category_scores.exists():
                scores = [cs.percentage for cs in category_scores]
                features.append([
                    assessment.overall_score,
                    np.mean(scores),
                    np.std(scores),
                    len(scores),
                    assessment.assessment_date.weekday(),  # Día de la semana
                ])
                assessment_info.append({
                    'id': str(assessment.id),
                    'date': assessment.assessment_date.strftime('%Y-%m-%d'),
                    'score': assessment.overall_score,
                    'type': assessment.assessment_type
                })
        
        if len(features) < 5:
            return None
            
        # Aplicar Isolation Forest
        isolation_forest = IsolationForest(contamination=0.2, random_state=42)
        anomalies = isolation_forest.fit_predict(features)
        
        anomalous_assessments = []
        for i, is_anomaly in enumerate(anomalies):
            if is_anomaly == -1:  # -1 indica anomalía
                anomalous_assessments.append(assessment_info[i])
        
        return {
            'total_assessments': len(features),
            'anomalies_count': len(anomalous_assessments),
            'anomalous_assessments': anomalous_assessments,
            'anomaly_rate': round((len(anomalous_assessments) / len(features)) * 100, 1)
        }
    
    def get_risk_pattern_analysis(self):
        """Análisis de patrones de riesgo con PCA"""
        category_matrix = []
        assessment_dates = []
        
        # Crear matriz de puntuaciones por categoría
        for assessment in self.assessments:
            category_scores = {}
            for cat_score in SecurityCategoryScore.objects.filter(assessment=assessment):
                category_scores[cat_score.category.name] = cat_score.percentage
            
            # Asegurar que todas las categorías estén representadas
            all_categories = SecurityCategory.objects.filter(is_active=True)
            score_vector = []
            for category in all_categories:
                score_vector.append(category_scores.get(category.name, 50.0))  # Score neutro por defecto
            
            if len(score_vector) >= 3:  # Mínimo 3 categorías para PCA
                category_matrix.append(score_vector)
                assessment_dates.append(assessment.assessment_date)
        
        if len(category_matrix) < 3:
            return None
        
        # Aplicar PCA para identificar patrones principales
        try:
            pca = PCA(n_components=min(3, len(category_matrix[0])))
            pca_result = pca.fit_transform(category_matrix)
            
            # Identificar componentes principales
            feature_importance = []
            categories = list(SecurityCategory.objects.filter(is_active=True).values_list('name', flat=True))
            
            for i, component in enumerate(pca.components_[:3]):
                top_features = []
                for j, weight in enumerate(component):
                    if j < len(categories):
                        top_features.append({
                            'category': categories[j],
                            'weight': round(weight, 3)
                        })
                
                top_features.sort(key=lambda x: abs(x['weight']), reverse=True)
                feature_importance.append({
                    'component': f'Patrón {i+1}',
                    'variance_explained': round(pca.explained_variance_ratio_[i] * 100, 1),
                    'top_categories': top_features[:3]
                })
            
            return {
                'patterns_found': len(feature_importance),
                'total_variance_explained': round(sum(pca.explained_variance_ratio_) * 100, 1),
                'feature_importance': feature_importance
            }
        except:
            return None
    
    def get_benchmarking_analysis(self):
        """Análisis comparativo con otros hoteles similares"""
        similar_hotels = Hotel.objects.filter(
            category=self.hotel.category,
            is_active=True
        ).exclude(id=self.hotel.id)
        
        if not similar_hotels.exists():
            return None
        
        # Calcular estadísticas comparativas
        hotel_avg = self.hotel.get_average_assessment_percentage()
        if not hotel_avg:
            return None
        
        competitor_scores = []
        for hotel in similar_hotels:
            avg_score = hotel.get_average_assessment_percentage()
            if avg_score:
                competitor_scores.append(avg_score)
        
        if not competitor_scores:
            return None
        
        # Análisis estadístico
        percentile_rank = (sum(1 for score in competitor_scores if score < hotel_avg) / len(competitor_scores)) * 100
        
        return {
            'hotel_score': round(hotel_avg, 1),
            'industry_average': round(np.mean(competitor_scores), 1),
            'industry_median': round(np.median(competitor_scores), 1),
            'percentile_rank': round(percentile_rank, 1),
            'competitors_analyzed': len(competitor_scores),
            'performance_vs_industry': 'above' if hotel_avg > np.mean(competitor_scores) else 'below'
        }
    
    def _calculate_trend(self, scores):
        """Calcula la tendencia de una serie de puntuaciones"""
        if len(scores) < 2:
            return 'stable'
        
        X = np.array(range(len(scores))).reshape(-1, 1)
        y = np.array(scores)
        
        model = LinearRegression()
        model.fit(X, y)
        
        slope = model.coef_[0]
        return 'improving' if slope > 0.1 else 'declining' if slope < -0.1 else 'stable'
    
    def _analyze_sentiment(self, comments):
        """Análisis de sentimientos en comentarios"""
        if not comments:
            return {'sentiment': 'neutral', 'polarity': 0.0}
        
        combined_text = ' '.join(comments)
        blob = TextBlob(combined_text)
        
        polarity = blob.sentiment.polarity
        sentiment = 'positive' if polarity > 0.1 else 'negative' if polarity < -0.1 else 'neutral'
        
        return {
            'sentiment': sentiment,
            'polarity': round(polarity, 3),
            'comments_analyzed': len(comments)
        }

@login_required
def reporte_general_preview(request, hotel_id):
    """Vista de preview del reporte general avanzado"""
    hotel = get_hotel_or_404(request.user, hotel_id)
    
    # Inicializar sistema de analytics avanzado
    analytics = AdvancedHotelAnalytics(hotel)
    
    # Obtener datos básicos del hotel
    basic_stats = {
        'total_assessments': analytics.assessments.count(),
        'assessment_period': {
            'start': analytics.assessments.first().assessment_date if analytics.assessments.exists() else None,
            'end': analytics.assessments.last().assessment_date if analytics.assessments.exists() else None
        },
        'average_score': hotel.get_average_assessment_percentage(),
        'last_assessment': analytics.assessments.last() if analytics.assessments.exists() else None
    }
    
    # Análisis avanzados con IA/ML
    analyses = {
        'temporal_trends': analytics.get_temporal_trends(),
        'category_performance': analytics.get_category_performance_analysis(),
        'anomaly_detection': analytics.get_anomaly_detection(),
        'risk_patterns': analytics.get_risk_pattern_analysis(),
        'benchmarking': analytics.get_benchmarking_analysis()
    }
    
    # Calcular variación de rendimiento por categorías
    category_variation = None
    if analyses['category_performance']:
        percentages = [cat['avg_percentage'] for cat in analyses['category_performance']]
        if percentages:
            category_variation = {
                'max_score': max(percentages),
                'min_score': min(percentages),
                'variation': round(max(percentages) - min(percentages), 1)
            }
    
    # Generar recomendaciones inteligentes
    ai_recommendations = None
    if analytics.assessments.exists():
        latest_assessment = analytics.assessments.last()
        
        # Recopilar datos de la evaluación más reciente para IA
        categories_data = {}
        for cat_score in SecurityCategoryScore.objects.filter(assessment=latest_assessment):
            # Obtener comentarios de la categoría
            cat_comment = SecurityCategoryComment.objects.filter(
                assessment=latest_assessment, 
                category=cat_score.category
            ).first()
            
            categories_data[cat_score.category.code] = {
                'category': cat_score.category.name,
                'percentage': cat_score.percentage,
                'score': cat_score.percentage / 20.0,  # Convertir de 0-100 a 0-5
                'comments': cat_comment.comments if cat_comment else '',
                'question_count': cat_score.category.questions.count()
            }
        
        assessment_data = {
            'categories': categories_data,
            'overall_score': latest_assessment.overall_score,
            'hotel_info': {
                'id': str(hotel.id),
                'name': hotel.name,
                'address': hotel.address
            },
            'responses': []  # Placeholder para respuestas detalladas
        }
        
        try:
            ai_recommendations = analytics.ai_engine.analyze_assessment_data(assessment_data)
        except Exception as e:
            ai_recommendations = {'error': f'Error en análisis IA: {str(e)}'}
    
    # Estadísticas de resumen para el reporte
    summary_stats = {
        'total_categories_analyzed': SecurityCategory.objects.filter(is_active=True).count(),
        'data_quality_score': min(100, max(0, (basic_stats['total_assessments'] * 20))),  # Máximo 100%
        'analysis_confidence': 'high' if basic_stats['total_assessments'] >= 5 else 'medium' if basic_stats['total_assessments'] >= 3 else 'low'
    }
    
    context = {
        'hotel': hotel,
        'basic_stats': basic_stats,
        'analyses': analyses,
        'ai_recommendations': ai_recommendations,
        'summary_stats': summary_stats,
        'category_variation': category_variation,
        'generated_at': timezone.now(),
        'is_preview': True
    }
    
    return render(request, 'risk_hoteles/reporte_general_preview.html', context)

@login_required 
def reporte_general_print(request, hotel_id):
    """Vista optimizada para impresión con Browser Print JavaScript"""
    hotel = get_hotel_or_404(request.user, hotel_id)
    
    # Reutilizar la misma lógica de análisis
    analytics = AdvancedHotelAnalytics(hotel)
    
    basic_stats = {
        'total_assessments': analytics.assessments.count(),
        'assessment_period': {
            'start': analytics.assessments.first().assessment_date if analytics.assessments.exists() else None,
            'end': analytics.assessments.last().assessment_date if analytics.assessments.exists() else None
        },
        'average_score': hotel.get_average_assessment_percentage(),
        'last_assessment': analytics.assessments.last() if analytics.assessments.exists() else None
    }
    
    analyses = {
        'temporal_trends': analytics.get_temporal_trends(),
        'category_performance': analytics.get_category_performance_analysis(),
        'anomaly_detection': analytics.get_anomaly_detection(),
        'risk_patterns': analytics.get_risk_pattern_analysis(),
        'benchmarking': analytics.get_benchmarking_analysis()
    }
    
    # Calcular variación de rendimiento por categorías para impresión
    category_variation = None
    if analyses['category_performance']:
        percentages = [cat['avg_percentage'] for cat in analyses['category_performance']]
        if percentages:
            category_variation = {
                'max_score': max(percentages),
                'min_score': min(percentages),
                'variation': round(max(percentages) - min(percentages), 1)
            }
    
    # Generar recomendaciones IA para impresión
    ai_recommendations = None
    if analytics.assessments.exists():
        latest_assessment = analytics.assessments.last()
        
        # Recopilar datos de la evaluación más reciente para IA
        categories_data = {}
        for cat_score in SecurityCategoryScore.objects.filter(assessment=latest_assessment):
            # Obtener comentarios de la categoría
            cat_comment = SecurityCategoryComment.objects.filter(
                assessment=latest_assessment, 
                category=cat_score.category
            ).first()
            
            categories_data[cat_score.category.code] = {
                'category': cat_score.category.name,
                'percentage': cat_score.percentage,
                'score': cat_score.percentage / 20.0,  # Convertir de 0-100 a 0-5
                'comments': cat_comment.comments if cat_comment else '',
                'question_count': cat_score.category.questions.count()
            }
        
        assessment_data = {
            'categories': categories_data,
            'overall_score': latest_assessment.overall_score,
            'hotel_info': {
                'id': str(hotel.id),
                'name': hotel.name,
                'address': hotel.address
            },
            'responses': []  # Placeholder para respuestas detalladas
        }
        
        try:
            ai_recommendations = analytics.ai_engine.analyze_assessment_data(assessment_data)
        except Exception as e:
            ai_recommendations = {'error': f'Error en análisis IA: {str(e)}'}
    
    summary_stats = {
        'total_categories_analyzed': SecurityCategory.objects.filter(is_active=True).count(),
        'data_quality_score': min(100, max(0, (basic_stats['total_assessments'] * 20))),
        'analysis_confidence': 'high' if basic_stats['total_assessments'] >= 5 else 'medium' if basic_stats['total_assessments'] >= 3 else 'low'
    }
    
    context = {
        'hotel': hotel,
        'basic_stats': basic_stats,
        'analyses': analyses,
        'ai_recommendations': ai_recommendations,
        'summary_stats': summary_stats,
        'category_variation': category_variation,
        'generated_at': timezone.now(),
        'is_print': True,
        'auto_print': True  # Activar auto-print con JavaScript
    }
    
    return render(request, 'risk_hoteles/reporte_general_print.html', context)

@login_required
def reporte_general_api(request, hotel_id):
    """API endpoint para obtener datos del reporte en formato JSON"""
    hotel = get_hotel_or_404(request.user, hotel_id)
    
    analytics = AdvancedHotelAnalytics(hotel)
    
    # Datos simplificados para API
    data = {
        'hotel': {
            'id': str(hotel.id),
            'name': hotel.name,
            'category': hotel.get_category_display(),
            'city': hotel.city,
            'country': hotel.country
        },
        'summary': {
            'total_assessments': analytics.assessments.count(),
            'average_score': hotel.get_average_assessment_percentage(),
            'last_assessment_date': analytics.assessments.last().assessment_date.isoformat() if analytics.assessments.exists() else None
        },
        'trends': analytics.get_temporal_trends(),
        'category_performance': analytics.get_category_performance_analysis(),
        'anomalies': analytics.get_anomaly_detection(),
        'benchmarking': analytics.get_benchmarking_analysis(),
        'generated_at': timezone.now().isoformat()
    }
    
    return JsonResponse(data, safe=False)
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


# ─────────────────────────────────────────────────────────────
#  NUEVO REPORTE GENERAL  (templates/risk_hoteles/reports/)
# ─────────────────────────────────────────────────────────────

from collections import defaultdict
from .models import SecurityCategoryScore as _CatScore


def _score_level(pct):
    """Devuelve 'success'/'warning'/'danger' según el porcentaje."""
    if pct >= 70:
        return 'success'
    if pct >= 40:
        return 'warning'
    return 'danger'


def _risk_from_pct(pct):
    """Devuelve nivel de riesgo, etiqueta y descripción."""
    if pct >= 80:
        return {
            'level': 'bajo',
            'label': 'Riesgo Bajo',
            'css': 'success',
            'icon': 'fas fa-shield-check',
            'desc': (
                'El hotel presenta controles de seguridad sólidos y bien implementados. '
                'Los procesos de protección superan el estándar del sector. '
                'Se recomienda mantener las buenas prácticas y programar auditorías periódicas.'
            ),
        }
    if pct >= 60:
        return {
            'level': 'medio',
            'label': 'Riesgo Moderado',
            'css': 'warning',
            'icon': 'fas fa-triangle-exclamation',
            'desc': (
                'El hotel cuenta con medidas de seguridad aceptables, aunque existen áreas '
                'de mejora identificadas. Se recomienda reforzar las categorías con menor '
                'desempeño y establecer un plan de acción correctiva a corto plazo.'
            ),
        }
    if pct >= 40:
        return {
            'level': 'alto',
            'label': 'Riesgo Alto',
            'css': 'danger',
            'icon': 'fas fa-circle-exclamation',
            'desc': (
                'Se detectan deficiencias significativas en múltiples áreas de seguridad. '
                'Es prioritario implementar medidas correctivas inmediatas en las categorías '
                'críticas para reducir la exposición al riesgo operativo.'
            ),
        }
    return {
        'level': 'critico',
        'label': 'Riesgo Crítico',
        'css': 'danger',
        'icon': 'fas fa-skull-crossbones',
        'desc': (
            'El hotel presenta vulnerabilidades críticas que requieren atención urgente. '
            'Los controles de seguridad están por debajo del umbral mínimo aceptable. '
            'Se recomienda intervención inmediata y revisión integral de todos los procesos.'
        ),
    }


def _build_report_context(hotel, page_size, back_url, auto_print):
    """Construye el contexto completo para el reporte general."""

    # ─── Evaluaciones completadas (orden cronológico para tendencias) ───
    assessments_qs = hotel.security_assessments.filter(
        status='completed',
        overall_score__isnull=False,
    ).select_related('created_by').order_by('assessment_date')

    assessments_list = list(assessments_qs)

    assessments_data = []
    for a in reversed(assessments_list):          # recientes primero para tabla
        pct = round((a.overall_score / 5.0) * 100, 1)
        assessments_data.append({
            'obj': a,
            'percentage': pct,
            'level': _score_level(pct),
        })

    # ─── Puntuaciones por categoría (todos los assessments completados) ───
    cat_scores_qs = _CatScore.objects.filter(
        assessment__hotel=hotel,
        assessment__status='completed',
        assessment__overall_score__isnull=False,
    ).select_related('category', 'assessment').order_by(
        'category__order', 'assessment__assessment_date'
    )

    # Agrupar por categoría → lista de porcentajes en orden cronológico
    cat_map = defaultdict(list)
    for cs in cat_scores_qs:
        cat_map[cs.category].append(cs.percentage)

    category_analysis = []
    for cat, scores in cat_map.items():
        avg_pct = round(sum(scores) / len(scores), 1)
        last_pct = round(scores[-1], 1)

        # Tendencia: regresión simple sobre los últimos puntos
        if len(scores) >= 3:
            n = len(scores)
            x_mean = (n - 1) / 2
            y_mean = sum(scores) / n
            num = sum((i - x_mean) * (s - y_mean) for i, s in enumerate(scores))
            den = sum((i - x_mean) ** 2 for i in range(n))
            slope = num / den if den else 0
            trend = 'improving' if slope > 1.0 else 'declining' if slope < -1.0 else 'stable'
        elif len(scores) == 2:
            delta = scores[1] - scores[0]
            trend = 'improving' if delta > 3 else 'declining' if delta < -3 else 'stable'
        else:
            trend = 'stable'

        # Variación entre mejor y peor
        variation = round(max(scores) - min(scores), 1) if len(scores) > 1 else 0

        category_analysis.append({
            'name': cat.name,
            'icon': cat.icon,
            'avg_pct': avg_pct,
            'last_pct': last_pct,
            'count': len(scores),
            'trend': trend,
            'variation': variation,
            'risk': _risk_from_pct(avg_pct)['level'],
            'level': _score_level(avg_pct),
        })

    category_analysis.sort(key=lambda x: x['avg_pct'], reverse=True)

    strengths  = category_analysis[:3]
    weaknesses = list(reversed(category_analysis[-3:])) if len(category_analysis) >= 3 else list(reversed(category_analysis))

    # ─── Nivel de riesgo global ───
    avg_pct_global = hotel.get_average_assessment_percentage()
    global_risk = _risk_from_pct(avg_pct_global) if avg_pct_global is not None else None

    # ─── Tendencia global (comparando primera vs última evaluación) ───
    global_trend = None
    if len(assessments_list) >= 2:
        first_pct = round((assessments_list[0].overall_score / 5.0) * 100, 1)
        last_pct_g = round((assessments_list[-1].overall_score / 5.0) * 100, 1)
        delta_g = round(last_pct_g - first_pct, 1)
        direction = 'improving' if delta_g > 2 else 'declining' if delta_g < -2 else 'stable'
        global_trend = {'direction': direction, 'delta': delta_g, 'first': first_pct, 'last': last_pct_g}

    return {
        'hotel': hotel,
        'generated_at': timezone.now(),
        'page_size': page_size,
        'back_url': back_url,
        'auto_print': auto_print,
        # evaluaciones
        'assessments_data': assessments_data,
        'total_assessments': len(assessments_data),
        'best_score': max((a['percentage'] for a in assessments_data), default=None),
        'worst_score': min((a['percentage'] for a in assessments_data), default=None),
        'latest_assessment': assessments_data[0] if assessments_data else None,
        # análisis
        'category_analysis': category_analysis,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'global_risk': global_risk,
        'global_trend': global_trend,
        'avg_pct_global': avg_pct_global,
    }


@login_required
def reporte_general(request, hotel_id):
    """Preview del nuevo Reporte General de Seguridad."""
    hotel = get_hotel_or_404(request.user, hotel_id)
    page_size = request.GET.get('size', 'a4').lower()
    ctx = _build_report_context(
        hotel, page_size,
        back_url=request.META.get('HTTP_REFERER', ''),
        auto_print=False,
    )
    return render(request, 'risk_hoteles/reports/reporte_general.html', ctx)


@login_required
def reporte_general_print(request, hotel_id):
    """Versión de impresión directa del nuevo Reporte General."""
    hotel = get_hotel_or_404(request.user, hotel_id)
    page_size = request.GET.get('size', 'a4').lower()
    ctx = _build_report_context(hotel, page_size, back_url='', auto_print=True)
    return render(request, 'risk_hoteles/reports/reporte_general.html', ctx)
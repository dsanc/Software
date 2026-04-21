"""
Servicio de Inteligencia Artificial para Recomendaciones de Seguridad Hotelera
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class HotelSecurityAIRecommendations:
    """
    Sistema de IA para generar recomendaciones inteligentes basadas en:
    - Puntuaciones de categorías
    - Comentarios de categorías
    - Patrones de evaluaciones similares
    - Análisis de sentimientos
    """
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1500,
            stop_words='english',
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.95
        )
        self.priority_keywords = {
            'critical': ['emergencia', 'urgente', 'crítico', 'peligro', 'riesgo alto', 'falla', 'problema grave', 'no funciona', 'deficiente', 'inexistente'],
            'security': ['acceso', 'control', 'vigilancia', 'cámara', 'seguridad', 'cerraduras', 'llaves', 'alarma', 'detector', 'monitoreo'],
            'training': ['capacitación', 'entrenamiento', 'personal', 'staff', 'empleados', 'formación', 'conocimiento', 'preparación'],
            'maintenance': ['mantenimiento', 'reparación', 'equipos', 'sistemas', 'actualización', 'revisión', 'inspección', 'limpieza'],
            'compliance': ['cumplimiento', 'normativa', 'regulación', 'estándar', 'certificación', 'legal', 'requerimiento'],
            'guest_safety': ['huésped', 'cliente', 'habitación', 'bienestar', 'comodidad', 'experiencia', 'satisfacción'],
            'infrastructure': ['estructura', 'edificio', 'instalación', 'equipamiento', 'tecnología', 'sistemas'],
            'procedures': ['procedimiento', 'protocolo', 'manual', 'proceso', 'instrucción', 'guía']
        }
        
        # Patrones de contexto para mejor comprensión
        self.context_patterns = {
            'urgency_indicators': ['inmediatamente', 'cuanto antes', 'prioritario', 'sin demora'],
            'frequency_indicators': ['siempre', 'nunca', 'frecuentemente', 'ocasionalmente', 'rara vez'],
            'quality_indicators': ['excelente', 'bueno', 'regular', 'malo', 'deficiente', 'satisfactorio'],
            'completeness_indicators': ['completo', 'incompleto', 'parcial', 'total', 'limitado']
        }
    
    def analyze_assessment_data(self, assessment_data: Dict) -> Dict:
        """
        Analizar datos completos de evaluación para generar recomendaciones IA
        
        Args:
            assessment_data: {
                'categories': {category_code: {percentage, comments, question_count}},
                'overall_score': float,
                'hotel_info': dict,
                'responses': list
            }
        """
        try:
            # 1. Análisis de puntuaciones por categoría
            category_analysis = self._analyze_category_scores(assessment_data['categories'])
            
            # 2. Análisis de sentimientos en comentarios
            sentiment_analysis = self._analyze_comments_sentiment(assessment_data['categories'])
            
            # 3. Identificación de patrones de riesgo
            risk_patterns = self._identify_risk_patterns(assessment_data)
            
            # 4. Análisis de tendencias y correlaciones
            trend_analysis = self._analyze_trends_and_correlations(assessment_data)
            
            # 5. Análisis contextual avanzado
            context_analysis = self._perform_contextual_analysis(assessment_data)
            
            # 6. Generación de recomendaciones priorizadas con IA avanzada
            ai_recommendations = self._generate_enhanced_ai_recommendations(
                category_analysis, sentiment_analysis, risk_patterns, 
                trend_analysis, context_analysis, assessment_data
            )
            
            # 7. Métricas de confianza mejoradas
            confidence_metrics = self._calculate_enhanced_confidence_metrics(assessment_data)
            
            # 8. Insights predictivos
            predictive_insights = self._generate_predictive_insights(assessment_data)
            
            return {
                'ai_recommendations': ai_recommendations,
                'category_analysis': category_analysis,
                'sentiment_analysis': sentiment_analysis,
                'risk_patterns': risk_patterns,
                'trend_analysis': trend_analysis,
                'context_analysis': context_analysis,
                'predictive_insights': predictive_insights,
                'confidence_metrics': confidence_metrics,
                'generated_at': datetime.now().isoformat(),
                'analysis_version': '2.0'
            }
            
        except Exception as e:
            return {
                'error': f"Error en análisis IA: {str(e)}",
                'ai_recommendations': [],
                'category_analysis': {},
                'sentiment_analysis': {},
                'risk_patterns': {},
                'trend_analysis': {},
                'context_analysis': {},
                'predictive_insights': {},
                'confidence_metrics': {'overall': 0.0},
                'analysis_version': '2.0'
            }
    
    def _analyze_category_scores(self, categories: Dict) -> Dict:
        """Analizar puntuaciones de categorías para identificar patrones"""
        analysis = {
            'critical_categories': [],
            'improvement_areas': [],
            'strong_areas': [],
            'score_distribution': {}
        }
        
        scores = []
        for category_code, data in categories.items():
            if data.get('question_count', 0) > 0:
                percentage = data.get('percentage', 0)
                scores.append(percentage)
                
                if percentage < 40:
                    analysis['critical_categories'].append({
                        'category': category_code,
                        'name': data.get('category_name', category_code),
                        'score': percentage,
                        'severity': 'critical'
                    })
                elif percentage < 70:
                    analysis['improvement_areas'].append({
                        'category': category_code,
                        'name': data.get('category_name', category_code),
                        'score': percentage,
                        'severity': 'moderate'
                    })
                else:
                    analysis['strong_areas'].append({
                        'category': category_code,
                        'name': data.get('category_name', category_code),
                        'score': percentage,
                        'severity': 'good'
                    })
        
        if scores:
            analysis['score_distribution'] = {
                'mean': np.mean(scores),
                'std': np.std(scores),
                'min': np.min(scores),
                'max': np.max(scores),
                'variance': np.var(scores)
            }
        
        return analysis
    
    def _analyze_comments_sentiment(self, categories: Dict) -> Dict:
        """Análisis de sentimientos en comentarios de categorías"""
        sentiment_analysis = {
            'category_sentiments': {},
            'overall_sentiment': 'neutral',
            'negative_indicators': [],
            'positive_indicators': [],
            'keyword_frequency': {}
        }
        
        all_comments = []
        
        for category_code, data in categories.items():
            comments = data.get('comments', [])
            if comments:
                # Combinar todos los comentarios de la categoría
                category_text = ' '.join([c.get('comments', '') for c in comments if c.get('comments')])
                
                if category_text.strip():
                    # Análisis de sentimiento
                    blob = TextBlob(category_text)
                    sentiment_score = blob.sentiment.polarity
                    
                    sentiment_analysis['category_sentiments'][category_code] = {
                        'text': category_text[:200] + '...' if len(category_text) > 200 else category_text,
                        'sentiment_score': sentiment_score,
                        'sentiment_label': self._get_sentiment_label(sentiment_score),
                        'category_name': data.get('category_name', category_code)
                    }
                    
                    all_comments.append(category_text)
                    
                    # Identificar keywords críticos
                    self._extract_keywords(category_text, sentiment_analysis, category_code)
        
        # Sentiment general
        if all_comments:
            overall_text = ' '.join(all_comments)
            overall_blob = TextBlob(overall_text)
            overall_sentiment_score = overall_blob.sentiment.polarity
            sentiment_analysis['overall_sentiment'] = self._get_sentiment_label(overall_sentiment_score)
            sentiment_analysis['overall_sentiment_score'] = overall_sentiment_score
        
        return sentiment_analysis
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convertir score de sentimiento a etiqueta"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_keywords(self, text: str, sentiment_analysis: Dict, category_code: str):
        """Extraer keywords importantes del texto"""
        text_lower = text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if priority not in sentiment_analysis['keyword_frequency']:
                        sentiment_analysis['keyword_frequency'][priority] = []
                    
                    sentiment_analysis['keyword_frequency'][priority].append({
                        'keyword': keyword,
                        'category': category_code,
                        'context': self._extract_context(text, keyword)
                    })
    
    def _extract_context(self, text: str, keyword: str, context_window: int = 50) -> str:
        """Extraer contexto alrededor de una keyword"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        start_idx = text_lower.find(keyword_lower)
        if start_idx != -1:
            start = max(0, start_idx - context_window)
            end = min(len(text), start_idx + len(keyword) + context_window)
            return text[start:end].strip()
        return ""
    
    def _identify_risk_patterns(self, assessment_data: Dict) -> Dict:
        """Identificar patrones de riesgo usando ML"""
        patterns = {
            'high_risk_combinations': [],
            'correlation_insights': [],
            'anomaly_detection': [],
            'risk_clusters': []
        }
        
        categories = assessment_data.get('categories', {})
        
        # Crear matriz de features
        feature_matrix = []
        category_names = []
        
        for category_code, data in categories.items():
            if data.get('question_count', 0) > 0:
                features = [
                    data.get('percentage', 0),
                    data.get('question_count', 0),
                    len(data.get('comments', [])),
                    1 if data.get('percentage', 0) < 50 else 0  # Risk flag
                ]
                feature_matrix.append(features)
                category_names.append(category_code)
        
        if len(feature_matrix) >= 2:
            # Clustering para identificar patrones
            try:
                n_clusters = min(3, len(feature_matrix))
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(feature_matrix)
                
                # Analizar clusters
                for i in range(n_clusters):
                    cluster_categories = [category_names[j] for j, c in enumerate(clusters) if c == i]
                    cluster_scores = [feature_matrix[j][0] for j, c in enumerate(clusters) if c == i]
                    
                    if cluster_scores:
                        avg_score = np.mean(cluster_scores)
                        patterns['risk_clusters'].append({
                            'cluster_id': i,
                            'categories': cluster_categories,
                            'avg_score': avg_score,
                            'risk_level': 'high' if avg_score < 50 else 'medium' if avg_score < 75 else 'low'
                        })
            except Exception as e:
                patterns['clustering_error'] = str(e)
        
        # Detectar combinaciones de alto riesgo
        low_score_categories = [
            cat for cat, data in categories.items() 
            if data.get('percentage', 0) < 50 and data.get('question_count', 0) > 0
        ]
        
        if len(low_score_categories) >= 2:
            patterns['high_risk_combinations'].append({
                'categories': low_score_categories,
                'risk_description': f"Múltiples categorías críticas: {', '.join(low_score_categories)}",
                'severity': 'high'
            })
        
        return patterns
    
    def _analyze_trends_and_correlations(self, assessment_data: Dict) -> Dict:
        """Análisis de tendencias y correlaciones entre categorías"""
        trends = {
            'score_variance': 0,
            'category_correlations': [],
            'performance_gaps': [],
            'balanced_categories': [],
            'outlier_categories': []
        }
        
        categories = assessment_data.get('categories', {})
        scores = [data.get('percentage', 0) for data in categories.values() if data.get('question_count', 0) > 0]
        
        if len(scores) > 1:
            trends['score_variance'] = np.var(scores)
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            
            # Identificar categorías outlier (más de 1.5 desviaciones estándar)
            for cat_code, data in categories.items():
                if data.get('question_count', 0) > 0:
                    score = data.get('percentage', 0)
                    z_score = abs(score - mean_score) / std_score if std_score > 0 else 0
                    
                    if z_score > 1.5:
                        trends['outlier_categories'].append({
                            'category': cat_code,
                            'name': data.get('category_name', cat_code),
                            'score': score,
                            'deviation': z_score,
                            'type': 'above_average' if score > mean_score else 'below_average'
                        })
                    elif abs(score - mean_score) < std_score * 0.5:
                        trends['balanced_categories'].append({
                            'category': cat_code,
                            'name': data.get('category_name', cat_code),
                            'score': score
                        })
            
            # Identificar gaps de rendimiento
            sorted_scores = sorted([(k, v.get('percentage', 0)) for k, v in categories.items() if v.get('question_count', 0) > 0], key=lambda x: x[1])
            if len(sorted_scores) >= 2:
                worst = sorted_scores[0]
                best = sorted_scores[-1]
                gap = best[1] - worst[1]
                
                if gap > 30:  # Gap significativo
                    trends['performance_gaps'].append({
                        'worst_category': worst[0],
                        'best_category': best[0],
                        'gap_percentage': gap,
                        'severity': 'high' if gap > 50 else 'medium'
                    })
        
        return trends
    
    def _perform_contextual_analysis(self, assessment_data: Dict) -> Dict:
        """Análisis contextual avanzado de comentarios y respuestas"""
        context = {
            'urgency_indicators': [],
            'quality_indicators': [],
            'frequency_patterns': [],
            'stakeholder_mentions': [],
            'technical_issues': [],
            'procedural_gaps': []
        }
        
        # Analizar todos los comentarios
        all_comments = []
        categories = assessment_data.get('categories', {})
        
        for cat_code, data in categories.items():
            comments = data.get('comments', [])
            for comment_data in comments:
                comment_text = comment_data.get('comments', '')
                if comment_text.strip():
                    all_comments.append({
                        'text': comment_text,
                        'category': cat_code,
                        'category_name': data.get('category_name', cat_code)
                    })
        
        # Analizar patrones contextuales
        for comment in all_comments:
            text_lower = comment['text'].lower()
            
            # Indicadores de urgencia
            for indicator in self.context_patterns['urgency_indicators']:
                if indicator in text_lower:
                    context['urgency_indicators'].append({
                        'indicator': indicator,
                        'category': comment['category'],
                        'context': self._extract_context(comment['text'], indicator, 30)
                    })
            
            # Indicadores de calidad
            for indicator in self.context_patterns['quality_indicators']:
                if indicator in text_lower:
                    context['quality_indicators'].append({
                        'indicator': indicator,
                        'category': comment['category'],
                        'sentiment': 'positive' if indicator in ['excelente', 'bueno', 'satisfactorio'] else 'negative'
                    })
            
            # Identificar menciones técnicas
            technical_terms = ['sistema', 'equipo', 'tecnología', 'software', 'hardware', 'instalación']
            for term in technical_terms:
                if term in text_lower:
                    context['technical_issues'].append({
                        'term': term,
                        'category': comment['category'],
                        'context': self._extract_context(comment['text'], term, 25)
                    })
        
        return context
    
    def _generate_predictive_insights(self, assessment_data: Dict) -> Dict:
        """Generar insights predictivos basados en patrones identificados"""
        insights = {
            'risk_trajectory': 'stable',
            'improvement_potential': 0,
            'critical_timeline': None,
            'recommended_focus_areas': [],
            'success_probability': 0.5
        }
        
        overall_score = assessment_data.get('overall_score', 0)
        categories = assessment_data.get('categories', {})
        
        # Calcular potencial de mejora
        scores = [data.get('percentage', 0) for data in categories.values() if data.get('question_count', 0) > 0]
        if scores:
            current_avg = np.mean(scores)
            max_possible = 100
            insights['improvement_potential'] = max_possible - current_avg
            
            # Determinar trayectoria de riesgo
            critical_count = sum(1 for score in scores if score < 40)
            moderate_count = sum(1 for score in scores if 40 <= score < 70)
            
            if critical_count > len(scores) * 0.3:
                insights['risk_trajectory'] = 'deteriorating'
                insights['critical_timeline'] = '1-3 meses'
            elif moderate_count > len(scores) * 0.5:
                insights['risk_trajectory'] = 'concerning'
                insights['critical_timeline'] = '3-6 meses'
            else:
                insights['risk_trajectory'] = 'stable'
            
            # Probabilidad de éxito
            if current_avg > 75:
                insights['success_probability'] = 0.8
            elif current_avg > 50:
                insights['success_probability'] = 0.6
            else:
                insights['success_probability'] = 0.4
        
        # Áreas de enfoque recomendadas
        sorted_categories = sorted(
            [(k, v.get('percentage', 0)) for k, v in categories.items() if v.get('question_count', 0) > 0],
            key=lambda x: x[1]
        )
        
        if sorted_categories:
            # Enfocar en las 3 categorías más bajas
            insights['recommended_focus_areas'] = [cat[0] for cat in sorted_categories[:3]]
        
        return insights
    
    def _calculate_enhanced_confidence_metrics(self, assessment_data: Dict) -> Dict:
        """Calcular métricas de confianza mejoradas del análisis"""
        total_questions = sum(
            cat.get('question_count', 0) 
            for cat in assessment_data.get('categories', {}).values()
        )
        
        total_comments = sum(
            len(cat.get('comments', [])) 
            for cat in assessment_data.get('categories', {}).values()
        )
        
        categories_count = len([
            cat for cat in assessment_data.get('categories', {}).values()
            if cat.get('question_count', 0) > 0
        ])
        
        # Calcular confianza basada en completitud de datos
        data_completeness = min(1.0, total_questions / 60)  # Ajustado para más preguntas
        comment_richness = min(1.0, total_comments / 15)    # Más comentarios esperados
        category_coverage = min(1.0, categories_count / 8)   # Cobertura de categorías
        
        # Peso ajustado para mayor precisión
        overall_confidence = (
            data_completeness * 0.5 + 
            comment_richness * 0.3 + 
            category_coverage * 0.2
        )
        
        return {
            'overall': round(overall_confidence, 2),
            'data_completeness': round(data_completeness, 2),
            'comment_richness': round(comment_richness, 2),
            'category_coverage': round(category_coverage, 2),
            'total_questions': total_questions,
            'total_comments': total_comments,
            'categories_evaluated': categories_count,
            'recommendation_reliability': 'high' if overall_confidence > 0.75 else 'medium' if overall_confidence > 0.5 else 'low',
            'analysis_depth': 'comprehensive' if overall_confidence > 0.8 else 'standard' if overall_confidence > 0.6 else 'basic'
        }
    
    def _generate_enhanced_ai_recommendations(self, category_analysis: Dict, sentiment_analysis: Dict, 
                                           risk_patterns: Dict, trend_analysis: Dict, context_analysis: Dict,
                                           assessment_data: Dict) -> List[Dict]:
        """Generar recomendaciones inteligentes mejoradas basadas en todos los análisis"""
        recommendations = []
        
        # 1. Recomendaciones basadas en categorías críticas con contexto mejorado
        for critical_cat in category_analysis.get('critical_categories', []):
            # Buscar contexto adicional
            urgency_context = [
                u for u in context_analysis.get('urgency_indicators', [])
                if u['category'] == critical_cat['category']
            ]
            
            recommendations.append({
                'type': 'critical_improvement',
                'priority': 'high',
                'category': critical_cat['category'],
                'title': f"🚨 Acción Inmediata: {critical_cat['name']}",
                'description': f"La categoría {critical_cat['name']} presenta un puntaje crítico de {critical_cat['score']:.1f}%. " +
                             f"{'Se detectaron indicadores de urgencia en los comentarios. ' if urgency_context else ''}" +
                             "Se requiere intervención inmediata para evitar riesgos operacionales.",
                'action_items': self._generate_enhanced_category_actions(
                    critical_cat['category'], critical_cat['score'], urgency_context
                ),
                'confidence': 0.95,
                'ai_source': 'critical_analysis_v2',
                'timeline': '1-2 semanas',
                'impact_level': 'high',
                'urgency_detected': len(urgency_context) > 0
            })
        
        # 2. Recomendaciones basadas en análisis de tendencias
        for outlier in trend_analysis.get('outlier_categories', []):
            if outlier['type'] == 'below_average':
                recommendations.append({
                    'type': 'trend_based',
                    'priority': 'medium',
                    'category': outlier['category'],
                    'title': f"📊 Categoría Subdesempeño: {outlier['name']}",
                    'description': f"La categoría {outlier['name']} está {outlier['deviation']:.1f} desviaciones por debajo del promedio general. " +
                                 "Esta disparidad puede indicar problemas sistémicos específicos.",
                    'action_items': self._generate_trend_based_actions(outlier),
                    'confidence': 0.8,
                    'ai_source': 'trend_analysis',
                    'timeline': '2-4 semanas',
                    'impact_level': 'medium',
                    'statistical_significance': outlier['deviation']
                })
        
        # 3. Recomendaciones basadas en gaps de rendimiento
        for gap in trend_analysis.get('performance_gaps', []):
            recommendations.append({
                'type': 'performance_gap',
                'priority': 'high' if gap['severity'] == 'high' else 'medium',
                'category': 'multiple',
                'title': f"⚖️ Gap de Rendimiento Significativo",
                'description': f"Se detectó una brecha de {gap['gap_percentage']:.1f}% entre las categorías de mejor y peor rendimiento. " +
                             "Esta disparidad sugiere desequilibrios en la aplicación de recursos y atención.",
                'action_items': self._generate_gap_closure_actions(gap),
                'confidence': 0.85,
                'ai_source': 'gap_analysis',
                'timeline': '1-2 meses',
                'impact_level': gap['severity'],
                'affected_categories': [gap['worst_category'], gap['best_category']]
            })
        
        # 4. Recomendaciones basadas en análisis contextual
        technical_issues = context_analysis.get('technical_issues', [])
        if len(technical_issues) > 2:  # Si hay múltiples menciones técnicas
            recommendations.append({
                'type': 'technical_focus',
                'priority': 'medium',
                'category': 'infrastructure',
                'title': f"🔧 Enfoque en Infraestructura Técnica",
                'description': f"Se identificaron {len(technical_issues)} menciones de aspectos técnicos en los comentarios. " +
                             "Esto sugiere que la infraestructura tecnológica requiere atención especial.",
                'action_items': self._generate_technical_actions(technical_issues),
                'confidence': 0.75,
                'ai_source': 'contextual_analysis',
                'timeline': '3-6 semanas',
                'impact_level': 'medium',
                'technical_mentions': len(technical_issues)
            })
        
        # 5. Recomendaciones predictivas mejoradas
        predictive_recs = self._generate_enhanced_predictive_recommendations(assessment_data, trend_analysis)
        recommendations.extend(predictive_recs)
        
        # 6. Recomendaciones basadas en sentimientos negativos con contexto
        for category_code, sentiment_data in sentiment_analysis.get('category_sentiments', {}).items():
            if sentiment_data['sentiment_label'] == 'negative':
                recommendations.append({
                    'type': 'sentiment_based',
                    'priority': 'medium',
                    'category': category_code,
                    'title': f"💬 Atención a Feedback: {sentiment_data['category_name']}",
                    'description': f"Los comentarios en {sentiment_data['category_name']} reflejan preocupaciones específicas " +
                                 f"(sentimiento: {sentiment_data['sentiment_score']:.2f}). Es importante abordar estas percepciones " +
                                 "para mejorar la satisfacción general.",
                    'action_items': self._generate_enhanced_sentiment_actions(sentiment_data),
                    'confidence': 0.7,
                    'ai_source': 'sentiment_analysis_v2',
                    'comment_preview': sentiment_data['text'][:150] + '...',
                    'timeline': '2-3 semanas',
                    'impact_level': 'medium',
                    'sentiment_score': sentiment_data['sentiment_score']
                })
        
        # 7. Recomendaciones basadas en keywords críticos con mejor contexto
        critical_keywords = sentiment_analysis.get('keyword_frequency', {}).get('critical', [])
        if critical_keywords:
            recommendations.append({
                'type': 'keyword_based',
                'priority': 'high',
                'category': 'multiple',
                'title': f"🎯 Temas Críticos Recurrentes",
                'description': f"Se detectaron {len(critical_keywords)} menciones de temas críticos distribuidas en múltiples categorías. " +
                             "Esta recurrencia indica problemas sistémicos que requieren atención coordinada.",
                'action_items': self._generate_enhanced_keyword_actions(critical_keywords),
                'confidence': 0.8,
                'ai_source': 'keyword_analysis_v2',
                'keywords': [kw['keyword'] for kw in critical_keywords[:5]],
                'timeline': '1-3 semanas',
                'impact_level': 'high',
                'recurrence_level': len(critical_keywords)
            })
        
        # Ordenar por prioridad, confianza e impacto
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(
            key=lambda x: (
                priority_order.get(x['priority'], 0),
                x['confidence'],
                1 if x.get('impact_level') == 'high' else 0.5
            ), 
            reverse=True
        )
        
        return recommendations[:12]  # Aumentar a top 12 recomendaciones
    
    def _generate_category_actions(self, category: str, score: float) -> List[str]:
        """Generar acciones específicas para una categoría"""
        actions = []
        
        category_actions = {
            'physical_security': [
                "Revisar y mejorar sistemas de vigilancia",
                "Actualizar protocolos de acceso físico",
                "Inspeccionar cerraduras y sistemas de seguridad"
            ],
            'access_control': [
                "Implementar sistema de llaves maestras",
                "Revisar protocolos de acceso de huéspedes",
                "Capacitar personal en control de acceso"
            ],
            'emergency_procedures': [
                "Actualizar planes de evacuación",
                "Realizar simulacros de emergencia",
                "Revisar señalización de emergencia"
            ],
            'staff_training': [
                "Implementar programa de capacitación en seguridad",
                "Establecer protocolos de respuesta a incidentes",
                "Crear manual de procedimientos"
            ]
        }
        
        if category in category_actions:
            actions = category_actions[category]
        else:
            actions = [
                f"Revisar procedimientos en {category}",
                f"Capacitar personal en {category}",
                f"Implementar mejoras en {category}"
            ]
        
        # Agregar acciones basadas en severidad
        if score < 30:
            actions.insert(0, "⚠️ ACCIÓN INMEDIATA REQUERIDA")
        elif score < 50:
            actions.insert(0, "📋 Plan de mejora a corto plazo")
        
        return actions
    
    def _generate_sentiment_actions(self, sentiment_data: Dict) -> List[str]:
        """Generar acciones basadas en análisis de sentimiento"""
        return [
            "Revisar comentarios específicos para identificar problemas",
            "Implementar mejoras basadas en feedback recibido",
            "Hacer seguimiento con el personal responsable",
            "Crear plan de acción específico para esta área"
        ]
    
    def _generate_pattern_actions(self, risk_cluster: Dict) -> List[str]:
        """Generar acciones basadas en patrones de riesgo"""
        return [
            f"Revisar de forma integral las {len(risk_cluster['categories'])} categorías identificadas",
            "Implementar enfoque holístico de mejora",
            "Asignar recursos adicionales a estas áreas",
            "Establecer métricas de seguimiento específicas"
        ]
    
    def _generate_keyword_actions(self, keywords: List[Dict]) -> List[str]:
        """Generar acciones basadas en keywords críticos"""
        return [
            "Investigar problemas específicos mencionados en comentarios",
            "Priorizar resolución de temas críticos identificados",
            "Implementar monitoreo continuo de estas áreas",
            "Crear protocolo de respuesta para temas recurrentes"
        ]
    
    def _generate_predictive_recommendations(self, assessment_data: Dict) -> List[Dict]:
        """Generar recomendaciones predictivas basadas en tendencias"""
        recommendations = []
        
        overall_score = assessment_data.get('overall_score', 0)
        
        # Recomendación predictiva basada en score general
        if overall_score < 60:
            recommendations.append({
                'type': 'predictive',
                'priority': 'medium',
                'category': 'general',
                'title': "Riesgo de Degradación Continua",
                'description': f"Con un puntaje general de {overall_score:.1f}%, existe riesgo de deterioro progresivo sin intervención.",
                'action_items': [
                    "Establecer programa de mejora continua",
                    "Implementar métricas de seguimiento mensual",
                    "Crear comité de seguridad hotelera"
                ],
                'confidence': 0.6,
                'ai_source': 'predictive_analysis'
            })
        
        return recommendations
    
    def _calculate_confidence_metrics(self, assessment_data: Dict) -> Dict:
        """Calcular métricas de confianza del análisis"""
        total_questions = sum(
            cat.get('question_count', 0) 
            for cat in assessment_data.get('categories', {}).values()
        )
        
        total_comments = sum(
            len(cat.get('comments', [])) 
            for cat in assessment_data.get('categories', {}).values()
        )
        
        # Calcular confianza basada en completitud de datos
        data_completeness = min(1.0, total_questions / 50)  # Asumiendo 50 preguntas ideales
        comment_richness = min(1.0, total_comments / 10)    # Asumiendo 10 comentarios ideales
        
        overall_confidence = (data_completeness * 0.7 + comment_richness * 0.3)
        
        return {
            'overall': round(overall_confidence, 2),
            'data_completeness': round(data_completeness, 2),
            'comment_richness': round(comment_richness, 2),
            'total_questions': total_questions,
            'total_comments': total_comments,
            'recommendation_reliability': 'high' if overall_confidence > 0.7 else 'medium' if overall_confidence > 0.4 else 'low'
        }
    
    # =============================================
    # MÉTODOS MEJORADOS PARA ANÁLISIS AVANZADO
    # =============================================
    
    def _generate_enhanced_category_actions(self, category: str, score: float, urgency_context: List[Dict]) -> List[str]:
        """Generar acciones específicas mejoradas para una categoría"""
        actions = []
        
        # Acciones específicas por categoría con mayor detalle
        enhanced_category_actions = {
            'seguridad_perimetral': [
                "Inspeccionar y reforzar cercas y barreras perimetrales",
                "Revisar iluminación exterior y puntos ciegos",
                "Actualizar sistema de videovigilancia perimetral",
                "Implementar controles de acceso vehicular y peatonal"
            ],
            'seguridad_fisica': [
                "Auditar sistemas de cerraduras y llaves maestras",
                "Evaluar resistencia física de puertas y ventanas",
                "Revisar protocolos de acceso a áreas restringidas",
                "Actualizar sistemas de detección de intrusión"
            ],
            'gestion_humana': [
                "Desarrollar programa integral de capacitación en seguridad",
                "Establecer protocolos claros de respuesta a incidentes",
                "Implementar sistema de verificación de antecedentes",
                "Crear manual actualizado de procedimientos de seguridad"
            ],
            'prevencion_incendios': [
                "Inspeccionar y mantener sistemas de detección de humo",
                "Revisar extintores y sistemas de supresión",
                "Actualizar rutas de evacuación y señalización",
                "Realizar simulacros de evacuación regulares"
            ],
            'comunicaciones': [
                "Evaluar sistemas de comunicación de emergencia",
                "Implementar protocolos de notificación escalada",
                "Revisar equipos de radio y comunicación interna",
                "Establecer canales de comunicación con autoridades"
            ]
        }
        
        # Usar acciones específicas o genéricas
        if category in enhanced_category_actions:
            actions = enhanced_category_actions[category].copy()
        else:
            actions = [
                f"Realizar auditoría completa en {category.replace('_', ' ')}",
                f"Desarrollar plan de mejora específico para {category.replace('_', ' ')}",
                f"Capacitar personal especializado en {category.replace('_', ' ')}",
                f"Implementar métricas de seguimiento en {category.replace('_', ' ')}"
            ]
        
        # Agregar acciones basadas en severidad y contexto
        if score < 25:
            actions.insert(0, "🚨 INTERVENCIÓN INMEDIATA - Suspender operaciones hasta resolver")
        elif score < 40:
            actions.insert(0, "⚠️ ACCIÓN URGENTE - Implementar medidas temporales inmediatas")
        elif score < 60:
            actions.insert(0, "📋 MEJORA PRIORITARIA - Desarrollar plan de acción en 48 horas")
        
        # Agregar acciones específicas si hay contexto de urgencia
        if urgency_context:
            actions.insert(-1, "🔍 Investigar inmediatamente las preocupaciones específicas mencionadas")
            actions.insert(-1, "📞 Contactar con personal responsable para clarificaciones urgentes")
        
        return actions
    
    def _generate_trend_based_actions(self, outlier: Dict) -> List[str]:
        """Generar acciones basadas en análisis de tendencias"""
        return [
            f"Realizar análisis comparativo detallado de {outlier['name']}",
            "Identificar factores específicos que causan el bajo rendimiento",
            "Implementar benchmarking con categorías de mejor desempeño",
            f"Asignar recursos adicionales específicos para {outlier['name']}",
            "Establecer métricas de seguimiento quincenal",
            "Crear grupo de trabajo especializado para esta categoría"
        ]
    
    def _generate_gap_closure_actions(self, gap: Dict) -> List[str]:
        """Generar acciones para cerrar gaps de rendimiento"""
        return [
            "Realizar transferencia de mejores prácticas entre categorías",
            f"Analizar factores de éxito en la categoría de mejor rendimiento",
            f"Implementar programa de nivelación acelerada",
            "Establecer mentorías cruzadas entre equipos responsables",
            "Crear plan de redistribución de recursos",
            f"Implementar sistema de monitoreo comparativo continuo"
        ]
    
    def _generate_technical_actions(self, technical_issues: List[Dict]) -> List[str]:
        """Generar acciones para problemas técnicos identificados"""
        return [
            "Realizar auditoría técnica completa de infraestructura",
            "Evaluar y actualizar sistemas tecnológicos obsoletos",
            "Implementar programa de mantenimiento preventivo",
            "Capacitar personal técnico en nuevas tecnologías",
            "Establecer presupuesto para upgrades tecnológicos",
            "Crear protocolo de evaluación tecnológica periódica"
        ]
    
    def _generate_enhanced_sentiment_actions(self, sentiment_data: Dict) -> List[str]:
        """Generar acciones mejoradas basadas en análisis de sentimiento"""
        return [
            "Realizar entrevistas detalladas con personal involucrado",
            "Implementar sistema de feedback continuo",
            "Crear plan de comunicación para abordar preocupaciones",
            "Establecer métricas de satisfacción del personal",
            "Desarrollar programa de reconocimiento y motivación",
            f"Hacer seguimiento específico a comentarios negativos en {sentiment_data['category_name']}"
        ]
    
    def _generate_enhanced_keyword_actions(self, keywords: List[Dict]) -> List[str]:
        """Generar acciones mejoradas basadas en keywords críticos"""
        return [
            "Crear matriz de temas críticos y responsabilidades",
            "Implementar sistema de escalamiento automático",
            "Establecer protocolos de respuesta rápida",
            "Desarrollar alertas tempranas para temas recurrentes",
            "Crear base de conocimiento de soluciones probadas",
            "Implementar revisión ejecutiva semanal de temas críticos"
        ]
    
    def _generate_enhanced_predictive_recommendations(self, assessment_data: Dict, trend_analysis: Dict) -> List[Dict]:
        """Generar recomendaciones predictivas mejoradas"""
        recommendations = []
        
        overall_score = assessment_data.get('overall_score', 0)
        score_variance = trend_analysis.get('score_variance', 0)
        
        # Recomendación predictiva basada en varianza
        if score_variance > 400:  # Alta variabilidad
            recommendations.append({
                'type': 'predictive_variance',
                'priority': 'medium',
                'category': 'management',
                'title': '📈 Riesgo por Alta Variabilidad',
                'description': f'La alta variabilidad en puntuaciones ({score_variance:.0f}) indica inconsistencia en la aplicación de estándares.',
                'action_items': [
                    "Estandarizar procesos y procedimientos",
                    "Implementar sistema de calidad uniforme",
                    "Crear protocolos de supervisión consistente",
                    "Establecer métricas de control de calidad"
                ],
                'confidence': 0.75,
                'ai_source': 'predictive_variance',
                'timeline': '4-6 semanas',
                'impact_level': 'medium',
                'variance_level': score_variance
            })
        
        # Recomendación predictiva de deterioro
        if overall_score < 65:
            recommendations.append({
                'type': 'predictive_deterioration',
                'priority': 'high',
                'category': 'strategic',
                'title': '⚠️ Riesgo de Deterioro Progresivo',
                'description': f'Con un puntaje general de {overall_score:.1f}%, existe alto riesgo de deterioro sin intervención inmediata.',
                'action_items': [
                    "Desarrollar plan de recuperación acelerada",
                    "Implementar supervisión intensiva",
                    "Establecer métricas de alerta temprana",
                    "Crear comité de crisis de seguridad",
                    "Asignar recursos de emergencia"
                ],
                'confidence': 0.85,
                'ai_source': 'predictive_deterioration',
                'timeline': '1-2 semanas',
                'impact_level': 'high',
                'risk_level': 'critical'
            })
        
        return recommendations

    def generate_critical_categories_recommendations(self, critical_categories: List[Dict]) -> Dict:
        """
        Genera recomendaciones específicas con IA/ML para las categorías más críticas
        
        Args:
            critical_categories: Lista de las 5 categorías más críticas con sus datos
            
        Returns:
            Dict con recomendaciones personalizadas por categoría
        """
        recommendations = {}
        
        # Base de conocimiento de recomendaciones por categoría
        category_recommendations = {
            'seguridad_eventos': {
                'immediate': [
                    'Implementar protocolos de evacuación específicos para eventos',
                    'Capacitar personal de seguridad en manejo de multitudes',
                    'Instalar sistemas de comunicación de emergencia en áreas de eventos'
                ],
                'short_term': [
                    'Desarrollar plan de contingencia para diferentes tipos de eventos',
                    'Establecer puntos de control de acceso adicionales',
                    'Crear sistema de identificación para personal autorizado'
                ],
                'long_term': [
                    'Inversión en tecnología de detección de amenazas',
                    'Certificación en seguridad para eventos masivos',
                    'Implementar IA para análisis de comportamiento en tiempo real'
                ]
            },
            'seguridad_ayb': {
                'immediate': [
                    'Implementar controles de acceso estrictos en cocinas',
                    'Capacitación intensiva en manejo seguro de alimentos',
                    'Instalación de cámaras de seguridad en áreas de almacenamiento'
                ],
                'short_term': [
                    'Desarrollar protocolos HACCP robustos',
                    'Implementar sistema de trazabilidad de alimentos',
                    'Crear checklist de seguridad diario para F&B'
                ],
                'long_term': [
                    'Automatización de sistemas de control de temperatura',
                    'Integración con sistemas de gestión de inventario',
                    'Certificación en estándares internacionales de seguridad alimentaria'
                ]
            },
            'seguridad_externa': {
                'immediate': [
                    'Reforzar perímetro de seguridad con iluminación LED',
                    'Implementar patrullajes regulares 24/7',
                    'Instalar cámaras con visión nocturna en puntos ciegos'
                ],
                'short_term': [
                    'Integrar sistema de detección de intrusos con IA',
                    'Establecer protocolos de coordinación con autoridades locales',
                    'Crear zones de seguridad graduales alrededor del hotel'
                ],
                'long_term': [
                    'Implementar reconocimiento facial para acceso vehicular',
                    'Desarrollar centro de comando y control integrado',
                    'Inversión en drones de seguridad automatizados'
                ]
            },
            'gestion_emergencias': {
                'immediate': [
                    'Actualizar planes de evacuación con rutas alternativas',
                    'Capacitar todo el personal en primeros auxilios básicos',
                    'Verificar funcionamiento de sistemas de alarma semanalmente'
                ],
                'short_term': [
                    'Implementar simulacros mensuales de emergencia',
                    'Crear brigadas especializadas por tipo de emergencia',
                    'Establecer comunicación directa con servicios de emergencia'
                ],
                'long_term': [
                    'Desarrollar sistema predictivo de riesgos meteorológicos',
                    'Implementar centro de crisis con tecnología avanzada',
                    'Certificación internacional en gestión de emergencias'
                ]
            },
            'areas_internas': {
                'immediate': [
                    'Instalar cerraduras electrónicas en áreas restringidas',
                    'Implementar sistema de tarjetas de acceso por niveles',
                    'Capacitar personal en protocolos de seguridad interna'
                ],
                'short_term': [
                    'Desarrollar sistema de monitoreo de movimientos internos',
                    'Crear auditorías de seguridad internas mensuales',
                    'Implementar controles de acceso biométricos'
                ],
                'long_term': [
                    'Integrar IA para detección de comportamientos anómalos',
                    'Desarrollar gemelo digital para optimización de seguridad',
                    'Implementar IoT para monitoreo en tiempo real'
                ]
            }
        }
        
        # Generar recomendaciones personalizadas para cada categoría crítica
        for i, category in enumerate(critical_categories[:5]):
            category_key = self._normalize_category_name(category['name'])
            percentage = category['percentage']
            
            # Determinar nivel de criticidad
            if percentage < 30:
                priority_level = 'emergency'
                urgency = 'Acción inmediata requerida'
                timeline = '24-48 horas'
            elif percentage < 50:
                priority_level = 'critical'
                urgency = 'Alta prioridad'
                timeline = '1-2 semanas'
            else:
                priority_level = 'moderate'
                urgency = 'Prioridad media'
                timeline = '1 mes'
            
            # Obtener recomendaciones base
            base_recommendations = category_recommendations.get(category_key, {
                'immediate': ['Evaluar situación actual y definir plan de acción'],
                'short_term': ['Desarrollar estrategia específica para esta categoría'],
                'long_term': ['Implementar mejoras continuas y monitoreo']
            })
            
            # Generar recomendaciones personalizadas usando IA
            ai_recommendations = self._generate_ai_recommendations(category, percentage, i+1)
            
            recommendations[category['code']] = {
                'category_name': category['name'],
                'current_score': f"{percentage}%",
                'priority_level': priority_level,
                'urgency': urgency,
                'timeline': timeline,
                'ranking': i + 1,
                'immediate_actions': base_recommendations['immediate'],
                'short_term_actions': base_recommendations['short_term'],
                'long_term_actions': base_recommendations['long_term'],
                'ai_insights': ai_recommendations,
                'expected_improvement': self._calculate_expected_improvement(percentage),
                'investment_level': self._estimate_investment_level(percentage),
                'risk_factors': self._identify_risk_factors(category['name'], percentage)
            }
        
        return recommendations
    
    def _normalize_category_name(self, category_name: str) -> str:
        """Normaliza el nombre de la categoría para mapeo"""
        name_lower = category_name.lower()
        
        if 'evento' in name_lower:
            return 'seguridad_eventos'
        elif 'ayb' in name_lower or 'alimento' in name_lower or 'bebida' in name_lower:
            return 'seguridad_ayb'
        elif 'externa' in name_lower or 'perímetro' in name_lower:
            return 'seguridad_externa'
        elif 'emergencia' in name_lower or 'gestión' in name_lower:
            return 'gestion_emergencias'
        elif 'interna' in name_lower or 'área' in name_lower:
            return 'areas_internas'
        else:
            return 'general'
    
    def _generate_ai_recommendations(self, category: Dict, percentage: float, ranking: int) -> List[str]:
        """Genera recomendaciones usando lógica de IA basada en datos"""
        ai_insights = []
        
        # Análisis basado en el ranking
        if ranking == 1:
            ai_insights.append(f"🚨 PRIORIDAD MÁXIMA: Esta es la categoría más crítica del hotel")
        elif ranking <= 3:
            ai_insights.append(f"⚠️ ALTA PRIORIDAD: Entre las 3 categorías más problemáticas")
        
        # Análisis basado en porcentaje
        if percentage < 30:
            ai_insights.append("📉 Puntuación extremadamente baja - Requiere intervención inmediata")
            ai_insights.append("🔴 Riesgo crítico para la operación del hotel")
        elif percentage < 40:
            ai_insights.append("📊 Puntuación muy por debajo del estándar aceptable")
            ai_insights.append("🟡 Impacto significativo en la seguridad general")
        elif percentage < 50:
            ai_insights.append("📈 Oportunidad de mejora sustancial identificada")
            ai_insights.append("🔵 Inversión estratégica recomendada")
        
        # Recomendaciones de ML basadas en patrones
        if percentage < 35:
            ai_insights.append("🤖 IA recomienda: Plan de recuperación acelerado en 30 días")
        
        ai_insights.append(f"📊 Potencial de mejora estimado: {100 - percentage:.1f} puntos porcentuales")
        
        return ai_insights
    
    def _calculate_expected_improvement(self, current_percentage: float) -> Dict:
        """Calcula mejoras esperadas basadas en IA"""
        if current_percentage < 30:
            return {
                '30_days': f"{current_percentage + 15:.1f}%",
                '90_days': f"{current_percentage + 30:.1f}%",
                '180_days': f"{min(current_percentage + 45, 85):.1f}%"
            }
        elif current_percentage < 50:
            return {
                '30_days': f"{current_percentage + 10:.1f}%",
                '90_days': f"{current_percentage + 20:.1f}%",
                '180_days': f"{min(current_percentage + 35, 85):.1f}%"
            }
        else:
            return {
                '30_days': f"{current_percentage + 5:.1f}%",
                '90_days': f"{current_percentage + 12:.1f}%",
                '180_days': f"{min(current_percentage + 20, 85):.1f}%"
            }
    
    def _estimate_investment_level(self, percentage: float) -> str:
        """Estima el nivel de inversión requerido"""
        if percentage < 30:
            return "Alto - Inversión significativa requerida"
        elif percentage < 40:
            return "Medio-Alto - Inversión moderada necesaria"
        elif percentage < 50:
            return "Medio - Inversión estratégica recomendada"
        else:
            return "Bajo-Medio - Ajustes y mejoras puntuales"
    
    def _identify_risk_factors(self, category_name: str, percentage: float) -> List[str]:
        """Identifica factores de riesgo específicos"""
        risk_factors = []
        
        if percentage < 40:
            risk_factors.append("Riesgo operacional elevado")
            risk_factors.append("Posible impacto en satisfacción del huésped")
        
        if percentage < 30:
            risk_factors.append("Riesgo de incumplimiento normativo")
            risk_factors.append("Exposición a responsabilidad legal")
        
        # Riesgos específicos por categoría
        category_lower = category_name.lower()
        if 'evento' in category_lower and percentage < 40:
            risk_factors.append("Riesgo de incidentes en eventos masivos")
        elif 'emergencia' in category_lower and percentage < 40:
            risk_factors.append("Capacidad de respuesta a emergencias comprometida")
        elif 'externa' in category_lower and percentage < 40:
            risk_factors.append("Vulnerabilidad del perímetro de seguridad")
        
        return risk_factors
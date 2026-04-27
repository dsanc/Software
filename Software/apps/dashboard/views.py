from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home_view(request):
    """Vista principal del dashboard con módulos y planes"""
    try:
        from apps.subscriptions.models import Module, Plan
        from apps.subscriptions.services import SubscriptionService
        
        # Obtener módulos activos con sus planes
        modules = Module.objects.filter(is_active=True).prefetch_related(
            'plans__plan_type'
        ).order_by('order')
        
        # Ordenar planes por order y precio para cada módulo
        for module in modules:
            plans_list = list(module.plans.filter(is_active=True).order_by('order', 'monthly_price'))
            module.ordered_plans = plans_list
            module.first_plan = plans_list[0] if plans_list else None
            module.top_plan = plans_list[-1] if plans_list else None
        
        # Si el usuario está autenticado, obtener sus suscripciones
        user_subscriptions = {}
        if request.user.is_authenticated:
            for module in modules:
                subscription = SubscriptionService.get_user_subscriptions(
                    request.user, module.name
                ).first()
                if subscription:
                    user_subscriptions[module.name] = subscription
        
        context = {
            'title': 'Dashboard - Proyecto Django Modular',
            'modules': modules,
            'user_subscriptions': user_subscriptions,
            'has_subscriptions': len(user_subscriptions) > 0,
        }
        
    except ImportError:
        # Si el módulo de subscriptions no está disponible
        context = {
            'title': 'Dashboard - Proyecto Django Modular',
            'modules': [],
            'user_subscriptions': {},
            'has_subscriptions': False,
        }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def dashboard_view(request):
    """Vista del dashboard para usuarios autenticados"""
    # Validación explícita del usuario autenticado
    if not request.user.is_authenticated:
        return redirect('users:login')

    # Si el usuario es evaluador, redirigir a su propio dashboard
    is_evaluador = False
    try:
        from apps.evaluadores.models import Evaluador
        evaluador_qs = Evaluador.objects.filter(
            usuario_evaluador=request.user,
            is_active=True
        )
        perfiles_activos = evaluador_qs.filter(estado='active')
        if perfiles_activos.exists():
            count = perfiles_activos.count()
            if count == 1:
                # Un solo usuario principal: ir directo al dashboard del evaluador
                perfil = perfiles_activos.select_related('usuario_principal').first()
                return redirect(
                    'evaluadores:dashboard_evaluador',
                    usuario_principal_id=perfil.usuario_principal_id
                )
            else:
                # Múltiples usuarios principales: elegir desde mi perfil
                return redirect('evaluadores:mi_perfil_evaluador')
        # Puede ser evaluador pendiente — igual restringir la vista de suscripciones
        is_evaluador = evaluador_qs.exists()
    except Exception:
        pass
    
    try:
        from apps.subscriptions.models import Module, Subscription
        
        # Obtener suscripciones activas del usuario autenticado únicamente
        user_subscriptions = Subscription.objects.filter(
            user=request.user,
            status='active'
        ).select_related('plan', 'plan__module', 'plan__plan_type').order_by(
            'plan__module__order', 'plan__order'
        )
        
        # Agrupar suscripciones por módulo y agregar estadísticas de uso
        subscriptions_by_module = {}
        for subscription in user_subscriptions:
            module_name = subscription.plan.module.name
            if module_name not in subscriptions_by_module:
                subscriptions_by_module[module_name] = []
            
            # Agregar estadísticas de uso a la suscripción
            try:
                from apps.subscriptions.usage_tracker import get_subscription_usage_stats
                # Validar que la suscripción pertenece al usuario autenticado
                if subscription.user_id != request.user.id:
                    raise PermissionError("Acceso no autorizado a suscripción")
                usage_stats = get_subscription_usage_stats(request.user, subscription)
                subscription.usage_stats = usage_stats
            except ImportError:
                subscription.usage_stats = {}
            except PermissionError:
                # Log de seguridad podría ir aquí
                subscription.usage_stats = {}
            
            subscriptions_by_module[module_name].append(subscription)
        
        # Calcular estadísticas - solo del usuario autenticado
        from django.utils import timezone
        total_modules = len(subscriptions_by_module)
        expiring_soon = user_subscriptions.filter(
            end_date__lte=timezone.now() + timezone.timedelta(days=30)
        ).count()
        trial_subscriptions = user_subscriptions.filter(is_trial=True).count()
        
        # Estadísticas de uso global - validar que pertenecen al usuario
        total_reports_used = 0
        total_reports_limit = 0
        total_evaluations = 0
        
        for subscription in user_subscriptions:
            # Validación adicional de seguridad
            if subscription.user_id != request.user.id:
                continue  # Saltar suscripciones que no pertenecen al usuario
            
            if hasattr(subscription, 'usage_stats') and subscription.usage_stats:
                total_reports_used += subscription.usage_stats.get('reports_used', 0)
                if subscription.usage_stats.get('reports_limit', -1) != -1:
                    total_reports_limit += subscription.usage_stats.get('reports_limit', 0)
                total_evaluations += subscription.usage_stats.get('evaluations_count', 0)
        
        # Obtener datos de evaluadores y actividades recientes - solo del usuario autenticado
        try:
            from apps.evaluadores.models import Evaluador, EvaluatorActivity
            from django.contrib.contenttypes.models import ContentType
            from django.utils import timezone
            from datetime import timedelta
            from django.db.models import Count
            
            # Obtener evaluadores del usuario principal autenticado únicamente
            user_evaluadores = Evaluador.objects.filter(
                usuario_principal=request.user,
                estado='active'
            ).select_related('usuario_evaluador')
            
            # Obtener actividades recientes de los evaluadores del usuario principal autenticado
            recent_evaluator_activities = EvaluatorActivity.objects.select_related(
                'evaluador', 'evaluador__usuario_evaluador'
            ).filter(
                evaluador__usuario_principal=request.user
            ).order_by('-created_at')[:5]
            
            # Estadísticas de actividades del día - solo del usuario autenticado
            today = timezone.now().date()
            daily_activities_count = EvaluatorActivity.objects.filter(
                created_at__date=today,
                evaluador__usuario_principal=request.user
            ).count()
            
            weekly_activities_count = EvaluatorActivity.objects.filter(
                created_at__date__gte=today - timedelta(days=7),
                evaluador__usuario_principal=request.user
            ).count()
            
            monthly_activities_count = EvaluatorActivity.objects.filter(
                created_at__date__gte=today - timedelta(days=30),
                evaluador__usuario_principal=request.user
            ).count()
            
            completed_evaluations_today = EvaluatorActivity.objects.filter(
                created_at__date=today,
                action='evaluation_completed',
                evaluador__usuario_principal=request.user
            ).count()
            
            in_progress_evaluations = EvaluatorActivity.objects.filter(
                status='in_progress',
                evaluador__usuario_principal=request.user
            ).count()
            
            # Evaluadores activos del usuario principal autenticado (con actividad en los últimos 7 días)
            active_evaluators_today = Evaluador.objects.filter(
                usuario_principal=request.user,
                activities__created_at__gte=timezone.now() - timedelta(days=7)
            ).distinct().count()
            
            total_evaluators = Evaluador.objects.filter(
                usuario_principal=request.user,
                estado='active'
            ).count()
            
        except ImportError:
            recent_evaluator_activities = []
            daily_activities_count = 0
            weekly_activities_count = 0
            monthly_activities_count = 0
            completed_evaluations_today = 0
            in_progress_evaluations = 0
            active_evaluators_today = 0
            total_evaluators = 0

        # ── Métricas globales Risk Hoteles (todos los evaluadores + propias) ─────
        dash_hoteles = {
            'tiene_datos': False,
            'evaluaciones_por_tipo': [],
            'evaluaciones_tipo_max': 1,
            'hoteles_por_categoria': [],
            'geo_dist': [],
            'tendencia_meses': [],
            'tendencia_max': 1,
            'categorias_ranking': [],
            'categoria_mas_debil': None,
            'categoria_mas_fuerte': None,
            # Métricas nuevas
            'riesgo_dist': [],
            'riesgo_max': 1,
            'funnel_estados': [],
            'funnel_max': 1,
            'hoteles_sin_cobertura': [],
            'pct_cobertura': 0,
            'total_hoteles': 0,
            'total_hoteles_eval': 0,
            'histograma': [],
            'histograma_max': 1,
            'gauge_30d': 0,
            'tiempo_promedio_dias': None,
        }
        hoteles_sin_reevaluar = []
        pendientes_revision = []
        mejor_hotel_global = None
        peor_hotel_global = None

        try:
            from apps.risk_hoteles.models import Hotel, SecurityAssessment, SecurityCategoryScore
            from django.db.models import Count, Avg, Max, Q
            from django.db.models.functions import TruncMonth
            from datetime import timedelta
            from django.utils import timezone as tz_rh

            # Base: todas las evaluaciones sobre hoteles del usuario principal
            all_assessments = SecurityAssessment.objects.filter(
                hotel__owner=request.user
            ).select_related('hotel')

            total_all = all_assessments.count()
            dash_hoteles['tiene_datos'] = total_all > 0

            if dash_hoteles['tiene_datos']:
                # -- Distribución por tipo --
                tipo_map = {
                    'inicial':   ('Inicial',   'primary'),
                    'periodico': ('Periódico', 'success'),
                    'especial':  ('Especial',  'warning'),
                    'auditoria': ('Auditoría', 'danger'),
                }
                tipo_counts = (
                    all_assessments
                    .values('assessment_type')
                    .annotate(total=Count('id'))
                )
                tipo_index = {r['assessment_type']: r['total'] for r in tipo_counts}
                dash_hoteles['evaluaciones_por_tipo'] = [
                    {'tipo': k, 'label': v[0], 'color': v[1], 'total': tipo_index.get(k, 0)}
                    for k, v in tipo_map.items() if tipo_index.get(k, 0) > 0
                ]
                dash_hoteles['evaluaciones_tipo_max'] = max(
                    (e['total'] for e in dash_hoteles['evaluaciones_por_tipo']), default=1
                )

                # -- Distribución por categoría de hotel --
                hoteles_ids = all_assessments.values_list('hotel_id', flat=True).distinct()
                hoteles_eval = Hotel.objects.filter(id__in=hoteles_ids)
                total_hoteles_eval = hoteles_eval.count()

                cat_map = {
                    '1_star': '1 Estrella', '2_star': '2 Estrellas',
                    '3_star': '3 Estrellas', '4_star': '4 Estrellas',
                    '5_star': '5 Estrellas', 'luxury': 'Lujo',
                }
                cat_counts = (
                    hoteles_eval
                    .values('category')
                    .annotate(total=Count('id'))
                    .order_by('category')
                )
                dash_hoteles['hoteles_por_categoria'] = [
                    {'cat': r['category'], 'label': cat_map.get(r['category'], r['category']), 'total': r['total']}
                    for r in cat_counts
                ]
                dash_hoteles['total_hoteles_eval'] = total_hoteles_eval

                # -- Distribución geográfica --
                dash_hoteles['geo_dist'] = list(
                    hoteles_eval
                    .values('city', 'country')
                    .annotate(total=Count('id'))
                    .order_by('-total')[:10]
                )

                # -- Alertas: hoteles sin re-evaluar (>60 días) --
                sixty_ago = tz_rh.now() - timedelta(days=60)
                hoteles_sin_reevaluar = list(
                    Hotel.objects.filter(owner=request.user, id__in=hoteles_ids)
                    .annotate(ultima_eval=Max('security_assessments__assessment_date'))
                    .filter(ultima_eval__lt=sixty_ago)
                    .order_by('ultima_eval')[:10]
                )

                # -- Alertas: evaluaciones completadas pendientes de revisión --
                pendientes_revision = list(
                    all_assessments
                    .filter(status='completed')
                    .select_related('hotel')
                    .order_by('-completed_at')[:10]
                )

                # -- Tendencia mensual (últimos 6 meses) --
                six_months_ago = tz_rh.now() - timedelta(days=180)
                tendencia_raw = (
                    all_assessments
                    .filter(assessment_date__gte=six_months_ago)
                    .annotate(mes=TruncMonth('assessment_date'))
                    .values('mes')
                    .annotate(total=Count('id'))
                    .order_by('mes')
                )
                tendencia_meses = [
                    {'mes': r['mes'], 'mes_label': r['mes'].strftime('%b %Y'), 'total': r['total']}
                    for r in tendencia_raw if r['mes']
                ]
                dash_hoteles['tendencia_meses'] = tendencia_meses
                dash_hoteles['tendencia_max'] = max((m['total'] for m in tendencia_meses), default=1)

                # -- Mejor y peor hotel (avg overall_score) --
                hoteles_scored = (
                    Hotel.objects.filter(owner=request.user, id__in=hoteles_ids)
                    .annotate(avg_score=Avg('security_assessments__overall_score'))
                    .filter(avg_score__isnull=False)
                    .order_by('-avg_score')
                )
                _mejor = hoteles_scored.first()
                _peor  = hoteles_scored.last()
                if _mejor:
                    _mejor.pct = round(_mejor.avg_score / 5 * 100)
                    mejor_hotel_global = _mejor
                if _peor and (_mejor is None or _peor.pk != _mejor.pk):
                    _peor.pct = round(_peor.avg_score / 5 * 100)
                    peor_hotel_global = _peor

                # -- Ranking de categorías de seguridad --
                categorias_ranking = list(
                    SecurityCategoryScore.objects
                    .filter(assessment__hotel__owner=request.user)
                    .values('category__name')
                    .annotate(avg_pct=Avg('percentage'), total=Count('id'))
                    .order_by('-avg_pct')
                )
                dash_hoteles['categorias_ranking'] = categorias_ranking
                dash_hoteles['categoria_mas_fuerte'] = categorias_ranking[0] if categorias_ranking else None
                dash_hoteles['categoria_mas_debil']  = categorias_ranking[-1] if categorias_ranking else None

                # ── Estadística 1: Distribución por nivel de riesgo ───────────
                riesgo_map = [
                    ('muy_bajo', 'Muy Bajo',  'success'),
                    ('bajo',     'Bajo',      'info'),
                    ('medio',    'Medio',     'warning'),
                    ('alto',     'Alto',      'orange'),
                    ('muy_alto', 'Muy Alto',  'danger'),
                ]
                riesgo_counts_raw = (
                    all_assessments
                    .filter(status__in=['completed', 'reviewed'], risk_level__isnull=False)
                    .values('risk_level')
                    .annotate(total=Count('id'))
                )
                riesgo_index = {r['risk_level']: r['total'] for r in riesgo_counts_raw}
                riesgo_dist = [
                    {'key': k, 'label': lbl, 'color': col, 'total': riesgo_index.get(k, 0)}
                    for k, lbl, col in riesgo_map if riesgo_index.get(k, 0) > 0
                ]
                dash_hoteles['riesgo_dist'] = riesgo_dist
                dash_hoteles['riesgo_max'] = max((r['total'] for r in riesgo_dist), default=1)

                # ── Estadística 2: Hoteles con riesgo alto / muy alto ─────────
                hoteles_alto_riesgo = list(
                    all_assessments
                    .filter(status__in=['completed', 'reviewed'], risk_level__in=['alto', 'muy_alto'])
                    .select_related('hotel')
                    .order_by('-assessment_date')
                    .values('hotel__id', 'hotel__name', 'hotel__city', 'risk_level', 'assessment_date', 'overall_score')
                    [:10]
                )
                dash_hoteles['hoteles_alto_riesgo'] = hoteles_alto_riesgo

                # ── Estadística 3: Cobertura de hoteles ───────────────────────
                total_hoteles_owner = Hotel.objects.filter(owner=request.user, is_active=True).count()
                hoteles_sin_cobertura = list(
                    Hotel.objects.filter(owner=request.user, is_active=True)
                    .exclude(id__in=hoteles_ids)
                    .values('id', 'name', 'city', 'category')[:10]
                )
                pct_cobertura = round(total_hoteles_eval / total_hoteles_owner * 100) if total_hoteles_owner else 0
                dash_hoteles['hoteles_sin_cobertura'] = hoteles_sin_cobertura
                dash_hoteles['pct_cobertura'] = pct_cobertura
                dash_hoteles['total_hoteles'] = total_hoteles_owner
                dash_hoteles['total_hoteles_eval'] = total_hoteles_eval

                # ── Estadística 4: Funnel de estados ──────────────────────────
                estado_map = [
                    ('in_progress', 'En Progreso', 'warning'),
                    ('completed',   'Completadas', 'success'),
                    ('reviewed',    'Revisadas',   'info'),
                ]
                estado_counts_raw = (
                    all_assessments
                    .values('status')
                    .annotate(total=Count('id'))
                )
                estado_index = {r['status']: r['total'] for r in estado_counts_raw}
                dash_hoteles['funnel_estados'] = [
                    {'key': k, 'label': lbl, 'color': col, 'total': estado_index.get(k, 0)}
                    for k, lbl, col in estado_map
                ]
                dash_hoteles['funnel_max'] = max(
                    (e['total'] for e in dash_hoteles['funnel_estados']), default=1
                )

                # ── Estadística 5: Rendimiento por evaluador ──────────────────
                rendimiento_evaluadores = list(
                    all_assessments
                    .filter(status__in=['completed', 'reviewed'])
                    .values('created_by__id', 'created_by__first_name', 'created_by__last_name', 'created_by__username')
                    .annotate(
                        total=Count('id'),
                        avg_score=Avg('overall_score'),
                    )
                    .order_by('-total')
                    [:10]
                )
                for r in rendimiento_evaluadores:
                    r['avg_pct'] = round(r['avg_score'] / 5 * 100) if r['avg_score'] else 0
                    r['nombre'] = (
                        f"{r['created_by__first_name']} {r['created_by__last_name']}".strip()
                        or r['created_by__username']
                    )
                dash_hoteles['rendimiento_evaluadores'] = rendimiento_evaluadores

                # ── Estadística 6: Evolución de score por hotel ───────────────
                evolucion_hoteles = []
                for h in hoteles_scored[:8]:  # top 8 hoteles con score
                    evals_h = list(
                        all_assessments
                        .filter(hotel=h, status__in=['completed', 'reviewed'], overall_score__isnull=False)
                        .order_by('assessment_date')
                        .values('overall_score', 'assessment_date')
                    )
                    if len(evals_h) >= 2:
                        primera = evals_h[0]['overall_score']
                        ultima  = evals_h[-1]['overall_score']
                        delta   = round(ultima - primera, 2)
                        evolucion_hoteles.append({
                            'nombre': h.name,
                            'ciudad': h.city,
                            'primera': round(primera / 5 * 100),
                            'ultima': round(ultima / 5 * 100),
                            'delta': delta,
                            'tendencia': 'up' if delta > 0 else ('down' if delta < 0 else 'flat'),
                        })
                dash_hoteles['evolucion_hoteles'] = evolucion_hoteles

                # ── Estadística 7: Histograma de puntajes (rangos 20%) ────────
                rangos = [
                    (0,  20, '0-20%',   'danger'),
                    (20, 40, '20-40%',  'warning'),
                    (40, 60, '40-60%',  'secondary'),
                    (60, 80, '60-80%',  'info'),
                    (80, 101,'80-100%', 'success'),
                ]
                evals_completadas = all_assessments.filter(
                    status__in=['completed', 'reviewed'], overall_score__isnull=False
                )
                histograma = []
                for lo, hi, lbl, col in rangos:
                    lo_score = lo / 100 * 5
                    hi_score = hi / 100 * 5
                    cnt = evals_completadas.filter(
                        overall_score__gte=lo_score, overall_score__lt=hi_score
                    ).count()
                    histograma.append({'label': lbl, 'color': col, 'total': cnt})
                dash_hoteles['histograma'] = histograma
                dash_hoteles['histograma_max'] = max((h['total'] for h in histograma), default=1)

                # ── Estadística 8: Tiempo promedio para completar ─────────────
                from django.db.models import F, ExpressionWrapper, DurationField
                tiempos = (
                    evals_completadas
                    .filter(completed_at__isnull=False)
                    .annotate(
                        duracion=ExpressionWrapper(
                            F('completed_at') - F('created_at'),
                            output_field=DurationField()
                        )
                    )
                    .values_list('duracion', flat=True)
                )
                duraciones_dias = [d.total_seconds() / 86400 for d in tiempos if d is not None]
                dash_hoteles['tiempo_promedio_dias'] = (
                    round(sum(duraciones_dias) / len(duraciones_dias), 1) if duraciones_dias else None
                )

                # ── Estadística 9: Gauge cumplimiento ciclo 30 días ──────────
                thirty_ago = tz_rh.now() - timedelta(days=30)
                hoteles_evaluados_30d = (
                    all_assessments
                    .filter(assessment_date__gte=thirty_ago)
                    .values_list('hotel_id', flat=True)
                    .distinct()
                    .count()
                )
                dash_hoteles['gauge_30d'] = (
                    round(hoteles_evaluados_30d / total_hoteles_owner * 100)
                    if total_hoteles_owner else 0
                )

        except ImportError:
            pass  # risk_hoteles no instalado

        # ── Risk Conjuntos Dashboard ──────────────────────────────────────────
        dash_conjuntos = {'tiene_datos': False}
        conjuntos_recientes = []
        conjuntos_alto_riesgo = []
        try:
            from apps.risk_conjuntos.models import Conjunto, EvaluacionRiesgo
            from django.db.models import (
                Avg as _CAvg, Count as _CCount, Max as _CMax, Subquery as _CSub, OuterRef as _COut
            )
            from django.utils import timezone as _tz_conj
            from datetime import timedelta as _td_conj

            conj_qs = Conjunto.objects.filter(propietario=request.user, activo=True)
            total_conjuntos = conj_qs.count()
            dash_conjuntos['total_conjuntos'] = total_conjuntos

            # EvaluacionRiesgo usa SoftDeleteModel — el manager por defecto ya excluye borrados
            evals_qs = EvaluacionRiesgo.objects.filter(conjunto__propietario=request.user)
            completadas = evals_qs.filter(estado__in=['completada', 'revisada'])

            dash_conjuntos['tiene_datos'] = True
            dash_conjuntos['total_evaluaciones'] = evals_qs.count()
            dash_conjuntos['evaluaciones_completadas'] = completadas.count()
            dash_conjuntos['evaluaciones_en_progreso'] = evals_qs.filter(estado='en_progreso').count()
            dash_conjuntos['evaluaciones_borrador'] = evals_qs.filter(estado='borrador').count()

            # Promedio de riesgo (0-1 → porcentaje; mayor = más riesgo)
            avg_prm = completadas.filter(
                promedio_general__isnull=False
            ).aggregate(avg=_CAvg('promedio_general'))['avg']
            dash_conjuntos['promedio_riesgo_pct'] = round(float(avg_prm) * 100, 1) if avg_prm else 0.0

            # Distribución por nivel de riesgo
            riesgo_bajo = riesgo_medio = riesgo_alto = 0
            for prm in completadas.filter(
                promedio_general__isnull=False
            ).values_list('promedio_general', flat=True):
                pct = float(prm) * 100
                if pct <= 30:
                    riesgo_bajo += 1
                elif pct <= 60:
                    riesgo_medio += 1
                else:
                    riesgo_alto += 1
            dash_conjuntos['riesgo_dist'] = [
                {'label': 'Bajo',   'total': riesgo_bajo,  'color': 'success'},
                {'label': 'Medio',  'total': riesgo_medio, 'color': 'warning'},
                {'label': 'Alto',   'total': riesgo_alto,  'color': 'danger'},
            ]

            # Conjuntos sin ninguna evaluación
            conjs_con_eval_ids = evals_qs.values_list('conjunto_id', flat=True).distinct()
            dash_conjuntos['conjuntos_sin_evaluar'] = conj_qs.exclude(id__in=conjs_con_eval_ids).count()

            # Conjuntos con mayor riesgo (última eval completada, promedio_general desc)
            latest_eval_sub = completadas.filter(
                conjunto=_COut('pk'), promedio_general__isnull=False
            ).order_by('-fecha_evaluacion').values('promedio_general')[:1]
            top_riesgo_qs = conj_qs.annotate(
                ultimo_riesgo=_CSub(latest_eval_sub)
            ).filter(ultimo_riesgo__isnull=False).order_by('-ultimo_riesgo')[:5]
            conjuntos_alto_riesgo = [
                {
                    'nombre': c.nombre,
                    'ciudad': c.ciudad,
                    'pct': round(float(c.ultimo_riesgo) * 100, 1),
                    'nivel': ('alto' if float(c.ultimo_riesgo) * 100 > 60 else
                              'medio' if float(c.ultimo_riesgo) * 100 > 30 else 'bajo'),
                    'id': c.id,
                }
                for c in top_riesgo_qs
            ]

            # Conjuntos sin reevaluar (última eval completada hace >30 días)
            treinta_atras = _tz_conj.now() - _td_conj(days=30)
            conjs_sin_reeval = list(
                conj_qs.annotate(
                    ultima_eval=_CMax('evaluaciones_riesgo__fecha_evaluacion')
                ).filter(
                    ultima_eval__isnull=False,
                    ultima_eval__lt=treinta_atras,
                ).values('nombre', 'ciudad', 'ultima_eval')[:5]
            )
            dash_conjuntos['conjuntos_sin_reevaluar'] = conjs_sin_reeval

            # Funnel de estados
            estados_labels = [
                ('borrador',   'Borrador',   'secondary'),
                ('en_progreso','En Progreso', 'warning'),
                ('completada', 'Completada',  'success'),
                ('revisada',   'Revisada',    'info'),
            ]
            funnel = [
                {'label': lbl, 'total': evals_qs.filter(estado=est).count(), 'color': col}
                for est, lbl, col in estados_labels
            ]
            dash_conjuntos['funnel'] = funnel
            dash_conjuntos['funnel_max'] = max((f['total'] for f in funnel), default=1) or 1

            # Últimas 5 evaluaciones completadas
            ultimas = completadas.select_related('conjunto').order_by('-fecha_evaluacion')[:5]
            dash_conjuntos['ultimas_evaluaciones'] = [
                {
                    'conjunto_nombre': ev.conjunto.nombre,
                    'conjunto_id': ev.conjunto.id,
                    'fecha': ev.fecha_evaluacion,
                    'pct': ev.get_promedio_porcentaje(),
                    'nivel': ev.get_nivel_riesgo(),
                    'tipo': ev.get_tipo_evaluacion_display(),
                }
                for ev in ultimas
            ]

            conjuntos_recientes = list(conj_qs.order_by('-fecha_creacion')[:5])
        except ImportError:
            pass

        # ── Security Probabilistic Dashboard ─────────────────────────────────
        dash_sp = {'tiene_datos': False}
        perfiles_recientes = []
        perfiles_alto_riesgo_sp = []
        try:
            from apps.security_probabilistic.models import PerfilSeguridad, EvaluacionSeguridad as EvalSP
            from django.db.models import Count as _Count2, Avg as _AvgSP
            from django.utils import timezone as _tz_sp
            from datetime import timedelta as _td_sp

            perfiles_qs = PerfilSeguridad.objects.filter(owner=request.user)
            total_perfiles = perfiles_qs.count()
            dash_sp['total_perfiles'] = total_perfiles
            dash_sp['tiene_datos'] = True

            # Perfiles KPIs
            dash_sp['perfiles_activos'] = perfiles_qs.filter(estado_perfil='activo').count()
            dash_sp['perfiles_con_amenazas'] = perfiles_qs.filter(amenazas_recibidas=True).count()
            dash_sp['perfiles_sin_esquema'] = perfiles_qs.filter(
                estado_perfil='activo', tiene_esquema_seguridad=False
            ).count()
            # Amenaza reciente (últimos 90 días)
            noventa_atras = _tz_sp.now().date() - _td_sp(days=90)
            dash_sp['amenaza_reciente'] = perfiles_qs.filter(
                amenazas_recibidas=True,
                fecha_ultima_amenaza__isnull=False,
                fecha_ultima_amenaza__gte=noventa_atras,
            ).count()

            # Distribución por nivel de exposición
            dash_sp['exposicion_dist'] = list(
                perfiles_qs.values('nivel_exposicion')
                .annotate(total=_Count2('id'))
                .order_by('-total')
            )
            # Distribución por cargo (top 5)
            dash_sp['cargo_dist'] = list(
                perfiles_qs.values('cargo_politico')
                .annotate(total=_Count2('id'))
                .order_by('-total')[:5]
            )

            # Evaluaciones
            evals_sp = EvalSP.objects.filter(perfil__owner=request.user)
            completadas_sp = evals_sp.filter(estado='completada')
            dash_sp['total_evaluaciones'] = evals_sp.count()
            dash_sp['evaluaciones_completadas'] = completadas_sp.count()
            dash_sp['evaluaciones_en_progreso'] = evals_sp.filter(
                estado__in=['iniciada', 'en_progreso']
            ).count()

            # Probabilidad promedio (0-1 → porcentaje)
            avg_prob = completadas_sp.aggregate(
                avg=_AvgSP('probabilidad_con_geografia')
            )['avg']
            dash_sp['probabilidad_promedio'] = round(float(avg_prob) * 100, 1) if avg_prob else 0.0

            # Distribución por nivel de riesgo
            riesgo_meta = [
                ('muy_bajo', 'Muy Bajo', 'success'),
                ('bajo',     'Bajo',     'info'),
                ('medio',    'Medio',    'warning'),
                ('alto',     'Alto',     'danger'),
                ('muy_alto', 'Muy Alto', 'danger'),
            ]
            dash_sp['riesgo_dist'] = [
                {'key': key, 'label': lbl, 'color': col,
                 'total': completadas_sp.filter(nivel_riesgo=key).count()}
                for key, lbl, col in riesgo_meta
            ]

            # Funnel de estados evaluaciones
            estados_sp = [
                ('iniciada',   'Iniciada',   'secondary'),
                ('en_progreso','En Progreso','warning'),
                ('completada', 'Completada', 'success'),
                ('cancelada',  'Cancelada',  'danger'),
            ]
            funnel_sp = [
                {'label': lbl, 'total': evals_sp.filter(estado=est).count(), 'color': col}
                for est, lbl, col in estados_sp
            ]
            dash_sp['funnel'] = funnel_sp
            dash_sp['funnel_max'] = max((f['total'] for f in funnel_sp), default=1) or 1

            # Últimas 5 evaluaciones completadas
            ultimas_sp = completadas_sp.select_related('perfil').order_by('-completada_en')[:5]
            dash_sp['ultimas_evaluaciones'] = [
                {
                    'perfil_nombre': ev.perfil.nombre_completo,
                    'perfil_id': ev.perfil.pk,
                    'probabilidad_pct': round(float(ev.probabilidad_con_geografia) * 100, 1),
                    'nivel_riesgo': ev.nivel_riesgo,
                    'fecha': ev.completada_en or ev.creada_en,
                }
                for ev in ultimas_sp
            ]

            # Perfiles de alto riesgo (exposición alta/muy_alta + amenazas)
            perfiles_alto_riesgo_sp = list(
                perfiles_qs.filter(
                    nivel_exposicion__in=['muy_alta', 'alta'],
                    amenazas_recibidas=True,
                ).order_by('-creado_en')[:5]
            )
            perfiles_recientes = list(perfiles_qs.order_by('-creado_en')[:5])
        except ImportError:
            pass

        # Calcular porcentaje del día transcurrido (0-100)
        from django.utils import timezone as tz
        now_local = tz.localtime(tz.now())
        day_progress = int((now_local.hour * 60 + now_local.minute) / 1440 * 100)

        context = {
            'user': request.user,
            'title': 'Mi Dashboard',
            'is_evaluador': is_evaluador,
            'day_progress': day_progress,
            'user_subscriptions': user_subscriptions,
            'subscriptions_by_module': subscriptions_by_module,
            'total_subscriptions': user_subscriptions.count(),
            'total_modules': total_modules,
            'expiring_soon': expiring_soon,
            'trial_subscriptions': trial_subscriptions,
            'total_reports_used': total_reports_used,
            'total_evaluations': total_evaluations,
            # Variables para actividades de evaluadores
            'recent_evaluator_activities': recent_evaluator_activities,
            'daily_activities_count': daily_activities_count,
            'weekly_activities_count': weekly_activities_count,
            'monthly_activities_count': monthly_activities_count,
            'completed_evaluations_today': completed_evaluations_today,
            'in_progress_evaluations': in_progress_evaluations,
            'active_evaluators_today': active_evaluators_today,
            'total_evaluators': total_evaluators,
            # Métricas globales Risk Hoteles
            'dash_hoteles': dash_hoteles,
            'hoteles_sin_reevaluar': hoteles_sin_reevaluar,
            'pendientes_revision': pendientes_revision,
            'mejor_hotel_global': mejor_hotel_global,
            'peor_hotel_global': peor_hotel_global,
            # Métricas Risk Conjuntos
            'dash_conjuntos': dash_conjuntos,
            'conjuntos_recientes': conjuntos_recientes,
            'conjuntos_alto_riesgo': conjuntos_alto_riesgo,
            # Métricas Security Probabilistic
            'dash_sp': dash_sp,
            'perfiles_recientes': perfiles_recientes,
            'perfiles_alto_riesgo_sp': perfiles_alto_riesgo_sp,
        }
        
        # Validación final de seguridad: verificar que todos los datos pertenecen al usuario autenticado
        try:
            # Verificar suscripciones
            for subscription in context['user_subscriptions']:
                if subscription.user_id != request.user.id:
                    raise PermissionError("Datos de suscripción no autorizados")
            
            # Verificar actividades de evaluadores
            for activity in context['recent_evaluator_activities']:
                if activity.evaluador.usuario_principal_id != request.user.id:
                    raise PermissionError("Datos de actividad no autorizados")
                    
        except (AttributeError, PermissionError) as e:
            # Log de seguridad podría ir aquí
            # Por seguridad, limpiar datos sensibles en caso de error
            context.update({
                'user_subscriptions': [],
                'subscriptions_by_module': {},
                'total_subscriptions': 0,
                'recent_evaluator_activities': [],
                'daily_activities_count': 0,
                'total_evaluators': 0,
            })
    
    except ImportError:
        # Si el módulo de subscriptions no está disponible
        from django.utils import timezone as tz
        now_local = tz.localtime(tz.now())
        day_progress = int((now_local.hour * 60 + now_local.minute) / 1440 * 100)
        context = {
            'user': request.user,
            'title': 'Mi Dashboard',
            'is_evaluador': is_evaluador,
            'day_progress': day_progress,
            'user_subscriptions': [],
            'subscriptions_by_module': {},
            'total_subscriptions': 0,
            'total_modules': 0,
            'expiring_soon': 0,
            'trial_subscriptions': 0,
            'total_reports_used': 0,
            'total_evaluations': 0,
            # Valores por defecto para actividades
            'recent_evaluator_activities': [],
            'daily_activities_count': 0,
            'weekly_activities_count': 0,
            'monthly_activities_count': 0,
            'completed_evaluations_today': 0,
            'in_progress_evaluations': 0,
            'active_evaluators_today': 0,
            'total_evaluators': 0,
            # Métricas globales Risk Hoteles (vacías)
            'dash_hoteles': {'tiene_datos': False, 'evaluaciones_por_tipo': [], 'evaluaciones_tipo_max': 1, 'hoteles_por_categoria': [], 'geo_dist': [], 'tendencia_meses': [], 'tendencia_max': 1, 'categorias_ranking': [], 'categoria_mas_debil': None, 'categoria_mas_fuerte': None, 'riesgo_dist': [], 'riesgo_max': 1, 'funnel_estados': [], 'funnel_max': 1, 'hoteles_sin_cobertura': [], 'hoteles_alto_riesgo': [], 'rendimiento_evaluadores': [], 'evolucion_hoteles': [], 'histograma': [], 'histograma_max': 1, 'pct_cobertura': 0, 'total_hoteles': 0, 'total_hoteles_eval': 0, 'gauge_30d': 0, 'tiempo_promedio_dias': None},
            'hoteles_sin_reevaluar': [],
            'pendientes_revision': [],
            'mejor_hotel_global': None,
            'peor_hotel_global': None,
            # Métricas Risk Conjuntos (vacías)
            'dash_conjuntos': {'tiene_datos': False},
            'conjuntos_recientes': [],
            'conjuntos_alto_riesgo': [],
            # Métricas Security Probabilistic (vacías)
            'dash_sp': {'tiene_datos': False},
            'perfiles_recientes': [],
            'perfiles_alto_riesgo_sp': [],
        }
    
    return render(request, 'dashboard/dashboard.html', context)
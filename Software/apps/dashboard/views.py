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
            'completed_evaluations_today': 0,
            'in_progress_evaluations': 0,
            'active_evaluators_today': 0,
            # Métricas globales Risk Hoteles (vacías)
            'dash_hoteles': {'tiene_datos': False, 'evaluaciones_por_tipo': [], 'hoteles_por_categoria': [], 'geo_dist': [], 'tendencia_meses': [], 'tendencia_max': 1, 'categorias_ranking': [], 'categoria_mas_debil': None, 'categoria_mas_fuerte': None, 'riesgo_dist': [], 'riesgo_max': 1, 'funnel_estados': [], 'hoteles_sin_cobertura': [], 'hoteles_alto_riesgo': [], 'rendimiento_evaluadores': [], 'evolucion_hoteles': [], 'histograma': [], 'histograma_max': 1, 'pct_cobertura': 0, 'total_hoteles': 0, 'total_hoteles_eval': 0, 'gauge_30d': 0, 'tiempo_promedio_dias': None},
            'hoteles_sin_reevaluar': [],
            'pendientes_revision': [],
            'mejor_hotel_global': None,
            'peor_hotel_global': None,
        }
    
    return render(request, 'dashboard/dashboard.html', context)
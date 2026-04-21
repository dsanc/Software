"""
Vistas para gestión de evaluadores
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError

# Importar decoradores de suscripción
from apps.subscriptions.decorators import (
    subscription_required, 
    feature_required,
    simple_subscription_required
)
from .decorators import evaluadores_subscription_required, get_user_evaluator_limits, main_users_only

from .models import Evaluador
from .forms import (
    EvaluadorForm, 
    BuscarEvaluadorForm
)

User = get_user_model()


@login_required
@main_users_only
@evaluadores_subscription_required(action_type='view')
def lista_evaluadores(request):
    """
    Vista principal para listar evaluadores del usuario autenticado
    """
    # Verificar que el usuario tenga suscripciones activas
    if not request.user.subscriptions.filter(status='active').exists():
        messages.warning(
            request,
            'Necesitas una suscripción activa para gestionar evaluadores.'
        )
        return redirect('dashboard:home')
    
    # Obtener evaluadores del usuario
    evaluadores = Evaluador.objects.filter(
        usuario_principal=request.user
    ).select_related(
        'usuario_evaluador',
        'usuario_principal'
    ).order_by('-created_at')
    
    # Aplicar filtros si existen
    form_busqueda = BuscarEvaluadorForm(request.GET)
    if form_busqueda.is_valid():
        data = form_busqueda.cleaned_data
        
        if data.get('busqueda'):
            busqueda = data['busqueda']
            evaluadores = evaluadores.filter(
                Q(usuario_evaluador__first_name__icontains=busqueda) |
                Q(usuario_evaluador__last_name__icontains=busqueda) |
                Q(usuario_evaluador__email__icontains=busqueda) |
                Q(notas__icontains=busqueda)
            )
        
        if data.get('estado'):
            evaluadores = evaluadores.filter(estado=data['estado'])
        
        if data.get('tipo_evaluador'):
            evaluadores = evaluadores.filter(tipo_evaluador=data['tipo_evaluador'])
        
        if data.get('modulo'):
            evaluadores = evaluadores.filter(
                modulos_permitidos__icontains=data['modulo']
            )
        
        if data.get('activos_solo'):
            evaluadores = evaluadores.filter(is_active=True)
    
    # Paginación
    paginator = Paginator(evaluadores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas generales
    stats = {
        'total': Evaluador.objects.filter(usuario_principal=request.user).count(),
        'activos': Evaluador.objects.filter(usuario_principal=request.user, estado='active').count(),
        'pendientes': Evaluador.objects.filter(usuario_principal=request.user, estado='pending').count(),
    }
    
    # Obtener límites de evaluadores del usuario
    evaluator_limits = get_user_evaluator_limits(request.user)
    
    context = {
        'evaluadores': page_obj,
        'form_busqueda': form_busqueda,
        'stats': stats,
        'evaluator_limits': evaluator_limits,
        'page_title': 'Gestión de Evaluadores'
    }
    
    return render(request, 'evaluadores/lista.html', context)


@login_required
@main_users_only
@evaluadores_subscription_required(action_type='create')
def crear_evaluador(request):
    """
    Vista para crear un nuevo evaluador
    """
    if request.method == 'POST':
        form = EvaluadorForm(request.POST, usuario_principal=request.user)
        
        if form.is_valid():
            try:
                evaluador = form.save()
                evaluador.refresh_from_db()
                
                nombre_completo = evaluador.get_full_name()
                messages.success(
                    request,
                    f'Evaluador {nombre_completo} creado exitosamente. '
                    f'Puede acceder al sistema con el email: {evaluador.usuario_evaluador.email}'
                )
                return redirect('evaluadores:detalle', pk=evaluador.pk)
                
            except ValidationError as e:
                # Manejar errores de validación del modelo
                if 'suscripción activa' in str(e):
                    messages.error(
                        request,
                        'Para crear evaluadores necesitas tener al menos una suscripción activa. '
                        'Contacta al administrador si crees que esto es un error.'
                    )
                else:
                    messages.error(request, f'Error de validación: {e}')
            except Exception as e:
                messages.error(
                    request,
                    f'Error inesperado al crear el evaluador: {str(e)}'
                )
    else:
        form = EvaluadorForm(usuario_principal=request.user)
    
    context = {
        'form': form,
        'page_title': 'Crear Evaluador'
    }
    
    return render(request, 'evaluadores/crear.html', context)


@login_required
@main_users_only
def detalle_evaluador(request, pk):
    """
    Vista de detalle de un evaluador específico
    """
    evaluador = get_object_or_404(
        Evaluador,
        pk=pk,
        usuario_principal=request.user
    )
    
    # Obtener estadísticas del evaluador
    estadisticas = evaluador.obtener_estadisticas_uso()
    
    # Obtener suscripciones heredadas
    suscripciones_heredadas = evaluador.obtener_suscripciones_heredadas()
    
    # Obtener suscripciones directas del evaluador
    suscripciones_evaluador = evaluador.usuario_evaluador.subscriptions.filter(status='active')
    
    context = {
        'evaluador': evaluador,
        'estadisticas': estadisticas,
        'suscripciones_heredadas': suscripciones_heredadas,
        'suscripciones_evaluador': suscripciones_evaluador,
        'page_title': f'Evaluador - {evaluador.usuario_evaluador.get_full_name()}'
    }
    
    return render(request, 'evaluadores/detalle.html', context)


@login_required
@main_users_only
def editar_evaluador(request, pk):
    """
    Vista para editar un evaluador existente
    """
    evaluador = get_object_or_404(
        Evaluador,
        pk=pk,
        usuario_principal=request.user
    )
    
    if request.method == 'POST':
        form = EvaluadorForm(
            request.POST, 
            instance=evaluador,
            usuario_principal=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Evaluador {evaluador.usuario_evaluador.get_full_name()} actualizado exitosamente.'
            )
            return redirect('evaluadores:detalle', pk=evaluador.pk)
    else:
        form = EvaluadorForm(instance=evaluador, usuario_principal=request.user)
    
    context = {
        'form': form,
        'evaluador': evaluador,
        'page_title': f'Editar Evaluador - {evaluador.usuario_evaluador.get_full_name()}'
    }
    
    return render(request, 'evaluadores/editar.html', context)


@login_required
@main_users_only
@require_http_methods(["POST"])
def eliminar_evaluador(request, pk):
    """
    Vista para eliminar un evaluador
    """
    evaluador = get_object_or_404(
        Evaluador,
        pk=pk,
        usuario_principal=request.user
    )
    
    nombre_evaluador = evaluador.usuario_evaluador.get_full_name()
    evaluador.delete()
    
    messages.success(
        request,
        f'Evaluador {nombre_evaluador} eliminado exitosamente.'
    )
    
    return redirect('evaluadores:lista')


@login_required
@main_users_only
@require_http_methods(["POST"])
def cambiar_estado_evaluador(request, pk):
    """
    Vista para cambiar el estado de un evaluador (activar/suspender/etc.)
    """
    evaluador = get_object_or_404(
        Evaluador,
        pk=pk,
        usuario_principal=request.user
    )
    
    nuevo_estado = request.POST.get('estado')
    
    if nuevo_estado in dict(Evaluador.ESTADOS):
        estado_anterior = evaluador.estado
        
        if nuevo_estado == 'active':
            evaluador.activar()
            mensaje = 'activado'
        elif nuevo_estado == 'suspended':
            evaluador.suspender()
            mensaje = 'suspendido'
        elif nuevo_estado == 'inactive':
            evaluador.desactivar()
            mensaje = 'desactivado'
        else:
            evaluador.estado = nuevo_estado
            evaluador.save()
            mensaje = f'cambiado a {evaluador.get_estado_display()}'
        
        messages.success(
            request,
            f'Evaluador {evaluador.usuario_evaluador.get_full_name()} {mensaje}.'
        )
    else:
        messages.error(request, 'Estado no válido.')
    
    return redirect('evaluadores:detalle', pk=evaluador.pk)


# --- VISTAS PARA EVALUADORES (desde su perspectiva) ---

@login_required
def mi_perfil_evaluador(request):
    """
    Vista para que los evaluadores vean su perfil y accesos
    """
    # Buscar si el usuario es evaluador de alguien
    perfiles_evaluador = Evaluador.objects.filter(
        usuario_evaluador=request.user,
        is_active=True
    ).select_related('usuario_principal')
    
    if not perfiles_evaluador.exists():
        messages.info(
            request,
            'No tienes perfiles de evaluador activos.'
        )
        return redirect('dashboard:home')
    
    # Obtener estadísticas combinadas
    estadisticas_generales = {
        'usuarios_principales': perfiles_evaluador.count(),
        'modulos_disponibles': set(),
        'suscripciones_heredadas': []
    }
    
    for perfil in perfiles_evaluador:
        estadisticas_generales['modulos_disponibles'].update(perfil.modulos_permitidos)
        estadisticas_generales['suscripciones_heredadas'].extend(
            perfil.obtener_suscripciones_heredadas()
        )
    
    context = {
        'perfiles_evaluador': perfiles_evaluador,
        'estadisticas': estadisticas_generales,
        'page_title': 'Mi Perfil de Evaluador'
    }
    
    return render(request, 'evaluadores/mi_perfil.html', context)


@login_required
def dashboard_evaluador(request, usuario_principal_id):
    """
    Dashboard específico para un evaluador bajo un usuario principal
    """
    # Verificar que el usuario es evaluador del usuario principal especificado
    try:
        perfil_evaluador = Evaluador.objects.get(
            usuario_evaluador=request.user,
            usuario_principal_id=usuario_principal_id,
            is_active=True,
            estado='active'
        )
    except Evaluador.DoesNotExist:
        messages.error(request, 'No tienes acceso a este dashboard.')
        return redirect('dashboard:home')

    # Verificar que el evaluador esté activo (ya incluido en el .get() anterior,
    # pero validamos expiración explícitamente)
    if perfil_evaluador.fecha_expiracion:
        from django.utils import timezone as tz
        if tz.now() > perfil_evaluador.fecha_expiracion:
            messages.warning(request, 'Tu acceso ha expirado. Contacta a tu usuario principal.')
            return redirect('evaluadores:mi_perfil_evaluador')

    # Actualizar último acceso
    perfil_evaluador.actualizar_ultimo_acceso()

    # Obtener datos base
    suscripciones_heredadas = perfil_evaluador.obtener_suscripciones_heredadas()
    estadisticas = perfil_evaluador.obtener_estadisticas_uso()

    # ── Estadísticas de Risk Hoteles ──────────────────────────────────────
    stats_hoteles = {}
    hoteles_recientes = []
    evaluaciones_recientes = []
    evaluaciones_por_estado = {}
    evaluaciones_por_mes = []
    hoteles_con_riesgo = []

    if 'risk_hoteles' in perfil_evaluador.modulos_permitidos:
        try:
            from apps.risk_hoteles.models import Hotel, SecurityAssessment, SecurityCategoryScore
            from django.db.models import Count, Avg, Q, Max
            from django.db.models.functions import TruncMonth
            from django.utils import timezone
            from datetime import timedelta

            usuario_eval = request.user
            usuario_principal = perfil_evaluador.usuario_principal

            # Solo evaluaciones creadas por este evaluador sobre hoteles del usuario principal
            evaluaciones_qs = SecurityAssessment.objects.filter(
                hotel__owner=usuario_principal,
                created_by=usuario_eval
            ).select_related('hotel')

            # Solo hoteles sobre los que el evaluador tiene al menos una evaluación
            hoteles_ids = evaluaciones_qs.values_list('hotel_id', flat=True).distinct()
            hoteles_qs = Hotel.objects.filter(
                id__in=hoteles_ids
            ).select_related('owner')

            # Conteos globales
            total_hoteles = hoteles_qs.count()
            total_evaluaciones = evaluaciones_qs.count()
            evaluaciones_completadas = evaluaciones_qs.filter(status='completed').count()
            evaluaciones_en_progreso = evaluaciones_qs.filter(status='in_progress').count()
            evaluaciones_revisadas = evaluaciones_qs.filter(status='reviewed').count()

            # Promedio general de puntuación (escala 0-5)
            avg_score_raw = evaluaciones_qs.filter(
                status__in=['completed', 'reviewed'],
                overall_score__isnull=False
            ).aggregate(avg=Avg('overall_score'))['avg']
            avg_score = round(avg_score_raw * 20, 1) if avg_score_raw is not None else None  # → porcentaje

            # Evaluaciones este mes
            inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            evaluaciones_este_mes = evaluaciones_qs.filter(created_at__gte=inicio_mes).count()

            # Evaluaciones últimos 30 días
            hace_30 = timezone.now() - timedelta(days=30)
            evaluaciones_30d = evaluaciones_qs.filter(created_at__gte=hace_30).count()

            # Distribución por nivel de riesgo (evaluaciones completadas)
            riesgo_dist = evaluaciones_qs.filter(
                status__in=['completed', 'reviewed'],
                risk_level__isnull=False
            ).values('risk_level').annotate(total=Count('id'))

            riesgo_labels = {
                'muy_bajo': 'Muy Bajo', 'bajo': 'Bajo', 'medio': 'Medio',
                'alto': 'Alto', 'muy_alto': 'Muy Alto'
            }
            riesgo_colores = {
                'muy_bajo': 'success', 'bajo': 'info',
                'medio': 'warning', 'alto': 'danger', 'muy_alto': 'dark'
            }
            evaluaciones_por_nivel = [
                {
                    'nivel': r['risk_level'],
                    'label': riesgo_labels.get(r['risk_level'], r['risk_level']),
                    'color': riesgo_colores.get(r['risk_level'], 'secondary'),
                    'total': r['total']
                }
                for r in riesgo_dist
            ]

            # Distribución por estado
            evaluaciones_por_estado = {
                'in_progress': evaluaciones_en_progreso,
                'completed': evaluaciones_completadas,
                'reviewed': evaluaciones_revisadas,
            }

            # Hoteles recientes (con su última evaluación del evaluador)
            hoteles_recientes = hoteles_qs.order_by('-created_at')[:5]
            for h in hoteles_recientes:
                h.ultima_eval = evaluaciones_qs.filter(hotel=h).order_by('-created_at').first()

            # Evaluaciones más recientes
            evaluaciones_recientes = evaluaciones_qs.order_by('-created_at')[:8]

            # Hoteles con nivel de riesgo (última evaluación completada)
            hoteles_con_riesgo = []
            for hotel in hoteles_qs.order_by('name'):
                ultima = evaluaciones_qs.filter(
                    hotel=hotel,
                    status__in=['completed', 'reviewed'],
                    overall_score__isnull=False
                ).order_by('-completed_at').first()
                if ultima:
                    pct = round((ultima.overall_score / 5.0) * 100, 1)
                    hoteles_con_riesgo.append({
                        'hotel': hotel,
                        'evaluacion': ultima,
                        'porcentaje': pct,
                        'color': riesgo_colores.get(ultima.risk_level, 'secondary'),
                    })

            # ── Distribución por tipo de evaluación ──────────────────
            tipo_labels = {
                'inicial': 'Inicial', 'periodico': 'Periódico',
                'especial': 'Especial', 'auditoria': 'Auditoría'
            }
            tipo_colores = {
                'inicial': 'primary', 'periodico': 'success',
                'especial': 'warning', 'auditoria': 'danger'
            }
            evaluaciones_por_tipo = [
                {
                    'tipo': r['assessment_type'],
                    'label': tipo_labels.get(r['assessment_type'], r['assessment_type']),
                    'color': tipo_colores.get(r['assessment_type'], 'secondary'),
                    'total': r['total'],
                }
                for r in evaluaciones_qs.values('assessment_type').annotate(total=Count('id'))
            ]

            # ── Distribución por categoría de hotel ──────────────────
            cat_hotel_labels = {
                '1_star': '1 Estrella', '2_star': '2 Estrellas', '3_star': '3 Estrellas',
                '4_star': '4 Estrellas', '5_star': '5 Estrellas', 'luxury': 'Lujo'
            }
            hoteles_por_categoria = [
                {
                    'categoria': r['category'],
                    'label': cat_hotel_labels.get(r['category'], r['category']),
                    'total': r['total'],
                }
                for r in hoteles_qs.values('category').annotate(total=Count('id')).order_by('-total')
            ]

            # ── Distribución geográfica ───────────────────────────────
            geo_dist = list(
                hoteles_qs.values('city', 'country').annotate(total=Count('id')).order_by('-total')[:10]
            )

            # ── Hoteles sin re-evaluar (sin evaluación en los últimos 60 días) ──
            hace_60 = timezone.now() - timedelta(days=60)
            hoteles_sin_reevaluar = list(
                hoteles_qs
                .annotate(ultima_eval=Max(
                    'security_assessments__created_at',
                    filter=Q(security_assessments__created_by=usuario_eval)
                ))
                .filter(ultima_eval__lt=hace_60)
                .order_by('ultima_eval')[:10]
            )

            # ── Evaluaciones completadas pendientes de revisión ───────
            pendientes_revision = list(evaluaciones_qs.filter(status='completed').order_by('-completed_at')[:8])
            total_pendientes_revision = evaluaciones_qs.filter(status='completed').count()

            # ── Ranking de categorías de seguridad (mejor/peor) ──────
            cat_scores_qs = (
                SecurityCategoryScore.objects
                .filter(assessment__in=evaluaciones_qs.filter(status__in=['completed', 'reviewed']))
                .values('category__name', 'category__code', 'category__icon')
                .annotate(avg_pct=Avg('percentage'), total=Count('id'))
                .filter(total__gte=1)
                .order_by('avg_pct')
            )
            categorias_ranking = list(cat_scores_qs)
            categoria_mas_debil = categorias_ranking[0] if categorias_ranking else None
            categoria_mas_fuerte = categorias_ranking[-1] if categorias_ranking else None

            # ── Tendencia mensual (últimos 6 meses) ───────────────────
            hace_6_meses = timezone.now() - timedelta(days=180)
            tendencia_raw = list(
                evaluaciones_qs
                .filter(created_at__gte=hace_6_meses)
                .annotate(mes=TruncMonth('created_at'))
                .values('mes')
                .annotate(total=Count('id'))
                .order_by('mes')
            )
            tendencia_meses = [
                {'mes_label': item['mes'].strftime('%b %Y'), 'total': item['total']}
                for item in tendencia_raw
            ]
            tendencia_max = max((m['total'] for m in tendencia_meses), default=1)

            # ── Mejor y peor hotel evaluado ───────────────────────────
            hoteles_con_avg = list(
                hoteles_qs
                .annotate(avg_score=Avg(
                    'security_assessments__overall_score',
                    filter=Q(
                        security_assessments__created_by=usuario_eval,
                        security_assessments__status__in=['completed', 'reviewed'],
                        security_assessments__overall_score__isnull=False
                    )
                ))
                .filter(avg_score__isnull=False)
                .order_by('-avg_score')
            )
            mejor_hotel = None
            peor_hotel = None
            if hoteles_con_avg:
                mh = hoteles_con_avg[0]
                mejor_hotel = {'hotel': mh, 'pct': round((mh.avg_score / 5.0) * 100, 1)}
                ph = hoteles_con_avg[-1]
                if ph.id != mh.id:
                    peor_hotel = {'hotel': ph, 'pct': round((ph.avg_score / 5.0) * 100, 1)}

            stats_hoteles = {
                'total_hoteles': total_hoteles,
                'total_evaluaciones': total_evaluaciones,
                'evaluaciones_completadas': evaluaciones_completadas,
                'evaluaciones_en_progreso': evaluaciones_en_progreso,
                'evaluaciones_revisadas': evaluaciones_revisadas,
                'evaluaciones_este_mes': evaluaciones_este_mes,
                'evaluaciones_30d': evaluaciones_30d,
                'avg_score': avg_score,
                'evaluaciones_por_nivel': evaluaciones_por_nivel,
                'evaluaciones_por_tipo': evaluaciones_por_tipo,
                'hoteles_por_categoria': hoteles_por_categoria,
                'geo_dist': geo_dist,
                'total_pendientes_revision': total_pendientes_revision,
                'categorias_ranking': categorias_ranking,
                'categoria_mas_debil': categoria_mas_debil,
                'categoria_mas_fuerte': categoria_mas_fuerte,
                'tendencia_meses': tendencia_meses,
                'tendencia_max': tendencia_max,
                'tiene_datos': total_evaluaciones > 0,
            }

        except Exception:
            stats_hoteles = {'tiene_datos': False}

    context = {
        'perfil_evaluador': perfil_evaluador,
        'usuario_principal': perfil_evaluador.usuario_principal,
        'suscripciones_heredadas': suscripciones_heredadas,
        'estadisticas': estadisticas,
        'stats_hoteles': stats_hoteles,
        'hoteles_recientes': hoteles_recientes,
        'evaluaciones_recientes': evaluaciones_recientes,
        'evaluaciones_por_estado': evaluaciones_por_estado,
        'hoteles_con_riesgo': hoteles_con_riesgo,
        'hoteles_sin_reevaluar': hoteles_sin_reevaluar,
        'pendientes_revision': pendientes_revision,
        'mejor_hotel': mejor_hotel,
        'peor_hotel': peor_hotel,
        'page_title': f'Dashboard - {perfil_evaluador.usuario_principal.get_full_name()}'
    }

    return render(request, 'evaluadores/dashboard_evaluador.html', context)


@login_required
def permisos_ejemplo(request):
    """
    Vista de ejemplo para mostrar el sistema de permisos
    """
    return render(request, 'evaluadores/permisos_ejemplo.html', {
        'page_title': 'Ejemplo de Sistema de Permisos'
    })


# --- APIS Y VISTAS AJAX ---

@login_required
@main_users_only
@require_http_methods(["GET"])
def api_verificar_usuario(request):
    """
    API para verificar si un email corresponde a un usuario registrado
    """
    email = request.GET.get('email', '').strip()
    
    if not email:
        return JsonResponse({'valid': False, 'message': 'Email requerido'})
    
    try:
        usuario = User.objects.get(email=email)
        
        # Verificar si ya es evaluador
        es_evaluador = Evaluador.objects.filter(
            usuario_principal=request.user,
            usuario_evaluador=usuario
        ).exists()
        
        return JsonResponse({
            'valid': True,
            'exists': True,
            'name': usuario.get_full_name(),
            'is_evaluator': es_evaluador,
            'message': 'Usuario encontrado' if not es_evaluador else 'Usuario ya es evaluador'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'valid': True,
            'exists': False,
            'name': '',
            'is_evaluator': False,
            'message': 'Usuario no registrado (se creará automáticamente)'
        })


@login_required
@main_users_only
@require_http_methods(["GET"])
def api_estadisticas_evaluador(request, pk):
    """
    API para obtener estadísticas actualizadas de un evaluador
    """
    evaluador = get_object_or_404(
        Evaluador,
        pk=pk,
        usuario_principal=request.user
    )
    
    estadisticas = evaluador.obtener_estadisticas_uso()
    
    return JsonResponse({
        'success': True,
        'estadisticas': estadisticas
    })


# Vista para manejar errores 
def error_404(request, exception):
    """Vista personalizada para error 404"""
    return render(request, 'evaluadores/404.html', status=404)


def error_500(request):
    """Vista personalizada para error 500"""
    return render(request, 'evaluadores/500.html', status=500)


@login_required
@require_http_methods(["GET"])
def permission_denied_view(request):
    """
    Vista para mostrar página de error de permisos denegados
    """
    context = {
        'error_type': request.GET.get('error_type', 'permission_denied'),
        'module': request.GET.get('module', 'desconocido'),
        'action': request.GET.get('action', 'acceder'),
        'user_type': 'evaluador' if hasattr(request.user, 'evaluador') else 'usuario',
        'return_url': request.META.get('HTTP_REFERER', '/'),
    }
    
    # Mapeo de acciones a español
    action_map = {
        'read': 'ver',
        'create': 'crear', 
        'update': 'editar',
        'delete': 'eliminar',
        'export': 'exportar',
        'approve': 'aprobar',
        'access': 'acceder'
    }
    
    # Mapeo de módulos a español
    module_map = {
        'risk_hoteles': 'Risk Hoteles',
        'risk_conjuntos': 'Risk Conjuntos', 
        'security_probabilistic': 'Security Probabilistic'
    }
    
    # Mapeo de URLs de redirección por módulo
    module_urls = {
        'risk_hoteles': '/risk-hoteles/dashboard/',
        'risk_conjuntos': '/risk-conjuntos/dashboard/',
        'security_probabilistic': '/security-probabilistic/',
    }
    
    # Si no hay URL de referencia, usar la URL del módulo correspondiente
    if context['return_url'] == '/':
        context['return_url'] = module_urls.get(context['module'], '/dashboard/')
    
    context['action_display'] = action_map.get(context['action'], context['action'])
    context['module_display'] = module_map.get(context['module'], context['module'])
    
    # Email del administrador específico por módulo
    admin_emails = {
        'risk_hoteles': 'admin.hoteles@empresa.com',
        'risk_conjuntos': 'admin.conjuntos@empresa.com',
        'security_probabilistic': 'admin.security@empresa.com',
    }
    context['admin_email'] = admin_emails.get(context['module'], 'admin@empresa.com')
    
    return render(request, 'evaluadores/permission_denied.html', context)


@login_required
@require_http_methods(["GET"])
def permission_denied_modal(request):
    """
    Vista AJAX para obtener datos del modal de permisos denegados
    """
    error_type = request.GET.get('error_type', 'permission_denied')
    module = request.GET.get('module', 'desconocido')
    action = request.GET.get('action', 'acceder')
    
    # Mapeo de acciones a español
    action_map = {
        'read': 'ver',
        'create': 'crear', 
        'update': 'editar',
        'delete': 'eliminar',
        'export': 'exportar',
        'approve': 'aprobar'
    }
    
    # Mapeo de módulos a español
    module_map = {
        'risk_hoteles': 'Risk Hoteles',
        'risk_conjuntos': 'Risk Conjuntos', 
        'security_probabilistic': 'Security Probabilistic'
    }
    
    action_display = action_map.get(action, action)
    module_display = module_map.get(module, module)
    
    if error_type == 'module_access':
        title = "Acceso Denegado al Módulo"
        message = f"No tienes permisos para acceder al módulo <strong>{module_display}</strong>."
        suggestion = "Contacta a tu administrador para solicitar acceso a este módulo."
    else:
        title = "Permisos Insuficientes"
        message = f"No tienes permisos para <strong>{action_display}</strong> en el módulo <strong>{module_display}</strong>."
        suggestion = f"Solo puedes realizar las acciones para las que tienes permisos en {module_display}."
    
    return JsonResponse({
        'success': True,
        'title': title,
        'message': message,
        'suggestion': suggestion,
        'error_type': error_type,
        'module': module_display,
        'action': action_display
    })


@login_required
def test_permission_system(request):
    """
    Vista de prueba para verificar el sistema de permisos
    """
    from .permissions import evaluador_permission_required, evaluador_module_required
    
    # Aplicar decoradores para probar diferentes escenarios
    if request.GET.get('test') == 'permission':
        # Probar permiso CRUD específico
        module = request.GET.get('module', 'risk_hoteles')
        action = request.GET.get('action', 'create')
        
        @evaluador_permission_required(module, action)
        def test_permission_view(req):
            return JsonResponse({
                'success': True, 
                'message': f'Permiso concedido para {action} en {module}'
            })
        
        return test_permission_view(request)
    
    elif request.GET.get('test') == 'module':
        # Probar acceso a módulo
        module = request.GET.get('module', 'risk_hoteles')
        
        @evaluador_module_required(module)
        def test_module_view(req):
            return JsonResponse({
                'success': True, 
                'message': f'Acceso concedido al módulo {module}'
            })
        
        return test_module_view(request)
    
    # Vista principal con enlaces de prueba
    context = {
        'title': 'Prueba del Sistema de Permisos'
    }
    
    # Añadir información del evaluador si existe
    try:
        evaluator = Evaluador.objects.get(usuario=request.user)
        context['evaluator'] = evaluator
    except Evaluador.DoesNotExist:
        context['evaluator'] = None
    
    return render(request, 'evaluadores/test_permissions.html', context)


@login_required 
def test_ownership_system(request):
    """
    Vista para probar el sistema de filtrado por propietario en los 3 módulos
    """
    from apps.core.decorators import get_user_access_info
    
    # Información del usuario
    user_info = get_user_access_info(request.user)
    
    # Obtener estadísticas de cada módulo usando los helpers de filtrado
    
    # Risk Hoteles
    try:
        from apps.risk_hoteles.views import get_user_hotels, get_user_assessments
        hoteles = get_user_hotels(request.user)
        evaluaciones_hoteles = get_user_assessments(request.user)
        hoteles_count = hoteles.count()
        evaluaciones_hoteles_count = evaluaciones_hoteles.count()
    except Exception as e:
        hoteles_count = 0
        evaluaciones_hoteles_count = 0
    
    # Risk Conjuntos  
    try:
        from apps.risk_conjuntos.views import get_user_conjuntos, get_user_evaluaciones
        conjuntos = get_user_conjuntos(request.user)
        evaluaciones_conjuntos = get_user_evaluaciones(request.user)
        conjuntos_count = conjuntos.count()
        evaluaciones_conjuntos_count = evaluaciones_conjuntos.count()
    except Exception as e:
        conjuntos_count = 0
        evaluaciones_conjuntos_count = 0
    
    # Security Probabilistic
    try:
        from apps.security_probabilistic.views import get_user_perfiles, get_user_evaluaciones_security
        perfiles = get_user_perfiles(request.user)
        evaluaciones_security = get_user_evaluaciones_security(request.user)
        perfiles_count = perfiles.count()
        evaluaciones_security_count = evaluaciones_security.count()
    except Exception as e:
        perfiles_count = 0
        evaluaciones_security_count = 0
    
    # Calcular totales
    total_main_records = hoteles_count + conjuntos_count + perfiles_count
    total_evaluaciones = evaluaciones_hoteles_count + evaluaciones_conjuntos_count + evaluaciones_security_count
    grand_total = total_main_records + total_evaluaciones
    
    context = {
        'user_info': user_info,
        'hoteles_count': hoteles_count,
        'evaluaciones_hoteles_count': evaluaciones_hoteles_count,
        'hoteles_total': hoteles_count + evaluaciones_hoteles_count,
        'conjuntos_count': conjuntos_count,
        'evaluaciones_conjuntos_count': evaluaciones_conjuntos_count,
        'conjuntos_total': conjuntos_count + evaluaciones_conjuntos_count,
        'perfiles_count': perfiles_count,
        'evaluaciones_security_count': evaluaciones_security_count,
        'security_total': perfiles_count + evaluaciones_security_count,
        'total_main_records': total_main_records,
        'total_evaluaciones': total_evaluaciones,
        'grand_total': grand_total,
    }
    
    return render(request, 'evaluadores/test_ownership.html', context)


@login_required
def test_ownership_api(request):
    """
    API endpoint para obtener datos en tiempo real del sistema de filtrado
    """
    from django.http import JsonResponse
    
    module = request.GET.get('module')
    action = request.GET.get('action', 'count')
    record_type = request.GET.get('type', 'main')
    
    try:
        if module == 'hoteles':
            from apps.risk_hoteles.views import get_user_hotels, get_user_assessments
            
            if record_type == 'evaluaciones':
                queryset = get_user_assessments(request.user)
                if action == 'detail':
                    records = list(queryset.values('id', 'hotel__name', 'assessment_type', 'status', 'created_by__username', 'assessment_date')[:20])
                    return JsonResponse({'success': True, 'records': records})
            else:
                queryset = get_user_hotels(request.user)
                if action == 'detail':
                    records = list(queryset.values('id', 'name', 'city', 'category', 'owner__username', 'created_at')[:20])
                    return JsonResponse({'success': True, 'records': records})
            
            count = queryset.count()
            return JsonResponse({'success': True, 'count': count})
            
        elif module == 'conjuntos':
            from apps.risk_conjuntos.views import get_user_conjuntos, get_user_evaluaciones
            
            if record_type == 'evaluaciones':
                queryset = get_user_evaluaciones(request.user)
            else:
                queryset = get_user_conjuntos(request.user)
            
            count = queryset.count()
            return JsonResponse({'success': True, 'count': count})
            
        elif module == 'security':
            from apps.security_probabilistic.views import get_user_perfiles, get_user_evaluaciones_security
            
            if record_type == 'evaluaciones':
                queryset = get_user_evaluaciones_security(request.user)
            else:
                queryset = get_user_perfiles(request.user)
            
            count = queryset.count()
            return JsonResponse({'success': True, 'count': count})
            
        else:
            return JsonResponse({'success': False, 'error': 'Módulo no válido'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
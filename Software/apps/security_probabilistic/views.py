from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy, reverse
import logging

from apps.subscriptions.access_control import requires_security_probabilistic
from apps.subscriptions.access_control import AccessControlMixin

# Importar sistema de permisos de evaluadores
from apps.evaluadores.permissions import (
    evaluador_permission_required, 
    evaluador_module_required,
    EvaluadorPermissionMixin
)

# Importar mixins de filtrado por propiedad
from apps.core.mixins import (
    OwnershipFilterMixin,
    CreatedByMixin,
    UserTypeContextMixin,
    OwnershipValidationMixin
)

from .models import ArbolDecision, EvaluacionSeguridad, Pregunta, OpcionRespuesta, ZonaRiesgo, PerfilSeguridad
from .forms import CrearEvaluacionForm

logger = logging.getLogger(__name__)


# Helper class para aplicar filtrado por propiedad a vistas funcionales
class SecurityProbabilisticOwnershipMixin(OwnershipFilterMixin):
    """
    Mixin específico para Security Probabilistic con configuración de campos
    """
    ownership_field = 'owner'  # Para perfiles de seguridad
    creator_field = 'created_by'  # Para evaluaciones
    allow_related_access = True


def get_user_perfiles(user):
    """
    Función helper para obtener perfiles según el tipo de usuario
    """
    mixin = SecurityProbabilisticOwnershipMixin()
    mixin.request = type('obj', (object,), {'user': user})()  # Mock request object
    
    from .models import PerfilSeguridad
    queryset = PerfilSeguridad.objects.filter(estado_perfil='activo')
    return mixin.get_ownership_queryset(queryset)


def get_user_evaluaciones_security(user):
    """
    Función helper para obtener evaluaciones según el tipo de usuario
    """
    mixin = SecurityProbabilisticOwnershipMixin()
    mixin.request = type('obj', (object,), {'user': user})()  # Mock request object
    
    from .models import EvaluacionSeguridad
    queryset = EvaluacionSeguridad.objects.all()
    return mixin.get_ownership_queryset(queryset)


def ensure_perfil_ownership(user, perfil):
    """
    Verifica que el usuario tenga acceso a un perfil específico
    """
    mixin = SecurityProbabilisticOwnershipMixin()
    mixin.request = type('obj', (object,), {'user': user})()  # Mock request object
    
    if not mixin.get_object_ownership(perfil):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("No tienes permisos para acceder a este perfil")


def ensure_evaluacion_security_ownership(user, evaluacion):
    """
    Verifica que el usuario tenga acceso a una evaluación específica
    """
    mixin = SecurityProbabilisticOwnershipMixin()
    mixin.request = type('obj', (object,), {'user': user})()  # Mock request object
    
    if not mixin.get_object_ownership(evaluacion):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("No tienes permisos para acceder a esta evaluación")


class DashboardView(AccessControlMixin, EvaluadorPermissionMixin, TemplateView):
    """Vista principal del dashboard de evaluaciones de seguridad - Requiere suscripción"""
    template_name = 'security_probabilistic/dashboard.html'
    required_module = 'security_probabilistic'
    evaluador_module = 'security_probabilistic'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Estadísticas usando filtrado por propiedad
        user_perfiles = get_user_perfiles(user)
        context['total_perfiles'] = user_perfiles.count()
        context['perfiles_activos'] = user_perfiles.count()  # Ya están filtrados por activos
        
        # Estadísticas de evaluaciones usando filtrado por propiedad
        user_evaluaciones = get_user_evaluaciones_security(user)
        context['total_evaluaciones'] = user_evaluaciones.count()
        context['evaluaciones_completadas'] = user_evaluaciones.filter(estado='completada').count()
        context['evaluaciones_pendientes'] = user_evaluaciones.filter(estado__in=['iniciada', 'en_progreso']).count()
        
        # Última evaluación del usuario
        context['ultima_evaluacion'] = user_evaluaciones.order_by('-creada_en').first()
        
        # Evaluaciones recientes del usuario
        context['evaluaciones_recientes'] = user_evaluaciones.order_by('-creada_en')[:5]
        
        # Perfiles disponibles para el usuario
        context['perfiles_disponibles'] = user_perfiles.order_by('-creado_en')[:10]
        
        return context


class ListaPerfilesView(AccessControlMixin, EvaluadorPermissionMixin, OwnershipFilterMixin, ListView):
    """Vista mejorada para mostrar lista de perfiles de seguridad con filtros avanzados"""
    model = PerfilSeguridad
    template_name = 'security_probabilistic/lista_perfiles.html'
    ownership_field = 'owner'
    allow_related_access = True
    context_object_name = 'perfiles'
    paginate_by = 20
    required_module = 'security_probabilistic'
    evaluador_module = 'security_probabilistic'
    required_permission = 'read'
    
    def get_queryset(self):
        queryset = PerfilSeguridad.objects.all()
        
        # Filtros
        cargo = self.request.GET.get('cargo')
        estado = self.request.GET.get('estado')
        orden = self.request.GET.get('orden', '-creado_en')
        
        # Aplicar filtros
        if cargo:
            queryset = queryset.filter(cargo_politico=cargo)
            
        if estado:
            queryset = queryset.filter(estado_perfil=estado)
        
        # Filtro por nivel de riesgo (calculado)
        riesgo = self.request.GET.get('riesgo')
        if riesgo:
            # Filtrar por nivel de riesgo calculado
            perfiles_con_riesgo = []
            for perfil in queryset:
                if perfil.nivel_riesgo_perfil == riesgo:
                    perfiles_con_riesgo.append(perfil.id)
            queryset = queryset.filter(id__in=perfiles_con_riesgo)
        
        # Ordenamiento
        valid_orders = [
            'nombres', '-nombres', 
            'creado_en', '-creado_en',
            'cargo_politico', '-cargo_politico'
        ]
        if orden in valid_orders:
            queryset = queryset.order_by(orden)
        else:
            queryset = queryset.order_by('-creado_en')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar estadísticas
        all_perfiles = PerfilSeguridad.objects.all()
        context['total_perfiles'] = all_perfiles.count()
        
        # Estadísticas por nivel de riesgo
        context['stats_riesgo'] = {
            'muy_alto': len([p for p in all_perfiles if p.nivel_riesgo_perfil == 'muy_alto']),
            'alto': len([p for p in all_perfiles if p.nivel_riesgo_perfil == 'alto']),
            'medio': len([p for p in all_perfiles if p.nivel_riesgo_perfil == 'medio']),
            'bajo': len([p for p in all_perfiles if p.nivel_riesgo_perfil == 'bajo']),
        }
        
        # Mantener filtros en el contexto
        context['filtros_actuales'] = {
            'cargo': self.request.GET.get('cargo', ''),
            'estado': self.request.GET.get('estado', ''),
            'riesgo': self.request.GET.get('riesgo', ''),
            'orden': self.request.GET.get('orden', '-creado_en'),
        }
        
        return context


class DetallePerfilView(AccessControlMixin, EvaluadorPermissionMixin, DetailView):
    """Vista para mostrar los detalles completos de un perfil de seguridad"""
    model = PerfilSeguridad
    template_name = 'security_probabilistic/detalle_perfil.html'
    context_object_name = 'perfil'
    required_module = 'security_probabilistic'
    evaluador_module = 'security_probabilistic'
    required_permission = 'read'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil = self.get_object()
        
        # Obtener evaluaciones del perfil
        evaluaciones = EvaluacionSeguridad.objects.filter(perfil=perfil).order_by('-creada_en')
        context['evaluaciones'] = evaluaciones
        context['total_evaluaciones'] = evaluaciones.count()
        context['evaluaciones_completadas'] = evaluaciones.filter(estado='completada').count()
        context['evaluaciones_pendientes'] = evaluaciones.filter(estado__in=['iniciada', 'en_progreso']).count()
        
        # Última evaluación
        context['ultima_evaluacion'] = evaluaciones.first()
        
        # Estadísticas de riesgo de las evaluaciones
        evaluaciones_completadas = evaluaciones.filter(estado='completada')
        if evaluaciones_completadas.exists():
            niveles_riesgo = {}
            for eval in evaluaciones_completadas:
                nivel = eval.nivel_riesgo
                if nivel:
                    niveles_riesgo[nivel] = niveles_riesgo.get(nivel, 0) + 1
            context['estadisticas_riesgo'] = niveles_riesgo
            
            # Promedio de probabilidad de riesgo (incluyendo factor geográfico)
            # Calcular promedio completo para cada evaluación
            promedio_total = 0
            count_evaluaciones = 0
            for evaluacion in evaluaciones_completadas:
                resultado_promedio = evaluacion.calcular_promedio_completo()
                promedio_total += resultado_promedio['promedio_completo']
                count_evaluaciones += 1
            
            promedio = promedio_total / count_evaluaciones if count_evaluaciones > 0 else 0
            context['promedio_riesgo'] = promedio
        
        # Información adicional del perfil
        context['edad'] = perfil.edad
        context['nivel_riesgo_calculado'] = perfil.nivel_riesgo_perfil
        
        # Verificar si puede ser evaluado
        context['puede_evaluar'] = perfil.puede_ser_evaluado()
        
        return context


class CrearEvaluacionView(AccessControlMixin, EvaluadorPermissionMixin, CreatedByMixin, OwnershipValidationMixin, CreateView):
    """Vista para crear una nueva evaluación de seguridad"""
    model = EvaluacionSeguridad
    form_class = CrearEvaluacionForm
    template_name = 'security_probabilistic/crear_evaluacion.html'
    required_module = 'security_probabilistic'
    evaluador_module = 'security_probabilistic'
    required_permission = 'create'
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el perfil existe y puede ser evaluado"""
        # Usar filtrado por propiedad para obtener el perfil
        self.perfil = get_object_or_404(get_user_perfiles(request.user), pk=kwargs['perfil_id'])
        
        # Verificar propiedad del perfil
        ensure_perfil_ownership(request.user, self.perfil)
        
        # Verificar si el perfil está activo
        if self.perfil.estado_perfil != 'activo':
            messages.error(
                request, 
                f"No se pueden crear evaluaciones para el perfil de {self.perfil.nombre_completo} "
                "porque está inactivo."
            )
            return redirect('security_probabilistic:detalle_perfil', pk=self.perfil.pk)
        
        # Verificar si ya tiene una evaluación en progreso
        evaluacion_en_progreso = EvaluacionSeguridad.objects.filter(
            perfil=self.perfil,
            estado__in=['iniciada', 'en_progreso']
        ).first()
        
        if evaluacion_en_progreso:
            messages.warning(
                request,
                f"Ya existe una evaluación en progreso para {self.perfil.nombre_completo}. "
                f"Complete o cancele la evaluación #{evaluacion_en_progreso.id} antes de crear una nueva."
            )
            return redirect('security_probabilistic:detalle_perfil', pk=self.perfil.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Pasar el perfil al formulario"""
        kwargs = super().get_form_kwargs()
        kwargs['perfil'] = self.perfil
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['perfil'] = self.perfil
        
        # Información adicional para la plantilla
        context['arboles_disponibles'] = ArbolDecision.objects.filter(activo=True)
        
        # Estadísticas del perfil
        evaluaciones_previas = EvaluacionSeguridad.objects.filter(perfil=self.perfil)
        context['total_evaluaciones_previas'] = evaluaciones_previas.count()
        context['ultima_evaluacion'] = evaluaciones_previas.order_by('-creada_en').first()
        
        return context
    
    def form_valid(self, form):
        """Procesar formulario válido y crear la evaluación"""
        try:
            # Guardar la evaluación pasando el usuario autenticado
            evaluacion = form.save(user=self.request.user)
            
            messages.success(
                self.request,
                f"¡Evaluación creada exitosamente! "
                f"Se ha iniciado la evaluación #{evaluacion.id} para {self.perfil.nombre_completo}."
            )
            
            # Log de la acción
            logger.info(
                f"Nueva evaluación creada - ID: {evaluacion.id}, "
                f"Perfil: {self.perfil.nombre_completo}, "
                f"Evaluador: {evaluacion.evaluador_nombre}, "
                f"Tipo: {evaluacion.arbol.nombre}"
            )
            
            # Redirigir directamente a realizar la evaluación
            return redirect('security_probabilistic:realizar_evaluacion', evaluacion_id=evaluacion.id)
            
        except Exception as e:
            logger.error(f"Error al crear evaluación: {str(e)}")
            messages.error(
                self.request,
                "Ocurrió un error al crear la evaluación. Por favor, inténtelo nuevamente."
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Manejar formulario inválido"""
        messages.error(
            self.request,
            "Por favor, corrija los errores en el formulario antes de continuar."
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        """URL de redirección después de crear exitosamente"""
        # Esto no se usará porque redirigimos en form_valid, pero lo mantenemos por si acaso
        return reverse('security_probabilistic:detalle_perfil', kwargs={'pk': self.perfil.pk})


class RealizarEvaluacionView(AccessControlMixin, EvaluadorPermissionMixin, TemplateView):
    """Vista para realizar una evaluación paso a paso"""
    template_name = 'security_probabilistic/realizar_evaluacion.html'
    required_module = 'security_probabilistic'
    evaluador_module = 'security_probabilistic'
    required_permission = 'update'
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que la evaluación existe y puede ser realizada"""
        self.evaluacion = get_object_or_404(EvaluacionSeguridad, pk=kwargs['evaluacion_id'])
        
        print(f"[DISPATCH] Cargando evaluación ID: {self.evaluacion.id}")
        print(f"[DISPATCH] Estado: {self.evaluacion.estado}")
        print(f"[DISPATCH] Respuestas actuales: {self.evaluacion.respuestas_json}")
        
        # Verificar que la evaluación puede ser realizada
        if self.evaluacion.estado not in ['iniciada', 'en_progreso']:
            messages.error(
                request,
                f"La evaluación #{self.evaluacion.id} no puede ser modificada porque está "
                f"en estado '{self.evaluacion.get_estado_display()}'."
            )
            return redirect('security_probabilistic:detalle_perfil', pk=self.evaluacion.perfil.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_pregunta_inicial(self):
        """Obtener la primera pregunta del árbol de decisión"""
        return Pregunta.objects.filter(
            arbol=self.evaluacion.arbol,
            es_pregunta_inicial=True
        ).first()
    
    def get_pregunta_actual(self):
        """Determinar la pregunta actual basada en las respuestas previas"""
        respuestas = self.evaluacion.respuestas_json
        
        if not respuestas:
            # Primera pregunta
            return self.get_pregunta_inicial()
        
        # Obtener la última respuesta para determinar la siguiente pregunta
        ultima_respuesta_id = list(respuestas.keys())[-1] if respuestas else None
        
        if ultima_respuesta_id:
            try:
                ultima_opcion = OpcionRespuesta.objects.get(id=ultima_respuesta_id)
                
                # Prioridad 1: Si hay pregunta siguiente, ir a ella (aunque sea final)
                if ultima_opcion.pregunta_siguiente:
                    return ultima_opcion.pregunta_siguiente
                
                # Prioridad 2: Si es respuesta final y no hay siguiente, terminar
                if ultima_opcion.es_respuesta_final:
                    return None
                
                # Si no es final y no tiene siguiente, es un error en los datos
                logger.warning(
                    f"Opción {ultima_opcion.id} no es final pero no tiene pregunta siguiente. "
                    f"Pregunta: {ultima_opcion.pregunta.texto[:50]}..."
                )
                return None
                
            except OpcionRespuesta.DoesNotExist:
                logger.error(f"Opción de respuesta {ultima_respuesta_id} no encontrada")
                # Si hay error, empezar desde el inicio
                return self.get_pregunta_inicial()
        
        # Si no hay respuestas válidas, empezar desde el inicio
        return self.get_pregunta_inicial()
    
    def calcular_progreso(self):
        """Calcular el progreso de la evaluación basado en respuestas dadas"""
        # Refrescar la instancia desde la base de datos para evitar cache
        self.evaluacion.refresh_from_db()
        
        total_preguntas = Pregunta.objects.filter(arbol=self.evaluacion.arbol).count()
        respuestas_dadas = len(self.evaluacion.respuestas_json)
        
        print(f"[CALCULAR_PROGRESO] Evaluación ID: {self.evaluacion.id}")
        print(f"[CALCULAR_PROGRESO] Total preguntas en árbol: {total_preguntas}")
        print(f"[CALCULAR_PROGRESO] Respuestas JSON: {self.evaluacion.respuestas_json}")
        print(f"[CALCULAR_PROGRESO] Número de respuestas: {respuestas_dadas}")
        
        if total_preguntas == 0:
            print("[CALCULAR_PROGRESO] ERROR: No hay preguntas en el árbol")
            return 0, 0, 0
        
        # Para árboles de decisión, el progreso es aproximado
        # basado en las respuestas dadas vs total de preguntas posibles
        porcentaje = min((respuestas_dadas / total_preguntas) * 100, 95)  # Máximo 95% hasta completar
        
        print(f"[CALCULAR_PROGRESO] Porcentaje calculado: {porcentaje}")
        
        # Asegurar que el porcentaje sea un float para evitar problemas de localización
        return respuestas_dadas, total_preguntas, float(round(porcentaje, 1))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evaluacion'] = self.evaluacion
        
        # Obtener pregunta actual
        pregunta_actual = self.get_pregunta_actual()
        context['pregunta_actual'] = pregunta_actual
        
        if pregunta_actual:
            # Obtener opciones de respuesta
            opciones = OpcionRespuesta.objects.filter(
                pregunta=pregunta_actual
            ).order_by('orden')
            context['opciones'] = opciones
            
            # Verificar si hay respuesta previa para esta pregunta
            respuestas = self.evaluacion.respuestas_json
            respuesta_seleccionada = None
            for opcion_id, datos in respuestas.items():
                if datos.get('pregunta_id') == pregunta_actual.id:
                    respuesta_seleccionada = int(opcion_id)
                    break
            
            context['respuesta_seleccionada'] = respuesta_seleccionada
            
            # Calcular número de pregunta (posición en el recorrido)
            context['numero_pregunta'] = len(respuestas) + 1
            
            # Verificar si es la última pregunta (todas las opciones son finales)
            context['es_ultima_pregunta'] = all(
                opcion.es_respuesta_final or not opcion.pregunta_siguiente 
                for opcion in opciones
            )
        
        # Información de progreso
        respondidas, total, porcentaje = self.calcular_progreso()
        context['preguntas_respondidas'] = respondidas
        context['total_preguntas'] = total
        context['progreso_porcentaje'] = porcentaje
        
        # Verificar si hay pregunta anterior
        context['hay_pregunta_anterior'] = len(self.evaluacion.respuestas_json) > 0
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesar respuesta del usuario"""
        # Debug temporal
        print(f"POST data recibido: {dict(request.POST)}")
        print(f"Método: {request.method}")
        
        accion = request.POST.get('accion')
        respuesta = request.POST.get('respuesta')
        
        print(f"Acción extraída: '{accion}'")
        print(f"Respuesta extraída: '{respuesta}'")
        
        if accion == 'anterior':
            print("Procesando acción: anterior")
            return self.ir_pregunta_anterior()
        elif accion == 'siguiente':
            print("Procesando acción: siguiente")
            return self.procesar_respuesta()
        else:
            print(f"Acción no reconocida: '{accion}'. Mostrando formulario.")
        
        return self.get(request, *args, **kwargs)
    
    def ir_pregunta_anterior(self):
        """Volver a la pregunta anterior eliminando la última respuesta"""
        respuestas = self.evaluacion.respuestas_json.copy()
        
        if respuestas:
            # Eliminar la última respuesta
            ultima_clave = list(respuestas.keys())[-1]
            del respuestas[ultima_clave]
            
            # Actualizar la evaluación
            self.evaluacion.respuestas_json = respuestas
            self.evaluacion.save()
            
            messages.info(
                self.request,
                "Has vuelto a la pregunta anterior. Puedes cambiar tu respuesta."
            )
        
        return redirect(
            'security_probabilistic:realizar_evaluacion',
            evaluacion_id=self.evaluacion.id
        )
    
    def procesar_respuesta(self):
        """Procesar la respuesta seleccionada y avanzar"""
        respuesta_id = self.request.POST.get('respuesta')
        
        # Debug temporal
        print(f"[PROCESAR_RESPUESTA] Iniciando con respuesta_id: {respuesta_id}")
        
        if not respuesta_id:
            print("[PROCESAR_RESPUESTA] ERROR: No se recibió respuesta_id")
            messages.error(self.request, "Debe seleccionar una opción para continuar.")
            return self.get(self.request)
        
        try:
            opcion_seleccionada = OpcionRespuesta.objects.get(id=respuesta_id)
            
            # Verificar que la opción pertenece a la pregunta actual
            pregunta_actual = self.get_pregunta_actual()
            if opcion_seleccionada.pregunta != pregunta_actual:
                messages.error(self.request, "Respuesta inválida.")
                return self.get(self.request)
            
            # Log para debugging
            logger.info(
                f"Evaluación {self.evaluacion.id}: Respuesta {respuesta_id} "
                f"para pregunta {pregunta_actual.id}. "
                f"Siguiente: {opcion_seleccionada.pregunta_siguiente.id if opcion_seleccionada.pregunta_siguiente else 'None'}, "
                f"Final: {opcion_seleccionada.es_respuesta_final}"
            )
            
            # Guardar la respuesta
            respuestas = self.evaluacion.respuestas_json.copy()
            respuestas[str(respuesta_id)] = {
                'pregunta_id': pregunta_actual.id,
                'pregunta_texto': pregunta_actual.texto,
                'opcion_texto': opcion_seleccionada.texto,
                'valor_ponderado': float(opcion_seleccionada.valor_ponderado),
                'var_amenaza': pregunta_actual.var_amenaza,
                'timestamp': timezone.now().isoformat()
            }
            
            self.evaluacion.respuestas_json = respuestas
            self.evaluacion.estado = 'en_progreso'
            
            # Verificar si la evaluación debe completarse
            debe_completar = False
            
            # Caso 1: Es respuesta final y no hay pregunta siguiente
            if opcion_seleccionada.es_respuesta_final and not opcion_seleccionada.pregunta_siguiente:
                debe_completar = True
                logger.info(f"Evaluación {self.evaluacion.id}: Completando por respuesta final sin siguiente")
            
            # Caso 2: No hay más preguntas que seguir
            elif not opcion_seleccionada.pregunta_siguiente and not opcion_seleccionada.es_respuesta_final:
                debe_completar = True
                logger.info(f"Evaluación {self.evaluacion.id}: Completando por falta de pregunta siguiente")
            
            if debe_completar:
                self.completar_evaluacion()
                
                messages.success(
                    self.request,
                    f"¡Evaluación completada exitosamente! "
                    f"Se ha calculado el nivel de riesgo."
                )
                
                return redirect(
                    'security_probabilistic:detalle_perfil',
                    pk=self.evaluacion.perfil.pk
                )
            
            self.evaluacion.save()
            
            return redirect(
                'security_probabilistic:realizar_evaluacion',
                evaluacion_id=self.evaluacion.id
            )
            
        except OpcionRespuesta.DoesNotExist:
            messages.error(self.request, "Opción de respuesta inválida.")
            return self.get(self.request)
        except Exception as e:
            logger.error(f"Error al procesar respuesta: {str(e)}")
            messages.error(
                self.request,
                "Ocurrió un error al procesar la respuesta. Inténtelo nuevamente."
            )
            return self.get(self.request)
    
    def completar_evaluacion(self):
        """Completar la evaluación y calcular resultados"""
        try:
            # Calcular probabilidad total
            probabilidad_total = 0
            respuestas = self.evaluacion.respuestas_json
            
            for datos_respuesta in respuestas.values():
                probabilidad_total += datos_respuesta.get('valor_ponderado', 0)
            
            # Determinar nivel de riesgo basado en la probabilidad
            if probabilidad_total >= 0.8:
                nivel_riesgo = 'muy_alto'
            elif probabilidad_total >= 0.6:
                nivel_riesgo = 'alto'
            elif probabilidad_total >= 0.4:
                nivel_riesgo = 'medio'
            elif probabilidad_total >= 0.2:
                nivel_riesgo = 'bajo'
            else:
                nivel_riesgo = 'muy_bajo'
            
            # Actualizar la evaluación
            self.evaluacion.probabilidad_total = probabilidad_total
            self.evaluacion.nivel_riesgo = nivel_riesgo
            self.evaluacion.estado = 'completada'
            self.evaluacion.completada_en = timezone.now()
            self.evaluacion.save()
            
            # Log del resultado
            logger.info(
                f"Evaluación completada - ID: {self.evaluacion.id}, "
                f"Probabilidad: {probabilidad_total:.3f}, "
                f"Nivel de riesgo: {nivel_riesgo}"
            )
            
        except Exception as e:
            logger.error(f"Error al completar evaluación: {str(e)}")
            raise


# === VISTAS API PARA DATOS GEOGRÁFICOS ===

from django.http import JsonResponse
from .models import Departamento, Municipio

@login_required
@requires_security_probabilistic()
@evaluador_module_required('security_probabilistic')
@evaluador_permission_required('security_probabilistic', 'read')
def api_departamentos(request):
    """API para obtener lista de departamentos"""
    try:
        departamentos = Departamento.objects.all().order_by('nombre')
        data = []
        
        for dept in departamentos:
            municipios_count = dept.municipios.count()
            data.append({
                'id': dept.id,
                'codigo_dane': dept.codigo_dane,
                'nombre': dept.nombre,
                'region': dept.region,
                'nivel_riesgo': dept.nivel_riesgo,
                'municipios_count': municipios_count
            })
        
        return JsonResponse({
            'success': True,
            'departamentos': data,
            'total': len(data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@requires_security_probabilistic()
@evaluador_module_required('security_probabilistic')
@evaluador_permission_required('security_probabilistic', 'read')
def api_municipios(request):
    """API para obtener municipios por departamento(s)"""
    try:
        departamentos_ids = request.GET.getlist('departamentos[]')
        
        if not departamentos_ids:
            return JsonResponse({
                'success': False,
                'error': 'No se especificaron departamentos'
            })
        
        municipios = Municipio.objects.filter(
            departamento_id__in=departamentos_ids
        ).select_related('departamento').order_by('departamento__nombre', 'nombre')
        
        data = {}
        for municipio in municipios:
            dept_id = str(municipio.departamento.id)
            if dept_id not in data:
                data[dept_id] = {
                    'departamento': {
                        'id': municipio.departamento.id,
                        'nombre': municipio.departamento.nombre,
                        'codigo_dane': municipio.departamento.codigo_dane
                    },
                    'municipios': []
                }
            
            data[dept_id]['municipios'].append({
                'id': municipio.id,
                'codigo_dane': municipio.codigo_dane,
                'nombre': municipio.nombre,
                'categoria': municipio.categoria,
                'nivel_riesgo': municipio.nivel_riesgo
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'total_municipios': municipios.count()
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


class DetalleEvaluacionView(AccessControlMixin, EvaluadorPermissionMixin, DetailView):
    """Vista para mostrar el detalle completo de una evaluación específica"""
    model = EvaluacionSeguridad
    template_name = 'security_probabilistic/detalle_evaluacion.html'
    context_object_name = 'evaluacion'
    required_module = 'security_probabilistic'
    evaluador_module = 'security_probabilistic'
    required_permission = 'read'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evaluacion = self.get_object()
        
        # Calcular estadísticas adicionales
        if evaluacion.estado == 'completada':
            # Obtener el cálculo completo del promedio
            calculo_completo = evaluacion.calcular_promedio_completo()
            context['calculo_completo'] = calculo_completo
            
            # Analizar respuestas por variable de amenaza
            variables_amenaza = {}
            if evaluacion.respuestas_json:
                for opcion_id, datos in evaluacion.respuestas_json.items():
                    var_amenaza = datos.get('var_amenaza', 'Sin clasificar')
                    if var_amenaza not in variables_amenaza:
                        variables_amenaza[var_amenaza] = {
                            'total': 0,
                            'suma_valores': 0,
                            'respuestas': []
                        }
                    variables_amenaza[var_amenaza]['total'] += 1
                    variables_amenaza[var_amenaza]['suma_valores'] += datos.get('valor_ponderado', 0)
                    variables_amenaza[var_amenaza]['respuestas'].append(datos)
            
            context['variables_amenaza'] = variables_amenaza
            
            # Información sobre el árbol de decisión utilizado
            context['arbol_info'] = {
                'total_preguntas': evaluacion.arbol.preguntas.count() if evaluacion.arbol else 0,
                'respondidas': len(evaluacion.respuestas_json) if evaluacion.respuestas_json else 0
            }
        
        return context


# === GESTIÓN DE PERFILES ===

class CrearPerfilView(AccessControlMixin, EvaluadorPermissionMixin, CreatedByMixin, CreateView):
    """Vista para crear un nuevo perfil de seguridad"""
    model = PerfilSeguridad
    template_name = 'security_probabilistic/crear_perfil.html'
    success_url = reverse_lazy('security_probabilistic:lista_perfiles')
    required_module = 'security_probabilistic'
    evaluador_module = 'security_probabilistic'
    required_permission = 'create'
    
    def get_form_class(self):
        from .forms_perfil import PerfilForm
        return PerfilForm
    
    def form_valid(self, form):
        # Asignar el usuario actual como propietario
        if not form.instance.owner:
            form.instance.owner = self.request.user
            
        logger.info(f"✅ Nuevo perfil creado: {form.cleaned_data.get('nombres', '')} {form.cleaned_data.get('apellidos', '')}")
        messages.success(self.request, 'Perfil de seguridad creado exitosamente.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        logger.error(f"❌ Error al crear perfil: {form.errors}")
        messages.error(self.request, 'Error al crear el perfil. Por favor revise los datos.')
        return super().form_invalid(form)


class EditarPerfilView(AccessControlMixin, EvaluadorPermissionMixin, UpdateView):
    """Vista para editar un perfil de seguridad existente"""
    model = PerfilSeguridad
    template_name = 'security_probabilistic/editar_perfil.html'
    success_url = reverse_lazy('security_probabilistic:lista_perfiles')
    required_module = 'security_probabilistic'
    evaluador_module = 'security_probabilistic'
    required_permission = 'update'
    
    def get_form_class(self):
        from .forms_perfil import PerfilForm
        return PerfilForm
    
    def form_valid(self, form):
        logger.info(f"✅ Perfil actualizado: {self.object.nombre_completo}")
        messages.success(self.request, 'Perfil actualizado exitosamente.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        logger.error(f"❌ Error al actualizar perfil {self.object.pk}: {form.errors}")
        messages.error(self.request, 'Error al actualizar el perfil. Por favor revise los datos.')
        return super().form_invalid(form)
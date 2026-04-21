from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.http import JsonResponse, Http404
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
import logging

from .models import ArbolDecision, EvaluacionSeguridad, Pregunta, OpcionRespuesta, ZonaRiesgo, PerfilSeguridad
from .forms import IniciarEvaluacionForm, ResponderPreguntaForm, FiltroEvaluacionesForm
from .forms_perfil import PerfilForm
from .services import MotorEvaluacionSeguridad, GeneradorReportes

logger = logging.getLogger(__name__)


class RedirectToPerfilesView(View):
    """Vista para redireccionar desde la URL antigua /evaluacion/nueva/ a la lista de perfiles"""
    def get(self, request, *args, **kwargs):
        messages.info(
            request, 
            'Para iniciar una evaluación, primero debe seleccionar un perfil de seguridad.'
        )
        return redirect('security_probabilistic:lista_perfiles')


class DashboardView(TemplateView):
    """Vista principal del dashboard de evaluaciones de seguridad - Acceso público"""
    template_name = 'security_probabilistic/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Estadísticas generales del sistema
        context['total_perfiles'] = PerfilSeguridad.objects.count()
        context['perfiles_activos'] = PerfilSeguridad.objects.filter(estado_perfil='activo').count()
        
        # Estadísticas generales de evaluaciones
        todas_evaluaciones = EvaluacionSeguridad.objects.all()
        context['total_evaluaciones'] = todas_evaluaciones.count()
        context['evaluaciones_completadas'] = todas_evaluaciones.filter(estado='completada').count()
        context['evaluaciones_pendientes'] = todas_evaluaciones.filter(estado__in=['iniciada', 'en_progreso']).count()
        
        # Última evaluación del sistema
        context['ultima_evaluacion'] = todas_evaluaciones.order_by('-creada_en').first()
        
        # Evaluaciones recientes del sistema
        context['evaluaciones_recientes'] = todas_evaluaciones.order_by('-creada_en')[:5]
        
        # Perfiles disponibles para evaluar (público)
        context['perfiles_disponibles'] = PerfilSeguridad.objects.filter(
            estado_perfil='activo'
        ).order_by('-creado_en')[:10]
        
        return context


class CrearPerfilView(CreateView):
    """Vista para crear un nuevo perfil de seguridad - Sistema independiente"""
    model = PerfilSeguridad
    form_class = PerfilForm
    template_name = 'security_probabilistic/crear_perfil_mejorado.html'
    success_url = reverse_lazy('security_probabilistic:lista_perfiles')
    
    def dispatch(self, request, *args, **kwargs):
        logger.info(f"🌐 DISPATCH - Método: {request.method}, Path: {request.path}")
        logger.info(f"🌐 DISPATCH - User: {request.user}, Autenticado: {request.user.is_authenticated}")
        logger.info(f"🌐 DISPATCH - Content-Type: {request.content_type}")
        print(f"🌐 CONSOLE - Método: {request.method}, Path: {request.path}")
        print(f"🌐 CONSOLE - User: {request.user}, Autenticado: {request.user.is_authenticated}")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        logger.info(f"🔍 GET request - Usuario: {request.user}, Autenticado: {request.user.is_authenticated}")
        print(f"🔍 CONSOLE GET request - Usuario: {request.user}")
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        logger.info(f"🚀 POST request recibido - Usuario: {request.user}")
        logger.info(f"📋 Datos POST: {request.POST}")
        print(f"🚀 CONSOLE POST request recibido - Usuario: {request.user}")
        print(f"📋 CONSOLE Datos POST: {request.POST}")
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        logger.info(f"✅ Formulario válido - Guardando perfil...")
        logger.info(f"📊 Datos del formulario: {form.cleaned_data}")
        print(f"✅ CONSOLE Formulario válido - Guardando perfil...")
        print(f"📊 CONSOLE Datos del formulario: {form.cleaned_data}")
        messages.success(self.request, 'Perfil de seguridad creado exitosamente.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        logger.error(f"❌ Formulario inválido")
        logger.error(f"🔍 Errores del formulario: {form.errors}")
        logger.error(f"📋 Datos enviados: {form.data}")
        print(f"❌ CONSOLE Formulario inválido")
        print(f"🔍 CONSOLE Errores del formulario: {form.errors}")
        print(f"📋 CONSOLE Datos enviados: {form.data}")
        messages.error(self.request, 'Error al crear el perfil. Por favor revise los datos ingresados.')
        return super().form_invalid(form)


class ListaPerfilesView(ListView):
    """Vista mejorada para mostrar lista de perfiles de seguridad con filtros avanzados"""
    model = PerfilSeguridad
    template_name = 'security_probabilistic/lista_perfiles.html'
    context_object_name = 'perfiles'
    paginate_by = 20
    
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


class DetallePerfilView(DetailView):
    """Vista para mostrar detalle de un perfil específico con todas sus evaluaciones - Acceso público"""
    model = PerfilSeguridad
    template_name = 'security_probabilistic/evaluaciones_detalle_perfil.html'
    context_object_name = 'perfil'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de filtro
        estado_filtro = self.request.GET.get('estado', '')
        nivel_riesgo_filtro = self.request.GET.get('nivel_riesgo', '')
        orden = self.request.GET.get('orden', '-creada_en')
        
        # Queryset base de evaluaciones
        evaluaciones_qs = EvaluacionSeguridad.objects.filter(
            perfil=self.object
        )
        
        # Aplicar filtros
        if estado_filtro:
            evaluaciones_qs = evaluaciones_qs.filter(estado=estado_filtro)
        
        if nivel_riesgo_filtro:
            evaluaciones_qs = evaluaciones_qs.filter(nivel_riesgo=nivel_riesgo_filtro)
        
        # Aplicar ordenamiento
        evaluaciones_qs = evaluaciones_qs.order_by(orden)
        
        # Paginación
        from django.core.paginator import Paginator
        paginator = Paginator(evaluaciones_qs, self.paginate_by)
        page_number = self.request.GET.get('page')
        evaluaciones_page = paginator.get_page(page_number)
        
        # Estadísticas generales
        todas_evaluaciones = EvaluacionSeguridad.objects.filter(perfil=self.object)
        evaluaciones_completadas = todas_evaluaciones.filter(estado='completada')
        evaluaciones_pendientes = todas_evaluaciones.exclude(estado='completada')
        
        # Último nivel de riesgo
        ultima_evaluacion_completada = evaluaciones_completadas.order_by('-completada_en').first()
        
        context.update({
            'evaluaciones': evaluaciones_page,
            'total_evaluaciones': todas_evaluaciones.count(),
            'evaluaciones_completadas': evaluaciones_completadas.count(),
            'evaluaciones_pendientes': evaluaciones_pendientes.count(),
            'puede_evaluar': self.object.puede_ser_evaluado(),
            
            # Último nivel de riesgo
            'ultimo_nivel_riesgo': ultima_evaluacion_completada.nivel_riesgo if ultima_evaluacion_completada else None,
            'ultima_probabilidad': ultima_evaluacion_completada.probabilidad_total if ultima_evaluacion_completada else None,
            'ultima_fecha': ultima_evaluacion_completada.completada_en if ultima_evaluacion_completada else None,
            
            # Para filtros
            'estados_choices': EvaluacionSeguridad.ESTADO_CHOICES,
            'filtro_actual': {
                'estado': estado_filtro,
                'nivel_riesgo': nivel_riesgo_filtro,
                'orden': orden,
            }
        })
        
        return context


class EditarPerfilView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vista para editar un perfil de seguridad (solo staff)"""
    model = PerfilSeguridad
    form_class = PerfilForm
    template_name = 'security_probabilistic/editar_perfil.html'
    success_url = reverse_lazy('security_probabilistic:lista_perfiles')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, *args, **kwargs):
        """Debug del POST request"""
        print(f"🔍 POST recibido - Usuario: {request.user.username}")
        print(f"📝 Datos POST completos:")
        for key, value in request.POST.items():
            print(f"    {key}: '{value}'")
        print(f"🆔 PK del objeto: {kwargs.get('pk')}")
        
        # Obtener el objeto para el formulario
        self.object = self.get_object()
        form = self.get_form()
        
        print(f"📋 ¿Formulario válido?: {form.is_valid()}")
        if not form.is_valid():
            print(f"❌ Errores del formulario:")
            for field, errors in form.errors.items():
                print(f"    {field}: {errors}")
            if form.non_field_errors():
                print(f"    Non-field errors: {form.non_field_errors()}")
        
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        print("✅ form_valid llamado - El formulario es válido")
        messages.success(self.request, 'Perfil actualizado exitosamente.')
        result = super().form_valid(form)
        print(f"🔄 Redirigiendo a: {self.success_url}")
        return result
    
    def form_invalid(self, form):
        print("❌ form_invalid llamado - El formulario tiene errores")
        print(f"🚫 Errores: {form.errors}")
        messages.error(self.request, 'Error al actualizar el perfil. Por favor revise los datos.')
        return super().form_invalid(form)


# Vista para iniciar evaluación - ahora requiere seleccionar un perfil
class IniciarEvaluacionView(TemplateView):
    """Vista para iniciar una nueva evaluación para un perfil específico - Acceso público"""
    template_name = 'security_probabilistic/iniciar_evaluacion.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil_id = kwargs.get('perfil_id')
        
        try:
            # Obtener el perfil específico - usar get() en lugar de get_object_or_404
            perfil = PerfilSeguridad.objects.get(id=perfil_id, estado_perfil='activo')
            context['perfil'] = perfil
            
            # Contar evaluaciones existentes del perfil
            total_evaluaciones = EvaluacionSeguridad.objects.filter(perfil=perfil).count()
            context['total_evaluaciones'] = total_evaluaciones
            
            # Instanciar el formulario para los datos del evaluador
            context['form'] = IniciarEvaluacionForm()
            
            # Obtener árboles de decisión disponibles
            context['arboles_disponibles'] = ArbolDecision.objects.filter(activo=True)
            
        except PerfilSeguridad.DoesNotExist:
            messages.error(self.request, 'El perfil solicitado no existe o no está activo.')
            context['perfil'] = None
            context['form'] = None
            context['total_evaluaciones'] = 0
            context['arboles_disponibles'] = []
            
        return context
    
    def post(self, request, perfil_id):
        form = IniciarEvaluacionForm(request.POST)
        
        # Obtener el perfil desde la URL
        try:
            perfil = PerfilSeguridad.objects.get(id=perfil_id, estado_perfil='activo')
        except PerfilSeguridad.DoesNotExist:
            messages.error(request, 'El perfil solicitado no existe o no está activo.')
            return redirect('security_probabilistic:lista_perfiles')
        
        if form.is_valid():
            try:
                arbol = form.cleaned_data['arbol']
                
                if not perfil.puede_ser_evaluado():
                    messages.error(request, 'El perfil seleccionado no está disponible para evaluación.')
                    return self.form_invalid(form)
                
                # Crear nueva evaluación con los datos del formulario
                evaluador_nombre = form.cleaned_data['evaluador_nombre']
                evaluador_email = form.cleaned_data.get('evaluador_email', '')
                evaluador_organizacion = form.cleaned_data.get('evaluador_organizacion', '')
                evaluador_cargo = form.cleaned_data.get('evaluador_cargo', '')
                
                # Si hay usuario autenticado, dar opción de usar sus datos
                if request.user.is_authenticated and not evaluador_email:
                    evaluador_email = request.user.email
                
                evaluacion = EvaluacionSeguridad.objects.create(
                    perfil=perfil,
                    arbol=arbol,
                    evaluador_nombre=evaluador_nombre,
                    evaluador_email=evaluador_email,
                    estado='iniciada',
                    respuestas_json={
                        'fecha_inicio': timezone.now().isoformat(),
                        'ip_evaluador': self.get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'configuracion_inicial': {
                            'arbol_id': arbol.id,
                            'perfil_id': perfil.id,
                            'evaluador_info': {
                                'nombre': evaluador_nombre,
                                'email': evaluador_email,
                                'organizacion': evaluador_organizacion,
                                'cargo': evaluador_cargo
                            }
                        }
                    }
                )
                
                # Registrar el evento de inicio
                logger.info(
                    f"Nueva evaluación iniciada: ID={evaluacion.id}, "
                    f"Perfil={perfil.nombre_completo()}, "
                    f"Evaluador={evaluador_nombre}, "
                    f"IP={self.get_client_ip(request)}"
                )
                
                messages.success(
                    request, 
                    f'Evaluación iniciada correctamente para {perfil.nombre_completo()}.'
                )
                
                return redirect('security_probabilistic:continuar_evaluacion', 
                               evaluacion_id=evaluacion.id)
                
            except Exception as e:
                logger.error(f"Error al iniciar evaluación: {str(e)}")
                messages.error(request, 'Error al iniciar la evaluación. Intente nuevamente.')
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Manejar formulario inválido"""
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)
    
    def get_client_ip(self, request):
        """Obtener IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Vistas de evaluación (placeholders)
class ContinuarEvaluacionView(TemplateView):
    template_name = 'security_probabilistic/dashboard.html'
    
    def get(self, request, evaluacion_id):
        messages.info(request, 'Funcionalidad en desarrollo.')
        return redirect('security_probabilistic:dashboard')


class ResponderPreguntaView(TemplateView):
    template_name = 'security_probabilistic/dashboard.html'
    
    def get(self, request, evaluacion_id, pregunta_id):
        messages.info(request, 'Funcionalidad en desarrollo.')
        return redirect('security_probabilistic:dashboard')


class PreguntaAnteriorView(TemplateView):
    template_name = 'security_probabilistic/dashboard.html'
    
    def get(self, request, evaluacion_id):
        messages.info(request, 'Funcionalidad en desarrollo.')
        return redirect('security_probabilistic:dashboard')


class ResultadoEvaluacionView(TemplateView):
    template_name = 'security_probabilistic/dashboard.html'
    
    def get(self, request, evaluacion_id):
        messages.info(request, 'Funcionalidad en desarrollo.')
        return redirect('security_probabilistic:dashboard')


class ListaEvaluacionesView(ListView):
    """Vista para listar todas las evaluaciones del sistema"""
    model = EvaluacionSeguridad
    template_name = 'security_probabilistic/lista_evaluaciones.html'
    context_object_name = 'evaluaciones'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EvaluacionSeguridad.objects.select_related('perfil', 'arbol').order_by('-creada_en')
        
        # Filtros opcionales
        estado = self.request.GET.get('estado')
        perfil_id = self.request.GET.get('perfil_id')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if perfil_id:
            queryset = queryset.filter(perfil_id=perfil_id)
            
        return queryset


# Vistas de administración (placeholders)
class GestionArbolesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'security_probabilistic/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request):
        messages.info(request, 'Funcionalidad en desarrollo.')
        return redirect('security_probabilistic:dashboard')


class DetalleArbolView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'security_probabilistic/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request, arbol_id):
        messages.info(request, 'Funcionalidad en desarrollo.')
        return redirect('security_probabilistic:dashboard')


class EditarArbolView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'security_probabilistic/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request, arbol_id):
        messages.info(request, 'Funcionalidad en desarrollo.')
        return redirect('security_probabilistic:dashboard')


class EstadisticasView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'security_probabilistic/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request):
        messages.info(request, 'Funcionalidad en desarrollo.')
        return redirect('security_probabilistic:dashboard')


# Vistas API (placeholders)
class SiguientePreguntaAPIView(LoginRequiredMixin, View):
    def get(self, request, evaluacion_id):
        return JsonResponse({'status': 'development', 'message': 'API en desarrollo'})


class GuardarRespuestaAPIView(LoginRequiredMixin, View):
    def post(self, request, evaluacion_id):
        return JsonResponse({'status': 'development', 'message': 'API en desarrollo'})


class ZonasRiesgoAPIView(LoginRequiredMixin, View):
    def get(self, request):
        return JsonResponse({'status': 'development', 'message': 'API en desarrollo'})


class PerfilAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    """API para obtener datos de un perfil específico"""
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get(self, request, perfil_id):
        try:
            perfil = get_object_or_404(PerfilSeguridad, id=perfil_id)
            
            data = {
                'nombres': perfil.nombres,
                'apellidos': perfil.apellidos,
                'tipo_documento': perfil.tipo_documento,
                'numero_documento': perfil.numero_documento,
                'genero': perfil.genero,
                'fecha_nacimiento': perfil.fecha_nacimiento.strftime('%Y-%m-%d') if perfil.fecha_nacimiento else '',
                'telefono_principal': perfil.telefono_principal,
                'telefono_emergencia': perfil.telefono_emergencia or '',
                'cargo_politico': perfil.cargo_politico,
                'partido_politico': perfil.partido_politico or '',
                'direccion_trabajo': perfil.direccion_trabajo or '',
                'nivel_exposicion': perfil.nivel_exposicion,
            }
            
            return JsonResponse({'success': True, 'data': data})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class EditarPerfilAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    """API para actualizar datos de un perfil específico"""
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def post(self, request, perfil_id):
        try:
            perfil = get_object_or_404(PerfilSeguridad, id=perfil_id)
            
            # Actualizar campos del perfil
            perfil.nombres = request.POST.get('nombres', perfil.nombres)
            perfil.apellidos = request.POST.get('apellidos', perfil.apellidos)
            perfil.tipo_documento = request.POST.get('tipo_documento', perfil.tipo_documento)
            perfil.numero_documento = request.POST.get('numero_documento', perfil.numero_documento)
            perfil.genero = request.POST.get('genero', perfil.genero)
            
            # Fecha de nacimiento
            fecha_nacimiento = request.POST.get('fecha_nacimiento')
            if fecha_nacimiento:
                from datetime import datetime
                try:
                    perfil.fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            perfil.telefono_principal = request.POST.get('telefono_principal', perfil.telefono_principal)
            perfil.telefono_emergencia = request.POST.get('telefono_emergencia', '')
            perfil.cargo_politico = request.POST.get('cargo_politico', perfil.cargo_politico)
            perfil.partido_politico = request.POST.get('partido_politico', perfil.partido_politico)
            perfil.direccion_trabajo = request.POST.get('direccion_trabajo', perfil.direccion_trabajo)
            perfil.nivel_exposicion = request.POST.get('nivel_exposicion', perfil.nivel_exposicion)
            
            perfil.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Perfil de {perfil.nombre_completo} actualizado exitosamente.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

"""
Vistas para el proceso de evaluación paso a paso
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import json
import logging

# Configurar logger
logger = logging.getLogger(__name__)

from apps.subscriptions.decorators import subscription_required
from .models import (
    Conjunto, TipoRiesgo, EscenarioRiesgo, PreguntaEvaluacion,
    EvaluacionRiesgo, RespuestaPregunta, ResultadoPregunta, ComentarioRiesgo, ArchivoEvaluacion,
    CalificacionOpcion
)
from .forms_evaluacion import (
    SeleccionRiesgosForm, InformacionEvaluacionForm, RespuestaPreguntaForm,
    ObservacionesRecomendacionesForm, ConfirmacionEvaluacionForm, ArchivoEvaluacionForm
)
from .forms import ComentarioRiesgoForm


def get_conjunto_with_permissions(conjunto_id, user):
    """
    Helper function para obtener un conjunto verificando permisos de forma estricta.
    Lanza PermissionDenied si el usuario no tiene acceso.
    """
    conjunto = get_object_or_404(Conjunto, id=conjunto_id, activo=True)

    # Superusuario y staff tienen acceso completo
    if user.is_superuser or user.is_staff:
        return conjunto

    # Verificar propiedad directa
    if conjunto.propietario_id != user.pk:
        logger.warning(
            "Acceso denegado al conjunto %s por usuario %s (id=%s)",
            conjunto_id, user.username, user.pk
        )
        raise PermissionDenied("No tienes permisos para acceder a este conjunto")

    return conjunto


@login_required
@subscription_required('risk_conjuntos')
def iniciar_evaluacion(request, conjunto_id):
    """
    Redirecciona directamente al paso 1 de la evaluación
    """
    conjunto = get_conjunto_with_permissions(conjunto_id, request.user)
    
    # Redirigir directamente al paso 1
    return redirect('risk_conjuntos:paso_1_seleccion_riesgos', conjunto_id=conjunto_id)


@login_required
@subscription_required('risk_conjuntos')
def paso_1_seleccion_riesgos(request, conjunto_id):
    """
    Paso 1: Selección de tipos de riesgos a evaluar
    """
    conjunto = get_conjunto_with_permissions(conjunto_id, request.user)
    
    if request.method == 'POST':
        form = SeleccionRiesgosForm(request.POST)
        info_form = InformacionEvaluacionForm(request.POST)
        
        if form.is_valid() and info_form.is_valid():
            riesgos_seleccionados = form.get_riesgos_seleccionados()
            
            if not riesgos_seleccionados:
                messages.error(request, 'Debe seleccionar al menos un tipo de riesgo para evaluar.')
                return render(request, 'risk_conjuntos/evaluacion/paso_1.html', {
                    'conjunto': conjunto,
                    'form': form,
                    'info_form': info_form
                })
            
            # Guardar en sesión
            request.session['evaluacion_data'] = {
                'conjunto_id': str(conjunto_id),
                'riesgos_seleccionados': riesgos_seleccionados,
                'tipo_evaluacion': info_form.cleaned_data['tipo_evaluacion'],
                'paso_actual': 2
            }
            
            return redirect('risk_conjuntos:paso_2_preguntas', conjunto_id=conjunto_id, riesgo_index=0)
    else:
        form = SeleccionRiesgosForm(initial={'conjunto': conjunto_id})
        info_form = InformacionEvaluacionForm()
    
    # Obtener información de riesgos con conteos
    tipos_riesgos = TipoRiesgo.objects.filter(activo=True).order_by('orden')
    riesgos_info = []
    
    for tipo in tipos_riesgos:
        escenarios_count = EscenarioRiesgo.objects.filter(tipo_riesgo=tipo, activo=True).count()
        preguntas_count = PreguntaEvaluacion.objects.filter(
            escenario__tipo_riesgo=tipo, activa=True
        ).count()
        
        riesgos_info.append({
            'tipo': tipo,
            'escenarios_count': escenarios_count,
            'preguntas_count': preguntas_count
        })
    
    context = {
        'conjunto': conjunto,
        'form': form,
        'info_form': info_form,
        'riesgos_info': riesgos_info,
        'paso': 1,
        'total_pasos': 4
    }
    
    return render(request, 'risk_conjuntos/evaluacion/paso_1.html', context)


@login_required
@subscription_required('risk_conjuntos')
def paso_2_preguntas(request, conjunto_id, riesgo_index=0):
    """
    Paso 2: Responder preguntas por tipo de riesgo
    """
    conjunto = get_conjunto_with_permissions(conjunto_id, request.user)
    
    # Verificar datos de sesión
    evaluacion_data = request.session.get('evaluacion_data')
    if not evaluacion_data or evaluacion_data.get('conjunto_id') != str(conjunto_id):
        messages.error(request, 'Datos de evaluación no encontrados. Debe comenzar desde el paso 1.')
        return redirect('risk_conjuntos:paso_1_seleccion_riesgos', conjunto_id=conjunto_id)
    
    riesgos_seleccionados = evaluacion_data['riesgos_seleccionados']
    
    # Verificar índice válido
    if riesgo_index >= len(riesgos_seleccionados):
        logger.info(f"Índice fuera de rango, redirigiendo al paso 3")
        return redirect('risk_conjuntos:paso_3_observaciones', conjunto_id=conjunto_id)
    
    # Obtener el tipo de riesgo actual
    tipo_riesgo_id = riesgos_seleccionados[riesgo_index]
    tipo_riesgo = get_object_or_404(TipoRiesgo, id=tipo_riesgo_id)
    
    # Obtener preguntas activas para este tipo de riesgo
    preguntas = PreguntaEvaluacion.objects.filter(
        escenario__tipo_riesgo=tipo_riesgo,
        activa=True
    ).select_related('escenario').order_by('escenario__orden', 'orden')
    
    if not preguntas.exists():
        messages.warning(request, f'No hay preguntas disponibles para {tipo_riesgo.nombre}.')
        return redirect('risk_conjuntos:paso_2_preguntas', 
                       conjunto_id=conjunto_id, riesgo_index=riesgo_index + 1)
    
    if request.method == 'POST':
        todas_validas = True
        respuestas_data = []
        
        # Obtener comentario general del riesgo
        comentario_riesgo = request.POST.get('comentario_riesgo', '')
        
        for pregunta in preguntas:
            form = RespuestaPreguntaForm(pregunta, request.POST, prefix=str(pregunta.id))
            if form.is_valid():
                respuestas_data.append({
                    'pregunta_id': pregunta.id,
                    'calificacion_id': form.cleaned_data['calificacion'].id,
                    # Ya no se manejan comentarios individuales
                })
            else:
                todas_validas = False
        
        if todas_validas:
            # Guardar respuestas en sesión
            if 'respuestas' not in evaluacion_data:
                evaluacion_data['respuestas'] = {}
            
            evaluacion_data['respuestas'][str(tipo_riesgo_id)] = respuestas_data
            
            # Guardar comentario general del riesgo
            if 'comentarios_riesgo' not in evaluacion_data:
                evaluacion_data['comentarios_riesgo'] = {}
            
            evaluacion_data['comentarios_riesgo'][str(tipo_riesgo_id)] = comentario_riesgo
            request.session['evaluacion_data'] = evaluacion_data
            
            # Ir al siguiente riesgo
            next_index = riesgo_index + 1
            if next_index < len(riesgos_seleccionados):
                logger.info(f"Redirigiendo al siguiente riesgo: índice {next_index}")
                return redirect('risk_conjuntos:paso_2_preguntas', 
                               conjunto_id=conjunto_id, riesgo_index=next_index)
            else:
                logger.info("Todos los riesgos completados, yendo al paso 3")
                return redirect('risk_conjuntos:paso_3_observaciones', conjunto_id=conjunto_id)
    
    # Crear formularios para cada pregunta
    forms_preguntas = []
    for pregunta in preguntas:
        form = RespuestaPreguntaForm(pregunta, prefix=str(pregunta.id))
        forms_preguntas.append({
            'pregunta': pregunta,
            'form': form
        })
    
    # Información de progreso
    progreso = {
        'riesgo_actual': riesgo_index + 1,
        'total_riesgos': len(riesgos_seleccionados),
        'porcentaje': int(((riesgo_index + 1) / len(riesgos_seleccionados)) * 100)
    }
    
    # Cargar comentario existente para este riesgo
    comentario_inicial = ''
    if 'comentarios_riesgo' in evaluacion_data:
        comentario_inicial = evaluacion_data['comentarios_riesgo'].get(str(tipo_riesgo_id), '')
    
    # Formulario para comentario del riesgo
    comentario_form = ComentarioRiesgoForm(initial={'comentario_riesgo': comentario_inicial})
    
    context = {
        'conjunto': conjunto,
        'tipo_riesgo': tipo_riesgo,
        'forms_preguntas': forms_preguntas,
        'comentario_form': comentario_form,
        'progreso': progreso,
        'riesgo_index': riesgo_index,
        'paso': 2,
        'total_pasos': 4,
        'puede_retroceder': riesgo_index > 0
    }
    
    return render(request, 'risk_conjuntos/evaluacion/paso_2.html', context)


@login_required
@subscription_required('risk_conjuntos')
def paso_3_observaciones(request, conjunto_id):
    """
    Paso 3: Observaciones y recomendaciones generales con archivos adjuntos
    """
    conjunto = get_conjunto_with_permissions(conjunto_id, request.user)
    
    # Verificar datos de sesión
    evaluacion_data = request.session.get('evaluacion_data')
    if not evaluacion_data or evaluacion_data.get('conjunto_id') != str(conjunto_id):
        messages.error(request, 'Datos de evaluación no encontrados.')
        return redirect('risk_conjuntos:paso_1_seleccion_riesgos', conjunto_id=conjunto_id)
    
    if request.method == 'POST':
        observaciones_form = ObservacionesRecomendacionesForm(request.POST)
        archivo_form = ArchivoEvaluacionForm(request.POST, request.FILES)
        
        # Manejar subida de archivo si se envió uno
        if 'subir_archivo' in request.POST:
            print(f"DEBUG: Intento de subir archivo")
            print(f"DEBUG: Formulario válido: {archivo_form.is_valid()}")
            print(f"DEBUG: Errores del formulario: {archivo_form.errors}")
            
            if archivo_form.is_valid():
                from django.core.files.storage import default_storage
                from django.http import JsonResponse
                from django.conf import settings
                import os
                import uuid
                
                try:
                    print(f"DEBUG: Procesando archivo válido...")
                    # Crear directorio temporal si no existe
                    temp_dir = os.path.join(settings.MEDIA_ROOT, 'evaluaciones', 'temp')
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Guardar archivo temporalmente
                    archivo = archivo_form.cleaned_data['archivo']
                    print(f"DEBUG: Archivo recibido: {archivo.name}, Tamaño: {archivo.size}")
                    
                    extension = os.path.splitext(archivo.name)[1]
                    nombre_temporal = f"temp_{uuid.uuid4()}{extension}"
                    ruta_temporal = f"evaluaciones/temp/{nombre_temporal}"
                    
                    # Guardar archivo físicamente
                    ruta_guardada = default_storage.save(ruta_temporal, archivo)
                    print(f"DEBUG: Archivo guardado en: {ruta_guardada}")
                    
                    # Guardar información en sesión
                    if 'archivos_temporales' not in evaluacion_data:
                        evaluacion_data['archivos_temporales'] = []
                    
                    archivo_data = {
                        'tipo_archivo': archivo_form.cleaned_data['tipo_archivo'],
                        'descripcion': archivo_form.cleaned_data['descripcion'],
                        'nombre_original': archivo.name,
                        'ruta_temporal': ruta_guardada,
                        'tamaño': archivo.size
                    }
                    
                    evaluacion_data['archivos_temporales'].append(archivo_data)
                    request.session['evaluacion_data'] = evaluacion_data
                    
                    print(f"DEBUG: Archivo agregado a sesión. Total archivos: {len(evaluacion_data['archivos_temporales'])}")
                    
                    # Si es petición AJAX, devolver JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        print(f"DEBUG: Devolviendo respuesta JSON exitosa")
                        return JsonResponse({
                            'success': True,
                            'message': f'Archivo "{archivo.name}" agregado correctamente.',
                            'archivo': archivo_data
                        })
                        
                    messages.success(request, f'Archivo "{archivo.name}" agregado correctamente.')
                    return redirect('risk_conjuntos:paso_3_observaciones', conjunto_id=conjunto_id)
                    
                except Exception as e:
                    print(f"DEBUG: Error procesando archivo: {str(e)}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': f'Error al subir archivo: {str(e)}'
                        })
                    messages.error(request, f'Error al subir archivo: {str(e)}')
            else:
                # Formulario no válido
                print(f"DEBUG: Formulario no válido - Errores: {archivo_form.errors}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Formulario no válido',
                        'form_errors': archivo_form.errors
                    })
                messages.error(request, 'Error en el formulario de archivo')
        
        # Procesar formulario principal
        if 'continuar_paso_4' in request.POST and observaciones_form.is_valid():
            # Guardar observaciones y recomendaciones en sesión
            evaluacion_data.update({
                'observaciones_generales': observaciones_form.cleaned_data['observaciones_generales'],
                'recomendaciones_generales': observaciones_form.cleaned_data['recomendaciones_generales'],
                'conclusiones': observaciones_form.cleaned_data['conclusiones'],
                'metodologia_aplicada': observaciones_form.cleaned_data['metodologia_aplicada'],
                'limitaciones_evaluacion': observaciones_form.cleaned_data['limitaciones_evaluacion'],
                'proximas_acciones': observaciones_form.cleaned_data['proximas_acciones'],
            })
            request.session['evaluacion_data'] = evaluacion_data
            
            return redirect('risk_conjuntos:paso_4_resumen', conjunto_id=conjunto_id)
    else:
        # Pre-llenar con datos existentes si los hay
        initial_data = {}
        for field in ['observaciones_generales', 'recomendaciones_generales', 'conclusiones',
                     'metodologia_aplicada', 'limitaciones_evaluacion', 'proximas_acciones']:
            if field in evaluacion_data:
                initial_data[field] = evaluacion_data[field]
        
        observaciones_form = ObservacionesRecomendacionesForm(initial=initial_data)
        archivo_form = ArchivoEvaluacionForm()
    
    # Calcular resumen de respuestas con métricas avanzadas
    total_preguntas = 0
    riesgos_evaluados = []
    suma_calificaciones = 0
    riesgos_criticos = 0
    
    for riesgo_id in evaluacion_data['riesgos_seleccionados']:
        from .models import TipoRiesgo, CalificacionOpcion
        tipo_riesgo = TipoRiesgo.objects.get(id=riesgo_id)
        respuestas_riesgo = evaluacion_data.get('respuestas', {}).get(str(riesgo_id), [])
        total_preguntas += len(respuestas_riesgo)
        
        # Calcular promedio para este riesgo
        suma_riesgo = 0
        if respuestas_riesgo:
            for respuesta in respuestas_riesgo:
                calificacion = CalificacionOpcion.objects.get(id=respuesta['calificacion_id'])
                suma_riesgo += float(calificacion.valor)
                suma_calificaciones += float(calificacion.valor)
            
            promedio_riesgo = suma_riesgo / len(respuestas_riesgo)
            
            # Determinar nivel y clase CSS
            if promedio_riesgo >= 4.0:
                nivel_clase = 'success'
                nivel_texto = 'Aceptable'
            elif promedio_riesgo >= 2.5:
                nivel_clase = 'warning'
                nivel_texto = 'Moderado'
            else:
                nivel_clase = 'danger'
                nivel_texto = 'Crítico'
                riesgos_criticos += 1
        else:
            promedio_riesgo = 0
            nivel_clase = 'secondary'
            nivel_texto = 'Sin evaluar'
        
        riesgos_evaluados.append({
            'nombre': tipo_riesgo.nombre,
            'preguntas_respondidas': len(respuestas_riesgo),
            'promedio': promedio_riesgo,
            'porcentaje': promedio_riesgo * 100,  # Convertir de 0.0-1.0 a 0-100%
            'nivel_clase': nivel_clase,
            'nivel_texto': nivel_texto
        })
    
    # Calcular promedio general
    promedio_calificacion = suma_calificaciones / total_preguntas if total_preguntas > 0 else 0
    
    # Obtener archivos temporales
    archivos_temporales = evaluacion_data.get('archivos_temporales', [])
    
    context = {
        'conjunto': conjunto,
        'observaciones_form': observaciones_form,
        'archivo_form': archivo_form,
        'archivos_temporales': archivos_temporales,
        'riesgos_evaluados': riesgos_evaluados,
        'total_preguntas': total_preguntas,
        'promedio_calificacion': promedio_calificacion,
        'riesgos_criticos': riesgos_criticos,
        'paso': 3,
        'total_pasos': 4
    }
    
    return render(request, 'risk_conjuntos/evaluacion/paso_3.html', context)


@login_required
@subscription_required('risk_conjuntos')
def paso_4_resumen(request, conjunto_id):
    """
    Paso 4: Resumen y confirmación final
    """
    conjunto = get_conjunto_with_permissions(conjunto_id, request.user)
    
    # Verificar datos de sesión
    evaluacion_data = request.session.get('evaluacion_data')
    if not evaluacion_data or evaluacion_data.get('conjunto_id') != str(conjunto_id):
        messages.error(request, 'Datos de evaluación no encontrados. Debes completar los pasos anteriores.')
        return redirect('risk_conjuntos:paso_1_seleccion_riesgos', conjunto_id=conjunto_id)
    
    if request.method == 'POST':
        form = ConfirmacionEvaluacionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear la evaluación
                    evaluacion = crear_evaluacion_completa(evaluacion_data, request, conjunto)
                    
                    # Limpiar sesión
                    if 'evaluacion_data' in request.session:
                        del request.session['evaluacion_data']
                    
                    messages.success(request, 
                        f'¡Evaluación completada exitosamente! La evaluación ha sido guardada correctamente.')
                    
                    return redirect('risk_conjuntos:evaluacion_exitosa', 
                                   conjunto_id=conjunto_id, evaluacion_id=evaluacion.id)
                    
            except Exception as e:
                logger.error(f"Error al crear evaluación: {str(e)}")
                messages.error(request, f'Error al crear la evaluación: {str(e)}')
    else:
        form = ConfirmacionEvaluacionForm()
    
    # Preparar resumen completo con métricas avanzadas
    resumen_data = preparar_resumen_completo(evaluacion_data)
    
    # Crear objeto temporal con métodos de semáforo para el promedio general
    class PromedioTemporal:
        def __init__(self, promedio_porcentaje):
            self.promedio_porcentaje = promedio_porcentaje or 0
        
        def get_nivel_riesgo(self):
            """Determina el nivel de riesgo basado en el promedio (lógica inversa)"""
            porcentaje = float(self.promedio_porcentaje)  # Ya está en formato porcentaje
            if porcentaje <= 30:
                return 'bajo'
            elif porcentaje <= 60:
                return 'medio'
            else:
                return 'alto'
        
        def get_color_semaforo(self):
            """Retorna el color del semáforo según el nivel de riesgo"""
            nivel = self.get_nivel_riesgo()
            colores = {
                'bajo': '#28a745',   # Verde
                'medio': '#ffc107',  # Amarillo
                'alto': '#dc3545'    # Rojo
            }
            return colores[nivel]
        
        def get_texto_nivel_riesgo(self):
            """Retorna el texto descriptivo del nivel de riesgo"""
            nivel = self.get_nivel_riesgo()
            textos = {
                'bajo': 'Riesgo Bajo',
                'medio': 'Riesgo Moderado', 
                'alto': 'Riesgo Alto'
            }
            return textos[nivel]
    
    promedio_obj = PromedioTemporal(resumen_data['promedio_general'])
    
    context = {
        'conjunto': conjunto,
        'form': form,
        'info_evaluacion': evaluacion_data,
        'observaciones': {
            'observaciones_generales': evaluacion_data.get('observaciones_generales', ''),
            'recomendaciones_generales': evaluacion_data.get('recomendaciones_generales', ''),
            'evaluador_experiencia': evaluacion_data.get('evaluador_experiencia', ''),
        },
        'riesgos_evaluados': resumen_data['riesgos_evaluados'],
        'total_preguntas': resumen_data['total_preguntas'],
        'promedio_general': resumen_data['promedio_general'] * 100,  # Convertir a porcentaje
        'promedio_obj': promedio_obj,  # Objeto con métodos de semáforo
        'riesgos_aceptables': resumen_data['riesgos_aceptables'],
        'riesgos_moderados': resumen_data['riesgos_moderados'],
        'riesgos_criticos': resumen_data['riesgos_criticos'],
        'porcentaje_aceptables': resumen_data['porcentaje_aceptables'],
        'porcentaje_moderados': resumen_data['porcentaje_moderados'],
        'porcentaje_criticos': resumen_data['porcentaje_criticos'],
        'archivos_temporales': evaluacion_data.get('archivos_temporales', []),
        'comentarios_riesgos': evaluacion_data.get('comentarios_riesgos', {}),
        'paso': 4,
        'total_pasos': 4
    }
    
    return render(request, 'risk_conjuntos/evaluacion/paso_4.html', context)


def crear_evaluacion_completa(evaluacion_data, request, conjunto):
    """
    Crea la evaluación completa con todas las respuestas
    """
    from .models import CalificacionOpcion
    
    # Crear la evaluación principal
    evaluacion = EvaluacionRiesgo.objects.create(
        conjunto=conjunto,
        creado_por=request.user,
        tipo_evaluacion=evaluacion_data.get('tipo_evaluacion', 'periodica'),
        observaciones_generales=evaluacion_data.get('observaciones_generales', ''),
        recomendaciones_generales=evaluacion_data.get('recomendaciones_generales', ''),
        estado='completada',
        fecha_completado=timezone.now(),
        ip_evaluacion=request.META.get('REMOTE_ADDR', '')
    )
    
    # Crear todas las respuestas
    total_respuestas = 0
    for riesgo_id, respuestas in evaluacion_data.get('respuestas', {}).items():
        for respuesta_data in respuestas:
            pregunta = PreguntaEvaluacion.objects.get(id=respuesta_data['pregunta_id'])
            calificacion = CalificacionOpcion.objects.get(id=respuesta_data['calificacion_id'])
            
            respuesta = RespuestaPregunta.objects.create(
                evaluacion=evaluacion,
                pregunta=pregunta,
                calificacion=calificacion
                # Campo comentarios removido - ahora se manejan por tipo de riesgo
            )
            
            # Crear resultado procesado usando el método apropiado
            resultado_pregunta = ResultadoPregunta.objects.create(
                respuesta=respuesta
            )
            
            # Configurar el análisis completo usando el método especializado
            peso_pregunta = calcular_peso_por_tipo_riesgo(pregunta.escenario.tipo_riesgo.codigo)
            resultado_pregunta.crear_analisis_completo(
                valor_riesgo=float(calificacion.valor),
                peso_pregunta=peso_pregunta
            )
            
            total_respuestas += 1
    
    # Crear comentarios por riesgo
    for riesgo_id, comentario in evaluacion_data.get('comentarios_riesgo', {}).items():
        if comentario.strip():  # Solo crear si hay comentario
            tipo_riesgo = TipoRiesgo.objects.get(id=riesgo_id)
            ComentarioRiesgo.objects.create(
                evaluacion=evaluacion,
                tipo_riesgo=tipo_riesgo,
                comentario=comentario
            )
    
    # Procesar archivos temporales
    for archivo_temp in evaluacion_data.get('archivos_temporales', []):
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        
        # Leer archivo temporal
        if default_storage.exists(archivo_temp['ruta_temporal']):
            with default_storage.open(archivo_temp['ruta_temporal'], 'rb') as temp_file:
                contenido = temp_file.read()
            
            # Crear registro de archivo
            archivo_evaluacion = ArchivoEvaluacion(
                evaluacion=evaluacion,
                tipo_archivo=archivo_temp['tipo_archivo'],
                nombre_archivo=archivo_temp['nombre_original'],
                descripcion=archivo_temp['descripcion'],
                tamaño_archivo=archivo_temp['tamaño']
            )
            
            # Guardar archivo en ubicación final
            extension = os.path.splitext(archivo_temp['nombre_original'])[1]
            nombre_final = f"{archivo_evaluacion.evaluacion.id}_{len(evaluacion_data.get('archivos_temporales', []))}{extension}"
            
            archivo_evaluacion.archivo.save(
                nombre_final,
                ContentFile(contenido),
                save=False
            )
            archivo_evaluacion.save()
            
            # Eliminar archivo temporal
            default_storage.delete(archivo_temp['ruta_temporal'])
    
    # Actualizar campos adicionales
    evaluacion.tiempo_evaluacion_minutos = max(total_respuestas * 2, 15)  # Mínimo 15 min
    evaluacion.save()
    
    # APLICAR LA METODOLOGÍA CORRECTA
    # Calcular y guardar resultados con la metodología implementada
    try:
        resultados_correctos = guardar_resultados_con_metodologia_correcta(evaluacion, evaluacion_data)
        # Log success for monitoring
        import logging
        logger = logging.getLogger('risk_conjuntos.evaluacion')
        logger.info(f"Metodología aplicada correctamente. Evaluación ID: {evaluacion.id}, Promedio: {resultados_correctos['promedio_general']:.4f}")
    except Exception as e:
        # Log error but continue with normal flow
        import logging
        logger = logging.getLogger('risk_conjuntos.evaluacion')
        logger.error(f"Error aplicando metodología para evaluación {evaluacion.id}: {str(e)}")
        # Continuar con el flujo normal en caso de error
    
    return evaluacion


def get_nivel_riesgo_individual(porcentaje):
    """Determina el nivel de riesgo para un riesgo individual basado en el porcentaje"""
    if porcentaje <= 30:
        return 'bajo'
    elif porcentaje <= 60:
        return 'medio'
    else:
        return 'alto'


def get_color_semaforo_riesgo(porcentaje):
    """Retorna el color del semáforo para un riesgo individual"""
    nivel = get_nivel_riesgo_individual(porcentaje)
    colores = {
        'bajo': '#28a745',   # Verde
        'medio': '#ffc107',  # Amarillo
        'alto': '#dc3545'    # Rojo
    }
    return colores[nivel]


def get_texto_nivel_riesgo_individual(porcentaje):
    """Retorna el texto descriptivo del nivel de riesgo para un riesgo individual"""
    nivel = get_nivel_riesgo_individual(porcentaje)
    textos = {
        'bajo': 'Riesgo Bajo',
        'medio': 'Riesgo Moderado', 
        'alto': 'Riesgo Alto'
    }
    return textos[nivel]


def preparar_resumen_completo(evaluacion_data):
    """
    Prepara el resumen completo con métricas avanzadas para el paso 4
    USANDO LA METODOLOGÍA CORRECTA
    """
    from .models import CalificacionOpcion
    
    # Usar la nueva metodología para calcular
    try:
        resultados_correctos = calcular_promedios_por_metodologia_correcta(evaluacion_data)
        
        # Convertir resultados para mostrar en el resumen
        total_preguntas = 0
        suma_calificaciones = 0
        riesgos_evaluados = []
        
        # Contadores por nivel
        riesgos_bajos = 0
        riesgos_moderados = 0  
        riesgos_altos = 0
        
        for riesgo_id, datos_riesgo in resultados_correctos['resultados_por_riesgo'].items():
            tipo_riesgo = datos_riesgo['tipo_riesgo']
            promedio_riesgo = datos_riesgo['promedio_riesgo']
            
            # Contar preguntas totales
            for escenario_id, datos_escenario in datos_riesgo['escenarios'].items():
                total_preguntas += datos_escenario['numero_preguntas']
                # Calcular suma de calificaciones originales para mantener compatibilidad
                for respuesta in datos_escenario['respuestas']:
                    suma_calificaciones += float(respuesta['calificacion'].valor)
            
            # Clasificar nivel basado en porcentaje usando sistema de semáforo consistente
            porcentaje_riesgo = promedio_riesgo * 100  # Convertir a porcentaje
            if porcentaje_riesgo <= 30:
                nivel_clase = 'success'
                nivel_texto = 'Riesgo Bajo'
                riesgos_bajos += 1
            elif porcentaje_riesgo <= 60:
                nivel_clase = 'warning'
                nivel_texto = 'Riesgo Moderado'
                riesgos_moderados += 1
            else:
                nivel_clase = 'danger'
                nivel_texto = 'Riesgo Alto'
                riesgos_altos += 1
            
            riesgos_evaluados.append({
                'nombre': tipo_riesgo.nombre,
                'preguntas_respondidas': sum(d['numero_preguntas'] for d in datos_riesgo['escenarios'].values()),
                'promedio': promedio_riesgo,
                'porcentaje': promedio_riesgo * 100,
                'nivel_clase': nivel_clase,
                'nivel_texto': nivel_texto,
                'numero_escenarios': datos_riesgo['numero_escenarios'],
                # Métodos de semáforo para riesgos individuales
                'semaforo_color': get_color_semaforo_riesgo(promedio_riesgo * 100),
                'semaforo_nivel': get_nivel_riesgo_individual(promedio_riesgo * 100),
                'semaforo_texto': get_texto_nivel_riesgo_individual(promedio_riesgo * 100)
            })
        
        # Usar promedio general de la metodología correcta
        promedio_general = resultados_correctos['promedio_general']
        
        # Usar promedio general de la metodología correcta
        promedio_general = resultados_correctos['promedio_general']
        
        # Calcular porcentajes
        total_riesgos = len(evaluacion_data['riesgos_seleccionados'])
        porcentaje_bajos = (riesgos_bajos / total_riesgos * 100) if total_riesgos > 0 else 0
        porcentaje_moderados = (riesgos_moderados / total_riesgos * 100) if total_riesgos > 0 else 0
        porcentaje_altos = (riesgos_altos / total_riesgos * 100) if total_riesgos > 0 else 0
        
        return {
            'riesgos_evaluados': riesgos_evaluados,
            'total_preguntas': total_preguntas,
            'promedio_general': promedio_general,
            'riesgos_aceptables': riesgos_bajos,  # Mantener nombre original para compatibilidad con templates
            'riesgos_moderados': riesgos_moderados,
            'riesgos_criticos': riesgos_altos,   # Mantener nombre original para compatibilidad con templates
            'porcentaje_aceptables': porcentaje_bajos,  # Mantener nombre original para compatibilidad con templates
            'porcentaje_moderados': porcentaje_moderados,
            'porcentaje_criticos': porcentaje_altos     # Mantener nombre original para compatibilidad con templates
        }
        
    except Exception as e:
        # Log error and fallback to original method
        import logging
        logger = logging.getLogger('risk_conjuntos.evaluacion')
        logger.warning(f"Error en metodología correcta, usando cálculo fallback: {str(e)}")
        return preparar_resumen_completo_fallback(evaluacion_data)


def preparar_resumen_completo_fallback(evaluacion_data):
    """
    Método de respaldo si falla la nueva metodología
    """
    from .models import CalificacionOpcion
    
    total_preguntas = 0
    suma_calificaciones = 0
    riesgos_evaluados = []
    
    # Contadores por nivel
    riesgos_bajos = 0
    riesgos_moderados = 0  
    riesgos_altos = 0
    
    for riesgo_id in evaluacion_data['riesgos_seleccionados']:
        tipo_riesgo = TipoRiesgo.objects.get(id=riesgo_id)
        respuestas_riesgo = evaluacion_data.get('respuestas', {}).get(str(riesgo_id), [])
        total_preguntas += len(respuestas_riesgo)
        
        # Calcular promedio para este riesgo
        suma_riesgo = 0
        if respuestas_riesgo:
            for respuesta in respuestas_riesgo:
                calificacion = CalificacionOpcion.objects.get(id=respuesta['calificacion_id'])
                suma_riesgo += float(calificacion.valor)
                suma_calificaciones += float(calificacion.valor)
            
            promedio_riesgo = suma_riesgo / len(respuestas_riesgo)
            
            # Clasificar nivel basado en porcentaje usando sistema de semáforo consistente
            porcentaje_riesgo = promedio_riesgo * 100  # Convertir a porcentaje
            if porcentaje_riesgo <= 30:
                nivel_clase = 'success'
                nivel_texto = 'Riesgo Bajo'
                riesgos_bajos += 1
            elif porcentaje_riesgo <= 60:
                nivel_clase = 'warning'
                nivel_texto = 'Riesgo Moderado'
                riesgos_moderados += 1
            else:
                nivel_clase = 'danger'
                nivel_texto = 'Riesgo Alto'
                riesgos_altos += 1
        else:
            promedio_riesgo = 0
            nivel_clase = 'secondary'
            nivel_texto = 'Sin evaluar'
        
        riesgos_evaluados.append({
            'nombre': tipo_riesgo.nombre,
            'preguntas_respondidas': len(respuestas_riesgo),
            'promedio': promedio_riesgo,
            'porcentaje': promedio_riesgo * 100,
            'nivel_clase': nivel_clase,
            'nivel_texto': nivel_texto
        })
    
    # Calcular promedios y porcentajes
    promedio_general = suma_calificaciones / total_preguntas if total_preguntas > 0 else 0
    total_riesgos = len(evaluacion_data['riesgos_seleccionados'])
    
    porcentaje_bajos = (riesgos_bajos / total_riesgos * 100) if total_riesgos > 0 else 0
    porcentaje_moderados = (riesgos_moderados / total_riesgos * 100) if total_riesgos > 0 else 0
    porcentaje_altos = (riesgos_altos / total_riesgos * 100) if total_riesgos > 0 else 0
    
    return {
        'riesgos_evaluados': riesgos_evaluados,
        'total_preguntas': total_preguntas,
        'promedio_general': promedio_general,
        'riesgos_aceptables': riesgos_bajos,  # Mantener nombre original para compatibilidad con templates
        'riesgos_moderados': riesgos_moderados,
        'riesgos_criticos': riesgos_altos,   # Mantener nombre original para compatibilidad con templates
        'porcentaje_aceptables': porcentaje_bajos,  # Mantener nombre original para compatibilidad con templates
        'porcentaje_moderados': porcentaje_moderados,
        'porcentaje_criticos': porcentaje_altos     # Mantener nombre original para compatibilidad con templates
    }


def preparar_resumen_evaluacion(evaluacion_data):
    """
    Prepara el resumen completo de la evaluación
    """
    from .models import CalificacionOpcion
    
    resumen = {
        'riesgos': [],
        'total_preguntas': 0,
        'distribucion_calificaciones': {},
        'estimacion_tiempo': 0
    }
    
    # Contadores
    calificaciones_count = {}
    
    for riesgo_id in evaluacion_data['riesgos_seleccionados']:
        tipo_riesgo = TipoRiesgo.objects.get(id=riesgo_id)
        respuestas = evaluacion_data.get('respuestas', {}).get(str(riesgo_id), [])
        
        riesgo_info = {
            'tipo': tipo_riesgo,
            'preguntas': len(respuestas),
            'calificaciones': []
        }
        
        for respuesta in respuestas:
            calificacion = CalificacionOpcion.objects.get(id=respuesta['calificacion_id'])
            riesgo_info['calificaciones'].append(calificacion)
            
            # Contar para distribución general
            if calificacion.nombre not in calificaciones_count:
                calificaciones_count[calificacion.nombre] = 0
            calificaciones_count[calificacion.nombre] += 1
        
        resumen['riesgos'].append(riesgo_info)
        resumen['total_preguntas'] += len(respuestas)
    
    resumen['distribucion_calificaciones'] = calificaciones_count
    resumen['estimacion_tiempo'] = max(resumen['total_preguntas'] * 2, 15)
    
    return resumen


def calcular_peso_por_tipo_riesgo(codigo_tipo):
    """
    Calcula el peso específico por tipo de riesgo
    """
    from decimal import Decimal
    
    pesos = {
        'intrusion_general': Decimal('1.2'),
        'conspiracion_intrusion': Decimal('1.5'),
        'intrusion_unidad': Decimal('1.3'),
        'robo_vehiculos': Decimal('1.1'),
        'robo_bicicletas': Decimal('0.8'),
        'dano_areas_comunes': Decimal('0.9'),
        'conflictos_parqueos': Decimal('0.7'),
        'sustraccion_bienes': Decimal('1.0'),
        'secuestro': Decimal('2.0'),
    }
    
    return pesos.get(codigo_tipo, Decimal('1.0'))


def calcular_promedios_por_metodologia_correcta(evaluacion_data):
    """
    Implementa la metodología correcta:
    1. Para cada pregunta: resultado = 1 - valor_calificacion
    2. Para cada escenario: promedio = suma(resultados_preguntas) / 2
    3. Para cada riesgo: promedio = promedio(resultados_escenarios)
    4. Promedio general: promedio(resultados_riesgos)
    """
    from .models import TipoRiesgo, CalificacionOpcion, EscenarioRiesgo, PreguntaEvaluacion
    
    resultados_por_riesgo = {}
    suma_todos_los_riesgos = 0
    total_riesgos_evaluados = 0
    
    for riesgo_id in evaluacion_data['riesgos_seleccionados']:
        tipo_riesgo = TipoRiesgo.objects.get(id=riesgo_id)
        respuestas_riesgo = evaluacion_data.get('respuestas', {}).get(str(riesgo_id), [])
        
        if not respuestas_riesgo:
            continue
            
        # Agrupar respuestas por escenario
        respuestas_por_escenario = {}
        for respuesta_data in respuestas_riesgo:
            pregunta = PreguntaEvaluacion.objects.get(id=respuesta_data['pregunta_id'])
            escenario_id = pregunta.escenario.id
            
            if escenario_id not in respuestas_por_escenario:
                respuestas_por_escenario[escenario_id] = {
                    'escenario': pregunta.escenario,
                    'respuestas': []
                }
            
            calificacion = CalificacionOpcion.objects.get(id=respuesta_data['calificacion_id'])
            # PASO 2: Aplicar fórmula 1 - valor
            resultado_pregunta = 1 - float(calificacion.valor)
            
            respuestas_por_escenario[escenario_id]['respuestas'].append({
                'pregunta': pregunta,
                'calificacion': calificacion,
                'resultado': resultado_pregunta,
                'respuesta_data': respuesta_data
            })
        
        # PASO 3: Calcular promedio por escenario (suma/2 preguntas)
        promedios_escenarios = []
        resultados_escenarios = {}
        
        for escenario_id, datos_escenario in respuestas_por_escenario.items():
            suma_resultados = sum(r['resultado'] for r in datos_escenario['respuestas'])
            num_preguntas = len(datos_escenario['respuestas'])
            promedio_escenario = suma_resultados / num_preguntas
            
            promedios_escenarios.append(promedio_escenario)
            resultados_escenarios[escenario_id] = {
                'escenario': datos_escenario['escenario'],
                'promedio': promedio_escenario,
                'numero_preguntas': num_preguntas,
                'respuestas': datos_escenario['respuestas']
            }
        
        # PASO 4: Calcular promedio por riesgo = promedio(escenarios)
        if promedios_escenarios:
            promedio_riesgo = sum(promedios_escenarios) / len(promedios_escenarios)
            suma_todos_los_riesgos += promedio_riesgo
            total_riesgos_evaluados += 1
            
            resultados_por_riesgo[riesgo_id] = {
                'tipo_riesgo': tipo_riesgo,
                'promedio_riesgo': promedio_riesgo,
                'escenarios': resultados_escenarios,
                'numero_escenarios': len(resultados_escenarios)
            }
    
    # PASO 5: Promedio general = promedio(todos los riesgos)
    promedio_general = 0
    if total_riesgos_evaluados > 0:
        promedio_general = suma_todos_los_riesgos / total_riesgos_evaluados
    
    return {
        'resultados_por_riesgo': resultados_por_riesgo,
        'promedio_general': promedio_general,
        'total_riesgos_evaluados': total_riesgos_evaluados
    }


def guardar_resultados_con_metodologia_correcta(evaluacion, evaluacion_data):
    """
    Guarda los resultados calculados con la metodología correcta en la base de datos
    """
    from .models import ResultadoEscenario, ResultadoRiesgo
    from decimal import Decimal, InvalidOperation
    from django.db import transaction
    import logging
    
    logger = logging.getLogger('risk_conjuntos.evaluacion')
    
    try:
        with transaction.atomic():
            # Calcular resultados con metodología correcta
            resultados = calcular_promedios_por_metodologia_correcta(evaluacion_data)
            
            if not resultados['resultados_por_riesgo']:
                raise ValueError("No se pudieron calcular resultados válidos")
            
            # Guardar resultados por riesgo y escenario
            for riesgo_id, datos_riesgo in resultados['resultados_por_riesgo'].items():
                tipo_riesgo = datos_riesgo['tipo_riesgo']
                promedio_riesgo = datos_riesgo['promedio_riesgo']
                
                # Validar que el promedio esté en rango válido
                if not (0 <= promedio_riesgo <= 1):
                    logger.warning(f"Promedio de riesgo fuera de rango para {tipo_riesgo.nombre}: {promedio_riesgo}")
                    promedio_riesgo = max(0, min(1, promedio_riesgo))  # Clamp to valid range
                
                try:
                    # Crear resultado por riesgo
                    resultado_riesgo, created = ResultadoRiesgo.objects.update_or_create(
                        evaluacion=evaluacion,
                        tipo_riesgo=tipo_riesgo,
                        defaults={
                            'promedio_riesgo': Decimal(str(round(promedio_riesgo, 4)))
                        }
                    )
                    
                    # Crear resultados por escenario
                    for escenario_id, datos_escenario in datos_riesgo['escenarios'].items():
                        escenario = datos_escenario['escenario']
                        promedio_escenario = datos_escenario['promedio']
                        
                        # Validar promedio de escenario
                        if not (0 <= promedio_escenario <= 1):
                            logger.warning(f"Promedio de escenario fuera de rango para {escenario.nombre}: {promedio_escenario}")
                            promedio_escenario = max(0, min(1, promedio_escenario))
                        
                        ResultadoEscenario.objects.update_or_create(
                            evaluacion=evaluacion,
                            escenario=escenario,
                            defaults={
                                'promedio_escenario': Decimal(str(round(promedio_escenario, 4)))
                            }
                        )
                        
                except (InvalidOperation, ValueError) as e:
                    logger.error(f"Error procesando riesgo {tipo_riesgo.nombre}: {str(e)}")
                    raise
            
            # Validar y actualizar promedio general de la evaluación
            promedio_general = resultados['promedio_general']
            if not (0 <= promedio_general <= 1):
                logger.warning(f"Promedio general fuera de rango: {promedio_general}")
                promedio_general = max(0, min(1, promedio_general))
            
            evaluacion.promedio_general = Decimal(str(round(promedio_general, 4)))
            evaluacion.save(update_fields=['promedio_general'])
            
            logger.info(f"Resultados guardados exitosamente para evaluación {evaluacion.id}")
            return resultados
            
    except Exception as e:
        logger.error(f"Error crítico guardando resultados para evaluación {evaluacion.id}: {str(e)}")
        raise


def determinar_nivel_riesgo(valor_numerico):
    """
    Determina el nivel de riesgo basado en el valor numérico
    """
    if valor_numerico >= 4.0:
        return 'aceptable'
    elif valor_numerico >= 2.5:
        return 'moderado'
    else:
        return 'critico'


def generar_recomendacion_automatica(tipo_riesgo, valor_numerico):
    """
    Genera una recomendación automática basada en el tipo de riesgo y valor
    """
    nivel = determinar_nivel_riesgo(valor_numerico)
    
    recomendaciones_base = {
        'aceptable': f"Mantener las medidas actuales de {tipo_riesgo.nombre.lower()}. Realizar seguimiento periódico.",
        'moderado': f"Mejorar las medidas de {tipo_riesgo.nombre.lower()}. Implementar acciones correctivas a mediano plazo.",
        'critico': f"Acción inmediata requerida para {tipo_riesgo.nombre.lower()}. Prioridad alta en plan de mejoras."
    }
    
    return recomendaciones_base.get(nivel, "Revisar medidas de seguridad.")


@login_required
@subscription_required('risk_conjuntos')
def evaluacion_exitosa(request, conjunto_id, evaluacion_id):
    """
    Página de confirmación de evaluación exitosa
    """
    conjunto = get_conjunto_with_permissions(conjunto_id, request.user)
    evaluacion = get_object_or_404(EvaluacionRiesgo, id=evaluacion_id, conjunto=conjunto)
    
    # Obtener todas las respuestas organizadas por tipo de riesgo
    respuestas = RespuestaPregunta.objects.filter(evaluacion=evaluacion).select_related(
        'pregunta__escenario__tipo_riesgo', 'calificacion', 'resultado_procesado'
    ).order_by('pregunta__escenario__tipo_riesgo__orden', 'pregunta__orden')
    
    # Organizar por tipo de riesgo y calcular semáforos
    riesgos_data = {}
    for respuesta in respuestas:
        tipo_riesgo = respuesta.pregunta.escenario.tipo_riesgo
        if tipo_riesgo.id not in riesgos_data:
            riesgos_data[tipo_riesgo.id] = {
                'tipo': tipo_riesgo,
                'respuestas': [],
                'suma_valores': 0,
                'count_respuestas': 0
            }
        riesgos_data[tipo_riesgo.id]['respuestas'].append(respuesta)
        riesgos_data[tipo_riesgo.id]['suma_valores'] += float(respuesta.resultado_calculado)
        riesgos_data[tipo_riesgo.id]['count_respuestas'] += 1
    
    # Calcular promedios y añadir datos de semáforo
    for riesgo_id, data in riesgos_data.items():
        if data['count_respuestas'] > 0:
            promedio = data['suma_valores'] / data['count_respuestas']
            porcentaje = promedio * 100
            
            # Añadir datos de semáforo
            data['promedio'] = promedio
            data['porcentaje'] = porcentaje
            data['semaforo_color'] = get_color_semaforo_riesgo(porcentaje)
            data['semaforo_nivel'] = get_nivel_riesgo_individual(porcentaje)
            data['semaforo_texto'] = get_texto_nivel_riesgo_individual(porcentaje)
    
    # Calcular métricas adicionales para mostrar
    tipos_riesgos_evaluados = respuestas.values_list(
        'pregunta__escenario__tipo_riesgo__id', flat=True
    ).distinct()
    total_riesgos = len(set(tipos_riesgos_evaluados))
    
    total_preguntas = respuestas.count()
    tiempo_estimado = evaluacion.tiempo_evaluacion_minutos or 0
    
    # Calcular calificación promedio
    suma_calificaciones = sum(float(r.calificacion.valor) for r in respuestas)
    calificacion_promedio = suma_calificaciones / total_preguntas if total_preguntas > 0 else 0
    
    # Contar riesgos por nivel
    riesgos_aceptables = 0
    riesgos_moderados = 0
    riesgos_criticos = 0
    
    for data in riesgos_data.values():
        if 'porcentaje' in data:
            porcentaje = data['porcentaje']
            if porcentaje <= 30:
                riesgos_aceptables += 1
            elif porcentaje <= 60:
                riesgos_moderados += 1
            else:
                riesgos_criticos += 1
    
    context = {
        'conjunto': conjunto,
        'evaluacion': evaluacion,
        'riesgos_data': riesgos_data.values(),
        'total_respuestas': respuestas.count(),
        'total_riesgos': total_riesgos,
        'total_preguntas': total_preguntas,
        'tiempo_estimado': tiempo_estimado,
        'calificacion_promedio': calificacion_promedio,
        'riesgos_aceptables': riesgos_aceptables,
        'riesgos_moderados': riesgos_moderados,
        'riesgos_criticos': riesgos_criticos,
        'now': timezone.now()
    }
    
    return render(request, 'risk_conjuntos/evaluacion/detalle.html', context)


@login_required
@subscription_required('risk_conjuntos')
def detalle_evaluacion(request, conjunto_id, evaluacion_id):
    """
    Muestra el detalle completo de una evaluación terminada
    """
    conjunto = get_conjunto_with_permissions(conjunto_id, request.user)
    evaluacion = get_object_or_404(EvaluacionRiesgo, id=evaluacion_id, conjunto=conjunto)
    
    # Obtener todas las respuestas organizadas por tipo de riesgo
    respuestas = RespuestaPregunta.objects.filter(evaluacion=evaluacion).select_related(
        'pregunta__escenario__tipo_riesgo', 'calificacion', 'resultado_procesado'
    ).order_by('pregunta__escenario__tipo_riesgo__orden', 'pregunta__orden')
    
    # Organizar por tipo de riesgo y calcular semáforos
    riesgos_data = {}
    for respuesta in respuestas:
        tipo_riesgo = respuesta.pregunta.escenario.tipo_riesgo
        if tipo_riesgo.id not in riesgos_data:
            riesgos_data[tipo_riesgo.id] = {
                'tipo': tipo_riesgo,
                'respuestas': [],
                'suma_valores': 0,
                'count_respuestas': 0
            }
        riesgos_data[tipo_riesgo.id]['respuestas'].append(respuesta)
        riesgos_data[tipo_riesgo.id]['suma_valores'] += float(respuesta.resultado_calculado)
        riesgos_data[tipo_riesgo.id]['count_respuestas'] += 1
    
    # Calcular promedios y añadir datos de semáforo
    for riesgo_id, data in riesgos_data.items():
        if data['count_respuestas'] > 0:
            promedio = data['suma_valores'] / data['count_respuestas']
            porcentaje = promedio * 100
            
            # Añadir datos de semáforo
            data['promedio'] = promedio
            data['porcentaje'] = porcentaje
            data['semaforo_color'] = get_color_semaforo_riesgo(porcentaje)
            data['semaforo_nivel'] = get_nivel_riesgo_individual(porcentaje)
            data['semaforo_texto'] = get_texto_nivel_riesgo_individual(porcentaje)
    
    # Contar riesgos por nivel
    riesgos_aceptables = 0
    riesgos_moderados = 0
    riesgos_criticos = 0
    
    for data in riesgos_data.values():
        if 'porcentaje' in data:
            porcentaje = data['porcentaje']
            if porcentaje <= 30:
                riesgos_aceptables += 1
            elif porcentaje <= 60:
                riesgos_moderados += 1
            else:
                riesgos_criticos += 1
    
    context = {
        'conjunto': conjunto,
        'evaluacion': evaluacion,
        'riesgos_data': riesgos_data.values(),
        'total_respuestas': respuestas.count(),
        'riesgos_aceptables': riesgos_aceptables,
        'riesgos_moderados': riesgos_moderados,
        'riesgos_criticos': riesgos_criticos,
    }
    
    return render(request, 'risk_conjuntos/evaluacion/detalle.html', context)

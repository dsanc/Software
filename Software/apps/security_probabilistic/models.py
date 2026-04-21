from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json

User = get_user_model()


class PerfilSeguridad(models.Model):
    """Perfil de seguridad para evaluación de figuras políticas"""
    
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
        ('TI', 'Tarjeta de Identidad'),
    ]
    
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('NR', 'Prefiero no responder'),
    ]
    
    CARGO_POLITICO_CHOICES = [
        ('alcalde', 'Alcalde/Alcaldesa'),
        ('concejal', 'Concejal'),
        ('diputado', 'Diputado/Diputada'),
        ('senador', 'Senador/Senadora'),
        ('gobernador', 'Gobernador/Gobernadora'),
        ('ministro', 'Ministro/Ministra'),
        ('candidato', 'Candidato/Candidata'),
        ('lider_social', 'Líder Social'),
        ('activista', 'Activista Político'),
        ('funcionario', 'Funcionario Público'),
        ('otro', 'Otro'),
    ]
    
    NIVEL_EXPOSICION_CHOICES = [
        ('muy_alta', 'Muy Alta'),
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]
    
    ESTADO_PERFIL_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('suspendido', 'Suspendido'),
        ('archivado', 'Archivado'),
    ]
    
    # Información personal básica
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    tipo_documento = models.CharField(
        max_length=2, 
        choices=TIPO_DOCUMENTO_CHOICES, 
        default='CC',
        verbose_name="Tipo de Documento"
    )
    numero_documento = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Número de Documento"
    )
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento")
    genero = models.CharField(
        max_length=2, 
        choices=GENERO_CHOICES,
        verbose_name="Género"
    )
    telefono_principal = models.CharField(
        max_length=20, 
        verbose_name="Teléfono Principal"
    )
    telefono_emergencia = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Teléfono de Emergencia"
    )
    
    # Información política
    cargo_politico = models.CharField(
        max_length=20, 
        choices=CARGO_POLITICO_CHOICES,
        verbose_name="Cargo Político"
    )
    partido_politico = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Partido Político"
    )
    nivel_exposicion = models.CharField(
        max_length=10, 
        choices=NIVEL_EXPOSICION_CHOICES,
        default='media',
        verbose_name="Nivel de Exposición Pública"
    )
    
    # Información geográfica
    departamento = models.CharField(
        max_length=50, 
        verbose_name="Departamento"
    )
    municipio = models.CharField(
        max_length=50, 
        verbose_name="Municipio"
    )
    direccion_residencia = models.TextField(
        verbose_name="Dirección de Residencia"
    )
    direccion_trabajo = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Dirección de Trabajo"
    )
    
    # Información de seguridad
    tiene_esquema_seguridad = models.BooleanField(
        default=False,
        verbose_name="¿Tiene Esquema de Seguridad?"
    )
    nivel_esquema_seguridad = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        verbose_name="Nivel del Esquema de Seguridad"
    )
    amenazas_recibidas = models.BooleanField(
        default=False,
        verbose_name="¿Ha Recibido Amenazas?"
    )
    fecha_ultima_amenaza = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Fecha de Última Amenaza"
    )
    
    # Información adicional
    observaciones = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Observaciones Adicionales"
    )
    contacto_emergencia_nombre = models.CharField(
        max_length=100, 
        verbose_name="Nombre Contacto de Emergencia"
    )
    contacto_emergencia_telefono = models.CharField(
        max_length=20, 
        verbose_name="Teléfono Contacto de Emergencia"
    )
    contacto_emergencia_relacion = models.CharField(
        max_length=50, 
        verbose_name="Relación Contacto de Emergencia"
    )
    
    # Control del perfil
    estado_perfil = models.CharField(
        max_length=10, 
        choices=ESTADO_PERFIL_CHOICES,
        default='activo',
        verbose_name="Estado del Perfil"
    )
    
    # Información de propiedad
    owner = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='perfiles_seguridad',
        verbose_name="Propietario",
        help_text="Usuario que creó este perfil de seguridad",
        null=True,  # Temporal - permitir null
        blank=True
    )
    
    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil de Seguridad"
        verbose_name_plural = "Perfiles de Seguridad"
        ordering = ['-creado_en']
        
    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.get_cargo_politico_display()}"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del perfil"""
        return f"{self.nombres} {self.apellidos}"
    
    @property
    def edad(self):
        """Calcula la edad basada en la fecha de nacimiento"""
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
    
    @property
    def nivel_riesgo_perfil(self):
        """Calcula un nivel de riesgo base del perfil"""
        riesgo = 0
        
        # Factor por cargo político
        if self.cargo_politico in ['alcalde', 'gobernador', 'senador', 'ministro']:
            riesgo += 3
        elif self.cargo_politico in ['diputado', 'concejal']:
            riesgo += 2
        elif self.cargo_politico in ['candidato', 'lider_social']:
            riesgo += 2
        
        # Factor por exposición
        if self.nivel_exposicion == 'muy_alta':
            riesgo += 3
        elif self.nivel_exposicion == 'alta':
            riesgo += 2
        elif self.nivel_exposicion == 'media':
            riesgo += 1
        
        # Factor por amenazas
        if self.amenazas_recibidas:
            riesgo += 2
            if self.fecha_ultima_amenaza and (timezone.now().date() - self.fecha_ultima_amenaza).days <= 90:
                riesgo += 1  # Amenaza reciente
        
        # Factor por esquema de seguridad (inverso)
        if not self.tiene_esquema_seguridad:
            riesgo += 1
        
        # Clasificar nivel
        if riesgo >= 7:
            return 'muy_alto'
        elif riesgo >= 5:
            return 'alto'
        elif riesgo >= 3:
            return 'medio'
        else:
            return 'bajo'
    
    def puede_ser_evaluado(self):
        """Verifica si el perfil puede ser evaluado"""
        return self.estado_perfil == 'activo'
    
    @property
    def iniciales(self):
        """Genera las iniciales del nombre completo"""
        if not self.nombre_completo:
            return "PS"  # PerfilSeguridad por defecto
        
        words = self.nombre_completo.strip().split()
        if len(words) == 0:
            return "PS"
        elif len(words) == 1:
            return words[0][0].upper() if words[0] else "PS"
        else:
            # Tomar la primera letra de las dos primeras palabras
            first_initial = words[0][0].upper() if words[0] else ""
            second_initial = words[1][0].upper() if len(words) > 1 and words[1] else ""
            return first_initial + second_initial


class ArbolDecision(models.Model):
    """Árbol de decisiones para evaluación de seguridad"""
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Árbol")
    descripcion = models.TextField(verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Árbol de Decisión"
        verbose_name_plural = "Árboles de Decisión"
        
    def __str__(self):
        return self.nombre


class Pregunta(models.Model):
    """Preguntas del árbol de decisiones"""
    arbol = models.ForeignKey(ArbolDecision, on_delete=models.CASCADE, related_name='preguntas')
    texto = models.TextField(verbose_name="Texto de la Pregunta")
    orden = models.PositiveIntegerField(verbose_name="Orden")
    valor = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        validators=[MinValueValidator(0)],
        verbose_name="Valor/Peso de la Pregunta",
        default=0.000
    )
    var_amenaza = models.CharField(
        max_length=100, 
        verbose_name="Variable de Amenaza",
        help_text="Capacidad, Intencionalidad, Exposición, Inductor, Interés, Valuabilidad",
        blank=True
    )
    es_pregunta_inicial = models.BooleanField(default=False, verbose_name="Es Pregunta Inicial")
    pregunta_padre = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='preguntas_hijas',
        verbose_name="Pregunta Padre"
    )
    
    class Meta:
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"
        ordering = ['arbol', 'orden']
        
    def __str__(self):
        return f"{self.arbol.nombre} - {self.texto[:50]}..."


class OpcionRespuesta(models.Model):
    """Opciones de respuesta para cada pregunta con su ponderación"""
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='opciones')
    texto = models.CharField(max_length=500, verbose_name="Texto de la Opción")
    valor_ponderado = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        validators=[MinValueValidator(0)],
        verbose_name="Valor Ponderado"
    )
    orden = models.PositiveIntegerField(verbose_name="Orden")
    pregunta_siguiente = models.ForeignKey(
        Pregunta, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='opciones_que_llevan_aqui',
        verbose_name="Pregunta Siguiente"
    )
    es_respuesta_final = models.BooleanField(default=False, verbose_name="Es Respuesta Final")
    
    class Meta:
        verbose_name = "Opción de Respuesta"
        verbose_name_plural = "Opciones de Respuesta"
        ordering = ['pregunta', 'orden']
        
    def __str__(self):
        return f"{self.pregunta.texto[:30]}... - {self.texto}"


class EvaluacionSeguridad(models.Model):
    """Evaluación de seguridad realizada a un usuario"""
    ESTADO_CHOICES = [
        ('iniciada', 'Iniciada'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    NIVEL_RIESGO_CHOICES = [
        ('muy_bajo', 'Muy Bajo'),
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('muy_alto', 'Muy Alto'),
    ]
    
    perfil = models.ForeignKey(
        'PerfilSeguridad', 
        on_delete=models.CASCADE, 
        related_name='evaluaciones',
        verbose_name="Perfil de Seguridad Asociado",
        help_text="Cada evaluación debe estar asociada a un perfil de seguridad verificado"
    )
    arbol = models.ForeignKey(ArbolDecision, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='iniciada')
    
    # Información opcional del evaluador (sin relación formal)
    evaluador_nombre = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="Nombre del Evaluador",
        help_text="Nombre de la persona que realizó la evaluación (opcional)"
    )
    
    probabilidad_total = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        default=0,
        verbose_name="Probabilidad Total de Riesgo"
    )
    
    # Nuevos campos para factor geográfico
    factor_geografico = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=0,
        verbose_name="Factor de Riesgo Geográfico",
        help_text="Riesgo adicional basado en ubicación de residencia y desplazamientos"
    )
    probabilidad_con_geografia = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        default=0,
        verbose_name="Probabilidad Total con Factor Geográfico"
    )
    municipios_desplazamiento_json = models.JSONField(
        default=list, 
        verbose_name="Municipios de Desplazamiento",
        help_text="Lista de municipios donde se desplaza con frecuencia y motivo"
    )
    incluir_municipio_residencia = models.BooleanField(
        default=True,
        verbose_name="Incluir Municipio de Residencia",
        help_text="Si se debe considerar el municipio de residencia del perfil en el cálculo"
    )
    
    nivel_riesgo = models.CharField(max_length=20, choices=NIVEL_RIESGO_CHOICES, null=True, blank=True)
    respuestas_json = models.JSONField(default=dict, verbose_name="Respuestas en JSON")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    # Campo de seguimiento de quien crea la evaluación
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='evaluaciones_security_probabilistic_creadas',
        verbose_name="Creado por",
        help_text="Usuario que realizó esta evaluación de seguridad",
        null=True,  # Temporal - permitir null
        blank=True
    )
    
    creada_en = models.DateTimeField(auto_now_add=True)
    completada_en = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Evaluación de Seguridad"
        verbose_name_plural = "Evaluaciones de Seguridad"
        ordering = ['-creada_en']
        
    def __str__(self):
        return f"Evaluación {self.perfil.nombre_completo} - {self.creada_en.strftime('%d/%m/%Y')}"
    
    def calcular_nivel_riesgo(self, usar_geografia=True):
        """Calcula el nivel de riesgo basado en la probabilidad total"""
        probabilidad = self.probabilidad_con_geografia if usar_geografia else self.probabilidad_total
        
        if probabilidad >= 0.8:
            return 'muy_alto'
        elif probabilidad >= 0.6:
            return 'alto'
        elif probabilidad >= 0.4:
            return 'medio'
        elif probabilidad >= 0.2:
            return 'bajo'
        else:
            return 'muy_bajo'
    
    def calcular_factor_geografico(self):
        """Calcula el factor de riesgo geográfico basado en residencia y desplazamientos"""
        factor_total = 0.0
        
        # Factor de residencia
        if self.incluir_municipio_residencia:
            try:
                # Buscar municipio de residencia del perfil
                municipio_residencia = Municipio.objects.filter(
                    nombre__icontains=self.perfil.municipio,
                    departamento__nombre__icontains=self.perfil.departamento
                ).first()
                
                if municipio_residencia:
                    factor_residencia = float(municipio_residencia.factor_riesgo_efectivo) * 0.3  # 30% del factor
                    factor_total += factor_residencia
            except Exception as e:
                # Si no encuentra el municipio, usar factor promedio bajo
                factor_total += 0.05
        
        # Factor de desplazamientos
        for desplazamiento in self.municipios_desplazamiento_json:
            try:
                municipio = Municipio.objects.get(id=desplazamiento.get('municipio_id'))
                frecuencia = desplazamiento.get('frecuencia', 'ocasional')
                motivo = desplazamiento.get('motivo', 'personal')
                
                # Calcular multiplicador basado en frecuencia y motivo
                multiplicador = self._calcular_multiplicador_desplazamiento(frecuencia, motivo)
                
                # Factor del municipio multiplicado por la frecuencia/motivo
                factor_municipio = float(municipio.factor_riesgo_efectivo) * multiplicador * 0.2  # 20% cada municipio
                factor_total += factor_municipio
                
            except Municipio.DoesNotExist:
                continue
        
        # Limitar el factor geográfico a un máximo razonable
        return min(factor_total, 0.5)  # Máximo 50% adicional por geografía
    
    def calcular_promedio_completo(self):
        """
        Calcula el promedio de probabilidad considerando TODOS los componentes:
        - Cada respuesta del cuestionario individualmente
        - Factor de municipio de residencia (si aplica)
        - Factor de cada ubicación de desplazamiento
        
        Metodología oficial: (suma_todas_respuestas + suma_factores_geograficos) / total_componentes
        
        Returns:
            dict: Diccionario con detalles del cálculo del promedio
        """
        # 1. Respuestas del cuestionario (valores individuales)
        total_respuestas = len(self.respuestas_json) if self.respuestas_json else 0
        suma_respuestas = float(self.probabilidad_total) if self.probabilidad_total else 0.0
        
        # 2. Factor de residencia
        factor_residencia = 0.0
        incluye_residencia = False
        if self.incluir_municipio_residencia and self.perfil.municipio:
            try:
                municipio_residencia = Municipio.objects.filter(
                    nombre__icontains=self.perfil.municipio,
                    departamento__nombre__icontains=self.perfil.departamento
                ).first()
                
                if municipio_residencia:
                    factor_residencia = float(municipio_residencia.factor_riesgo_efectivo) * 0.3  # 30% del factor
                    incluye_residencia = True
                else:
                    factor_residencia = 0.001  # Factor promedio bajo si no se encuentra
                    incluye_residencia = True
            except Exception:
                factor_residencia = 0.001
                incluye_residencia = True
        
        # 3. Factores de desplazamiento (cada uno individualmente)
        factores_desplazamiento = []
        for desplazamiento in self.municipios_desplazamiento_json:
            try:
                municipio_id = desplazamiento.get('municipio_id')
                frecuencia = desplazamiento.get('frecuencia', 'ocasional')
                motivo = desplazamiento.get('motivo', 'otro')
                
                municipio = Municipio.objects.get(id=municipio_id)
                multiplicador = self._calcular_multiplicador_desplazamiento(frecuencia, motivo)
                
                # Factor del municipio multiplicado por la frecuencia/motivo
                factor_municipio = float(municipio.factor_riesgo_efectivo) * multiplicador * 0.2  # 20% cada municipio
                factores_desplazamiento.append(factor_municipio)
                
            except Municipio.DoesNotExist:
                continue
        
        # 4. Cálculo final según metodología oficial
        total_ubicaciones = (1 if incluye_residencia else 0) + len(factores_desplazamiento)
        total_componentes = total_respuestas + total_ubicaciones
        
        suma_factores_geograficos = factor_residencia + sum(factores_desplazamiento)
        suma_total = suma_respuestas + suma_factores_geograficos
        promedio_completo = suma_total / total_componentes if total_componentes > 0 else 0.0
        
        return {
            'total_respuestas': total_respuestas,
            'suma_respuestas': suma_respuestas,
            'incluye_residencia': incluye_residencia,
            'factor_residencia': factor_residencia,
            'factores_desplazamiento': factores_desplazamiento,
            'suma_factores_geograficos': suma_factores_geograficos,
            'total_ubicaciones': total_ubicaciones,
            'total_componentes': total_componentes,
            'suma_total': suma_total,
            'promedio_completo': promedio_completo,
            'porcentaje': promedio_completo * 100
        }
    
    def _calcular_multiplicador_desplazamiento(self, frecuencia, motivo):
        """Calcula el multiplicador basado en frecuencia y motivo"""
        multiplicadores_frecuencia = {
            'diario': 2.0,
            'semanal': 1.8,
            'quincenal': 1.5,
            'mensual': 1.3,
            'ocasional': 1.1,
            'unico': 1.0,
        }
        
        multiplicadores_motivo = {
            'politico': 1.4,
            'campana': 1.3,
            'eventos': 1.2,
            'gestion': 1.15,
            'trabajo': 1.1,
            'personal': 1.0,
            'otro': 1.0,
        }
        
        mult_freq = multiplicadores_frecuencia.get(frecuencia, 1.0)
        mult_motivo = multiplicadores_motivo.get(motivo, 1.0)
        
        # Promedio ponderado
        return (mult_freq * 0.6 + mult_motivo * 0.4)
    
    def agregar_municipio_desplazamiento(self, municipio_id, frecuencia='ocasional', motivo='personal', observaciones=''):
        """Agrega un municipio de desplazamiento a la evaluación"""
        municipios = self.municipios_desplazamiento_json.copy()
        
        # Verificar si ya existe
        for i, desp in enumerate(municipios):
            if desp.get('municipio_id') == municipio_id:
                # Actualizar existente
                municipios[i] = {
                    'municipio_id': municipio_id,
                    'frecuencia': frecuencia,
                    'motivo': motivo,
                    'observaciones': observaciones,
                    'agregado_en': timezone.now().isoformat()
                }
                self.municipios_desplazamiento_json = municipios
                self.save()
                return
        
        # Agregar nuevo
        municipios.append({
            'municipio_id': municipio_id,
            'frecuencia': frecuencia,
            'motivo': motivo,
            'observaciones': observaciones,
            'agregado_en': timezone.now().isoformat()
        })
        
        self.municipios_desplazamiento_json = municipios
        self.save()
    
    def actualizar_probabilidad_completa(self):
        """Actualiza la probabilidad total considerando respuestas + geografía"""
        # Recalcular probabilidad base de respuestas
        probabilidad_respuestas = sum(
            resp['valor_ponderado'] for resp in self.respuestas_json.values()
        )
        self.probabilidad_total = probabilidad_respuestas
        
        # Calcular factor geográfico
        self.factor_geografico = self.calcular_factor_geografico()
        
        # Probabilidad final combinada
        self.probabilidad_con_geografia = probabilidad_respuestas + self.factor_geografico
        
        # Actualizar nivel de riesgo usando la probabilidad con geografía
        self.nivel_riesgo = self.calcular_nivel_riesgo(usar_geografia=True)
        
        self.save()
    
    def agregar_respuesta(self, pregunta_id, opcion_id, valor_ponderado):
        """Agrega una respuesta y actualiza la probabilidad total"""
        respuestas = self.respuestas_json
        respuestas[str(pregunta_id)] = {
            'opcion_id': opcion_id,
            'valor_ponderado': float(valor_ponderado)
        }
        self.respuestas_json = respuestas
        
        # Actualizar probabilidad completa (respuestas + geografía)
        self.actualizar_probabilidad_completa()


class RespuestaEvaluacion(models.Model):
    """Respuestas individuales de una evaluación"""
    evaluacion = models.ForeignKey(EvaluacionSeguridad, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    opcion_seleccionada = models.ForeignKey(OpcionRespuesta, on_delete=models.CASCADE)
    valor_aplicado = models.DecimalField(max_digits=6, decimal_places=3)
    orden_respuesta = models.PositiveIntegerField(verbose_name="Orden de Respuesta")
    respondida_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Respuesta de Evaluación"
        verbose_name_plural = "Respuestas de Evaluación"
        ordering = ['evaluacion', 'orden_respuesta']
        unique_together = ['evaluacion', 'pregunta']
        
    def __str__(self):
        return f"Respuesta {self.evaluacion.id} - {self.pregunta.texto[:30]}..."


class ZonaRiesgo(models.Model):
    """Catálogo de zonas con niveles de riesgo predefinidos"""
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Zona")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    nivel_riesgo_base = models.DecimalField(
        max_digits=5, 
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Nivel de Riesgo Base"
    )
    coordenadas = models.TextField(blank=True, help_text="Coordenadas en formato JSON")
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Zona de Riesgo"
        verbose_name_plural = "Zonas de Riesgo"
        ordering = ['nombre']
        
    def __str__(self):
        return f"{self.nombre} (Riesgo: {self.nivel_riesgo_base})"


class Departamento(models.Model):
    """Departamentos de Colombia con información de riesgo"""
    codigo_dane = models.CharField(
        max_length=2, 
        unique=True,
        verbose_name="Código DANE"
    )
    nombre = models.CharField(
        max_length=100, 
        verbose_name="Nombre del Departamento"
    )
    region = models.CharField(
        max_length=50,
        choices=[
            ('andina', 'Región Andina'),
            ('caribe', 'Región Caribe'),
            ('pacifica', 'Región Pacífica'),
            ('orinoquia', 'Región Orinoquía'),
            ('amazonia', 'Región Amazonía'),
            ('insular', 'Región Insular'),
        ],
        verbose_name="Región Geográfica",
        blank=True
    )
    nivel_riesgo = models.CharField(
        max_length=20,
        choices=[
            ('muy_bajo', 'Muy Bajo'),
            ('bajo', 'Bajo'),
            ('medio', 'Medio'),
            ('alto', 'Alto'),
            ('muy_alto', 'Muy Alto'),
            ('critico', 'Crítico'),
        ],
        default='medio',
        verbose_name="Nivel de Riesgo de la Zona"
    )
    factor_riesgo = models.DecimalField(
        max_digits=5, 
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        default=0.500,
        verbose_name="Factor de Riesgo (0.000 - 1.000)",
        help_text="Valor numérico del riesgo para cálculos de evaluación"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones sobre el Nivel de Riesgo"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['nombre']
        
    def __str__(self):
        return f"{self.nombre} (Riesgo: {self.get_nivel_riesgo_display()})"
    
    @property
    def total_municipios(self):
        """Retorna el total de municipios del departamento"""
        return self.municipios.count()


class Municipio(models.Model):
    """Municipios de Colombia con información de riesgo específica"""
    departamento = models.ForeignKey(
        Departamento, 
        on_delete=models.CASCADE, 
        related_name='municipios',
        verbose_name="Departamento"
    )
    codigo_dane = models.CharField(
        max_length=5, 
        unique=True,
        verbose_name="Código DANE"
    )
    nombre = models.CharField(
        max_length=100, 
        verbose_name="Nombre del Municipio"
    )
    categoria = models.CharField(
        max_length=20,
        choices=[
            ('especial', 'Categoría Especial'),
            ('primera', 'Primera Categoría'),
            ('segunda', 'Segunda Categoría'),
            ('tercera', 'Tercera Categoría'),
            ('cuarta', 'Cuarta Categoría'),
            ('quinta', 'Quinta Categoría'),
            ('sexta', 'Sexta Categoría'),
        ],
        blank=True,
        verbose_name="Categoría Municipal"
    )
    nivel_riesgo = models.CharField(
        max_length=20,
        choices=[
            ('muy_bajo', 'Muy Bajo'),
            ('bajo', 'Bajo'),
            ('medio', 'Medio'),
            ('alto', 'Alto'),
            ('muy_alto', 'Muy Alto'),
            ('critico', 'Crítico'),
        ],
        default='medio',
        verbose_name="Nivel de Riesgo de la Zona"
    )
    factor_riesgo = models.DecimalField(
        max_digits=5, 
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        default=0.500,
        verbose_name="Factor de Riesgo (0.000 - 1.000)",
        help_text="Valor numérico del riesgo para cálculos de evaluación"
    )
    usa_riesgo_departamento = models.BooleanField(
        default=True,
        verbose_name="Usar Riesgo del Departamento",
        help_text="Si está marcado, usará el nivel de riesgo del departamento. Si no, usará el propio."
    )
    poblacion = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Población Estimada"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones sobre el Nivel de Riesgo"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        ordering = ['departamento__nombre', 'nombre']
        unique_together = ['departamento', 'nombre']
        
    def __str__(self):
        return f"{self.nombre} ({self.departamento.nombre})"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo con departamento"""
        return f"{self.nombre}, {self.departamento.nombre}"
    
    @property
    def nivel_riesgo_efectivo(self):
        """Retorna el nivel de riesgo efectivo (propio o del departamento)"""
        if self.usa_riesgo_departamento:
            return self.departamento.nivel_riesgo
        return self.nivel_riesgo
    
    @property
    def factor_riesgo_efectivo(self):
        """Retorna el factor de riesgo efectivo (propio o del departamento)"""
        if self.usa_riesgo_departamento:
            return self.departamento.factor_riesgo
        return self.factor_riesgo
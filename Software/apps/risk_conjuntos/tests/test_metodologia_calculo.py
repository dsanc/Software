"""
Tests unitarios para la nueva metodología de cálculo
"""
from django.test import TestCase
from decimal import Decimal
from apps.risk_conjuntos.models import (
    TipoRiesgo, EscenarioRiesgo, PreguntaEvaluacion, CalificacionOpcion,
    EvaluacionRiesgo, RespuestaPregunta, ResultadoRiesgo, ResultadoEscenario, Conjunto
)
from apps.risk_conjuntos.views_evaluacion import (
    calcular_promedios_por_metodologia_correcta,
    guardar_resultados_con_metodologia_correcta
)
from django.contrib.auth import get_user_model

User = get_user_model()


class MetodologiaCalculoTestCase(TestCase):
    """
    Tests para validar la metodología de cálculo paso a paso
    """
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear conjunto
        self.conjunto = Conjunto.objects.create(
            propietario=self.user,
            nit='123456789-0',
            nombre='Conjunto Test',
            direccion='Calle Test 123',
            ciudad='Bogotá',
            departamento='Cundinamarca',
            numero_unidades=100
        )
        
        # Crear calificaciones
        self.calificaciones = {
            'ausente': CalificacionOpcion.objects.create(
                codigo='ausente', nombre='Ausente', valor=Decimal('0.005'), orden=1
            ),
            'deficiente': CalificacionOpcion.objects.create(
                codigo='deficiente', nombre='Deficiente', valor=Decimal('0.100'), orden=2
            ),
            'vulnerable': CalificacionOpcion.objects.create(
                codigo='vulnerable', nombre='Vulnerable', valor=Decimal('0.250'), orden=3
            ),
            'adecuado': CalificacionOpcion.objects.create(
                codigo='adecuado', nombre='Adecuado', valor=Decimal('0.600'), orden=4
            ),
            'eficaz': CalificacionOpcion.objects.create(
                codigo='eficaz', nombre='Eficaz', valor=Decimal('0.900'), orden=5
            )
        }
        
        # Crear tipo de riesgo
        self.tipo_riesgo = TipoRiesgo.objects.create(
            codigo='test_riesgo',
            nombre='Riesgo de Prueba'
        )
        
        # Crear escenarios (2 escenarios, 2 preguntas cada uno)
        self.escenario1 = EscenarioRiesgo.objects.create(
            tipo_riesgo=self.tipo_riesgo,
            codigo='escenario_1',
            nombre='Escenario de Prueba 1'
        )
        
        self.escenario2 = EscenarioRiesgo.objects.create(
            tipo_riesgo=self.tipo_riesgo,
            codigo='escenario_2',
            nombre='Escenario de Prueba 2'
        )
        
        # Crear preguntas
        self.pregunta1_e1 = PreguntaEvaluacion.objects.create(
            escenario=self.escenario1,
            texto_pregunta='Pregunta 1 del Escenario 1',
            orden=1
        )
        
        self.pregunta2_e1 = PreguntaEvaluacion.objects.create(
            escenario=self.escenario1,
            texto_pregunta='Pregunta 2 del Escenario 1',
            orden=2
        )
        
        self.pregunta1_e2 = PreguntaEvaluacion.objects.create(
            escenario=self.escenario2,
            texto_pregunta='Pregunta 1 del Escenario 2',
            orden=1
        )
        
        self.pregunta2_e2 = PreguntaEvaluacion.objects.create(
            escenario=self.escenario2,
            texto_pregunta='Pregunta 2 del Escenario 2',
            orden=2
        )
    
    def test_calculo_metodologia_correcta(self):
        """
        Prueba el cálculo paso a paso de la metodología
        """
        # Datos de prueba: escenario con calificaciones conocidas
        evaluacion_data = {
            'riesgos_seleccionados': [self.tipo_riesgo.id],
            'respuestas': {
                str(self.tipo_riesgo.id): [
                    # Escenario 1
                    {'pregunta_id': self.pregunta1_e1.id, 'calificacion_id': self.calificaciones['vulnerable'].id},  # 0.250 -> 0.750
                    {'pregunta_id': self.pregunta2_e1.id, 'calificacion_id': self.calificaciones['deficiente'].id},  # 0.100 -> 0.900
                    # Escenario 2
                    {'pregunta_id': self.pregunta1_e2.id, 'calificacion_id': self.calificaciones['adecuado'].id},     # 0.600 -> 0.400
                    {'pregunta_id': self.pregunta2_e2.id, 'calificacion_id': self.calificaciones['eficaz'].id},       # 0.900 -> 0.100
                ]
            }
        }
        
        # Ejecutar cálculo
        resultados = calcular_promedios_por_metodologia_correcta(evaluacion_data)
        
        # Verificar que tenemos resultados
        self.assertIn('resultados_por_riesgo', resultados)
        self.assertIn('promedio_general', resultados)
        self.assertEqual(resultados['total_riesgos_evaluados'], 1)
        
        # Obtener resultados del riesgo
        datos_riesgo = resultados['resultados_por_riesgo'][self.tipo_riesgo.id]
        
        # Verificar estructura
        self.assertEqual(datos_riesgo['tipo_riesgo'], self.tipo_riesgo)
        self.assertEqual(datos_riesgo['numero_escenarios'], 2)
        self.assertIn('escenarios', datos_riesgo)
        
        # Verificar cálculos por escenario
        escenarios = datos_riesgo['escenarios']
        
        # Escenario 1: (0.750 + 0.900) / 2 = 0.825
        escenario1_datos = escenarios[self.escenario1.id]
        self.assertAlmostEqual(escenario1_datos['promedio'], 0.825, places=3)
        self.assertEqual(escenario1_datos['numero_preguntas'], 2)
        
        # Escenario 2: (0.400 + 0.100) / 2 = 0.250
        escenario2_datos = escenarios[self.escenario2.id]
        self.assertAlmostEqual(escenario2_datos['promedio'], 0.250, places=3)
        self.assertEqual(escenario2_datos['numero_preguntas'], 2)
        
        # Promedio del riesgo: (0.825 + 0.250) / 2 = 0.5375
        promedio_riesgo_esperado = (0.825 + 0.250) / 2
        self.assertAlmostEqual(datos_riesgo['promedio_riesgo'], promedio_riesgo_esperado, places=3)
        
        # Promedio general (igual al promedio del riesgo porque solo hay uno)
        self.assertAlmostEqual(resultados['promedio_general'], promedio_riesgo_esperado, places=3)
    
    def test_formula_1_menos_valor(self):
        """
        Prueba específica de la fórmula 1 - valor
        """
        casos_prueba = [
            ('ausente', 0.005, 0.995),
            ('deficiente', 0.100, 0.900),
            ('vulnerable', 0.250, 0.750),
            ('adecuado', 0.600, 0.400),
            ('eficaz', 0.900, 0.100),
        ]
        
        for codigo, valor_calificacion, resultado_esperado in casos_prueba:
            with self.subTest(calificacion=codigo):
                # Crear evaluacion_data con una sola respuesta
                evaluacion_data = {
                    'riesgos_seleccionados': [self.tipo_riesgo.id],
                    'respuestas': {
                        str(self.tipo_riesgo.id): [
                            {'pregunta_id': self.pregunta1_e1.id, 'calificacion_id': self.calificaciones[codigo].id},
                            {'pregunta_id': self.pregunta2_e1.id, 'calificacion_id': self.calificaciones[codigo].id},
                        ]
                    }
                }
                
                resultados = calcular_promedios_por_metodologia_correcta(evaluacion_data)
                datos_riesgo = resultados['resultados_por_riesgo'][self.tipo_riesgo.id]
                escenario_datos = datos_riesgo['escenarios'][self.escenario1.id]
                
                # El promedio del escenario debería ser igual al resultado esperado
                # porque ambas preguntas tienen la misma calificación
                self.assertAlmostEqual(escenario_datos['promedio'], resultado_esperado, places=3)
    
    def test_guardado_en_base_de_datos(self):
        """
        Prueba que los resultados se guarden correctamente en la base de datos
        """
        # Crear evaluación
        evaluacion = EvaluacionRiesgo.objects.create(
            conjunto=self.conjunto,
            creado_por=self.user,
            estado='completada'
        )
        
        # Datos de prueba
        evaluacion_data = {
            'riesgos_seleccionados': [self.tipo_riesgo.id],
            'respuestas': {
                str(self.tipo_riesgo.id): [
                    {'pregunta_id': self.pregunta1_e1.id, 'calificacion_id': self.calificaciones['vulnerable'].id},
                    {'pregunta_id': self.pregunta2_e1.id, 'calificacion_id': self.calificaciones['adecuado'].id},
                ]
            }
        }
        
        # Guardar resultados
        resultados = guardar_resultados_con_metodologia_correcta(evaluacion, evaluacion_data)
        
        # Verificar que se guardó en la evaluación
        evaluacion.refresh_from_db()
        self.assertIsNotNone(evaluacion.promedio_general)
        self.assertAlmostEqual(float(evaluacion.promedio_general), resultados['promedio_general'], places=3)
        
        # Verificar ResultadoRiesgo
        resultado_riesgo = ResultadoRiesgo.objects.get(evaluacion=evaluacion, tipo_riesgo=self.tipo_riesgo)
        self.assertAlmostEqual(float(resultado_riesgo.promedio_riesgo), resultados['resultados_por_riesgo'][self.tipo_riesgo.id]['promedio_riesgo'], places=3)
        
        # Verificar ResultadoEscenario
        resultado_escenario = ResultadoEscenario.objects.get(evaluacion=evaluacion, escenario=self.escenario1)
        datos_escenario = resultados['resultados_por_riesgo'][self.tipo_riesgo.id]['escenarios'][self.escenario1.id]
        self.assertAlmostEqual(float(resultado_escenario.promedio_escenario), datos_escenario['promedio'], places=3)
    
    def test_validacion_rangos(self):
        """
        Prueba que los valores se mantengan en rangos válidos (0-1)
        """
        # Esta prueba es más conceptual porque los valores siempre deberían estar en rango
        # con calificaciones válidas, pero es importante para casos edge
        
        evaluacion_data = {
            'riesgos_seleccionados': [self.tipo_riesgo.id],
            'respuestas': {
                str(self.tipo_riesgo.id): [
                    {'pregunta_id': self.pregunta1_e1.id, 'calificacion_id': self.calificaciones['ausente'].id},    # 1 - 0.005 = 0.995
                    {'pregunta_id': self.pregunta2_e1.id, 'calificacion_id': self.calificaciones['eficaz'].id},     # 1 - 0.900 = 0.100
                ]
            }
        }
        
        resultados = calcular_promedios_por_metodologia_correcta(evaluacion_data)
        
        # Verificar que todos los valores están en rango 0-1
        self.assertTrue(0 <= resultados['promedio_general'] <= 1)
        
        for datos_riesgo in resultados['resultados_por_riesgo'].values():
            self.assertTrue(0 <= datos_riesgo['promedio_riesgo'] <= 1)
            
            for datos_escenario in datos_riesgo['escenarios'].values():
                self.assertTrue(0 <= datos_escenario['promedio'] <= 1)
                
                for respuesta in datos_escenario['respuestas']:
                    self.assertTrue(0 <= respuesta['resultado'] <= 1)
    
    def test_multiples_riesgos(self):
        """
        Prueba con múltiples tipos de riesgo
        """
        # Crear segundo tipo de riesgo
        tipo_riesgo_2 = TipoRiesgo.objects.create(
            codigo='test_riesgo_2',
            nombre='Segundo Riesgo de Prueba'
        )
        
        escenario_2_1 = EscenarioRiesgo.objects.create(
            tipo_riesgo=tipo_riesgo_2,
            codigo='escenario_2_1',
            nombre='Escenario 2.1'
        )
        
        pregunta_2_1 = PreguntaEvaluacion.objects.create(
            escenario=escenario_2_1,
            texto_pregunta='Pregunta 2.1',
            orden=1
        )
        
        pregunta_2_2 = PreguntaEvaluacion.objects.create(
            escenario=escenario_2_1,
            texto_pregunta='Pregunta 2.2',
            orden=2
        )
        
        evaluacion_data = {
            'riesgos_seleccionados': [self.tipo_riesgo.id, tipo_riesgo_2.id],
            'respuestas': {
                str(self.tipo_riesgo.id): [
                    {'pregunta_id': self.pregunta1_e1.id, 'calificacion_id': self.calificaciones['adecuado'].id},  # 0.400
                    {'pregunta_id': self.pregunta2_e1.id, 'calificacion_id': self.calificaciones['adecuado'].id},  # 0.400
                ],
                str(tipo_riesgo_2.id): [
                    {'pregunta_id': pregunta_2_1.id, 'calificacion_id': self.calificaciones['eficaz'].id},      # 0.100
                    {'pregunta_id': pregunta_2_2.id, 'calificacion_id': self.calificaciones['eficaz'].id},      # 0.100
                ]
            }
        }
        
        resultados = calcular_promedios_por_metodologia_correcta(evaluacion_data)
        
        # Verificar que se procesaron ambos riesgos
        self.assertEqual(resultados['total_riesgos_evaluados'], 2)
        self.assertEqual(len(resultados['resultados_por_riesgo']), 2)
        
        # Riesgo 1: promedio = 0.400
        promedio_riesgo_1 = resultados['resultados_por_riesgo'][self.tipo_riesgo.id]['promedio_riesgo']
        self.assertAlmostEqual(promedio_riesgo_1, 0.400, places=3)
        
        # Riesgo 2: promedio = 0.100
        promedio_riesgo_2 = resultados['resultados_por_riesgo'][tipo_riesgo_2.id]['promedio_riesgo']
        self.assertAlmostEqual(promedio_riesgo_2, 0.100, places=3)
        
        # Promedio general: (0.400 + 0.100) / 2 = 0.250
        promedio_general_esperado = (0.400 + 0.100) / 2
        self.assertAlmostEqual(resultados['promedio_general'], promedio_general_esperado, places=3)
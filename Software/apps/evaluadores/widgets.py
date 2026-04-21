"""
Widgets personalizados para el formulario de evaluadores
"""
from django import forms
from django.utils.html import format_html, mark_safe


class PermisosCRUDWidget(forms.Widget):
    """
    Widget personalizado para manejar permisos CRUD por módulo
    """
    
    template_name = 'evaluadores/widgets/permisos_crud_widget.html'
    
    def __init__(self, modulos_choices=None, attrs=None):
        super().__init__(attrs)
        self.modulos_choices = modulos_choices or []
        
    def format_value(self, value):
        """Formatea el valor para mostrar en el widget"""
        if value is None:
            return {}
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return {}
        return value if isinstance(value, dict) else {}
    
    def render(self, name, value, attrs=None, renderer=None):
        """Renderiza el widget de permisos CRUD"""
        if attrs is None:
            attrs = {}
        
        formatted_value = self.format_value(value)
        
        # Verificación adicional de seguridad
        if formatted_value is None:
            formatted_value = {}
        
        # Definir los permisos disponibles con descripciones mejoradas
        permisos = [
            ('create', 'Crear', 'fas fa-plus-circle', 'success', 'Añadir nuevos elementos al módulo'),
            ('read', 'Consultar', 'fas fa-search', 'info', 'Ver y consultar información existente'), 
            ('update', 'Editar', 'fas fa-edit', 'warning', 'Modificar elementos existentes'),
            ('delete', 'Eliminar', 'fas fa-trash-alt', 'danger', 'Borrar elementos (acción irreversible)'),
            ('export', 'Exportar', 'fas fa-download', 'secondary', 'Generar reportes y descargas'),
            ('approve', 'Aprobar', 'fas fa-check-circle', 'primary', 'Validar y aprobar elementos'),
        ]
        
        html_output = []
        
        # CSS personalizado
        html_output.append('''
        <style>
        .permisos-crud-container {
            border: 1px solid #e3e6f0;
            border-radius: 0.5rem;
            padding: 0;
            overflow: hidden;
        }
        
        .modulo-card {
            border: none;
            border-bottom: 1px solid #e3e6f0;
            margin-bottom: 0;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .modulo-card:last-child {
            border-bottom: none;
        }
        
        .modulo-card:hover {
            background-color: #f8f9fc;
        }
        
        .modulo-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 1.25rem;
            border-bottom: 1px solid #e3e6f0;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .modulo-header:hover {
            background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        }
        
        .modulo-body {
            padding: 1.5rem 1.25rem;
            background: white;
        }
        
        .permiso-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .permiso-card {
            background: #f8f9fc;
            border: 2px solid #e2e8f0;
            border-radius: 0.5rem;
            padding: 1rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        
        .permiso-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .permiso-card.selected {
            border-color: #5a67d8;
            background: #edf2f7;
            transform: scale(1.02);
        }
        
        .permiso-card.create.selected { border-color: #38a169; background: #f0fff4; }
        .permiso-card.read.selected { border-color: #3182ce; background: #ebf8ff; }
        .permiso-card.update.selected { border-color: #ed8936; background: #fffaf0; }
        .permiso-card.delete.selected { border-color: #e53e3e; background: #fed7d7; }
        .permiso-card.export.selected { border-color: #805ad5; background: #faf5ff; }
        .permiso-card.approve.selected { border-color: #38b2ac; background: #e6fffa; }
        
        .permiso-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            display: block;
        }
        
        .permiso-label {
            font-weight: 600;
            margin: 0;
            display: block;
        }
        
        .permiso-description {
            font-size: 0.75rem;
            color: #718096;
            margin-top: 0.25rem;
        }
        
        .permiso-checkbox {
            position: absolute;
            opacity: 0;
            cursor: pointer;
            height: 0;
            width: 0;
        }
        
        .toggle-all-section {
            background: #f7fafc;
            padding: 1rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }
        
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        
        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        
        input:checked + .toggle-slider {
            background-color: #5a67d8;
        }
        
        input:checked + .toggle-slider:before {
            transform: translateX(26px);
        }
        
        .collapse-icon {
            transition: transform 0.3s ease;
        }
        
        .collapsed .collapse-icon {
            transform: rotate(-90deg);
        }
        </style>
        ''')
        
        html_output.append('<div class="permisos-crud-container">')
        
        # Si no hay módulos, mostrar mensaje
        if not self.modulos_choices:
            html_output.append('''
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    No hay módulos disponibles. Necesitas suscripciones activas para asignar permisos.
                </div>
            ''')
        else:
            # JavaScript para toggle de permisos y interacción mejorada
            html_output.append(f'''
            <script>
            // Función para toggle de todos los permisos de un módulo
            function toggleAllPermisos(moduloName, isChecked) {{
                const container = document.getElementById('modulo-' + moduloName);
                const checkboxes = container.querySelectorAll('input[type="checkbox"]:not(.toggle-all)');
                const cards = container.querySelectorAll('.permiso-card');
                
                checkboxes.forEach((cb, index) => {{
                    cb.checked = isChecked;
                    if (isChecked) {{
                        cards[index].classList.add('selected');
                    }} else {{
                        cards[index].classList.remove('selected');
                    }}
                }});
            }}
            
            // Función para actualizar el estado del toggle principal
            function updateToggleAll(moduloName) {{
                const container = document.getElementById('modulo-' + moduloName);
                const toggleAll = container.querySelector('.toggle-all');
                const checkboxes = container.querySelectorAll('input[type="checkbox"]:not(.toggle-all)');
                const checkedCount = container.querySelectorAll('input[type="checkbox"]:not(.toggle-all):checked').length;
                
                if (checkedCount === 0) {{
                    toggleAll.checked = false;
                    toggleAll.indeterminate = false;
                }} else if (checkedCount === checkboxes.length) {{
                    toggleAll.checked = true;
                    toggleAll.indeterminate = false;
                }} else {{
                    toggleAll.checked = false;
                    toggleAll.indeterminate = true;
                }}
            }}
            
            // Función para toggle de un permiso individual
            function togglePermiso(checkbox, card) {{
                if (checkbox.checked) {{
                    card.classList.add('selected');
                }} else {{
                    card.classList.remove('selected');
                }}
                
                // Actualizar el toggle general del módulo
                const moduloCard = card.closest('.modulo-card');
                const moduloName = moduloCard.id.replace('modulo-', '');
                updateToggleAll(moduloName);
            }}
            
            // Función para colapsar/expandir módulos
            function toggleModulo(moduloName) {{
                const header = document.querySelector('#modulo-' + moduloName + ' .modulo-header');
                const body = document.querySelector('#modulo-' + moduloName + ' .modulo-body');
                const icon = header.querySelector('.collapse-icon');
                
                if (body.style.display === 'none') {{
                    body.style.display = 'block';
                    header.classList.remove('collapsed');
                }} else {{
                    body.style.display = 'none';
                    header.classList.add('collapsed');
                }}
            }}
            
            // Inicialización cuando el DOM esté listo
            document.addEventListener('DOMContentLoaded', function() {{
                // Configurar estados iniciales
                document.querySelectorAll('.modulo-card').forEach(modulo => {{
                    const moduloName = modulo.id.replace('modulo-', '');
                    updateToggleAll(moduloName);
                    
                    // Configurar checkboxes para actualizar visual
                    modulo.querySelectorAll('.permiso-checkbox').forEach(checkbox => {{
                        const card = checkbox.closest('.permiso-card');
                        if (checkbox.checked) {{
                            card.classList.add('selected');
                        }}
                    }});
                }});
            }});
            </script>
            ''')
            
            # Renderizar cada módulo
            for modulo_value, modulo_display in self.modulos_choices:
                # Verificación adicional de seguridad para formatted_value
                if not formatted_value or not isinstance(formatted_value, dict):
                    formatted_value = {}
                permisos_modulo = formatted_value.get(modulo_value, {})
                # Asegurar que permisos_modulo también sea un diccionario
                if not isinstance(permisos_modulo, dict):
                    permisos_modulo = {}
                
                html_output.append(f'''
                <div class="modulo-card" id="modulo-{modulo_value}">
                    <div class="modulo-header" onclick="toggleModulo('{modulo_value}')">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-cube me-2"></i>
                            <span class="flex-grow-1">{modulo_display}</span>
                            <i class="fas fa-chevron-down collapse-icon"></i>
                        </div>
                    </div>
                    <div class="modulo-body">
                        <!-- Toggle para todos los permisos -->
                        <div class="toggle-all-section">
                            <div>
                                <strong><i class="fas fa-toggle-on me-2"></i>Seleccionar todos los permisos</strong>
                                <div class="text-muted small">Activa/desactiva todos los permisos de este módulo</div>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" class="toggle-all" 
                                       onchange="toggleAllPermisos('{modulo_value}', this.checked)">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        
                        <!-- Grid de permisos -->
                        <div class="permiso-grid">
                ''')
                
                # Renderizar checkboxes de permisos con nuevo diseño
                for permiso_key, permiso_label, permiso_icon, permiso_color, permiso_desc in permisos:
                    # Verificar que permisos_modulo sea un diccionario válido
                    if not isinstance(permisos_modulo, dict):
                        permisos_modulo = {}
                    checked = permisos_modulo.get(permiso_key, False)
                    input_name = f"{name}_{modulo_value}_{permiso_key}"
                    
                    html_output.append(f'''
                        <div class="permiso-card {permiso_key} {'selected' if checked else ''}" 
                             onclick="document.getElementById('id_{input_name}').click();">
                            <input type="checkbox" 
                                   class="permiso-checkbox" 
                                   name="{input_name}"
                                   id="id_{input_name}"
                                   value="1"
                                   {"checked" if checked else ""}
                                   onchange="togglePermiso(this, this.closest('.permiso-card'))">
                            <i class="{permiso_icon} text-{permiso_color} permiso-icon"></i>
                            <div class="permiso-label">{permiso_label}</div>
                            <div class="permiso-description">{permiso_desc}</div>
                        </div>
                    ''')
                
                html_output.append('''
                        </div>
                    </div>
                </div>
                ''')
        
        html_output.append('</div>')
        
        return mark_safe(''.join(html_output))
    
    def value_from_datadict(self, data, files, name):
        """Extrae el valor de los datos del formulario"""
        permisos_crud = {}
        
        # Iterar sobre los módulos y extraer sus permisos
        for modulo_value, _ in self.modulos_choices:
            permisos_modulo = {}
            
            # Verificar cada permiso
            permisos = ['create', 'read', 'update', 'delete', 'export', 'approve']
            for permiso in permisos:
                input_name = f"{name}_{modulo_value}_{permiso}"
                permisos_modulo[permiso] = input_name in data
            
            # Solo guardar si tiene al menos un permiso
            if any(permisos_modulo.values()):
                permisos_crud[modulo_value] = permisos_modulo
        
        return permisos_crud


class PermisosCRUDField(forms.Field):
    """
    Campo personalizado para manejar permisos CRUD
    """
    
    widget = PermisosCRUDWidget
    
    def __init__(self, modulos_choices=None, *args, **kwargs):
        self.modulos_choices = modulos_choices or []
        kwargs.setdefault('widget', self.widget(modulos_choices=self.modulos_choices))
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        """Convert the value to Python"""
        if value is None:
            return {}
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return {}
        return value if isinstance(value, dict) else {}
    
    def prepare_value(self, value):
        """Prepare value for display"""
        return self.to_python(value)
    
    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs['modulos_choices'] = self.modulos_choices
        return attrs
"""
Archivo WSGI para PythonAnywhere.

INSTRUCCIONES:
1. En PythonAnywhere > Web > tu app > Code section
2. En "WSGI configuration file" haz clic en el enlace para editar
3. Borra todo el contenido y pega este archivo (ajustando RUTA_PROYECTO y TUUSUARIO)
"""

import sys
import os

# === AJUSTA ESTAS DOS VARIABLES ===
TUUSUARIO = 'tuusuario'            # Tu nombre de usuario en PythonAnywhere
NOMBRE_PROYECTO = 'Software'        # Nombre de la carpeta raíz del proyecto
# ==================================

# Ruta al proyecto (donde está manage.py)
RUTA_PROYECTO = f'/home/{TUUSUARIO}/{NOMBRE_PROYECTO}'

# Agregar el proyecto al Python path
if RUTA_PROYECTO not in sys.path:
    sys.path.insert(0, RUTA_PROYECTO)

# Apuntar al virtualenv (PythonAnywhere lo crea automáticamente)
# Esto solo es necesario si NO usas el campo "Virtualenv" en el panel web
# RUTA_VENV = f'/home/{TUUSUARIO}/.virtualenvs/nombre_del_venv'
# activate_this = f'{RUTA_VENV}/bin/activate_this.py'
# exec(open(activate_this).read(), {'__file__': activate_this})

# Cargar variables de entorno desde .env
from decouple import AutoConfig
config = AutoConfig(search_path=RUTA_PROYECTO)

# Configurar settings de Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.pythonanywhere'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

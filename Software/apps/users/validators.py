"""
Validadores personalizados para contraseñas y seguridad
"""
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import CommonPasswordValidator
from django.core.files.images import get_image_dimensions
import re
import string
from typing import List, Dict, Any
import os
from PIL import Image

User = get_user_model()


# =============================================================================
# VALIDADORES DE ARCHIVOS E IMÁGENES
# =============================================================================

def validate_image_file_extension(value):
    """Validar extensiones de archivo de imagen permitidas"""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    ext = os.path.splitext(value.name)[1].lower()
    
    if ext not in valid_extensions:
        raise ValidationError(
            f'Tipo de archivo no permitido. Solo se permiten: {", ".join(valid_extensions)}'
        )


def validate_image_file_size(value):
    """Validar tamaño máximo de archivo de imagen (5MB)"""
    limit_mb = 5
    limit_bytes = limit_mb * 1024 * 1024
    
    if value.size > limit_bytes:
        raise ValidationError(
            f'El archivo es demasiado grande. Tamaño máximo permitido: {limit_mb}MB'
        )


def validate_image_dimensions(value):
    """Validar dimensiones mínimas y máximas de imagen"""
    try:
        width, height = get_image_dimensions(value)
        
        if width is None or height is None:
            raise ValidationError('No se pudieron obtener las dimensiones de la imagen.')
        
        # Dimensiones mínimas
        min_width, min_height = 50, 50
        if width < min_width or height < min_height:
            raise ValidationError(
                f'La imagen es demasiado pequeña. Dimensiones mínimas: {min_width}x{min_height}px'
            )
        
        # Dimensiones máximas
        max_width, max_height = 4000, 4000
        if width > max_width or height > max_height:
            raise ValidationError(
                f'La imagen es demasiado grande. Dimensiones máximas: {max_width}x{max_height}px'
            )
        
        # Aspect ratio para avatar (opcional)
        aspect_ratio = width / height
        if hasattr(value, '_avatar_validation'):
            # Para avatares, preferimos ratios cuadrados o cercanos
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                raise ValidationError(
                    'Para avatares, se recomienda una imagen más cuadrada (ratio de aspecto entre 0.5 y 2.0)'
                )
                
    except Exception as e:
        raise ValidationError(f'Error validando imagen: {str(e)}')


def validate_avatar_image(value):
    """Validador específico para imágenes de avatar"""
    # Marcar para validación de avatar
    value._avatar_validation = True
    
    # Aplicar todas las validaciones
    validate_image_file_extension(value)
    validate_image_file_size(value)
    validate_image_dimensions(value)
    
    # Validaciones específicas de avatar
    try:
        # Verificar que sea una imagen válida
        img = Image.open(value)
        img.verify()
        
        # Reset file pointer después de verify
        value.seek(0)
        
    except Exception:
        raise ValidationError('El archivo no es una imagen válida.')


def validate_phone_number(value):
    """Validar formato de número telefónico"""
    if not value:
        return
    
    # Remover espacios y caracteres comunes
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    
    # Verificar formato básico
    if not re.match(r'^\+?[\d]{9,15}$', cleaned):
        raise ValidationError(
            'Número de teléfono inválido. Use formato: +52123456789 o 123456789'
        )


def validate_twitter_username(value):
    """Validar nombre de usuario de Twitter"""
    if not value:
        return
    
    # Remover @ si está presente
    username = value.lstrip('@')
    
    # Validar formato de Twitter
    if not re.match(r'^[A-Za-z0-9_]{1,15}$', username):
        raise ValidationError(
            'Nombre de usuario de Twitter inválido. Solo letras, números y _ (máximo 15 caracteres)'
        )


def validate_bio_content(value):
    """Validar contenido de biografía"""
    if not value:
        return
    
    # Verificar longitud
    if len(value) > 500:
        raise ValidationError('La biografía no puede exceder 500 caracteres.')
    
    # Verificar contenido ofensivo básico (lista simple)
    prohibited_words = ['spam', 'hack', 'virus']  # Expandir según necesidades
    
    for word in prohibited_words:
        if word.lower() in value.lower():
            raise ValidationError('La biografía contiene contenido no permitido.')
    
    # Verificar que no sea solo espacios o caracteres especiales
    if not re.search(r'[a-zA-Z0-9]', value):
        raise ValidationError('La biografía debe contener al menos algunos caracteres alfanuméricos.')


class ImageValidator:
    """Validador de imágenes más completo y configurable"""
    
    def __init__(self, max_size_mb=5, min_dimensions=(50, 50), max_dimensions=(4000, 4000),
                 allowed_formats=None, check_corruption=True):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.min_dimensions = min_dimensions
        self.max_dimensions = max_dimensions
        self.allowed_formats = allowed_formats or ['JPEG', 'PNG', 'GIF', 'WEBP']
        self.check_corruption = check_corruption
    
    def __call__(self, value):
        self.validate_file_size(value)
        self.validate_file_type(value)
        self.validate_image_format(value)
        self.validate_dimensions(value)
        
        if self.check_corruption:
            self.validate_image_integrity(value)
    
    def validate_file_size(self, value):
        """Validar tamaño del archivo"""
        if value.size > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            raise ValidationError(
                f'El archivo es demasiado grande. Tamaño máximo: {max_mb}MB'
            )
    
    def validate_file_type(self, value):
        """Validar tipo MIME del archivo"""
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp'
        ]
        
        if hasattr(value, 'content_type') and value.content_type not in allowed_types:
            raise ValidationError(
                'Tipo de archivo no permitido. Solo se permiten imágenes JPEG, PNG, GIF y WebP.'
            )
    
    def validate_image_format(self, value):
        """Validar formato de imagen usando PIL"""
        try:
            img = Image.open(value)
            if img.format not in self.allowed_formats:
                raise ValidationError(
                    f'Formato de imagen no permitido. Formatos válidos: {", ".join(self.allowed_formats)}'
                )
            
            # Reset file pointer
            value.seek(0)
            
        except Exception as e:
            raise ValidationError(f'Error validando formato de imagen: {str(e)}')
    
    def validate_dimensions(self, value):
        """Validar dimensiones de la imagen"""
        try:
            width, height = get_image_dimensions(value)
            
            if width is None or height is None:
                raise ValidationError('No se pudieron obtener las dimensiones de la imagen.')
            
            # Verificar dimensiones mínimas
            min_w, min_h = self.min_dimensions
            if width < min_w or height < min_h:
                raise ValidationError(
                    f'Imagen demasiado pequeña. Dimensiones mínimas: {min_w}x{min_h}px'
                )
            
            # Verificar dimensiones máximas
            max_w, max_h = self.max_dimensions
            if width > max_w or height > max_h:
                raise ValidationError(
                    f'Imagen demasiado grande. Dimensiones máximas: {max_w}x{max_h}px'
                )
                
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f'Error validando dimensiones: {str(e)}')
    
    def validate_image_integrity(self, value):
        """Verificar que la imagen no esté corrupta"""
        try:
            img = Image.open(value)
            img.verify()
            
            # Reset file pointer después de verify
            value.seek(0)
            
        except Exception:
            raise ValidationError('La imagen está corrupta o no es válida.')


# Instancias preconfiguradas de validadores
avatar_validator = ImageValidator(
    max_size_mb=2,
    min_dimensions=(100, 100),
    max_dimensions=(1000, 1000),
    allowed_formats=['JPEG', 'PNG']
)

cover_image_validator = ImageValidator(
    max_size_mb=5,
    min_dimensions=(400, 200),
    max_dimensions=(2000, 1000),
    allowed_formats=['JPEG', 'PNG', 'WEBP']
)


class CustomPasswordValidator:
    """
    Validador personalizado para contraseñas con reglas específicas
    """
    
    def __init__(self, min_length=8, require_uppercase=True, require_lowercase=True,
                 require_numbers=True, require_special=True, max_personal_similarity=0.7):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_numbers = require_numbers
        self.require_special = require_special
        self.max_personal_similarity = max_personal_similarity
    
    def validate(self, password, user=None):
        """
        Validar contraseña según las reglas establecidas
        """
        errors = []
        
        # Verificar longitud mínima
        if len(password) < self.min_length:
            errors.append(f"La contraseña debe tener al menos {self.min_length} caracteres.")
        
        # Verificar letra mayúscula
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("La contraseña debe contener al menos una letra mayúscula.")
        
        # Verificar letra minúscula
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("La contraseña debe contener al menos una letra minúscula.")
        
        # Verificar números
        if self.require_numbers and not re.search(r'\d', password):
            errors.append("La contraseña debe contener al menos un número.")
        
        # Verificar caracteres especiales
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?\":{}|<>).")
        
        # Verificar similitud con información personal
        if user and self._is_too_similar_to_user_info(password, user):
            errors.append("La contraseña no puede ser muy similar a tu información personal.")
        
        # Verificar patrones comunes peligrosos
        if self._has_dangerous_patterns(password):
            errors.append("La contraseña no puede contener patrones comunes como '123', 'abc' o caracteres repetidos.")
        
        # Verificar que no sea una contraseña muy común
        if self._is_common_password(password):
            errors.append("Esta contraseña es demasiado común. Elige una más única.")
        
        if errors:
            raise ValidationError(errors)
    
    def _is_too_similar_to_user_info(self, password, user) -> bool:
        """
        Verificar si la contraseña es muy similar a la información del usuario
        """
        if not user:
            return False
        
        user_info = []
        
        # Recopilar información del usuario
        if hasattr(user, 'first_name') and user.first_name:
            user_info.append(user.first_name.lower())
        if hasattr(user, 'last_name') and user.last_name:
            user_info.append(user.last_name.lower())
        if hasattr(user, 'email') and user.email:
            user_info.append(user.email.split('@')[0].lower())
        if hasattr(user, 'username') and user.username:
            user_info.append(user.username.lower())
        
        password_lower = password.lower()
        
        for info in user_info:
            if info and len(info) > 2:
                # Verificar si la info está contenida en la contraseña
                if info in password_lower:
                    return True
                
                # Verificar similitud usando Levenshtein distance aproximada
                if self._similarity_ratio(info, password_lower) > self.max_personal_similarity:
                    return True
        
        return False
    
    def _has_dangerous_patterns(self, password) -> bool:
        """
        Verificar patrones peligrosos en la contraseña
        """
        # Caracteres repetidos (más de 2 seguidos)
        if re.search(r'(.)\1{2,}', password):
            return True
        
        # Secuencias comunes
        dangerous_sequences = [
            '123', '321', 'abc', 'cba', 'qwe', 'ewq',
            'asd', 'dsa', 'zxc', 'cxz', '000', '111'
        ]
        
        password_lower = password.lower()
        for sequence in dangerous_sequences:
            if sequence in password_lower:
                return True
        
        # Verificar secuencias numéricas ascendentes/descendentes
        for i in range(len(password) - 2):
            if password[i:i+3].isdigit():
                nums = [int(c) for c in password[i:i+3]]
                if nums == sorted(nums) or nums == sorted(nums, reverse=True):
                    return True
        
        return False
    
    def _is_common_password(self, password) -> bool:
        """
        Verificar si es una contraseña muy común
        """
        common_passwords = [
            'password', 'password123', '12345678', 'qwerty123',
            'admin123', 'letmein', 'welcome', 'monkey123',
            'dragon123', 'master123', 'shadow123', 'football',
            'baseball', 'basketball', 'superman', 'batman'
        ]
        
        return password.lower() in common_passwords
    
    def _similarity_ratio(self, a, b) -> float:
        """
        Calcular ratio de similitud simple entre dos strings
        """
        if not a or not b:
            return 0.0
        
        matches = sum(1 for char_a, char_b in zip(a, b) if char_a == char_b)
        return matches / max(len(a), len(b))
    
    def get_help_text(self):
        """
        Texto de ayuda para el usuario
        """
        help_texts = []
        help_texts.append(f"Tu contraseña debe tener al menos {self.min_length} caracteres.")
        
        if self.require_uppercase:
            help_texts.append("Debe contener al menos una letra mayúscula.")
        if self.require_lowercase:
            help_texts.append("Debe contener al menos una letra minúscula.")
        if self.require_numbers:
            help_texts.append("Debe contener al menos un número.")
        if self.require_special:
            help_texts.append("Debe contener al menos un carácter especial.")
        
        help_texts.append("No puede ser muy similar a tu información personal.")
        help_texts.append("No puede contener patrones comunes o secuencias obvias.")
        
        return " ".join(help_texts)


class NoPersonalInfoValidator:
    """
    Validador para evitar información personal en contraseñas
    """
    
    def validate(self, password, user=None):
        if not user:
            return
        
        personal_info = []
        
        # Recopilar información personal
        if hasattr(user, 'first_name') and user.first_name:
            personal_info.extend([
                user.first_name,
                user.first_name.lower(),
                user.first_name.upper()
            ])
        
        if hasattr(user, 'last_name') and user.last_name:
            personal_info.extend([
                user.last_name,
                user.last_name.lower(),
                user.last_name.upper()
            ])
        
        if hasattr(user, 'email') and user.email:
            email_parts = user.email.split('@')
            personal_info.extend([
                email_parts[0],
                email_parts[0].lower(),
                email_parts[0].upper()
            ])
        
        # Verificar si alguna información personal está en la contraseña
        for info in personal_info:
            if info and len(info) > 2 and info in password:
                raise ValidationError(
                    "La contraseña no puede contener tu información personal "
                    "como nombre, apellido o email."
                )
    
    def get_help_text(self):
        return (
            "Tu contraseña no puede contener tu información personal "
            "como nombre, apellido o email."
        )


class NoRepeatingCharactersValidator:
    """
    Validador para evitar caracteres repetidos excesivos
    """
    
    def __init__(self, max_repeats=2):
        self.max_repeats = max_repeats
    
    def validate(self, password, user=None):
        # Buscar caracteres repetidos
        pattern = rf'(.)\1{{{self.max_repeats},}}'
        if re.search(pattern, password):
            raise ValidationError(
                f"La contraseña no puede tener más de {self.max_repeats} "
                "caracteres iguales consecutivos."
            )
    
    def get_help_text(self):
        return (
            f"Tu contraseña no puede tener más de {self.max_repeats} "
            "caracteres iguales consecutivos."
        )


class NoSequentialCharactersValidator:
    """
    Validador para evitar secuencias de caracteres
    """
    
    def __init__(self, max_sequence_length=3):
        self.max_sequence_length = max_sequence_length
    
    def validate(self, password, user=None):
        # Verificar secuencias numéricas
        for i in range(len(password) - self.max_sequence_length + 1):
            substring = password[i:i + self.max_sequence_length]
            
            # Verificar si es una secuencia numérica
            if substring.isdigit():
                nums = [int(c) for c in substring]
                if self._is_sequence(nums):
                    raise ValidationError(
                        f"La contraseña no puede contener secuencias numéricas "
                        f"de {self.max_sequence_length} o más dígitos."
                    )
            
            # Verificar secuencias alfabéticas
            if substring.isalpha():
                chars = [ord(c.lower()) for c in substring]
                if self._is_sequence(chars):
                    raise ValidationError(
                        f"La contraseña no puede contener secuencias alfabéticas "
                        f"de {self.max_sequence_length} o más letras."
                    )
    
    def _is_sequence(self, numbers):
        """Verificar si una lista de números forma una secuencia"""
        if len(numbers) < 2:
            return False
        
        # Secuencia ascendente
        ascending = all(numbers[i] == numbers[i-1] + 1 for i in range(1, len(numbers)))
        
        # Secuencia descendente
        descending = all(numbers[i] == numbers[i-1] - 1 for i in range(1, len(numbers)))
        
        return ascending or descending
    
    def get_help_text(self):
        return (
            f"Tu contraseña no puede contener secuencias de "
            f"{self.max_sequence_length} o más caracteres consecutivos."
        )


class PasswordHistoryValidator:
    """
    Validador para evitar reutilización de contraseñas anteriores
    """
    
    def __init__(self, history_count=5):
        self.history_count = history_count
    
    def validate(self, password, user=None):
        # Este validador requeriría un modelo para almacenar historial
        # Por ahora solo validamos contra la contraseña actual
        if user and user.check_password(password):
            raise ValidationError(
                "No puedes usar tu contraseña actual. "
                "Elige una contraseña diferente."
            )
    
    def get_help_text(self):
        return (
            f"Tu nueva contraseña no puede ser igual a tus últimas "
            f"{self.history_count} contraseñas."
        )


# Funciones de utilidad para análisis de contraseñas

def calculate_password_entropy(password: str) -> float:
    """
    Calcular la entropía de una contraseña
    """
    charset_size = 0
    
    if re.search(r'[a-z]', password):
        charset_size += 26
    if re.search(r'[A-Z]', password):
        charset_size += 26
    if re.search(r'\d', password):
        charset_size += 10
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        charset_size += 32
    
    if charset_size == 0:
        return 0.0
    
    import math
    return len(password) * math.log2(charset_size)


def estimate_crack_time(password: str) -> Dict[str, Any]:
    """
    Estimar tiempo de crackeo de una contraseña
    """
    entropy = calculate_password_entropy(password)
    
    # Asumiendo 1 billón de intentos por segundo (GPU moderna)
    attempts_per_second = 1e12
    
    # Tiempo promedio = 2^(entropy-1) / attempts_per_second
    if entropy > 0:
        avg_time_seconds = (2 ** (entropy - 1)) / attempts_per_second
    else:
        avg_time_seconds = 0
    
    # Convertir a unidades legibles
    if avg_time_seconds < 60:
        time_str = f"{avg_time_seconds:.2f} segundos"
        level = "Muy débil"
    elif avg_time_seconds < 3600:
        time_str = f"{avg_time_seconds/60:.2f} minutos"
        level = "Débil"
    elif avg_time_seconds < 86400:
        time_str = f"{avg_time_seconds/3600:.2f} horas"
        level = "Regular"
    elif avg_time_seconds < 31536000:
        time_str = f"{avg_time_seconds/86400:.2f} días"
        level = "Buena"
    elif avg_time_seconds < 31536000000:
        time_str = f"{avg_time_seconds/31536000:.2f} años"
        level = "Fuerte"
    else:
        time_str = "Más de 1000 años"
        level = "Muy fuerte"
    
    return {
        'entropy': entropy,
        'crack_time_seconds': avg_time_seconds,
        'crack_time_readable': time_str,
        'strength_level': level
    }


def analyze_password_patterns(password: str) -> List[str]:
    """
    Analizar patrones problemáticos en una contraseña
    """
    issues = []
    
    # Caracteres repetidos
    if re.search(r'(.)\1{2,}', password):
        issues.append("Contiene caracteres repetidos")
    
    # Secuencias comunes
    common_sequences = ['123', '321', 'abc', 'cba', 'qwe', 'asd', 'zxc']
    for seq in common_sequences:
        if seq in password.lower():
            issues.append(f"Contiene la secuencia común '{seq}'")
    
    # Solo números
    if password.isdigit():
        issues.append("Solo contiene números")
    
    # Solo letras
    if password.isalpha():
        issues.append("Solo contiene letras")
    
    # Muy corta
    if len(password) < 8:
        issues.append("Demasiado corta")
    
    # Patrones de teclado
    keyboard_patterns = ['qwerty', 'asdf', 'zxcv', '1234', '4321']
    for pattern in keyboard_patterns:
        if pattern in password.lower():
            issues.append(f"Contiene patrón de teclado '{pattern}'")
    
    return issues
"""
Mixins para filtrado de registros por propietario
Permite que evaluadores solo vean registros propios y usuarios principales vean todos
"""
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from apps.evaluadores.models import Evaluador


class OwnershipFilterMixin:
    """
    Mixin que filtra registros basado en la propiedad/creación:
    - Evaluadores: Solo ven registros que crearon ellos mismos
    - Usuarios principales: Ven todos los registros de su "organización"
    - Admins/Staff: Ven todo
    """
    
    # Configuración del mixin (sobreescribir en las vistas)
    ownership_field = 'owner'  # Campo que indica el propietario del registro principal
    creator_field = 'created_by'  # Campo que indica quién creó el registro
    allow_related_access = True  # Si permite acceso a registros relacionados
    
    def get_ownership_queryset(self, queryset):
        """
        Filtra el queryset basado en el tipo de usuario y sus permisos de propiedad
        """
        user = self.request.user
        
        # Superusuarios y staff ven todo
        if user.is_superuser or user.is_staff:
            return queryset
            
        try:
            # Verificar si es evaluador
            evaluador = Evaluador.objects.get(usuario_evaluador=user)
            
            # Los evaluadores solo ven registros que son de su propiedad O que crearon
            filters = Q()
            
            # Si tiene campo de propietario (owner), incluir registros propios
            if hasattr(queryset.model, self.ownership_field):
                owner_filter = {self.ownership_field: user}
                filters |= Q(**owner_filter)
            
            # Si tiene campo de creador (created_by), incluir registros creados
            if hasattr(queryset.model, self.creator_field):
                creator_filter = {self.creator_field: user}
                filters |= Q(**creator_filter)
            
            # Si no hay ningún campo relevante, no puede ver nada
            if not filters:
                return queryset.none()
            
            return queryset.filter(filters)
                
        except Evaluador.DoesNotExist:
            # Es usuario principal - ve registros de su propiedad y los creados por sus evaluadores
            if hasattr(queryset.model, self.ownership_field):
                # Registros propios del usuario principal
                own_filter = {self.ownership_field: user}
                filters = Q(**own_filter)
                
                # Si permite acceso relacionado, incluir registros creados por sus evaluadores
                if self.allow_related_access and hasattr(queryset.model, self.creator_field):
                    # Obtener evaluadores del usuario principal
                    evaluadores_ids = Evaluador.objects.filter(
                        usuario_principal=user
                    ).values_list('usuario_evaluador_id', flat=True)
                    
                    if evaluadores_ids:
                        creator_filter = {f'{self.creator_field}__in': evaluadores_ids}
                        filters |= Q(**creator_filter)
                
                return queryset.filter(filters)
            else:
                # Si no tiene campo owner, asumir que puede ver todo
                return queryset
    
    def get_object_ownership(self, obj):
        """
        Verifica si el usuario actual tiene acceso a un objeto específico
        """
        user = self.request.user
        
        # Superusuarios y staff tienen acceso completo
        if user.is_superuser or user.is_staff:
            return True
            
        try:
            # Verificar si es evaluador
            evaluador = Evaluador.objects.get(usuario_evaluador=user)
            
            # Los evaluadores pueden acceder a objetos que son de su propiedad O que crearon
            # Verificar propiedad (owner)
            if hasattr(obj, self.ownership_field):
                owner = getattr(obj, self.ownership_field)
                if owner == user:
                    return True
            
            # Verificar creación (created_by)
            if hasattr(obj, self.creator_field):
                creator = getattr(obj, self.creator_field)
                if creator == user:
                    return True
            
            return False
                
        except Evaluador.DoesNotExist:
            # Es usuario principal
            if hasattr(obj, self.ownership_field):
                owner = getattr(obj, self.ownership_field)
                if owner == user:
                    return True
                    
            # También puede acceder si fue creado por uno de sus evaluadores
            if hasattr(obj, self.creator_field):
                creator = getattr(obj, self.creator_field)
                if Evaluador.objects.filter(
                    usuario_principal=user,
                    usuario_evaluador=creator
                ).exists():
                    return True
                    
            return False
    
    def check_object_ownership(self, obj):
        """
        Verifica propiedad y lanza excepción si no tiene acceso
        """
        if not self.get_object_ownership(obj):
            raise PermissionDenied("No tienes permisos para acceder a este registro")
    
    def get_queryset(self):
        """
        Override del get_queryset para aplicar filtrado automático
        """
        queryset = super().get_queryset()
        return self.get_ownership_queryset(queryset)
    
    def get_object(self):
        """
        Override del get_object para verificar permisos de acceso
        """
        obj = super().get_object()
        self.check_object_ownership(obj)
        return obj


class CreatedByMixin:
    """
    Mixin que automáticamente asigna el usuario actual al campo created_by
    al crear nuevos registros
    """
    
    def form_valid(self, form):
        """
        Asigna automáticamente el usuario actual como creator
        """
        if hasattr(form.instance, 'created_by') and not form.instance.created_by:
            form.instance.created_by = self.request.user
            
        return super().form_valid(form)
    
    def perform_create(self, serializer):
        """
        Para vistas basadas en DRF - asigna el usuario actual
        """
        serializer.save(created_by=self.request.user)


class UserTypeContextMixin:
    """
    Mixin que añade información del tipo de usuario al contexto del template
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Información del tipo de usuario
        context['user_type_info'] = {
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'is_evaluator': False,
            'is_principal_user': False,
            'evaluator_info': None,
            'can_see_all_records': user.is_superuser or user.is_staff
        }
        
        try:
            evaluador = Evaluador.objects.get(usuario_evaluador=user)
            context['user_type_info'].update({
                'is_evaluator': True,
                'evaluator_info': {
                    'tipo': evaluador.tipo_evaluador,
                    'usuario_principal': evaluador.usuario_principal,
                    'modulos_permitidos': evaluador.modulos_permitidos,
                    'estado': evaluador.estado
                }
            })
        except Evaluador.DoesNotExist:
            if not (user.is_superuser or user.is_staff):
                context['user_type_info']['is_principal_user'] = True
        
        return context


class OwnershipValidationMixin:
    """
    Mixin para validar que los registros relacionados pertenezcan al usuario
    """
    
    def validate_related_ownership(self, related_obj, related_field='owner'):
        """
        Valida que un objeto relacionado pertenezca al usuario actual
        """
        user = self.request.user
        
        if user.is_superuser or user.is_staff:
            return True
            
        try:
            evaluador = Evaluador.objects.get(usuario_evaluador=user)
            # Los evaluadores solo pueden relacionar con lo que pueden ver
            if hasattr(related_obj, 'created_by'):
                return related_obj.created_by == user
            return False
        except Evaluador.DoesNotExist:
            # Usuario principal
            if hasattr(related_obj, related_field):
                owner = getattr(related_obj, related_field)
                return owner == user
            return True
    
    def clean_related_objects(self, form):
        """
        Valida todos los objetos relacionados en el formulario
        """
        # Este método debe ser sobreescrito según las necesidades específicas
        pass
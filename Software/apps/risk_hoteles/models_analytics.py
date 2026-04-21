"""
Modelos para el sistema de analytics del módulo risk_hoteles
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class AnalyticsEvent(models.Model):
    """Modelo para registrar eventos de analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_event'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"


class UserSession(models.Model):
    """Modelo para registrar sesiones de usuario"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    pages_visited = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'user_session'
        ordering = ['-start_time']
        
    def __str__(self):
        return f"Session {self.session_id}"


class PageView(models.Model):
    """Modelo para registrar vistas de página"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    page_url = models.URLField()
    page_title = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    time_on_page = models.IntegerField(null=True, blank=True)  # seconds
    
    class Meta:
        db_table = 'page_view'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.page_url} - {self.timestamp}"


class ClickEvent(models.Model):
    """Modelo para registrar eventos de clic"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    element_id = models.CharField(max_length=255, null=True, blank=True)
    element_class = models.CharField(max_length=255, null=True, blank=True)
    element_text = models.TextField(null=True, blank=True)
    page_url = models.URLField()
    timestamp = models.DateTimeField(default=timezone.now)
    coordinates_x = models.IntegerField(null=True, blank=True)
    coordinates_y = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'click_event'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"Click on {self.element_id or 'unknown'}"


class ConversionGoal(models.Model):
    """Modelo para definir objetivos de conversión"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    goal_type = models.CharField(max_length=50, choices=[
        ('page_visit', 'Page Visit'),
        ('form_submit', 'Form Submit'),
        ('button_click', 'Button Click'),
        ('time_spent', 'Time Spent'),
    ])
    target_url = models.URLField(null=True, blank=True)
    target_element = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'conversion_goal'
        
    def __str__(self):
        return self.name


class Conversion(models.Model):
    """Modelo para registrar conversiones"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(ConversionGoal, on_delete=models.CASCADE)
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'conversion'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.goal.name} - {self.timestamp}"


class AnalyticsReport(models.Model):
    """Modelo para almacenar reportes de analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ])
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'analytics_report'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.report_type})"
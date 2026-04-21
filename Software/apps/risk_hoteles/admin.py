from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Hotel, RiskCategory,
    SecurityCategory, SecurityQuestion, SecurityAssessment, SecurityResponse, SecurityCategoryComment
)


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'country', 'category', 'total_rooms', 'owner', 'is_active', 'created_at']
    list_filter = ['category', 'country', 'is_active', 'created_at']
    search_fields = ['name', 'city', 'country', 'owner__username', 'owner__email']
    list_editable = ['is_active']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'name', 'category', 'total_rooms')
        }),
        ('Ubicación', {
            'fields': ('address', 'city', 'country')
        }),
        ('Contacto', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Administración', {
            'fields': ('owner', 'is_active', 'created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')


@admin.register(RiskCategory)
class RiskCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['weight', 'is_active']


@admin.register(SecurityCategory)
class SecurityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'icon', 'questions_count', 'weight', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['weight', 'order', 'is_active']
    ordering = ['order', 'name']
    
    def questions_count(self, obj):
        count = obj.questions.filter(is_active=True).count()
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} preguntas</span>',
            '#28a745' if count > 0 else '#dc3545',
            count
        )
    questions_count.short_description = 'Preguntas'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('questions')


class SecurityQuestionInline(admin.TabularInline):
    model = SecurityQuestion
    extra = 0
    fields = ['question_text', 'weight', 'order', 'is_required', 'is_active']
    ordering = ['order']


@admin.register(SecurityQuestion)
class SecurityQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'category', 'weight', 'order', 'is_required', 'is_active']
    list_filter = ['category', 'is_required', 'is_active']
    search_fields = ['question_text', 'help_text']
    list_editable = ['weight', 'order', 'is_required', 'is_active']
    ordering = ['category', 'order']
    
    def question_text_short(self, obj):
        return obj.question_text[:80] + "..." if len(obj.question_text) > 80 else obj.question_text
    question_text_short.short_description = 'Pregunta'


class SecurityResponseInline(admin.TabularInline):
    model = SecurityResponse
    extra = 0
    fields = ['question', 'rating', 'not_applicable', 'comments']
    readonly_fields = ['question']


@admin.register(SecurityAssessment)
class SecurityAssessmentAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'assessment_type', 'assessment_date', 'status', 'overall_score', 'risk_level', 'created_by']
    list_filter = ['assessment_type', 'status', 'risk_level', 'assessment_date']
    search_fields = ['hotel__name', 'description']
    readonly_fields = ['id', 'overall_score', 'created_at', 'updated_at', 'completed_at']
    filter_horizontal = ['selected_categories']
    inlines = [SecurityResponseInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'hotel', 'assessment_type', 'assessment_date', 'description')
        }),
        ('Configuración', {
            'fields': ('selected_categories', 'status')
        }),
        ('Resultados', {
            'fields': ('overall_score', 'risk_level', 'observations', 'recommendations')
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at', 'completed_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hotel', 'created_by')


@admin.register(SecurityResponse)
class SecurityResponseAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'question_short', 'rating', 'not_applicable', 'answered_at']
    list_filter = ['rating', 'not_applicable', 'assessment__status']
    search_fields = ['question__question_text', 'comments', 'assessment__hotel__name']
    readonly_fields = ['answered_at']
    
    def question_short(self, obj):
        return obj.question.question_text[:50] + "..." if len(obj.question.question_text) > 50 else obj.question.question_text
    question_short.short_description = 'Pregunta'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assessment', 'question')


@admin.register(SecurityCategoryComment)
class SecurityCategoryCommentAdmin(admin.ModelAdmin):
    list_display = ['assessment_hotel', 'category_name', 'comment_preview', 'updated_at']
    list_filter = ['category', 'updated_at']
    search_fields = ['assessment__hotel__name', 'category__name', 'comments']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('assessment', 'category', 'comments')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def assessment_hotel(self, obj):
        return obj.assessment.hotel.name
    assessment_hotel.short_description = 'Hotel'
    
    def category_name(self, obj):
        return obj.category.name
    category_name.short_description = 'Categoría'
    
    def comment_preview(self, obj):
        return obj.comments[:100] + "..." if len(obj.comments) > 100 else obj.comments
    comment_preview.short_description = 'Comentarios'

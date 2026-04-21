from django.urls import path
from . import views
from . import views_2fa

app_name = 'users'

urlpatterns = [
    # Autenticación básica
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.CustomRegisterView.as_view(), name='register'),
    
    # Autenticación de dos factores (2FA)
    path('2fa/setup/', views_2fa.TwoFactorSetupView.as_view(), name='2fa_setup'),
    path('2fa/verify/', views_2fa.TwoFactorVerificationView.as_view(), name='2fa_verify'),
    path('2fa/manage/', views_2fa.two_factor_manage_view, name='2fa_manage'),
    path('2fa/disable/', views_2fa.disable_two_factor, name='2fa_disable'),
    path('2fa/backup-tokens/', views_2fa.regenerate_backup_tokens, name='2fa_backup_tokens'),
    path('2fa/qr-code/', views_2fa.qr_code_view, name='2fa_qr_code'),
    
    # Gestión de perfil
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/public/<int:user_id>/', views.profile_public_view, name='profile_public'),
    path('settings/', views.settings_view, name='settings'),
    
    # Gestión de avatar
    path('avatar/upload/', views.avatar_upload_view, name='avatar_upload'),
    path('avatar/delete/', views.delete_avatar_view, name='avatar_delete'),
    
    # Gestión de contraseñas (solo AJAX - modal)
    # Las URLs tradicionales de cambio de contraseña han sido removidas
    # para usar únicamente el modal desde el perfil
    
    # Reset de contraseña
    path('password/reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # AJAX endpoints
    path('ajax/password-strength/', views.password_strength_check, name='password_strength_check'),
    path('ajax/change-password/', views.change_password_ajax, name='change_password_ajax'),
    path('ajax/quick-profile-edit/', views.quick_profile_edit, name='quick_profile_edit'),
    path('ajax/profile-completion-tips/', views.profile_completion_tips, name='profile_completion_tips'),
    path('ajax/update-notification-setting/', views.update_notification_setting, name='update_notification_setting'),
    path('ajax/update-notification-setting/', views.update_notification_setting, name='update_notification_setting'),
    
    # Utilidades
    path('export/profile-data/', views.export_profile_data, name='export_profile_data'),
]
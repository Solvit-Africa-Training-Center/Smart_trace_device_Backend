from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('login/', views.login_user, name='login'),
    path('resend-verification/', views.resend_verification_code, name='resend_verification'),
    # User management
    path('users/', views.users_list, name='users_list'),
    path('users/<int:id>/', views.user_detail, name='user_detail'),
    path('users/<int:id>/delete/', views.user_delete, name='user_delete'),
    path('me/', views.me_update, name='me_update'),
]
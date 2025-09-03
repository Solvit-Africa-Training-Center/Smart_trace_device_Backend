from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('login/', views.login_user, name='login'),
    path('resend-verification/', views.resend_verification_code, name='resend_verification'),
]
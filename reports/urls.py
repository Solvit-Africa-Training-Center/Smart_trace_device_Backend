from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_report, name='report-create'),
    path('list/', views.list_reports, name='report-list'),
]

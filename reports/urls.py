from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_report, name='report-create'),
    path('list/', views.list_reports, name='report-list'),
    path('stats/location/', views.location_statistics, name='report-location-stats'),
    path('stats/monthly/', views.monthly_statistics, name='report-monthly-stats'),
]

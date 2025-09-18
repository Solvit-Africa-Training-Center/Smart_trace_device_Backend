from django.urls import path
from . import views

urlpatterns = [
    # Device endpoints
    path('', views.device_create, name='device-create'),
    path('mine/', views.my_devices_list, name='device-mine'),
    path('search/', views.device_search, name='device-search'),
    path('<int:id>/', views.device_delete, name='device-delete'),

    # Lost item endpoints
    path('lost/', views.lostitem_create, name='lostitem-create'),
    path('lost/<int:id>/', views.lostitem_update, name='lostitem-update'),
    path('lost/<int:id>/delete/', views.lostitem_delete, name='lostitem-delete'),
    path('lost/list/', views.lostitem_list, name='lostitem-list'),
    path('lost/search/', views.lostitem_search, name='lostitem-search'),

    # Found item endpoints
    path('found/', views.founditem_create, name='founditem-create'),
    path('found/<int:id>/', views.founditem_update, name='founditem-update'),
    path('found/<int:id>/delete/', views.founditem_delete, name='founditem-delete'),
    path('found/list/', views.founditem_list, name='founditem-list'),
    path('found/search/', views.founditem_search, name='founditem-search'),

    # Match endpoints
    path('matches/', views.match_create, name='match-create'),
    path('matches/list/', views.match_list, name='match-list'),

    # Return endpoints
    path('returns/', views.return_create, name='return-create'),
    path('returns/list/', views.return_list, name='return-list'),

    # Contact endpoints
    path('contact/', views.contact_create, name='contact-create'),
    path('contact/list/', views.contact_list, name='contact-list'),

    # Filter and search endpoints
    path('lost/filter/', views.lostitem_filter_by_status, name='lostitem-filter-status'),
    path('found/filter/', views.founditem_filter_by_status, name='founditem-filter-status'),
    path('search/serial/', views.search_by_serial_number, name='search-serial-number'),
    path('categories/', views.get_categories, name='get-categories'),
]

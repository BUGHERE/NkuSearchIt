from django.urls import path

from . import views

app_name = 'search'
urlpatterns = [
    path('search/', views.search, name='search'),
    path('search_result/', views.search_result, name='search_result'),
    path('test/', views.test, name='test'),
    path('search_log/', views.search_log, name='search_log'),
    path('search_log_clear/', views.search_log_clear, name='search_log_clear'),
    path('search_result_open/', views.search_result_open, name='search_result_open'),
    path('search_result_url_open/', views.search_result_url_open, name='search_result_url_open'),
    path('search_result_document/', views.search_result_document, name='search_result_document'),
]
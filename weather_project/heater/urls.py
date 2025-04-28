from django.urls import path
from . import views

urlpatterns = [
    path('', views.heating_and_cooling_table, name='heating_and_cooling_table'),
    path('data/', views.get_heating_cooling_data, name='get_heating_cooling_data'),
]

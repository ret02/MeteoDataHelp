from django.urls import path
from . import views

urlpatterns = [
    path('', views.heating_and_cooling_table, name='heater'),  # fixato il nome corretto della view
    path('api/', views.get_heating_cooling_data, name='heater_api'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.precipitation_page, name='precipitation'),
    path('precipitation_data', views.precipitation_chart, name='precipitation_data'),
]


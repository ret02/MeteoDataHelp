from django.urls import path
from .views import precipitation_chart, get_precipitation_data

urlpatterns = [
    path("", precipitation_chart, name="precipitation_chart"),
    path("data/", get_precipitation_data, name="get_precipitation_data"),
]

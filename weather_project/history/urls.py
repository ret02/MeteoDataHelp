from django.urls import path
from . import views  # Import views from the history app

urlpatterns = [
    path('', views.history_view, name='history_view'),  # Use the correct view
]

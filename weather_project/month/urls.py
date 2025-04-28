from django.urls import path
from . import views

urlpatterns = [
    # Your existing paths
    path('', views.month_chart, name='month_chart'),  # Main chart page
    path('process_month_data/', views.process_month_data, name='process_month_data'),  # Add this line
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.month_chart, name='month'),  # <- fixed this line
    path('data/', views.process_month_data, name='month-data'),
]


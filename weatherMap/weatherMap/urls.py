from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('heater/', include('heater.urls')),
    path('history/', include('history.urls')),
    path('month/', include('month.urls')),
    path('precipitation/', include('precipitation.urls')),
]

"""
Главный файл с маршрутами всего проекта
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),        # Все маршруты для пользователей
    path('api/auth/', include('auth_system.urls')),   # Маршруты для управления правами
    path('api/shop/', include('shop.urls')),          # Демо-магазин
]

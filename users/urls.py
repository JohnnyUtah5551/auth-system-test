"""
Маршруты для работы с пользователями
"""
from django.urls import path
from . import views

urlpatterns = [
    # Регистрация и аутентификация
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Управление профилем
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/delete/', views.ProfileDeleteView.as_view(), name='profile-delete'),
    
    # Для админов - просмотр всех пользователей
    path('', views.UserListView.as_view(), name='user-list'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
]

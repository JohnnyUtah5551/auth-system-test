"""
Маршруты для управления правами доступа (только для админов)
"""
from django.urls import path
from . import views

urlpatterns = [
    # Управление ролями
    path('roles/', views.RoleListCreateView.as_view(), name='role-list'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role-detail'),
    
    # Управление ресурсами
    path('resources/', views.ResourceListCreateView.as_view(), name='resource-list'),
    path('resources/<int:pk>/', views.ResourceDetailView.as_view(), name='resource-detail'),
    
    # Управление правами
    path('permissions/', views.PermissionListCreateView.as_view(), name='permission-list'),
    path('permissions/<int:pk>/', views.PermissionDetailView.as_view(), name='permission-detail'),
    
    # Назначение ролей пользователям
    path('user-roles/', views.UserRoleListCreateView.as_view(), name='userrole-list'),
    path('user-roles/<int:pk>/', views.UserRoleDetailView.as_view(), name='userrole-detail'),
]

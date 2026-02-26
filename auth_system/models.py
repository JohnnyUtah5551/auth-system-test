from django.db import models
from users.models import User

class Role(models.Model):
    """Роли пользователей"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Resource(models.Model):
    """Ресурсы, к которым ограничиваем доступ"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Permission(models.Model):
    """Права доступа ролей к ресурсам"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    
    # Права на действия
    can_view = models.BooleanField(default=False)  # просмотр всех
    can_view_own = models.BooleanField(default=False)  # просмотр своих
    can_create = models.BooleanField(default=False)  # создание
    can_edit = models.BooleanField(default=False)  # редактирование всех
    can_edit_own = models.BooleanField(default=False)  # редактирование своих
    can_delete = models.BooleanField(default=False)  # удаление всех
    can_delete_own = models.BooleanField(default=False)  # удаление своих
    
    class Meta:
        unique_together = ['role', 'resource']

class UserRole(models.Model):
    """Назначение роли пользователю"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'role']

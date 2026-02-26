"""
Представления для управления системой прав доступа
Только для пользователей с ролью администратора
"""
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Role, Resource, Permission, UserRole
from users.models import User
from .decorators import require_permission  # Создадим этот декоратор позже

# Вспомогательная функция для проверки прав админа
def is_admin(user):
    if not user:
        return False
    return user.userrole_set.filter(role__name='admin').exists()

# Базовый класс для проверки админских прав
class AdminBaseView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user or not is_admin(request.user):
            return JsonResponse({'error': 'Forbidden. Admin access required.'}, status=403)
        return super().dispatch(request, *args, **kwargs)

# CRUD для ролей
class RoleListCreateView(AdminBaseView):
    def get(self, request):
        roles = Role.objects.all().values('id', 'name', 'description')
        return JsonResponse(list(roles), safe=False)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            role = Role.objects.create(
                name=data['name'],
                description=data.get('description', '')
            )
            return JsonResponse({'id': role.id, 'message': 'Role created'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class RoleDetailView(AdminBaseView):
    def get(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            return JsonResponse({
                'id': role.id,
                'name': role.name,
                'description': role.description
            })
        except Role.DoesNotExist:
            return JsonResponse({'error': 'Role not found'}, status=404)
    
    def put(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            data = json.loads(request.body)
            role.name = data.get('name', role.name)
            role.description = data.get('description', role.description)
            role.save()
            return JsonResponse({'message': 'Role updated'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def delete(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            role.delete()
            return JsonResponse({'message': 'Role deleted'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# CRUD для ресурсов
class ResourceListCreateView(AdminBaseView):
    def get(self, request):
        resources = Resource.objects.all().values('id', 'name', 'description')
        return JsonResponse(list(resources), safe=False)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            resource = Resource.objects.create(
                name=data['name'],
                description=data.get('description', '')
            )
            return JsonResponse({'id': resource.id, 'message': 'Resource created'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class ResourceDetailView(AdminBaseView):
    def get(self, request, pk):
        try:
            resource = Resource.objects.get(pk=pk)
            return JsonResponse({
                'id': resource.id,
                'name': resource.name,
                'description': resource.description
            })
        except Resource.DoesNotExist:
            return JsonResponse({'error': 'Resource not found'}, status=404)
    
    def put(self, request, pk):
        try:
            resource = Resource.objects.get(pk=pk)
            data = json.loads(request.body)
            resource.name = data.get('name', resource.name)
            resource.description = data.get('description', resource.description)
            resource.save()
            return JsonResponse({'message': 'Resource updated'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def delete(self, request, pk):
        try:
            resource = Resource.objects.get(pk=pk)
            resource.delete()
            return JsonResponse({'message': 'Resource deleted'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# CRUD для прав доступа
class PermissionListCreateView(AdminBaseView):
    def get(self, request):
        permissions = Permission.objects.all().select_related('role', 'resource')
        data = []
        for p in permissions:
            data.append({
                'id': p.id,
                'role_id': p.role_id,
                'role_name': p.role.name,
                'resource_id': p.resource_id,
                'resource_name': p.resource.name,
                'can_view': p.can_view,
                'can_view_own': p.can_view_own,
                'can_create': p.can_create,
                'can_edit': p.can_edit,
                'can_edit_own': p.can_edit_own,
                'can_delete': p.can_delete,
                'can_delete_own': p.can_delete_own
            })
        return JsonResponse(data, safe=False)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            permission = Permission.objects.create(
                role_id=data['role_id'],
                resource_id=data['resource_id'],
                can_view=data.get('can_view', False),
                can_view_own=data.get('can_view_own', False),
                can_create=data.get('can_create', False),
                can_edit=data.get('can_edit', False),
                can_edit_own=data.get('can_edit_own', False),
                can_delete=data.get('can_delete', False),
                can_delete_own=data.get('can_delete_own', False)
            )
            return JsonResponse({'id': permission.id, 'message': 'Permission created'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class PermissionDetailView(AdminBaseView):
    def get(self, request, pk):
        try:
            p = Permission.objects.select_related('role', 'resource').get(pk=pk)
            return JsonResponse({
                'id': p.id,
                'role_id': p.role_id,
                'role_name': p.role.name,
                'resource_id': p.resource_id,
                'resource_name': p.resource.name,
                'can_view': p.can_view,
                'can_view_own': p.can_view_own,
                'can_create': p.can_create,
                'can_edit': p.can_edit,
                'can_edit_own': p.can_edit_own,
                'can_delete': p.can_delete,
                'can_delete_own': p.can_delete_own
            })
        except Permission.DoesNotExist:
            return JsonResponse({'error': 'Permission not found'}, status=404)
    
    def put(self, request, pk):
        try:
            permission = Permission.objects.get(pk=pk)
            data = json.loads(request.body)
            
            for field in ['can_view', 'can_view_own', 'can_create', 'can_edit', 
                         'can_edit_own', 'can_delete', 'can_delete_own']:
                if field in data:
                    setattr(permission, field, data[field])
            
            permission.save()
            return JsonResponse({'message': 'Permission updated'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def delete(self, request, pk):
        try:
            permission = Permission.objects.get(pk=pk)
            permission.delete()
            return JsonResponse({'message': 'Permission deleted'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# Назначение ролей пользователям
class UserRoleListCreateView(AdminBaseView):
    def get(self, request):
        user_roles = UserRole.objects.all().select_related('user', 'role')
        data = []
        for ur in user_roles:
            data.append({
                'id': ur.id,
                'user_id': ur.user_id,
                'user_email': ur.user.email,
                'role_id': ur.role_id,
                'role_name': ur.role.name,
                'assigned_at': ur.assigned_at
            })
        return JsonResponse(data, safe=False)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_role = UserRole.objects.create(
                user_id=data['user_id'],
                role_id=data['role_id']
            )
            return JsonResponse({'id': user_role.id, 'message': 'Role assigned'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class UserRoleDetailView(AdminBaseView):
    def delete(self, request, pk):
        try:
            user_role = UserRole.objects.get(pk=pk)
            user_role.delete()
            return JsonResponse({'message': 'Role unassigned'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

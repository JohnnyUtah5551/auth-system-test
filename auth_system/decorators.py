"""
Декораторы для проверки прав доступа
Позволяют одной строкой проверить, есть ли у пользователя доступ к ресурсу
"""
from django.http import JsonResponse
from functools import wraps
from .models import Permission, Resource

def require_permission(resource_name, action, check_own=False):
    """
    Декоратор для проверки прав доступа
    
    Аргументы:
        resource_name (str): имя ресурса (например, 'products', 'users')
        action (str): действие ('view', 'create', 'edit', 'delete')
        check_own (bool): проверять ли право на свои объекты
    
    Примеры использования:
        @require_permission('products', 'view')
        def get(self, request):
            # только с правом на просмотр всех товаров
            
        @require_permission('products', 'edit', check_own=True)
        def put(self, request, pk):
            # с правом на редактирование своих товаров
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            # 1. Проверяем, есть ли пользователь
            if not request.user:
                return JsonResponse(
                    {'error': 'Unauthorized. Please login.'}, 
                    status=401
                )
            
            # 2. Проверяем, активен ли пользователь
            if not request.user.is_active:
                return JsonResponse(
                    {'error': 'Account is deactivated.'}, 
                    status=403
                )
            
            try:
                # 3. Получаем ресурс
                resource = Resource.objects.get(name=resource_name)
                
                # 4. Получаем все роли пользователя
                user_roles = request.user.userrole_set.all().values_list('role', flat=True)
                
                # 5. Ищем права для этих ролей на данный ресурс
                permissions = Permission.objects.filter(
                    role_id__in=user_roles,
                    resource=resource
                )
                
                if not permissions.exists():
                    return JsonResponse(
                        {'error': f'Forbidden. No access to {resource_name}.'}, 
                        status=403
                    )
                
                # 6. Проверяем нужное действие
                has_permission = False
                
                # Сопоставляем действия с полями в БД
                action_fields = {
                    'view': 'can_view',
                    'view_own': 'can_view_own',
                    'create': 'can_create',
                    'edit': 'can_edit',
                    'edit_own': 'can_edit_own',
                    'delete': 'can_delete',
                    'delete_own': 'can_delete_own'
                }
                
                if action not in action_fields:
                    return JsonResponse(
                        {'error': f'Unknown action: {action}'}, 
                        status=500
                    )
                
                field_name = action_fields[action]
                
                # Если нужно проверять "свои" объекты
                if check_own and action + '_own' in action_fields:
                    # Проверяем сначала право на свои объекты
                    own_field = action_fields[action + '_own']
                    for perm in permissions:
                        if getattr(perm, own_field, False):
                            has_permission = True
                            break
                    
                    # Если нет права на свои, проверяем право на все
                    if not has_permission:
                        for perm in permissions:
                            if getattr(perm, field_name, False):
                                has_permission = True
                                break
                else:
                    # Проверяем обычное право
                    for perm in permissions:
                        if getattr(perm, field_name, False):
                            has_permission = True
                            break
                
                if not has_permission:
                    action_words = {
                        'view': 'просматривать',
                        'create': 'создавать',
                        'edit': 'редактировать',
                        'delete': 'удалять'
                    }
                    word = action_words.get(action, action)
                    return JsonResponse(
                        {'error': f'Forbidden. You cannot {word} {resource_name}.'}, 
                        status=403
                    )
                
                # 7. Если нужно проверить владельца (для своих объектов)
                if check_own and 'pk' in kwargs:
                    # Передаем информацию о том, что нужно проверить владельца
                    request.check_ownership = True
                    request.resource_name = resource_name
                
                # Всё хорошо - выполняем view
                return view_func(view_instance, request, *args, **kwargs)
                
            except Resource.DoesNotExist:
                return JsonResponse(
                    {'error': f'Resource {resource_name} not found'}, 
                    status=500
                )
            except Exception as e:
                return JsonResponse(
                    {'error': str(e)}, 
                    status=500
                )
        
        return wrapper
    return decorator


def require_ownership(model_class, owner_field='owner_id'):
    """
    Декоратор для проверки, является ли пользователь владельцем объекта
    Используется вместе с require_permission(check_own=True)
    
    Аргументы:
        model_class: класс модели, которую проверяем
        owner_field: поле, содержащее id владельца
    
    Пример:
        @require_permission('products', 'edit', check_own=True)
        @require_ownership(Product)
        def put(self, request, pk):
            # только владелец может редактировать
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            # Проверяем, нужно ли вообще проверять владельца
            if not hasattr(request, 'check_ownership') or not request.check_ownership:
                return view_func(view_instance, request, *args, **kwargs)
            
            # Получаем id объекта из kwargs
            obj_id = kwargs.get('pk')
            if not obj_id:
                return JsonResponse(
                    {'error': 'Object ID not provided'}, 
                    status=400
                )
            
            try:
                # Ищем объект
                obj = model_class.objects.get(pk=obj_id)
                
                # Проверяем владельца
                owner_id = getattr(obj, owner_field)
                if owner_id != request.user.id:
                    # Проверяем, может быть у пользователя есть право на все объекты
                    from .models import Permission, Resource
                    
                    resource = Resource.objects.get(name=request.resource_name)
                    user_roles = request.user.userrole_set.all().values_list('role', flat=True)
                    
                    # Ищем право на все объекты
                    has_full_access = Permission.objects.filter(
                        role_id__in=user_roles,
                        resource=resource,
                        can_edit=True  # или нужное действие
                    ).exists()
                    
                    if not has_full_access:
                        return JsonResponse(
                            {'error': 'Forbidden. You can only access your own objects.'}, 
                            status=403
                        )
                
                return view_func(view_instance, request, *args, **kwargs)
                
            except model_class.DoesNotExist:
                return JsonResponse(
                    {'error': 'Object not found'}, 
                    status=404
                )
            except Exception as e:
                return JsonResponse(
                    {'error': str(e)}, 
                    status=500
                )
        
        return wrapper
    return decorator


# Упрощенные версии для частых случаев
def require_view(resource_name, check_own=False):
    """Упрощенный декоратор для проверки права на просмотр"""
    return require_permission(resource_name, 'view', check_own)

def require_create(resource_name):
    """Упрощенный декоратор для проверки права на создание"""
    return require_permission(resource_name, 'create')

def require_edit(resource_name, check_own=False):
    """Упрощенный декоратор для проверки права на редактирование"""
    return require_permission(resource_name, 'edit', check_own)

def require_delete(resource_name, check_own=False):
    """Упрощенный декоратор для проверки права на удаление"""
    return require_permission(resource_name, 'delete', check_own)

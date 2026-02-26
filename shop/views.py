"""
Демо-представления для магазина
Здесь мы показываем, как работает система прав доступа
"""
from django.http import JsonResponse
from django.views import View
from auth_system.decorators import require_view, require_create, require_edit, require_delete
from auth_system.models import Resource, Permission
import json

# Временное хранилище товаров (в реальном проекте была бы БД)
products = [
    {'id': 1, 'name': 'Телефон', 'price': 10000, 'owner_id': 1},
    {'id': 2, 'name': 'Ноутбук', 'price': 50000, 'owner_id': 2},
    {'id': 3, 'name': 'Наушники', 'price': 2000, 'owner_id': 1},
]

class ProductListView(View):
    """Получение списка товаров с проверкой прав на просмотр"""
    
    @require_view('products')  # Проверяем право на просмотр всех товаров
    def get(self, request):
        # Декоратор уже проверил:
        # 1. Пользователь авторизован
        # 2. У пользователя есть право can_view на ресурс 'products'
        
        # Проверяем, может пользователь видеть все товары или только свои
        user_roles = request.user.userrole_set.all().values_list('role', flat=True)
        resource = Resource.objects.get(name='products')
        
        # Ищем право на просмотр всех товаров
        can_view_all = Permission.objects.filter(
            role_id__in=user_roles,
            resource=resource,
            can_view=True
        ).exists()
        
        if can_view_all:
            # Может видеть все товары
            return JsonResponse(products, safe=False)
        else:
            # Может видеть только свои товары
            user_products = [p for p in products if p['owner_id'] == request.user.id]
            return JsonResponse(user_products, safe=False)


class ProductDetailView(View):
    """Получение конкретного товара с проверкой прав"""
    
    @require_view('products', check_own=True)  # Проверяем право на просмотр (своих или всех)
    def get(self, request, pk):
        # Декоратор проверил, что есть право на просмотр (либо всех, либо своих)
        
        # Ищем товар по id
        product = next((p for p in products if p['id'] == pk), None)
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        # Проверяем, может ли пользователь смотреть этот конкретный товар
        user_roles = request.user.userrole_set.all().values_list('role', flat=True)
        resource = Resource.objects.get(name='products')
        
        # Проверяем права
        can_view_all = Permission.objects.filter(
            role_id__in=user_roles,
            resource=resource,
            can_view=True
        ).exists()
        
        can_view_own = Permission.objects.filter(
            role_id__in=user_roles,
            resource=resource,
            can_view_own=True
        ).exists()
        
        # Если может видеть все - возвращаем
        if can_view_all:
            return JsonResponse(product)
        
        # Если может видеть только свои - проверяем владельца
        if can_view_own and product['owner_id'] == request.user.id:
            return JsonResponse(product)
        
        # Если ни одно условие не подходит
        return JsonResponse(
            {'error': 'Forbidden. You cannot view this product.'}, 
            status=403
        )


class ProductCreateView(View):
    """Создание нового товара"""
    
    @require_create('products')  # Проверяем право на создание товаров
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Проверяем обязательные поля
            if 'name' not in data or 'price' not in data:
                return JsonResponse(
                    {'error': 'Fields name and price are required'}, 
                    status=400
                )
            
            new_product = {
                'id': len(products) + 1,
                'name': data['name'],
                'price': data['price'],
                'owner_id': request.user.id  # Владелец - текущий пользователь
            }
            products.append(new_product)
            
            return JsonResponse({
                'message': 'Product created successfully',
                'product': new_product
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class ProductUpdateView(View):
    """Обновление товара с проверкой прав"""
    
    @require_edit('products', check_own=True)  # Проверяем право на редактирование
    def put(self, request, pk):
        # Декоратор проверил, что есть право на редактирование
        
        # Ищем товар
        product = next((p for p in products if p['id'] == pk), None)
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        # Проверяем, может ли пользователь редактировать этот конкретный товар
        user_roles = request.user.userrole_set.all().values_list('role', flat=True)
        resource = Resource.objects.get(name='products')
        
        # Проверяем права
        can_edit_all = Permission.objects.filter(
            role_id__in=user_roles,
            resource=resource,
            can_edit=True
        ).exists()
        
        can_edit_own = Permission.objects.filter(
            role_id__in=user_roles,
            resource=resource,
            can_edit_own=True
        ).exists()
        
        # Если может редактировать все - разрешаем
        if can_edit_all:
            pass  # Разрешаем
            
        # Если может редактировать только свои - проверяем владельца
        elif can_edit_own and product['owner_id'] == request.user.id:
            pass  # Разрешаем
            
        else:
            return JsonResponse(
                {'error': 'Forbidden. You cannot edit this product.'}, 
                status=403
            )
        
        try:
            data = json.loads(request.body)
            
            # Обновляем поля
            if 'name' in data:
                product['name'] = data['name']
            if 'price' in data:
                product['price'] = data['price']
            
            return JsonResponse({
                'message': 'Product updated successfully',
                'product': product
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class ProductDeleteView(View):
    """Удаление товара с проверкой прав"""
    
    @require_delete('products', check_own=True)  # Проверяем право на удаление
    def delete(self, request, pk):
        global products
        
        # Ищем товар
        product = next((p for p in products if p['id'] == pk), None)
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        # Проверяем, может ли пользователь удалить этот товар
        user_roles = request.user.userrole_set.all().values_list('role', flat=True)
        resource = Resource.objects.get(name='products')
        
        # Проверяем права
        can_delete_all = Permission.objects.filter(
            role_id__in=user_roles,
            resource=resource,
            can_delete=True
        ).exists()
        
        can_delete_own = Permission.objects.filter(
            role_id__in=user_roles,
            resource=resource,
            can_delete_own=True
        ).exists()
        
        # Если может удалять все - разрешаем
        if can_delete_all:
            pass  # Разрешаем
            
        # Если может удалять только свои - проверяем владельца
        elif can_delete_own and product['owner_id'] == request.user.id:
            pass  # Разрешаем
            
        else:
            return JsonResponse(
                {'error': 'Forbidden. You cannot delete this product.'}, 
                status=403
            )
        
        # Удаляем товар
        products = [p for p in products if p['id'] != pk]
        
        return JsonResponse({
            'message': 'Product deleted successfully'
        })

"""
Демо-представления для магазина
Здесь мы показываем, как работает система прав доступа
"""
from django.http import JsonResponse
from django.views import View
import json

# Временное хранилище товаров (в реальном проекте была бы БД)
products = [
    {'id': 1, 'name': 'Телефон', 'price': 10000, 'owner_id': 1},
    {'id': 2, 'name': 'Ноутбук', 'price': 50000, 'owner_id': 2},
    {'id': 3, 'name': 'Наушники', 'price': 2000, 'owner_id': 1},
]

class ProductListView(View):
    """Получение списка товаров (проверка прав на просмотр)"""
    def get(self, request):
        # Проверяем, залогинен ли пользователь
        if not request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        # Здесь должна быть проверка прав через систему авторизации
        # Пока просто возвращаем все товары для демонстрации
        return JsonResponse(products, safe=False)

class ProductDetailView(View):
    """Получение конкретного товара"""
    def get(self, request, pk):
        if not request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        # Ищем товар по id
        product = next((p for p in products if p['id'] == pk), None)
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        # Проверяем права доступа (упрощенно)
        # В реальном проекте здесь был бы вызов системы проверки прав
        return JsonResponse(product)

class ProductCreateView(View):
    """Создание нового товара"""
    def post(self, request):
        if not request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        try:
            data = json.loads(request.body)
            new_product = {
                'id': len(products) + 1,
                'name': data['name'],
                'price': data['price'],
                'owner_id': request.user.id  # Владелец - текущий пользователь
            }
            products.append(new_product)
            return JsonResponse(new_product, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class ProductUpdateView(View):
    """Обновление товара"""
    def put(self, request, pk):
        if not request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        product = next((p for p in products if p['id'] == pk), None)
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        # Проверяем, может ли пользователь редактировать этот товар
        # Упрощенно: только владелец или админ
        if product['owner_id'] != request.user.id and not request.user.userrole_set.filter(role__name='admin').exists():
            return JsonResponse({'error': 'Forbidden. You can only edit your own products.'}, status=403)
        
        try:
            data = json.loads(request.body)
            product['name'] = data.get('name', product['name'])
            product['price'] = data.get('price', product['price'])
            return JsonResponse(product)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class ProductDeleteView(View):
    """Удаление товара"""
    def delete(self, request, pk):
        if not request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        global products
        product = next((p for p in products if p['id'] == pk), None)
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        # Проверка прав (упрощенно)
        if product['owner_id'] != request.user.id and not request.user.userrole_set.filter(role__name='admin').exists():
            return JsonResponse({'error': 'Forbidden. You can only delete your own products.'}, status=403)
        
        products = [p for p in products if p['id'] != pk]
        return JsonResponse({'message': 'Product deleted'})

"""
Представления для работы с пользователями
Регистрация, вход, выход, управление профилем
"""
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password  # Используем для сравнения паролей
import json
from .models import User, Session
from datetime import datetime, timedelta
import secrets

# Вспомогательная функция для проверки админа
def is_admin(user):
    """Проверяет, является ли пользователь администратором"""
    if not user:
        return False
    # Проверяем через систему ролей (из auth_system)
    try:
        from auth_system.models import UserRole
        return UserRole.objects.filter(user=user, role__name='admin').exists()
    except:
        # Если модуль еще не создан или нет ролей, возвращаем False
        return False

# Регистрация нового пользователя
@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    """Регистрация нового пользователя"""
    
    def post(self, request):
        try:
            # Получаем данные из запроса
            data = json.loads(request.body)
            
            # Проверяем обязательные поля
            required_fields = ['email', 'first_name', 'last_name', 'password', 'password2']
            for field in required_fields:
                if field not in data:
                    return JsonResponse(
                        {'error': f'Поле {field} обязательно'}, 
                        status=400
                    )
            
            # Проверяем совпадение паролей
            if data['password'] != data['password2']:
                return JsonResponse(
                    {'error': 'Пароли не совпадают'}, 
                    status=400
                )
            
            # Проверяем, не занят ли email
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse(
                    {'error': 'Пользователь с таким email уже существует'}, 
                    status=400
                )
            
            # Создаем пользователя
            user = User(
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                patronymic=data.get('patronymic', '')  # Необязательное поле
            )
            user.set_password(data['password'])
            user.save()
            
            # Автоматически назначаем роль "user" новому пользователю
            try:
                from auth_system.models import Role, UserRole
                user_role = Role.objects.get(name='user')
                UserRole.objects.create(user=user, role=user_role)
            except:
                # Если система ролей еще не настроена, просто продолжаем
                pass
            
            # Генерируем токен для автоматического входа после регистрации
            token = user.generate_token()
            
            return JsonResponse({
                'message': 'Пользователь успешно зарегистрирован',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                },
                'token': token  # Отправляем токен, чтобы не логиниться отдельно
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Неверный формат JSON'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)}, 
                status=500
            )

# Вход в систему
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    """Вход пользователя в систему"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Проверяем наличие email и пароля
            if 'email' not in data or 'password' not in data:
                return JsonResponse(
                    {'error': 'Необходимо указать email и пароль'}, 
                    status=400
                )
            
            # Ищем пользователя
            try:
                user = User.objects.get(email=data['email'])
            except User.DoesNotExist:
                return JsonResponse(
                    {'error': 'Неверный email или пароль'}, 
                    status=401
                )
            
            # Проверяем активность аккаунта
            if not user.is_active:
                return JsonResponse(
                    {'error': 'Аккаунт деактивирован'}, 
                    status=401
                )
            
            # Проверяем пароль
            if not user.check_password(data['password']):
                return JsonResponse(
                    {'error': 'Неверный email или пароль'}, 
                    status=401
                )
            
            # Генерируем токен
            token = user.generate_token()
            
            # Создаем сессию (если используем сессии)
            # Можно использовать и токены, и сессии параллельно
            session_key = secrets.token_urlsafe(32)
            Session.objects.create(
                user=user,
                session_key=session_key,
                expires_at=datetime.now() + timedelta(days=1)
            )
            
            # Формируем ответ
            response = JsonResponse({
                'message': 'Вход выполнен успешно',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                },
                'token': token
            })
            
            # Устанавливаем cookie с сессией (если используем сессии)
            response.set_cookie(
                'sessionid',
                session_key,
                max_age=86400,  # 1 день в секундах
                httponly=True,  # Защита от XSS
                samesite='Lax'
            )
            
            return response
            
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Неверный формат JSON'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)}, 
                status=500
            )

# Выход из системы
class LogoutView(View):
    """Выход пользователя из системы"""
    
    def post(self, request):
        if not request.user:
            return JsonResponse(
                {'error': 'Вы не авторизованы'}, 
                status=401
            )
        
        # Удаляем сессию, если она есть
        session_key = request.COOKIES.get('sessionid')
        if session_key:
            Session.objects.filter(session_key=session_key).delete()
        
        response = JsonResponse({'message': 'Выход выполнен успешно'})
        response.delete_cookie('sessionid')
        
        return response

# Просмотр профиля
class ProfileView(View):
    """Получение информации о текущем пользователе"""
    
    def get(self, request):
        if not request.user:
            return JsonResponse(
                {'error': 'Не авторизован'}, 
                status=401
            )
        
        user = request.user
        
        # Получаем роли пользователя
        roles = []
        try:
            from auth_system.models import UserRole
            user_roles = UserRole.objects.filter(user=user).select_related('role')
            roles = [ur.role.name for ur in user_roles]
        except:
            pass
        
        return JsonResponse({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'patronymic': user.patronymic,
            'is_active': user.is_active,
            'roles': roles,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        })

# Обновление профиля
@method_decorator(csrf_exempt, name='dispatch')
class ProfileUpdateView(View):
    """Обновление информации о пользователе"""
    
    def put(self, request):
        if not request.user:
            return JsonResponse(
                {'error': 'Не авторизован'}, 
                status=401
            )
        
        try:
            data = json.loads(request.body)
            user = request.user
            
            # Обновляем поля, которые можно менять
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'patronymic' in data:
                user.patronymic = data['patronymic']
            
            # Если меняем пароль
            if 'password' in data and 'old_password' in data:
                if not user.check_password(data['old_password']):
                    return JsonResponse(
                        {'error': 'Неверный текущий пароль'}, 
                        status=400
                    )
                user.set_password(data['password'])
            
            user.save()
            
            return JsonResponse({
                'message': 'Профиль обновлен',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'patronymic': user.patronymic
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Неверный формат JSON'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)}, 
                status=500
            )

# Мягкое удаление аккаунта
@method_decorator(csrf_exempt, name='dispatch')
class ProfileDeleteView(View):
    """Мягкое удаление аккаунта (is_active=False)"""
    
    def delete(self, request):
        if not request.user:
            return JsonResponse(
                {'error': 'Не авторизован'}, 
                status=401
            )
        
        user = request.user
        
        # Мягкое удаление - просто деактивируем
        user.is_active = False
        user.save()
        
        # Удаляем все сессии пользователя
        Session.objects.filter(user=user).delete()
        
        response = JsonResponse({
            'message': 'Аккаунт деактивирован. Вы можете восстановить его, обратившись к администратору.'
        })
        response.delete_cookie('sessionid')
        
        return response

# Для админов: список всех пользователей
class UserListView(View):
    """Получение списка всех пользователей (только для админов)"""
    
    def get(self, request):
        if not request.user:
            return JsonResponse(
                {'error': 'Не авторизован'}, 
                status=401
            )
        
        # Проверяем, является ли пользователь админом
        if not is_admin(request.user):
            return JsonResponse(
                {'error': 'Доступ запрещен. Требуются права администратора.'}, 
                status=403
            )
        
        users = User.objects.all().values(
            'id', 'email', 'first_name', 'last_name', 
            'patronymic', 'is_active', 'created_at'
        )
        
        return JsonResponse(list(users), safe=False)

# Для админов: детальная информация о пользователе
class UserDetailView(View):
    """Получение информации о конкретном пользователе (только для админов)"""
    
    def get(self, request, pk):
        if not request.user:
            return JsonResponse(
                {'error': 'Не авторизован'}, 
                status=401
            )
        
        # Проверяем, является ли пользователь админом
        if not is_admin(request.user):
            return JsonResponse(
                {'error': 'Доступ запрещен. Требуются права администратора.'}, 
                status=403
            )
        
        try:
            user = User.objects.get(pk=pk)
            
            # Получаем роли пользователя
            roles = []
            try:
                from auth_system.models import UserRole
                user_roles = UserRole.objects.filter(user=user).select_related('role')
                roles = [{'id': ur.role.id, 'name': ur.role.name} for ur in user_roles]
            except:
                pass
            
            return JsonResponse({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'patronymic': user.patronymic,
                'is_active': user.is_active,
                'roles': roles,
                'created_at': user.created_at,
                'updated_at': user.updated_at
            })
        except User.DoesNotExist:
            return JsonResponse(
                {'error': 'Пользователь не найден'}, 
                status=404
            )

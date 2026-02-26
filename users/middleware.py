from django.utils.deprecation import MiddlewareMixin
from .models import User

class CustomAuthMiddleware(MiddlewareMixin):
    """Middleware для определения пользователя по токену"""
    
    def process_request(self, request):
        request.user = None
        
        # Ищем токен в заголовке Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Убираем 'Bearer '
            request.user = User.verify_token(token)
        
        # Если не нашли пользователя, но хотим использовать сессии
        # Можно добавить проверку cookie с sessionid

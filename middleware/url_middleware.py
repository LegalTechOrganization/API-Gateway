from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json
from typing import Any, Dict, List
from utils.url_builder import get_gateway_base_url, replace_auth_urls_in_response


class URLMiddleware(BaseHTTPMiddleware):
    """
    Middleware для замены URL auth сервиса на URL API Gateway в ответах
    """
    
    def __init__(self, app, include_paths: List[str] = None):
        super().__init__(app)
        # Пути, которые нужно обрабатывать (по умолчанию все)
        self.include_paths = include_paths or []
    
    async def dispatch(self, request: Request, call_next):
        # Проверяем, нужно ли обрабатывать этот путь
        if self.include_paths and not any(request.url.path.startswith(path) for path in self.include_paths):
            response = await call_next(request)
            return response
        
        # Получаем базовый URL API Gateway из запроса
        gateway_base_url = get_gateway_base_url(request)
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Обрабатываем ответ только если это JSON
        if isinstance(response, JSONResponse):
            try:
                # Получаем тело ответа
                body = response.body.decode('utf-8')
                data = json.loads(body)
                
                # Заменяем URL auth сервиса на URL API Gateway
                transformed_data = replace_auth_urls_in_response(data, gateway_base_url)
                
                # Создаем новый ответ с преобразованными данными
                return JSONResponse(
                    content=transformed_data,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Если не удалось декодировать JSON, возвращаем исходный ответ
                return response
        
        # Также обрабатываем обычные Response объекты
        elif hasattr(response, 'body') and response.body:
            try:
                # Пытаемся декодировать как JSON
                body = response.body.decode('utf-8')
                data = json.loads(body)
                
                # Заменяем URL auth сервиса на URL API Gateway
                transformed_data = replace_auth_urls_in_response(data, gateway_base_url)
                
                # Создаем новый ответ
                return Response(
                    content=json.dumps(transformed_data, ensure_ascii=False),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json"
                )
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                # Если не JSON или нет body, возвращаем исходный ответ
                return response
        
        return response

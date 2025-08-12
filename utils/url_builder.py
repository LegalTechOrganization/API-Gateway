from fastapi import Request
from typing import Optional


def get_gateway_base_url(request: Request) -> str:
    """
    Получает базовый URL API Gateway из входящего запроса
    
    Args:
        request: FastAPI Request объект
        
    Returns:
        Базовый URL API Gateway (например: http://localhost:8002)
    """
    scheme = request.url.scheme
    host = request.url.hostname
    port = request.url.port
    
    if port and port not in [80, 443]:
        return f"{scheme}://{host}:{port}"
    else:
        return f"{scheme}://{host}"


def replace_auth_urls_in_response(data: any, gateway_base_url: str) -> any:
    """
    Заменяет URL auth сервиса на URL API Gateway в ответе
    
    Args:
        data: Данные ответа (dict, list, str, etc.)
        gateway_base_url: Базовый URL API Gateway
        
    Returns:
        Данные с замененными URL
    """
    if isinstance(data, dict):
        return {key: replace_auth_urls_in_response(value, gateway_base_url) for key, value in data.items()}
    elif isinstance(data, list):
        return [replace_auth_urls_in_response(item, gateway_base_url) for item in data]
    elif isinstance(data, str):
        # Заменяем URL auth сервиса на URL API Gateway
        auth_urls = [
            "http://host.docker.internal:8000",
            "http://localhost:8000",
            "https://host.docker.internal:8000",
            "https://localhost:8000"
        ]
        
        for auth_url in auth_urls:
            if data.startswith(auth_url):
                return data.replace(auth_url, gateway_base_url)
        
        return data
    else:
        return data

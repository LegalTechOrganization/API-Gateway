from fastapi import Response
from typing import Optional


def set_auth_cookies(
    response: Response, 
    access_token: str, 
    refresh_token: str, 
    expires_in: int = 300
):
    """
    Устанавливает HTTP-Only cookies для токенов
    
    Args:
        response: FastAPI Response объект
        access_token: JWT access token
        refresh_token: Refresh token
        expires_in: Время жизни access token в секундах
    """
    # Access token cookie - короткое время жизни
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=expires_in,
        httponly=True,
        secure=False,  # False для разработки (HTTP), True для продакшена (HTTPS)
        samesite="lax",  # lax для разработки, strict для продакшена
        path="/"
    )
    
    # Refresh token cookie - длительное время жизни (7 дней)
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        max_age=7 * 24 * 60 * 60,  # 7 дней в секундах
        httponly=True,
        secure=False,  # False для разработки (HTTP), True для продакшена (HTTPS)
        samesite="lax",  # lax для разработки, strict для продакшена
        path="/v1/client/refresh_token"
    )


def clear_auth_cookies(response: Response):
    """
    Очищает cookies аутентификации
    
    Args:
        response: FastAPI Response объект
    """
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/v1/client/refresh_token")


def get_token_from_request(request) -> Optional[str]:
    """
    Извлекает токен из заголовка Authorization или из cookie
    
    Args:
        request: FastAPI Request объект
        
    Returns:
        Токен или None если не найден
    """
    # Сначала пробуем из заголовка Authorization
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    # Если нет в заголовке, пробуем из cookie
    access_token = request.cookies.get("access_token")
    if access_token:
        return access_token
    
    return None


def get_refresh_token_from_request(request) -> Optional[str]:
    """
    Извлекает refresh token из тела запроса или из cookie
    
    Args:
        request: FastAPI Request объект
        
    Returns:
        Refresh token или None если не найден
    """
    # Пытаемся получить из cookie
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        return refresh_token
    
    return None

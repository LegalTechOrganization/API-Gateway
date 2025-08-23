from fastapi import HTTPException, Request, Header, status
from typing import Dict, Any, Optional
from utils.cookie_utils import get_token_from_request
from services.auth_client import auth_client


async def get_token_from_auth_header_or_cookie(request: Request, authorization: str = Header(None)) -> str:
    """
    Извлекает токен из заголовка Authorization или из cookie
    
    Args:
        request: FastAPI Request объект
        authorization: Заголовок Authorization
        
    Returns:
        Токен
        
    Raises:
        HTTPException: Если токен не найден
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    else:
        token = get_token_from_request(request)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header or cookie"
        )
    
    return token


async def get_user_context_from_token(token: str) -> Dict[str, Any]:
    """
    Получает полный контекст пользователя из токена через Auth Service
    
    Args:
        token: JWT токен пользователя
        
    Returns:
        Словарь с контекстом пользователя
        
    Raises:
        HTTPException: Если токен невалидный или ошибка auth service
    """
    try:
        # Сначала валидируем токен
        validation_result = await auth_client.validate_token(token)
        if not validation_result.get("valid", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Получаем информацию о пользователе
        user_info = await auth_client.get_user_info(token)
        
        # Получаем организации пользователя (если есть user_id)
        user_id = user_info.get("user_id") or user_info.get("id")
        org_roles = []
        
        if user_id:
            try:
                # Получаем организации через внутренний API
                # Используем тот же токен для авторизации
                orgs_response = await auth_client._make_request(
                    "GET", 
                    f"/auth/user/{user_id}/orgs",
                    headers={"Authorization": f"Bearer {token}"}
                )
                org_roles = orgs_response if isinstance(orgs_response, list) else []
            except Exception:
                # Если не удалось получить организации, используем пустой список
                org_roles = []
        
        # Определяем активную организацию и роль
        active_org_id = user_info.get("active_org_id")
        org_role = "user"  # default role
        is_org_owner = False
        
        if active_org_id and org_roles:
            # Находим роль в активной организации
            for org in org_roles:
                if org.get("org_id") == active_org_id:
                    org_role = org.get("role", "user")
                    is_org_owner = org.get("is_owner", False)
                    break
        
        # Формируем контекст пользователя
        user_context = {
            "user_id": user_id,
            "email": user_info.get("email"),
            "full_name": user_info.get("full_name"),
            "active_org_id": active_org_id,
            "org_role": org_role,
            "is_org_owner": is_org_owner,
            "org_roles": org_roles
        }
        
        return user_context
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user context: {str(e)}"
        )


async def validate_user_token(request: Request, authorization: str = Header(None)) -> str:
    """
    Валидация и извлечение токена пользователя для chat/tarrification сервисов
    
    Args:
        request: FastAPI Request объект
        authorization: Заголовок Authorization
        
    Returns:
        Валидный токен
        
    Raises:
        HTTPException: Если токен невалидный
    """
    try:
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        
        # Валидируем токен через auth service
        validation_result = await auth_client.validate_token(token)
        if not validation_result.get("valid", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
            
        return token
        
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for service access"
        )

import base64
import json
from typing import Dict, Any, Optional


def decode_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    Декодирует JWT токен без проверки подписи (только для извлечения payload)
    
    Args:
        token: JWT токен
        
    Returns:
        Payload токена или None если не удалось декодировать
    """
    try:
        # Разделяем токен на части
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Декодируем payload (вторая часть)
        payload = parts[1]
        # Добавляем padding если нужно
        payload += '=' * (4 - len(payload) % 4)
        
        # Декодируем base64
        decoded = base64.urlsafe_b64decode(payload)
        
        # Парсим JSON
        return json.loads(decoded.decode('utf-8'))
    except Exception:
        return None


def extract_user_info_from_token(token: str) -> Dict[str, Any]:
    """
    Извлекает информацию о пользователе из JWT токена
    
    Args:
        token: JWT токен
        
    Returns:
        Словарь с информацией о пользователе
    """
    payload = decode_jwt_payload(token)
    
    if not payload:
        return {
            "user_id": "unknown",
            "email": "unknown@example.com",
            "full_name": None
        }
    
    # Извлекаем информацию из payload
    user_info = {
        "user_id": payload.get("sub", "unknown"),
        "email": payload.get("email", "unknown@example.com"),
        "full_name": payload.get("name") or payload.get("preferred_username")
    }
    
    return user_info


def transform_auth_response(auth_result: Dict[str, Any], email: str = None) -> Dict[str, Any]:
    """
    Преобразует ответ от auth сервиса в формат API Gateway
    
    Args:
        auth_result: Ответ от auth сервиса
        email: Email пользователя (если не указан, будет извлечен из токена)
        
    Returns:
        Преобразованный ответ в формате API Gateway
    """
    access_token = auth_result.get("access_token")
    
    # Извлекаем информацию о пользователе из токена
    user_info = extract_user_info_from_token(access_token) if access_token else {
        "user_id": "unknown",
        "email": email or "unknown@example.com",
        "full_name": None
    }
    
    # Если email не был извлечен из токена, используем переданный
    if not user_info.get("email") or user_info["email"] == "unknown@example.com":
        user_info["email"] = email or "unknown@example.com"
    
    result = {
        "jwt": access_token,
        "refresh_token": auth_result.get("refresh_token"),
        "user": {
            "user_id": user_info["user_id"],
            "email": user_info["email"],
            "full_name": user_info["full_name"],
            "orgs": []
        }
    }
    
    return result


def transform_user_response(auth_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Преобразует ответ от auth сервиса для эндпоинтов пользователя
    
    Args:
        auth_result: Ответ от auth сервиса
        
    Returns:
        Преобразованный ответ в формате API Gateway
    """
    # Auth сервис возвращает 'sub', а мы ожидаем 'user_id'
    if 'sub' in auth_result and 'user_id' not in auth_result:
        auth_result['user_id'] = auth_result.pop('sub')
    
    # Убеждаемся, что все обязательные поля присутствуют
    result = {
        "user_id": auth_result.get("user_id", "unknown"),
        "email": auth_result.get("email", "unknown@example.com"),
        "full_name": auth_result.get("full_name"),
        "orgs": auth_result.get("orgs", [])
    }
    
    return result


def transform_org_response(auth_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Преобразует ответ от auth сервиса для эндпоинтов организаций
    
    Args:
        auth_result: Ответ от auth сервиса
        
    Returns:
        Преобразованный ответ в формате API Gateway
    """
    # Убеждаемся, что все обязательные поля присутствуют
    result = {
        "org_id": auth_result.get("org_id", "unknown"),
        "name": auth_result.get("name", "Unknown Organization")
    }
    
    return result


def transform_switch_org_response(auth_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Преобразует ответ от auth сервиса для переключения организации
    
    Args:
        auth_result: Ответ от auth сервиса
        
    Returns:
        Преобразованный ответ в формате API Gateway
    """
    result = {
        "active_org_id": auth_result.get("active_org_id", "unknown")
    }
    
    return result


def transform_generic_response(auth_result: Any, response_type: str = "generic") -> Any:
    """
    Универсальная функция для преобразования ответов от auth сервиса
    
    Args:
        auth_result: Ответ от auth сервиса
        response_type: Тип ответа для специальной обработки
        
    Returns:
        Преобразованный ответ
    """
    if isinstance(auth_result, dict):
        # Преобразуем 'sub' в 'user_id' если это ответ пользователя
        if 'sub' in auth_result and 'user_id' not in auth_result:
            auth_result['user_id'] = auth_result.pop('sub')
        
        # Для списков пользователей/участников
        if response_type == "user_list" and isinstance(auth_result, list):
            return [transform_user_response(user) for user in auth_result]
        
        # Для ответов пользователя
        if response_type == "user":
            return transform_user_response(auth_result)
        
        # Для ответов организации
        if response_type == "org":
            return transform_org_response(auth_result)
        
        # Для ответов переключения организации
        if response_type == "switch_org":
            return transform_switch_org_response(auth_result)
    
    return auth_result

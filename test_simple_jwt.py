#!/usr/bin/env python3
"""
Простой тест JWT утилиты без внешних зависимостей
"""

import base64
import json

def decode_jwt_payload(token: str):
    """Декодирует JWT токен без проверки подписи"""
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
    except Exception as e:
        print(f"Ошибка декодирования: {e}")
        return None

def test_jwt_decoding():
    """Тестирует декодирование JWT"""
    
    # Тестовый JWT токен (из вашего примера)
    test_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIyMWxycmhaUFNVcXc3d0xjNGFoMmVfeUhGcXQ2NF95ZDdoZHpCZURTV1dVIn0.eyJleHAiOjE3NTQ5ODMwMDksImlhdCI6MTc1NDk4MjcwOSwianRpIjoib25ydHJvOjQ5ZmZlNWYwLTIwMDItZmExMS01ZWRkLWNjNzg5NGMzMGI4OSIsImlzcyI6Imh0dHA6Ly9rZXljbG9hazo4MDgwL3JlYWxtcy9hdXRoLXNlcnZpY2UiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiMzgyOWU5M2UtZjEzNC00YTZmLTg1MjUtYzhlMmQyYjBhYWQxIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiYXV0aC1zZXJ2aWNlIiwic2lkIjoiM2E4Njc1MTQtZWQ3Yy00MWVkLWI3MzYtNTNiMDI2MjExOGE1IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjgwMDAiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImRlZmF1bHQtcm9sZXMtYXV0aC1zZXJ2aWNlIiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoicHJvZmlsZSBlbWFpbCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiSHV1c2VyIEFjY291bnQiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJodXVzZXJAZXhhbXBsZS5jb20iLCJnaXZlbl9uYW1lIjoiSHV1c2VyIiwiZmFtaWx5X25hbWUiOiJBY2NvdW50IiwiZW1haWwiOiJodXVzZXJAZXhhbXBsZS5jb20ifQ.aLFZJuRrzqMjzLR0sLEylXF8oyXBchJLNWktDKW5IuuX65c9EiUrK25gyZ4sgJgv_FtqMlft-tkWEXzVbt4AeZUED4ZbOflTedwQ_F-raFELO8XAiJ0-WGQuvQUnNkCRAc597T-BSs2qx_DuGuKm6eRXVd60_taxJQsmyv0zxX5QHhixWCW5CrS_jUISrog03PZyTZtGlzsdOHOqUFEF7aXDS54O6oyzK4UHccu8-vzcbttSbUBy_J0bKQRnhwlPJhJ_7-Uufx0gwfA3FvNudjgufJIs0bZVp8I2xOb6ReVtcF-TOYteaLMcyyXps2e7WKcnhAwzqzva1i_vGRFeoA"
    
    print("🧪 Тестируем декодирование JWT без внешних зависимостей...")
    
    # Декодируем payload
    payload = decode_jwt_payload(test_token)
    
    if payload:
        print("✅ JWT payload успешно декодирован!")
        print(f"   sub: {payload.get('sub')}")
        print(f"   email: {payload.get('email')}")
        print(f"   name: {payload.get('name')}")
        print(f"   preferred_username: {payload.get('preferred_username')}")
        
        # Тестируем извлечение информации о пользователе
        user_info = {
            "user_id": payload.get("sub", "unknown"),
            "email": payload.get("email", "unknown@example.com"),
            "full_name": payload.get("name") or payload.get("preferred_username")
        }
        
        print("\n📋 Информация о пользователе:")
        print(f"   user_id: {user_info['user_id']}")
        print(f"   email: {user_info['email']}")
        print(f"   full_name: {user_info['full_name']}")
        
        # Тестируем преобразование ответа auth сервиса
        auth_response = {
            "access_token": test_token,
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "expires_in": 300
        }
        
        result = {
            "jwt": auth_response.get("access_token"),
            "refresh_token": auth_response.get("refresh_token"),
            "user": {
                "user_id": user_info["user_id"],
                "email": user_info["email"],
                "full_name": user_info["full_name"],
                "orgs": []
            }
        }
        
        print("\n🔄 Преобразованный ответ:")
        print(f"   jwt: {result['jwt'][:50]}...")
        print(f"   refresh_token: {result['refresh_token']}")
        print(f"   user.user_id: {result['user']['user_id']}")
        print(f"   user.email: {result['user']['email']}")
        print(f"   user.full_name: {result['user']['full_name']}")
        
    else:
        print("❌ Не удалось декодировать JWT payload")
    
    print("\n🎉 Тест завершен!")

if __name__ == "__main__":
    test_jwt_decoding()

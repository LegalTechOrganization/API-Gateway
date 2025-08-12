#!/usr/bin/env python3
"""
Тест для проверки валидации токена
"""

import httpx
import asyncio

async def test_token_validation():
    """Тестирует валидацию токена"""
    
    base_url = "http://localhost:8002"
    
    print("🧪 Тестируем валидацию токена...")
    
    # Тест 1: Валидация токена через /v1/client/validate
    print("\n1. Тестируем /v1/client/validate:")
    try:
        async with httpx.AsyncClient() as client:
            # Тестируем с невалидным токеном
            response = await client.get(f"{base_url}/v1/client/validate?token=invalid_token")
            print(f"   Невалидный токен: {response.status_code} - {response.text}")
            
            # Тестируем без токена
            response = await client.get(f"{base_url}/v1/client/validate")
            print(f"   Без токена: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 2: Получение профиля через /v1/client/me (автоматическая валидация)
    print("\n2. Тестируем /v1/client/me (автоматическая валидация):")
    try:
        async with httpx.AsyncClient() as client:
            # Тестируем без токена
            response = await client.get(f"{base_url}/v1/client/me")
            print(f"   Без токена: {response.status_code} - {response.text}")
            
            # Тестируем с невалидным токеном
            headers = {"Authorization": "Bearer invalid_token"}
            response = await client.get(f"{base_url}/v1/client/me", headers=headers)
            print(f"   Невалидный токен: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n🎉 Тест валидации токена завершен!")

if __name__ == "__main__":
    asyncio.run(test_token_validation())

#!/usr/bin/env python3
"""
Тест для проверки работы HTTP-Only cookies в API Gateway
"""

import httpx
import asyncio
import json

async def test_cookies():
    """Тестирует работу cookies в API Gateway"""
    
    base_url = "http://localhost:8002"
    
    print("🧪 Тестируем работу HTTP-Only cookies в API Gateway...")
    
    async with httpx.AsyncClient() as client:
        # Тест 1: Регистрация пользователя
        print("\n1. Тестируем sign-up с cookies:")
        signup_data = {
            "email": "test_cookies@example.com",
            "password": "testpassword123"
        }
        
        try:
            response = await client.post(f"{base_url}/v1/client/sign-up", json=signup_data)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 201:
                print("   ✅ Sign-up успешен!")
                
                # Проверяем cookies
                cookies = response.cookies
                print(f"   🍪 Access Token Cookie: {'access_token' in cookies}")
                print(f"   🍪 Refresh Token Cookie: {'refresh_token' in cookies}")
                
                if 'access_token' in cookies:
                    print(f"   📝 Access Token: {cookies['access_token'][:20]}...")
                if 'refresh_token' in cookies:
                    print(f"   📝 Refresh Token: {cookies['refresh_token'][:20]}...")
                
                # Сохраняем cookies для следующих тестов
                client.cookies = response.cookies
                
            else:
                print(f"   ❌ Sign-up не удался: {response.text}")
                return
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return
        
        # Тест 2: Получение профиля с cookies (без заголовка Authorization)
        print("\n2. Тестируем /v1/client/me с cookies (без Authorization header):")
        try:
            response = await client.get(f"{base_url}/v1/client/me")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Профиль получен с cookies!")
                user_data = response.json()
                print(f"   👤 User ID: {user_data.get('user_id')}")
                print(f"   📧 Email: {user_data.get('email')}")
            else:
                print(f"   ❌ Не удалось получить профиль: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # Тест 3: Обновление токена с cookies
        print("\n3. Тестируем refresh_token с cookies:")
        try:
            response = await client.post(f"{base_url}/v1/client/refresh_token")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Токен обновлен с cookies!")
                
                # Проверяем новые cookies
                cookies = response.cookies
                print(f"   🍪 Новый Access Token Cookie: {'access_token' in cookies}")
                print(f"   🍪 Новый Refresh Token Cookie: {'refresh_token' in cookies}")
                
                # Обновляем cookies
                client.cookies = response.cookies
                
            else:
                print(f"   ❌ Не удалось обновить токен: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # Тест 4: Выход с cookies
        print("\n4. Тестируем logout с cookies:")
        try:
            response = await client.post(f"{base_url}/v1/client/logout")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 204:
                print("   ✅ Выход выполнен с cookies!")
                
                # Проверяем, что cookies очищены
                cookies = response.cookies
                print(f"   🍪 Access Token Cookie очищен: {'access_token' not in cookies}")
                print(f"   🍪 Refresh Token Cookie очищен: {'refresh_token' not in cookies}")
                
            else:
                print(f"   ❌ Не удалось выйти: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # Тест 5: Попытка получить профиль после выхода
        print("\n5. Тестируем /v1/client/me после выхода:")
        try:
            response = await client.get(f"{base_url}/v1/client/me")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 401:
                print("   ✅ Правильно отклонен доступ после выхода!")
            else:
                print(f"   ⚠️ Неожиданный статус: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("\n🎉 Тест cookies завершен!")

async def test_mixed_auth():
    """Тестирует смешанную аутентификацию (заголовок + cookies)"""
    
    base_url = "http://localhost:8002"
    
    print("\n🧪 Тестируем смешанную аутентификацию...")
    
    async with httpx.AsyncClient() as client:
        # Сначала регистрируемся
        signup_data = {
            "email": "test_mixed@example.com",
            "password": "testpassword123"
        }
        
        try:
            response = await client.post(f"{base_url}/v1/client/sign-up", json=signup_data)
            if response.status_code != 201:
                print("   ❌ Не удалось зарегистрироваться для теста")
                return
            
            # Получаем токен из ответа
            token_data = response.json()
            access_token = token_data.get("jwt")
            
            # Сохраняем cookies
            client.cookies = response.cookies
            
            print("   ✅ Пользователь зарегистрирован")
            
            # Тест 1: Запрос с заголовком Authorization (должен работать)
            print("\n   1. Запрос с Authorization header:")
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(f"{base_url}/v1/client/me", headers=headers)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Работает с Authorization header!")
            else:
                print(f"   ❌ Не работает с Authorization header: {response.text}")
            
            # Тест 2: Запрос только с cookies (должен работать)
            print("\n   2. Запрос только с cookies:")
            response = await client.get(f"{base_url}/v1/client/me")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Работает с cookies!")
            else:
                print(f"   ❌ Не работает с cookies: {response.text}")
            
            # Тест 3: Запрос с неверным заголовком, но правильными cookies
            print("\n   3. Запрос с неверным Authorization header, но правильными cookies:")
            headers = {"Authorization": "Bearer invalid_token"}
            response = await client.get(f"{base_url}/v1/client/me", headers=headers)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Cookies имеют приоритет над неверным заголовком!")
            else:
                print(f"   ⚠️ Неверный заголовок блокирует доступ: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестов HTTP-Only cookies...")
    asyncio.run(test_cookies())
    asyncio.run(test_mixed_auth())
    print("\n✅ Все тесты завершены!")

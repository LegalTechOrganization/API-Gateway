#!/usr/bin/env python3
"""
Простой тест для проверки работы sign-up эндпоинта
"""

import requests
import json

def test_signup():
    """Тестирует sign-up эндпоинт"""
    
    # URL для тестирования
    base_url = "http://localhost:8002"
    signup_url = f"{base_url}/v1/client/sign-up"
    
    # Тестовые данные
    test_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    print(f"🧪 Тестируем sign-up эндпоинт: {signup_url}")
    print(f"📤 Отправляем данные: {json.dumps(test_data, indent=2)}")
    
    try:
        # Отправляем POST запрос
        response = requests.post(signup_url, json=test_data)
        
        print(f"📥 Получен ответ:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            print("✅ Sign-up успешно выполнен!")
            response_data = response.json()
            print(f"📋 Ответ: {json.dumps(response_data, indent=2)}")
        else:
            print("❌ Sign-up не удался!")
            print(f"📋 Ошибка: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу. Убедитесь, что API Gateway запущен на localhost:8002")
    except Exception as e:
        print(f"❌ Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    test_signup()

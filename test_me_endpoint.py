import pytest
import httpx
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_me_endpoint_with_fullname():
    """Тест эндпоинта /me с полным именем"""
    # Сначала регистрируем пользователя
    signup_data = {
        "email": "test_me@example.com",
        "password": "password123",
        "full_name": "Тест Пользователь"
    }
    
    signup_response = client.post("/v1/client/sign-up", json=signup_data)
    assert signup_response.status_code == 201
    
    signup_result = signup_response.json()
    jwt_token = signup_result["jwt"]
    
    # Теперь получаем информацию о пользователе через /me
    headers = {"Authorization": f"Bearer {jwt_token}"}
    me_response = client.get("/v1/client/me", headers=headers)
    
    # Проверяем, что запрос прошел успешно (200 OK)
    assert me_response.status_code == 200
    
    # Проверяем структуру ответа
    me_data = me_response.json()
    assert "user_id" in me_data
    assert "email" in me_data
    assert "full_name" in me_data
    assert "orgs" in me_data
    
    # Проверяем, что данные соответствуют зарегистрированному пользователю
    assert me_data["email"] == "test_me@example.com"
    assert me_data["full_name"] == "Тест Пользователь"
    assert isinstance(me_data["orgs"], list)


def test_me_endpoint_without_authorization():
    """Тест эндпоинта /me без авторизации"""
    response = client.get("/v1/client/me")
    
    # Проверяем, что запрос завершился ошибкой авторизации
    assert response.status_code == 401


def test_me_endpoint_with_invalid_token():
    """Тест эндпоинта /me с невалидным токеном"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/v1/client/me", headers=headers)
    
    # Проверяем, что запрос завершился ошибкой авторизации
    assert response.status_code == 401


def test_me_endpoint_with_cookie_token():
    """Тест эндпоинта /me с токеном в cookie"""
    # Сначала регистрируем пользователя
    signup_data = {
        "email": "test_cookie@example.com",
        "password": "password123",
        "full_name": "Cookie Пользователь"
    }
    
    signup_response = client.post("/v1/client/sign-up", json=signup_data)
    assert signup_response.status_code == 201
    
    # Получаем cookies из ответа регистрации
    cookies = signup_response.cookies
    
    # Теперь получаем информацию о пользователе через /me с cookie
    me_response = client.get("/v1/client/me", cookies=cookies)
    
    # Проверяем, что запрос прошел успешно (200 OK)
    assert me_response.status_code == 200
    
    # Проверяем структуру ответа
    me_data = me_response.json()
    assert "user_id" in me_data
    assert "email" in me_data
    assert "full_name" in me_data
    assert "orgs" in me_data
    
    # Проверяем, что данные соответствуют зарегистрированному пользователю
    assert me_data["email"] == "test_cookie@example.com"
    assert me_data["full_name"] == "Cookie Пользователь"


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])

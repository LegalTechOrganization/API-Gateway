import pytest
import httpx
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_signup_with_fullname():
    """Тест регистрации с полным именем"""
    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Иван Иванов"
    }
    
    response = client.post("/v1/client/sign-up", json=signup_data)
    
    # Проверяем, что запрос прошел успешно (201 Created)
    assert response.status_code == 201
    
    # Проверяем структуру ответа
    data = response.json()
    assert "jwt" in data
    assert "refresh_token" in data
    assert "user" in data
    
    # Проверяем, что в ответе есть информация о пользователе
    user = data["user"]
    assert "user_id" in user
    assert "email" in user
    assert user["email"] == "test@example.com"
    
    # Проверяем, что full_name передается в ответе (если поддерживается auth-service)
    if "full_name" in user:
        assert user["full_name"] == "Иван Иванов"


def test_signup_without_fullname_should_fail():
    """Тест, что регистрация без full_name должна завершиться ошибкой"""
    signup_data = {
        "email": "test2@example.com",
        "password": "password123"
        # full_name отсутствует
    }
    
    response = client.post("/v1/client/sign-up", json=signup_data)
    
    # Проверяем, что запрос завершился ошибкой валидации (422 Unprocessable Entity)
    assert response.status_code == 422


def test_signup_with_empty_fullname_should_fail():
    """Тест, что регистрация с пустым full_name должна завершиться ошибкой"""
    signup_data = {
        "email": "test3@example.com",
        "password": "password123",
        "full_name": ""  # Пустое имя
    }
    
    response = client.post("/v1/client/sign-up", json=signup_data)
    
    # Проверяем, что запрос завершился ошибкой валидации (422 Unprocessable Entity)
    assert response.status_code == 422


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])


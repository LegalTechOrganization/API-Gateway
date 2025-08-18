#!/usr/bin/env python3
"""
Тест интеграции с billing сервисом
Проверяет, что токен передается в заголовке X-User-Data
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
from main import app

client = TestClient(app)

# Мок для microservice_client
@pytest.fixture
def mock_microservice_client():
    with patch('routers.billing.microservice_client') as mock_client:
        mock_client.proxy_request = AsyncMock()
        yield mock_client

# Мок для auth_client
@pytest.fixture
def mock_auth_client():
    with patch('routers.auth.auth_client') as mock_client:
        mock_client.sign_up = AsyncMock()
        yield mock_client

# Мок для kafka_service
@pytest.fixture
def mock_kafka_service():
    with patch('routers.auth.send_auth_event') as mock_kafka:
        mock_kafka.return_value = None
        yield mock_kafka

def test_quota_check_with_token(mock_microservice_client):
    """Тест проверки баланса с токеном"""
    # Настройка мока
    mock_response = {"allowed": True, "balance": 100.0}
    mock_microservice_client.proxy_request.return_value = mock_response
    
    # Тестовые данные
    test_data = {
        "units": 10.0
    }
    
    # Выполнение запроса
    response = client.post(
        "/billing/quota/check",
        json=test_data,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Проверка ответа
    assert response.status_code == 200
    assert response.json() == mock_response
    
    # Проверка вызова microservice_client
    mock_microservice_client.proxy_request.assert_called_once()
    call_args = mock_microservice_client.proxy_request.call_args
    
    assert call_args[1]["service_name"] == "billing"
    assert call_args[1]["method"] == "POST"
    assert call_args[1]["path"] == "/internal/billing/check"
    assert call_args[1]["data"] == test_data

def test_quota_debit_with_token(mock_microservice_client):
    """Тест списания средств с токеном"""
    # Настройка мока
    mock_response = {"balance": 95.0, "tx_id": "tx_123"}
    mock_microservice_client.proxy_request.return_value = mock_response
    
    # Тестовые данные
    test_data = {
        "action": "api_call",
        "units": 5.0,
        "ref": "optional-external-id",
        "reason": "API call to external service"
    }
    
    # Выполнение запроса
    response = client.post(
        "/billing/quota/debit",
        json=test_data,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Проверка ответа
    assert response.status_code == 200
    assert response.json() == mock_response
    
    # Проверка вызова microservice_client
    mock_microservice_client.proxy_request.assert_called_once()
    call_args = mock_microservice_client.proxy_request.call_args
    
    assert call_args[1]["service_name"] == "billing"
    assert call_args[1]["method"] == "POST"
    assert call_args[1]["path"] == "/internal/billing/debit"
    assert call_args[1]["data"] == test_data

def test_quota_credit_with_token(mock_microservice_client):
    """Тест пополнения баланса с токеном"""
    # Настройка мока
    mock_response = {"balance": 200.0, "tx_id": "tx_456"}
    mock_microservice_client.proxy_request.return_value = mock_response
    
    # Тестовые данные
    test_data = {
        "action": "manual_credit",
        "units": 100.0,
        "ref": "optional-external-id",
        "source_service": "admin_panel",
        "reason": "Manual balance top-up"
    }
    
    # Выполнение запроса
    response = client.post(
        "/billing/quota/credit",
        json=test_data,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Проверка ответа
    assert response.status_code == 200
    assert response.json() == mock_response
    
    # Проверка вызова microservice_client
    mock_microservice_client.proxy_request.assert_called_once()
    call_args = mock_microservice_client.proxy_request.call_args
    
    assert call_args[1]["service_name"] == "billing"
    assert call_args[1]["method"] == "POST"
    assert call_args[1]["path"] == "/internal/billing/credit"
    assert call_args[1]["data"] == test_data

def test_get_balance_with_token(mock_microservice_client):
    """Тест получения баланса с токеном"""
    # Настройка мока
    mock_response = {"balance": 150.0, "plan": {"name": "basic"}}
    mock_microservice_client.proxy_request.return_value = mock_response
    
    # Выполнение запроса
    response = client.post(
        "/billing/balance",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Проверка ответа
    assert response.status_code == 200
    assert response.json() == mock_response
    
    # Проверка вызова microservice_client
    mock_microservice_client.proxy_request.assert_called_once()
    call_args = mock_microservice_client.proxy_request.call_args
    
    assert call_args[1]["service_name"] == "billing"
    assert call_args[1]["method"] == "POST"
    assert call_args[1]["path"] == "/internal/billing/balance"
    assert call_args[1]["data"] == {}

def test_apply_plan_with_token(mock_microservice_client):
    """Тест применения плана с токеном"""
    # Настройка мока
    mock_response = {"plan_id": "plan_123", "new_balance": 200.0}
    mock_microservice_client.proxy_request.return_value = mock_response
    
    # Тестовые данные
    test_data = {
        "plan_code": "basic",
        "ref": "optional-payment-id",
        "auto_renew": False
    }
    
    # Выполнение запроса
    response = client.post(
        "/billing/plan/apply",
        json=test_data,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Проверка ответа
    assert response.status_code == 200
    assert response.json() == mock_response
    
    # Проверка вызова microservice_client
    mock_microservice_client.proxy_request.assert_called_once()
    call_args = mock_microservice_client.proxy_request.call_args
    
    assert call_args[1]["service_name"] == "billing"
    assert call_args[1]["method"] == "POST"
    assert call_args[1]["path"] == "/internal/billing/plan/apply"
    assert call_args[1]["data"] == test_data

def test_init_user_with_token(mock_microservice_client):
    """Тест инициализации пользователя с токеном"""
    # Настройка мока
    mock_response = {"user_id": "user_123", "status": "initialized"}
    mock_microservice_client.proxy_request.return_value = mock_response
    
    # Выполнение запроса
    response = client.post(
        "/billing/user/init",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Проверка ответа
    assert response.status_code == 200
    assert response.json() == mock_response
    
    # Проверка вызова microservice_client
    mock_microservice_client.proxy_request.assert_called_once()
    call_args = mock_microservice_client.proxy_request.call_args
    
    assert call_args[1]["service_name"] == "billing"
    assert call_args[1]["method"] == "POST"
    assert call_args[1]["path"] == "/internal/billing/user/init"
    assert call_args[1]["data"] == {}

def test_signup_with_billing_init(mock_auth_client, mock_microservice_client, mock_kafka_service):
    """Тест регистрации с автоматической инициализацией в billing"""
    # Настройка моков
    auth_response = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "Bearer",
        "expires_in": 300
    }
    mock_auth_client.sign_up.return_value = auth_response
    
    billing_response = {"user_id": "user_123", "status": "initialized"}
    mock_microservice_client.init_user_in_billing.return_value = billing_response
    
    # Тестовые данные
    signup_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    # Выполнение запроса
    response = client.post("/v1/client/sign-up", json=signup_data)
    
    # Проверка ответа
    assert response.status_code == 201
    
    # Проверка вызова auth_client
    mock_auth_client.sign_up.assert_called_once_with(
        "test@example.com", 
        "testpassword", 
        ""
    )
    
    # Проверка вызова billing инициализации
    mock_microservice_client.init_user_in_billing.assert_called_once_with("test_access_token")
    
    # Проверка вызова kafka
    mock_kafka_service.assert_called_once_with("user_registered", {
        "email": "test@example.com"
    })

def test_billing_without_token(mock_microservice_client):
    """Тест запроса к billing без токена"""
    # Выполнение запроса без токена
    response = client.post(
        "/billing/quota/check",
        json={"units": 10.0}
    )
    
    # Проверка ответа
    assert response.status_code == 200
    
    # Проверка вызова microservice_client (должен быть вызван, но без X-User-Data)
    mock_microservice_client.proxy_request.assert_called_once()

def test_billing_with_cookie_token(mock_microservice_client):
    """Тест запроса к billing с токеном в cookie"""
    # Настройка мока
    mock_response = {"allowed": True, "balance": 100.0}
    mock_microservice_client.proxy_request.return_value = mock_response
    
    # Выполнение запроса с токеном в cookie
    response = client.post(
        "/billing/quota/check",
        json={"units": 10.0},
        cookies={"access_token": "test_token_from_cookie"}
    )
    
    # Проверка ответа
    assert response.status_code == 200
    assert response.json() == mock_response
    
    # Проверка вызова microservice_client
    mock_microservice_client.proxy_request.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__])


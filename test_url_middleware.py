#!/usr/bin/env python3
"""
Тестовый файл для проверки работы URL middleware
"""

import json
from utils.url_builder import get_gateway_base_url, replace_auth_urls_in_response


def test_url_builder():
    """Тестирует функции построения URL"""
    
    # Создаем mock Request объект
    class MockRequest:
        def __init__(self, scheme, hostname, port):
            self.url = MockURL(scheme, hostname, port)
    
    class MockURL:
        def __init__(self, scheme, hostname, port):
            self.scheme = scheme
            self.hostname = hostname
            self.port = port
    
    # Тест 1: HTTP с портом
    request1 = MockRequest("http", "localhost", 8002)
    assert get_gateway_base_url(request1) == "http://localhost:8002"
    
    # Тест 2: HTTPS без порта
    request2 = MockRequest("https", "api.example.com", None)
    assert get_gateway_base_url(request2) == "https://api.example.com"
    
    # Тест 3: HTTP с портом 80
    request3 = MockRequest("http", "example.com", 80)
    assert get_gateway_base_url(request3) == "http://example.com"
    
    print("✅ Все тесты URL builder прошли успешно!")


def test_url_replacement():
    """Тестирует замену URL auth сервиса"""
    
    gateway_base_url = "http://localhost:8002"
    
    # Тест 1: Замена URL auth сервиса
    data1 = {
        "sign_up_url": "http://host.docker.internal:8000/v1/client/sign-up",
        "sign_in_url": "http://localhost:8000/v1/client/sign-in/password"
    }
    expected1 = {
        "sign_up_url": "http://localhost:8002/v1/client/sign-up",
        "sign_in_url": "http://localhost:8002/v1/client/sign-in/password"
    }
    result1 = replace_auth_urls_in_response(data1, gateway_base_url)
    assert result1 == expected1
    
    # Тест 2: Объект с вложенными структурами
    data2 = {
        "links": {
            "auth": ["http://host.docker.internal:8000/v1/client/sign-up", "http://localhost:8000/v1/client/sign-in"],
            "api": "http://host.docker.internal:8000/v1/org"
        },
        "message": "Success"
    }
    expected2 = {
        "links": {
            "auth": ["http://localhost:8002/v1/client/sign-up", "http://localhost:8002/v1/client/sign-in"],
            "api": "http://localhost:8002/v1/org"
        },
        "message": "Success"
    }
    result2 = replace_auth_urls_in_response(data2, gateway_base_url)
    assert result2 == expected2
    
    # Тест 3: Строки, которые не являются URL auth сервиса
    data3 = {
        "url": "http://host.docker.internal:8000/v1/client/sign-up",
        "text": "This is not a URL",
        "number": 123,
        "boolean": True,
        "other_url": "https://api.example.com/some/endpoint"
    }
    expected3 = {
        "url": "http://localhost:8002/v1/client/sign-up",
        "text": "This is not a URL",
        "number": 123,
        "boolean": True,
        "other_url": "https://api.example.com/some/endpoint"
    }
    result3 = replace_auth_urls_in_response(data3, gateway_base_url)
    assert result3 == expected3
    
    print("✅ Все тесты URL replacement прошли успешно!")


if __name__ == "__main__":
    print("🧪 Запуск тестов URL middleware...")
    test_url_builder()
    test_url_replacement()
    print("🎉 Все тесты прошли успешно!")

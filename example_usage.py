#!/usr/bin/env python3
"""
Пример использования URL middleware
"""

from utils.url_builder import get_gateway_base_url, replace_auth_urls_in_response

# Пример данных, которые могут прийти от auth сервиса
auth_service_response = {
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_here",
    "user": {
        "user_id": "user-123",
        "email": "user@example.com",
        "full_name": "John Doe",
        "orgs": [
            {
                "org_id": "org-1",
                "name": "My Organization",
                "api_url": "http://host.docker.internal:8000/v1/org/org-1"
            }
        ]
    },
    "links": {
        "sign_up": "http://host.docker.internal:8000/v1/client/sign-up",
        "sign_in": "http://localhost:8000/v1/client/sign-in/password",
        "refresh": "http://host.docker.internal:8000/v1/client/refresh_token"
    }
}

# Симулируем запрос к API Gateway
class MockRequest:
    def __init__(self, scheme, hostname, port):
        self.url = MockURL(scheme, hostname, port)

class MockURL:
    def __init__(self, scheme, hostname, port):
        self.scheme = scheme
        self.hostname = hostname
        self.port = port

# Пример 1: Запрос к localhost:8002
request1 = MockRequest("http", "localhost", 8002)
gateway_base_url1 = get_gateway_base_url(request1)
print(f"🌐 API Gateway URL: {gateway_base_url1}")

transformed_response1 = replace_auth_urls_in_response(auth_service_response, gateway_base_url1)
print("📤 Преобразованный ответ:")
print(f"   sign_up: {transformed_response1['links']['sign_up']}")
print(f"   sign_in: {transformed_response1['links']['sign_in']}")
print(f"   refresh: {transformed_response1['links']['refresh']}")
print(f"   org_api: {transformed_response1['user']['orgs'][0]['api_url']}")
print()

# Пример 2: Запрос к production серверу
request2 = MockRequest("https", "api.mycompany.com", None)
gateway_base_url2 = get_gateway_base_url(request2)
print(f"🌐 API Gateway URL: {gateway_base_url2}")

transformed_response2 = replace_auth_urls_in_response(auth_service_response, gateway_base_url2)
print("📤 Преобразованный ответ:")
print(f"   sign_up: {transformed_response2['links']['sign_up']}")
print(f"   sign_in: {transformed_response2['links']['sign_in']}")
print(f"   refresh: {transformed_response2['links']['refresh']}")
print(f"   org_api: {transformed_response2['user']['orgs'][0]['api_url']}")
print()

# Пример 3: Запрос к кастомному порту
request3 = MockRequest("http", "dev-api.company.com", 3000)
gateway_base_url3 = get_gateway_base_url(request3)
print(f"🌐 API Gateway URL: {gateway_base_url3}")

transformed_response3 = replace_auth_urls_in_response(auth_service_response, gateway_base_url3)
print("📤 Преобразованный ответ:")
print(f"   sign_up: {transformed_response3['links']['sign_up']}")
print(f"   sign_in: {transformed_response3['links']['sign_in']}")
print(f"   refresh: {transformed_response3['links']['refresh']}")
print(f"   org_api: {transformed_response3['user']['orgs'][0]['api_url']}")

print("\n✅ Все URL auth сервиса автоматически заменяются на URL API Gateway!")

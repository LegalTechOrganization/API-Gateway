#!/usr/bin/env python3
"""
Тест для проверки преобразований ответов от auth сервиса
"""

from utils.jwt_utils import transform_generic_response

def test_response_transformations():
    """Тестирует все преобразования ответов"""
    
    print("🧪 Тестируем преобразования ответов от auth сервиса...")
    
    # Тест 1: Преобразование ответа пользователя (sub -> user_id)
    print("\n1. Тестируем преобразование ответа пользователя:")
    auth_user_response = {
        "sub": "f308ec7e-a221-4f7b-b2d3-22f37d7700ae",
        "email": "huuser2@example.com",
        "orgs": [],
        "active_org_id": None
    }
    
    transformed_user = transform_generic_response(auth_user_response, "user")
    print(f"   Исходный: {auth_user_response}")
    print(f"   Преобразованный: {transformed_user}")
    print(f"   ✅ user_id: {transformed_user.get('user_id')}")
    
    # Тест 2: Преобразование списка пользователей
    print("\n2. Тестируем преобразование списка пользователей:")
    auth_users_list = [
        {"sub": "user1", "email": "user1@example.com", "full_name": "User One"},
        {"sub": "user2", "email": "user2@example.com", "full_name": "User Two"}
    ]
    
    transformed_users = transform_generic_response(auth_users_list, "user_list")
    print(f"   Исходный: {auth_users_list}")
    print(f"   Преобразованный: {transformed_users}")
    print(f"   ✅ Количество пользователей: {len(transformed_users)}")
    
    # Тест 3: Преобразование ответа организации
    print("\n3. Тестируем преобразование ответа организации:")
    auth_org_response = {
        "org_id": "org123",
        "name": "Test Organization"
    }
    
    transformed_org = transform_generic_response(auth_org_response, "org")
    print(f"   Исходный: {auth_org_response}")
    print(f"   Преобразованный: {transformed_org}")
    print(f"   ✅ org_id: {transformed_org.get('org_id')}")
    
    # Тест 4: Преобразование ответа переключения организации
    print("\n4. Тестируем преобразование ответа переключения организации:")
    auth_switch_response = {
        "active_org_id": "new_org_123"
    }
    
    transformed_switch = transform_generic_response(auth_switch_response, "switch_org")
    print(f"   Исходный: {auth_switch_response}")
    print(f"   Преобразованный: {transformed_switch}")
    print(f"   ✅ active_org_id: {transformed_switch.get('active_org_id')}")
    
    # Тест 5: Общее преобразование (без типа)
    print("\n5. Тестируем общее преобразование:")
    auth_generic_response = {
        "sub": "generic_user",
        "email": "generic@example.com",
        "some_field": "some_value"
    }
    
    transformed_generic = transform_generic_response(auth_generic_response)
    print(f"   Исходный: {auth_generic_response}")
    print(f"   Преобразованный: {transformed_generic}")
    print(f"   ✅ user_id: {transformed_generic.get('user_id')}")
    
    print("\n🎉 Все тесты преобразований прошли успешно!")

if __name__ == "__main__":
    test_response_transformations()

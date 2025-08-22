#!/usr/bin/env python3
"""
Тесты интеграции с ChatGPT UI Server через Kafka
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any

# Импортируем функции для тестирования
from services.kafka_service import send_chat_ui_request, wait_for_chat_response, kafka_service

async def test_conversation_creation():
    """Тест создания разговора"""
    print("🧪 Тестируем создание разговора...")
    
    # Создаем тестовое сообщение
    kafka_message = {
        "message_id": str(uuid.uuid4()),
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "operation": "create_conversation",
        "payload": {
            "topic": "Тестовый разговор",
            "user_context": {
                "email": "test@example.com",
                "full_name": "Test User",
                "active_org_id": "org123",
                "org_role": "user",
                "is_org_owner": False
            },
            "request_metadata": {
                "source_ip": "127.0.0.1",
                "user_agent": "test-agent"
            }
        }
    }
    
    try:
        # Отправляем запрос
        await send_chat_ui_request(kafka_service.chat_ui_conversations_topic, kafka_message)
        
        # Ждем ответ
        response = await wait_for_chat_response(kafka_message["request_id"], timeout=10.0)
        
        print(f"✅ Ответ получен: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_message_creation():
    """Тест создания сообщения"""
    print("🧪 Тестируем создание сообщения...")
    
    kafka_message = {
        "message_id": str(uuid.uuid4()),
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "operation": "create_message",
        "payload": {
            "conversation": 1,
            "message": "Привет! Это тестовое сообщение.",
            "is_bot": False,
            "message_type": 0,
            "user_context": {
                "email": "test@example.com",
                "full_name": "Test User",
                "active_org_id": "org123",
                "org_role": "user",
                "is_org_owner": False
            },
            "request_metadata": {
                "source_ip": "127.0.0.1",
                "user_agent": "test-agent"
            }
        }
    }
    
    try:
        await send_chat_ui_request(kafka_service.chat_ui_messages_topic, kafka_message)
        response = await wait_for_chat_response(kafka_message["request_id"], timeout=10.0)
        
        print(f"✅ Ответ получен: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_ai_conversation():
    """Тест AI разговора"""
    print("🧪 Тестируем AI разговор...")
    
    kafka_message = {
        "message_id": str(uuid.uuid4()),
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "operation": "ai_conversation",
        "payload": {
            "name": "gpt-3.5-turbo",
            "message": [
                {
                    "content": "Привет! Как дела?",
                    "role": "user"
                }
            ],
            "conversationId": None,
            "max_tokens": 100,
            "temperature": 0.7,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "system_content": "You are a helpful assistant.",
            "openaiApiKey": "test-key",
            "frugalMode": False,
            "user_context": {
                "email": "test@example.com",
                "full_name": "Test User",
                "active_org_id": "org123",
                "org_role": "user",
                "is_org_owner": False
            },
            "request_metadata": {
                "source_ip": "127.0.0.1",
                "user_agent": "test-agent"
            }
        }
    }
    
    try:
        await send_chat_ui_request(kafka_service.chat_ui_ai_conversation_topic, kafka_message)
        response = await wait_for_chat_response(kafka_message["request_id"], timeout=30.0)
        
        print(f"✅ Ответ получен: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_prompt_creation():
    """Тест создания промпта"""
    print("🧪 Тестируем создание промпта...")
    
    kafka_message = {
        "message_id": str(uuid.uuid4()),
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "operation": "create_prompt",
        "payload": {
            "title": "Тестовый промпт",
            "content": "Ты полезный помощник для тестирования.",
            "user_context": {
                "email": "test@example.com",
                "full_name": "Test User",
                "active_org_id": "org123",
                "org_role": "user",
                "is_org_owner": False
            },
            "request_metadata": {
                "source_ip": "127.0.0.1",
                "user_agent": "test-agent"
            }
        }
    }
    
    try:
        await send_chat_ui_request(kafka_service.chat_ui_prompts_topic, kafka_message)
        response = await wait_for_chat_response(kafka_message["request_id"], timeout=10.0)
        
        print(f"✅ Ответ получен: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_settings():
    """Тест получения настроек"""
    print("🧪 Тестируем получение настроек...")
    
    kafka_message = {
        "message_id": str(uuid.uuid4()),
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "operation": "get_settings",
        "payload": {}
    }
    
    try:
        await send_chat_ui_request(kafka_service.chat_ui_settings_topic, kafka_message)
        response = await wait_for_chat_response(kafka_message["request_id"], timeout=10.0)
        
        print(f"✅ Ответ получен: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_kafka_connection():
    """Тест подключения к Kafka"""
    print("🧪 Тестируем подключение к Kafka...")
    
    try:
        # Запускаем producer
        await kafka_service.start_chat_producer()
        
        if kafka_service.chat_producer:
            print("✅ Chat Kafka producer подключен")
            
            # Тестируем отправку сообщения
            test_message = {
                "test": "message",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            success = await kafka_service.send_chat_message(
                "test-topic", 
                test_message, 
                key="test-key"
            )
            
            if success:
                print("✅ Сообщение успешно отправлено в Kafka")
                return True
            else:
                print("❌ Не удалось отправить сообщение в Kafka")
                return False
        else:
            print("❌ Chat Kafka producer не подключен")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Kafka: {e}")
        return False

async def run_all_tests():
    """Запускает все тесты"""
    print("🚀 Запуск тестов интеграции с ChatGPT UI Server")
    print("=" * 60)
    
    # Инициализируем Kafka
    await kafka_service.start_chat_producer()
    
    tests = [
        ("Kafka Connection", test_kafka_connection),
        ("Settings", test_settings),
        ("Conversation Creation", test_conversation_creation),
        ("Message Creation", test_message_creation),
        ("Prompt Creation", test_prompt_creation),
        ("AI Conversation", test_ai_conversation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Неожиданная ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Выводим итоги
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТОВ")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Итого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️  Некоторые тесты не пройдены")
    
    # Закрываем соединения
    await kafka_service.stop_chat_producer()

if __name__ == "__main__":
    # Запускаем тесты
    asyncio.run(run_all_tests())

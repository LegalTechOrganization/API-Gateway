#!/usr/bin/env python3
"""
Тест подключения к chat-service Kafka как Gateway
По рекомендации Chat Service команды
"""

import json
import uuid
from datetime import datetime
import asyncio
import sys

try:
    from aiokafka import AIOKafkaProducer
    from aiokafka.errors import KafkaError
except ImportError:
    print("❌ aiokafka не установлен. Установите: pip install aiokafka")
    sys.exit(1)


async def test_kafka_connection():
    """Тест подключения к chat-service Kafka как Gateway"""
    bootstrap_servers = "host.docker.internal:9095"  # Как Gateway
    
    print(f"🔍 Тестируем подключение к {bootstrap_servers}...")
    
    producer = None
    try:
        # Подключение как Gateway
        producer = AIOKafkaProducer(
            bootstrap_servers=[bootstrap_servers],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            request_timeout_ms=30000,  # 30 секунд timeout
            retry_backoff_ms=1000,
            retries=3
        )
        
        print("🔌 Подключаемся к Kafka...")
        await producer.start()
        print("✅ Подключение к Kafka установлено!")
        
        # Отправляем тест событие
        request_id = str(uuid.uuid4())
        test_event = {
            "message_id": str(uuid.uuid4()),
            "request_id": request_id,
            "operation": "chat_create_conversation",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": {
                "title": "Test from Gateway simulation",
                "user_context": {
                    "email": "test@gateway.com",
                    "full_name": "Gateway Test User",
                    "active_org_id": "test-org",
                    "org_role": "admin",
                    "is_org_owner": True
                },
                "request_metadata": {
                    "source_ip": "192.168.1.100",
                    "user_agent": "Gateway-Test/1.0",
                    "gateway_request_id": f"gw-test-{uuid.uuid4()}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        }
        
        topic = "chat-service-create-conversation"
        print(f"📤 Отправляем тестовое событие в топик: {topic}")
        print(f"🆔 Request ID: {request_id}")
        
        await producer.send_and_wait(topic, value=test_event, key=request_id)
        print("✅ Gateway → Chat Service Kafka connection successful!")
        print(f"📤 Sent test event to {topic}")
        print("📋 Event payload:")
        print(json.dumps(test_event, indent=2, ensure_ascii=False))
        
        return True
        
    except KafkaError as e:
        print(f"❌ Kafka Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Gateway → Chat Service Kafka connection failed: {e}")
        return False
    finally:
        if producer:
            await producer.stop()
            print("🔌 Подключение к Kafka закрыто")


async def main():
    """Основная функция тестирования"""
    print("🧪 Тест Gateway → Chat Service Kafka интеграции")
    print("=" * 50)
    
    success = await test_kafka_connection()
    
    print("=" * 50)
    if success:
        print("🎉 ТЕСТ ПРОЙДЕН! Gateway может подключиться к Chat Service Kafka")
        print("✅ Готово к реальной интеграции!")
    else:
        print("⚠️  ТЕСТ НЕ ПРОЙДЕН! Проверьте:")
        print("   1. Chat Service Kafka запущен на localhost:9095")
        print("   2. Топик chat-service-create-conversation существует")
        print("   3. Нет блокировки firewall")
        print("   4. Docker DNS настроен корректно")


if __name__ == "__main__":
    asyncio.run(main())

import os
import json
import asyncio
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError


class KafkaService:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None

    async def start_producer(self):
        """Запуск Kafka producer"""
        if not self.producer:
            try:
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None
                )
                await self.producer.start()
                print(f"✅ Kafka producer успешно подключен к {self.bootstrap_servers}")
            except Exception as e:
                print(f"⚠️  Не удалось подключиться к Kafka: {e}")
                print("📝 Сервис будет работать без Kafka (события не будут отправляться)")
                self.producer = None

    async def stop_producer(self):
        """Остановка Kafka producer"""
        if self.producer:
            await self.producer.stop()
            self.producer = None

    async def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """Отправка сообщения в Kafka"""
        if not self.producer:
            return False
        
        try:
            await self.producer.send_and_wait(topic, value=message, key=key)
            return True
        except KafkaError as e:
            print(f"Ошибка отправки сообщения в Kafka: {e}")
            return False

    async def start_consumer(self, topic: str, group_id: str):
        """Запуск Kafka consumer"""
        if not self.consumer:
            self.consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            await self.consumer.start()

    async def stop_consumer(self):
        """Остановка Kafka consumer"""
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None

    async def consume_messages(self, callback):
        """Потребление сообщений из Kafka"""
        if not self.consumer:
            raise RuntimeError("Consumer не запущен. Вызовите start_consumer() сначала.")
        
        try:
            async for message in self.consumer:
                await callback(message)
        except KafkaError as e:
            print(f"Ошибка потребления сообщений из Kafka: {e}")

    async def close(self):
        """Закрытие всех соединений"""
        await self.stop_producer()
        await self.stop_consumer()


# Глобальный экземпляр Kafka сервиса
kafka_service = KafkaService()


async def send_auth_event(event_type: str, data: Dict[str, Any]):
    """Отправка события аутентификации в Kafka"""
    try:
        message = {
            "event_type": event_type,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        
        await kafka_service.send_message("auth-events", message, key=event_type)
    except Exception as e:
        print(f"⚠️  Не удалось отправить auth событие в Kafka: {e}")


async def send_user_event(event_type: str, data: Dict[str, Any]):
    """Отправка события пользователя в Kafka"""
    try:
        message = {
            "event_type": event_type,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        
        await kafka_service.send_message("user-events", message, key=event_type)
    except Exception as e:
        print(f"⚠️  Не удалось отправить user событие в Kafka: {e}")


async def send_organization_event(event_type: str, data: Dict[str, Any]):
    """Отправка события организации в Kafka"""
    try:
        message = {
            "event_type": event_type,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        
        await kafka_service.send_message("organization-events", message, key=event_type)
    except Exception as e:
        print(f"⚠️  Не удалось отправить organization событие в Kafka: {e}")



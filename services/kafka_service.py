import os
import json
import asyncio
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError


class KafkaService:
    def __init__(self):
        # Общий кластер Kafka (для общих событий)
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None

        # Отдельный кластер Kafka для chat-service (по руководству)
        self.chat_bootstrap_servers = os.getenv(
            "CHAT_SERVICE_KAFKA_BOOTSTRAP_SERVERS",
            os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        )
        self.chat_producer: Optional[AIOKafkaProducer] = None
        self.chat_consumer: Optional[AIOKafkaConsumer] = None

        # Топики chat-service из окружения (с дефолтами)
        self.chat_responses_topic = os.getenv("CHAT_SERVICE_RESPONSES_TOPIC", "chat-service-responses")
        self.chat_events_topic = os.getenv("CHAT_SERVICE_EVENTS_TOPIC", "chat-service-events")
        
        # Топики для ChatGPT UI Server
        self.chat_ui_conversations_topic = os.getenv("CHAT_UI_CONVERSATIONS_TOPIC", "chat-ui-conversations")
        self.chat_ui_messages_topic = os.getenv("CHAT_UI_MESSAGES_TOPIC", "chat-ui-messages")
        self.chat_ui_ai_conversation_topic = os.getenv("CHAT_UI_AI_CONVERSATION_TOPIC", "chat-ui-ai-conversation")
        self.chat_ui_gen_title_topic = os.getenv("CHAT_UI_GEN_TITLE_TOPIC", "chat-ui-gen-title")
        self.chat_ui_upload_conversations_topic = os.getenv("CHAT_UI_UPLOAD_CONVERSATIONS_TOPIC", "chat-ui-upload-conversations")
        self.chat_ui_prompts_topic = os.getenv("CHAT_UI_PROMPTS_TOPIC", "chat-ui-prompts")
        self.chat_ui_documents_topic = os.getenv("CHAT_UI_DOCUMENTS_TOPIC", "chat-ui-documents")
        self.chat_ui_settings_topic = os.getenv("CHAT_UI_SETTINGS_TOPIC", "chat-ui-settings")

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
        
        # ИСПРАВЛЕНИЕ: Также запускаем chat producer
        await self.start_chat_producer()

    async def stop_producer(self):
        """Остановка Kafka producer"""
        if self.producer:
            await self.producer.stop()
            self.producer = None

    # Chat-service producer lifecycle
    async def start_chat_producer(self):
        """Запуск Kafka producer для chat-service (отдельный кластер)"""
        if not self.chat_producer:
            try:
                self.chat_producer = AIOKafkaProducer(
                    bootstrap_servers=self.chat_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None
                )
                await self.chat_producer.start()
                print(f"✅ Chat Kafka producer подключен к {self.chat_bootstrap_servers}")
            except Exception as e:
                print(f"⚠️  Не удалось подключиться к Chat Kafka: {e}")
                self.chat_producer = None

    async def stop_chat_producer(self):
        if self.chat_producer:
            await self.chat_producer.stop()
            self.chat_producer = None

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

    async def send_chat_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """Отправка сообщения в chat Kafka кластер"""
        if not self.chat_producer:
            return False
        try:
            await self.chat_producer.send_and_wait(topic, value=message, key=key)
            return True
        except KafkaError as e:
            print(f"Ошибка отправки сообщения в Chat Kafka: {e}")
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

    async def start_chat_consumer(self, topic: str, group_id: str):
        """Запуск chat Kafka consumer (отдельный кластер)"""
        if not self.chat_consumer:
            self.chat_consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.chat_bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            await self.chat_consumer.start()

    async def stop_consumer(self):
        """Остановка Kafka consumer"""
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None

    async def stop_chat_consumer(self):
        if self.chat_consumer:
            await self.chat_consumer.stop()
            self.chat_consumer = None

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
        await self.stop_chat_producer()
        await self.stop_chat_consumer()


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


# ═══════════════════════════════════════════════════════════════════
# CHAT SERVICE KAFKA INTEGRATION - точно как billing
# ═══════════════════════════════════════════════════════════════════

# Словарь для ожидания ответов от chat service
pending_chat_requests: Dict[str, asyncio.Future] = {}

async def send_chat_request(topic: str, message: Dict[str, Any]):
    """Отправляет запрос в chat топик - аналогично billing"""
    success = await kafka_service.send_chat_message(topic, message, key=message["request_id"])
    if not success:
        raise Exception(f"Failed to send message to chat topic {topic}: chat producer not ready")

async def send_chat_ui_request(topic: str, message: Dict[str, Any]):
    """Отправляет запрос в ChatGPT UI Server топик"""
    success = await kafka_service.send_chat_message(topic, message, key=message["request_id"])
    if not success:
        raise Exception(f"Failed to send message to chat UI topic {topic}: chat producer not ready")

async def wait_for_chat_response(request_id: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Ждет ответ из chat-responses топика - аналогично billing"""
    
    # Создаем Future для ожидания ответа
    future = asyncio.Future()
    pending_chat_requests[request_id] = future
    
    try:
        # Ждем ответ с timeout
        response = await asyncio.wait_for(future, timeout=timeout)
        return response
    finally:
        # Очищаем pending request
        pending_chat_requests.pop(request_id, None)

async def start_chat_response_consumer():
    """Запускает consumer для chat-responses - аналогично billing"""
    # Подписка на responses-топик из окружения
    topic = kafka_service.chat_responses_topic
    await kafka_service.start_chat_consumer(topic=topic, group_id='api-gateway-chat')

    try:
        async for message in kafka_service.chat_consumer:
            response_data = message.value
            request_id = response_data.get("request_id")

            if request_id in pending_chat_requests:
                future = pending_chat_requests[request_id]
                if not future.done():
                    future.set_result(response_data)
    except Exception as e:
        print(f"Error in chat response consumer: {e}")
    finally:
        await kafka_service.stop_chat_consumer()

async def send_chat_event(event_type: str, data: Dict[str, Any]):
    """Отправка события chat service в Kafka для аудита"""
    try:
        message = {
            "event_type": event_type,
            "timestamp": asyncio.get_event_loop().time(),
            "data": data
        }
        # Используем events-топик chat-service
        await kafka_service.send_chat_message(kafka_service.chat_events_topic, message, key=event_type)
    except Exception as e:
        print(f"⚠️  Не удалось отправить chat событие в Kafka: {e}")

# Добавить в startup приложения
async def init_chat_kafka():
    """Инициализация Kafka для chat service - аналогично billing"""
    await kafka_service.start_chat_producer()
    
    # Запускаем consumer в фоне
    asyncio.create_task(start_chat_response_consumer())



from fastapi import FastAPI
from routers import user, tpl, billing, user, auth, chat_srv
from models.user import Base
from db import engine
from services.kafka_service import kafka_service, init_chat_kafka
from middleware.url_middleware import URLMiddleware
import asyncio

app = FastAPI()

# Добавляем middleware для автоматического преобразования URL
app.add_middleware(URLMiddleware)

app.include_router(auth.router)

app.include_router(chat_srv.router)  # ← ДОБАВИЛИ chat-srv роутер
app.include_router(tpl.router)
app.include_router(billing.router)
app.include_router(user.router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Инициализируем Kafka producer
    await kafka_service.start_producer()
    
    # Инициализируем Chat Service Kafka интеграцию
    await init_chat_kafka()

@app.on_event("shutdown")
async def on_shutdown():
    # Закрываем Kafka соединения
    await kafka_service.close() 
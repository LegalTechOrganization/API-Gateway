from fastapi import FastAPI
from routers import user, chat, tpl, billing, user, auth
from models.user import Base
from db import engine
from services.kafka_service import kafka_service
from middleware.url_middleware import URLMiddleware
import asyncio

app = FastAPI()

# Добавляем middleware для автоматического преобразования URL
app.add_middleware(URLMiddleware)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(tpl.router)
app.include_router(billing.router)
app.include_router(user.router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Инициализируем Kafka producer
    await kafka_service.start_producer()

@app.on_event("shutdown")
async def on_shutdown():
    # Закрываем Kafka соединения
    await kafka_service.close() 
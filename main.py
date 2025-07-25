from fastapi import FastAPI
from routers import user, chat, tpl, billing, user, auth
from models.user import Base
from db import engine
import asyncio

app = FastAPI()
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(tpl.router)
app.include_router(billing.router)
app.include_router(user.router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 
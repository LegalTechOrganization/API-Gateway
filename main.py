from fastapi import FastAPI
from routers import auth, chat, tpl, billing

app = FastAPI(title="API Gateway (All Services)")

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(tpl.router)
app.include_router(billing.router) 
from fastapi import APIRouter, status, Query, Body, Depends
from pydantic import BaseModel, Field
from typing import Optional
from services.microservice_client import microservice_client

router = APIRouter()

# Pydantic модели для запросов
class CheckBalanceRequest(BaseModel):
    user_id: str
    action: str
    units: float = Field(gt=0, description="Количество единиц (должно быть больше 0)")

class DebitRequest(BaseModel):
    user_id: str
    action: str
    units: float = Field(gt=0, description="Количество единиц (должно быть больше 0)")
    ref: Optional[str] = None
    reason: str = Field(..., description="Причина списания")

class CreditRequest(BaseModel):
    user_id: str
    action: str
    units: float = Field(gt=0, description="Количество единиц (должно быть больше 0)")
    ref: Optional[str] = None
    reason: str = Field(..., description="Причина пополнения")

class ApplyPlanRequest(BaseModel):
    user_id: str
    plan_id: str

# Pydantic модели для ответов
class CheckBalanceResponse(BaseModel):
    allowed: bool
    balance: float

class DebitResponse(BaseModel):
    balance: float
    tx_id: str

class CreditResponse(BaseModel):
    balance: float
    tx_id: str

class BalanceResponse(BaseModel):
    balance: float
    plan: dict

class ApplyPlanResponse(BaseModel):
    plan_id: str
    new_balance: float

@router.post("/billing/quota/check", response_model=CheckBalanceResponse)
async def quota_check(request: CheckBalanceRequest):
    """Проксирует запрос проверки баланса к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/check",
        data=request.dict()
    )

@router.post("/billing/quota/debit", response_model=DebitResponse)
async def quota_debit(request: DebitRequest):
    """Проксирует запрос списания средств к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/debit",
        data=request.dict()
    )

@router.post("/billing/quota/credit", response_model=CreditResponse)
async def quota_credit(request: CreditRequest):
    """Проксирует запрос пополнения баланса к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/credit",
        data=request.dict()
    )

@router.get("/billing/balance", response_model=BalanceResponse)
async def get_balance(user_id: str = Query(..., description="ID пользователя")):
    """Проксирует запрос получения баланса к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="GET",
        path="/internal/billing/balance",
        params={"user_id": user_id}
    )

@router.post("/billing/plan/apply", response_model=ApplyPlanResponse)
async def apply_plan(request: ApplyPlanRequest):
    """Проксирует запрос применения плана к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/plan/apply",
        data=request.dict()
    ) 
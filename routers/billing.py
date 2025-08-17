from fastapi import APIRouter, status, Query, Body, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from services.microservice_client import microservice_client

router = APIRouter()

# Pydantic модели для запросов
class CheckBalanceRequest(BaseModel):
    units: float = Field(gt=0, description="Количество единиц (должно быть больше 0)")

class DebitRequest(BaseModel):
    action: str = Field(..., description="Действие для списания")
    units: float = Field(gt=0, description="Количество единиц (должно быть больше 0)")
    ref: Optional[str] = None
    reason: str = Field(..., description="Причина списания")

class CreditRequest(BaseModel):
    action: str = Field(..., description="Действие для пополнения")
    units: float = Field(gt=0, description="Количество единиц (должно быть больше 0)")
    ref: Optional[str] = None
    source_service: str = Field(..., description="Источник пополнения")
    reason: str = Field(..., description="Причина пополнения")

class ApplyPlanRequest(BaseModel):
    plan_code: str = Field(..., description="Код плана")
    ref: str = Field(..., description="Ссылка на платеж")
    auto_renew: bool = Field(..., description="Автопродление")

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

class UserInitResponse(BaseModel):
    user_id: str
    status: str

@router.post("/billing/quota/check", response_model=CheckBalanceResponse)
async def quota_check(request_data: CheckBalanceRequest, request: Request):
    """Проксирует запрос проверки баланса к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/check",
        request=request,
        data=request_data.dict()
    )

@router.post("/billing/quota/debit", response_model=DebitResponse)
async def quota_debit(request_data: DebitRequest, request: Request):
    """Проксирует запрос списания средств к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/debit",
        request=request,
        data=request_data.dict()
    )

@router.post("/billing/quota/credit", response_model=CreditResponse)
async def quota_credit(request_data: CreditRequest, request: Request):
    """Проксирует запрос пополнения баланса к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/credit",
        request=request,
        data=request_data.dict()
    )

@router.post("/billing/balance", response_model=BalanceResponse)
async def get_balance(request: Request):
    """Проксирует запрос получения баланса к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/balance",
        request=request,
        data={}
    )

@router.post("/billing/plan/apply", response_model=ApplyPlanResponse)
async def apply_plan(request_data: ApplyPlanRequest, request: Request):
    """Проксирует запрос применения плана к микросервису billing"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/plan/apply",
        request=request,
        data=request_data.dict()
    )

@router.post("/billing/user/init", response_model=UserInitResponse)
async def init_user(request: Request):
    """Инициализирует пользователя в billing сервисе"""
    return await microservice_client.proxy_request(
        service_name="billing",
        method="POST",
        path="/internal/billing/user/init",
        request=request,
        data={}
    ) 
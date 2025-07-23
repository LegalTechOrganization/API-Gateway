from fastapi import APIRouter, status, Query, Body
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class QuotaCheckResponse(BaseModel):
    allowed: bool
    remain: float

class QuotaDebitRequest(BaseModel):
    user_id: str
    action: str
    units: float
    ref: Optional[str] = None

class QuotaDebitResponse(BaseModel):
    remain: float

class QuotaCreditRequest(BaseModel):
    user_id: str
    action: str
    units: float
    ref: Optional[str] = None

class QuotaCreditResponse(BaseModel):
    remain: float

@router.get("/billing/quota/check", response_model=QuotaCheckResponse)
def quota_check(user_id: str = Query(...), action: str = Query(...), units: float = Query(...)):
    return {"allowed": True, "remain": 41.0}

@router.post("/billing/quota/debit", response_model=QuotaDebitResponse)
def quota_debit(req: QuotaDebitRequest):
    return {"remain": 40.0}

@router.post("/billing/quota/credit", response_model=QuotaCreditResponse)
def quota_credit(req: QuotaCreditRequest):
    return {"remain": 50.0} 
from fastapi import APIRouter, status, UploadFile, File, Form, Body
from pydantic import BaseModel, RootModel
from typing import List, Optional
from fastapi.responses import StreamingResponse, JSONResponse
import io

router = APIRouter()

# --- Pydantic Schemas ---
class TplAddRequest(BaseModel):
    text: Optional[str] = None
    files: Optional[List[dict]] = None

class TplHistoryItem(BaseModel):
    t: str
    text: Optional[str] = None
    files: Optional[List[dict]] = None

class TplHistoryResponse(RootModel[List[TplHistoryItem]]):
    pass

class TplStatusResponse(BaseModel):
    status: str

# --- Public Endpoints ---
@router.post("/tpl/{code}/add", response_model=TplStatusResponse)
def tpl_add(code: str, req: TplAddRequest):
    return {"status": "ok"}

@router.get("/tpl/{code}/history", response_model=List[TplHistoryItem])
def tpl_history(code: str):
    return [
        {"t": "user", "text": "Нужна претензия по договору 14/05", "files": [{"filename": "contract.pdf", "download_url": "url"}]},
        {"t": "assistant", "text": "Задайте, пожалуйста, сумму долга", "files": []}
    ]

@router.post("/tpl/{code}/run")
def tpl_run(code: str):
    # Возвращаем PDF как поток
    pdf_bytes = b"%PDF-1.4...mock..."
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={code}.pdf"})

@router.post("/tpl/{code}/reset", status_code=status.HTTP_204_NO_CONTENT)
def tpl_reset(code: str):
    return

# --- Internal Endpoints ---
@router.post("/internal/tpl/{code}/add", response_model=TplStatusResponse)
def internal_tpl_add(code: str, req: TplAddRequest):
    return {"status": "ok"}

@router.get("/internal/tpl/{code}/history", response_model=List[TplHistoryItem])
def internal_tpl_history(code: str):
    return [
        {"t": "user", "text": "Нужна претензия по договору 14/05", "files": [{"filename": "contract.pdf", "download_url": "url"}]},
        {"t": "assistant", "text": "Задайте, пожалуйста, сумму долга", "files": []}
    ]

@router.post("/internal/tpl/{code}/run")
def internal_tpl_run(code: str):
    pdf_bytes = b"%PDF-1.4...mock..."
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={code}.pdf"})

@router.post("/internal/tpl/{code}/reset", status_code=status.HTTP_204_NO_CONTENT)
def internal_tpl_reset(code: str):
    return

@router.post("/internal/tpl/{code}/direct-run")
def internal_tpl_direct_run(code: str, user_id: str = Body(...), chat_history: list = Body(...)):
    pdf_bytes = b"%PDF-1.4...mock..."
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={code}.pdf"}) 
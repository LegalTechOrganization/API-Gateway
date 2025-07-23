from fastapi import APIRouter, status, UploadFile, File, Form, Body
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import StreamingResponse, JSONResponse
import io

router = APIRouter()

# --- Pydantic Schemas ---
class ChatConversation(BaseModel):
    id: int
    topic: str
    created_at: Optional[str] = None

class ChatMessage(BaseModel):
    id: int
    content: str
    conversation_id: Optional[int] = None

class ChatPrompt(BaseModel):
    id: int
    text: str
    title: Optional[str] = None

class EmbeddingDocument(BaseModel):
    id: int
    name: str

class ImportResult(BaseModel):
    imported: int

class TitleResult(BaseModel):
    title: str

# --- Public Endpoints ---
@router.get("/chat/conversations/", response_model=List[ChatConversation])
def list_conversations():
    return [
        {"id": 1, "topic": "Quantum computing FAQ", "created_at": "2023-08-20T09:17:00Z"}
    ]

@router.post("/chat/conversations/", response_model=ChatConversation, status_code=status.HTTP_201_CREATED)
def create_conversation(topic: Optional[str] = None):
    return {"id": 104, "topic": topic or "New Chat", "created_at": "2023-08-20T09:17:00Z"}

@router.put("/chat/conversations/{id}/", response_model=ChatConversation)
def rename_conversation(id: int, topic: str = Form(...)):
    return {"id": id, "topic": topic}

@router.delete("/chat/conversations/{id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(id: int):
    return

@router.post("/chat/conversations/delete_all", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_conversations():
    return

@router.get("/chat/messages/", response_model=List[ChatMessage])
def get_messages(conversationId: int):
    return [
        {"id": 1, "content": "Hello!", "conversation_id": conversationId},
        {"id": 2, "content": "How can I help you?", "conversation_id": conversationId}
    ]

@router.put("/chat/messages/{id}/", response_model=ChatMessage)
def edit_message(id: int, content: str = Form(...)):
    return {"id": id, "content": content}

@router.delete("/chat/messages/{id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(id: int):
    return

@router.post("/conversation/")
def sse_conversation():
    def event_stream():
        yield b"event: delta\ndata: {\"content\":\"Qubits are the quantum version of bits.\"}\n\n"
        yield b"event: done\ndata: {\"messageId\":876}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/chat/prompts/", response_model=List[ChatPrompt])
def list_prompts():
    return [
        {"id": 1, "text": "Say hello!", "title": "Greeting"}
    ]

@router.post("/chat/prompts/", response_model=ChatPrompt, status_code=status.HTTP_201_CREATED)
def create_prompt(text: str = Form(...), title: Optional[str] = Form(None)):
    return {"id": 2, "text": text, "title": title}

@router.put("/chat/prompts/{id}/", response_model=ChatPrompt)
def update_prompt(id: int, text: str = Form(...), title: Optional[str] = Form(None)):
    return {"id": id, "text": text, "title": title}

@router.delete("/chat/prompts/{id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(id: int):
    return

@router.get("/chat/embedding_document/", response_model=List[EmbeddingDocument])
def list_embedding_documents():
    return [
        {"id": 55, "name": "whitepaper.pdf"}
    ]

@router.post("/chat/embedding_document/", response_model=EmbeddingDocument, status_code=status.HTTP_201_CREATED)
def upload_embedding_document(file: UploadFile = File(...), name: str = Form(...)):
    return {"id": 56, "name": name}

@router.put("/chat/embedding_document/{id}/", response_model=EmbeddingDocument)
def rename_embedding_document(id: int, name: str = Form(...)):
    return {"id": id, "name": name}

@router.delete("/chat/embedding_document/{id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_embedding_document(id: int):
    return

@router.get("/chat/settings/")
def get_settings():
    return {"theme": "light", "notifications": True}

@router.post("/upload_conversations/", response_model=ImportResult)
def upload_conversations(file: UploadFile = File(...)):
    return {"imported": 1}

@router.post("/gen_title/", response_model=TitleResult)
def generate_title(conversationId: int = Form(...), prompt: str = Form(...)):
    return {"title": "Generated Title"}

# --- Internal Endpoints (health, metrics, etc.) ---
@router.get("/health/")
def health():
    return {"status": "ok"}

@router.get("/metrics/")
def metrics():
    return "# HELP django_http_requests_total_total Total count for requests\n# TYPE django_http_requests_total_total counter\ndjango_http_requests_total_total{method=\"POST\",view=\"conversation\"} 1562\n", 200, {"content-type": "text/plain"}

@router.get("/docs/")
def docs():
    return JSONResponse(content={"info": {"title": "ChatGPT-UI API", "version": "v1"}})

@router.get("/openapi.json")
def openapi():
    return JSONResponse(content={"openapi": "3.0.2", "info": {"title": "ChatGPT-UI API", "version": "v1"}})

@router.get("/celery/heartbeat")
def celery_heartbeat():
    return {"workers": 3, "queues": {"default": "OK", "long_tasks": "OK"}, "timestamp": "2023-08-20T10:21:46Z"}

@router.post("/tasks/embeddings/reindex/", status_code=status.HTTP_202_ACCEPTED)
def reindex_embeddings(id_list: List[int] = Body(...)):
    return JSONResponse(content={}, status_code=202, headers={"Location": "/tasks/embeddings/status/873e3ac6"})

@router.get("/internal/settings/refresh/", status_code=status.HTTP_204_NO_CONTENT)
def refresh_settings():
    return 
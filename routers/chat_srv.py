from fastapi import APIRouter, Request, Header, HTTPException, status, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from services.kafka_service import send_chat_ui_request, wait_for_chat_response, kafka_service
from services.microservice_client import microservice_client
from utils.auth_utils import get_user_context_from_token, get_token_from_auth_header_or_cookie
import uuid
from datetime import datetime
import asyncio

router = APIRouter()

# ═══════════════════════════════════════════════════════════════════
# PYDANTIC МОДЕЛИ для ChatGPT UI Server API
# ═══════════════════════════════════════════════════════════════════

# Модели для разговоров
class ConversationCreateRequest(BaseModel):
    topic: str = Field(..., description="Название разговора")

class ConversationUpdateRequest(BaseModel):
    topic: str = Field(..., description="Новое название разговора")

class ConversationResponse(BaseModel):
    id: int
    topic: str
    created_at: str
    updated_at: str

# Модели для сообщений
class MessageCreateRequest(BaseModel):
    conversation: int = Field(..., description="ID разговора")
    message: str = Field(..., description="Текст сообщения")
    is_bot: bool = Field(False, description="Сообщение от бота")
    message_type: int = Field(0, description="Тип сообщения")

class MessageResponse(BaseModel):
    id: int
    conversation: int
    message: str
    is_bot: bool
    message_type: int
    created_at: str
    tokens: int

# Модели для ИИ чата
class ConversationAIRequest(BaseModel):
    name: str = Field(..., description="Модель ИИ")
    message: List[Dict[str, str]] = Field(..., description="Сообщения")
    conversationId: Optional[int] = Field(None, description="ID разговора")
    max_tokens: int = Field(1000, description="Максимум токенов")
    temperature: float = Field(0.7, description="Температура")
    top_p: float = Field(1.0, description="Top-p")
    frequency_penalty: float = Field(0.0, description="Штраф частоты")
    presence_penalty: float = Field(0.0, description="Штраф присутствия")
    system_content: str = Field("You are a helpful assistant.", description="Системный промпт")
    openaiApiKey: str = Field(..., description="API ключ")
    frugalMode: bool = Field(False, description="Экономный режим")

class TitleGenerationRequest(BaseModel):
    conversationId: int = Field(..., description="ID разговора")
    prompt: str = Field(..., description="Промпт для генерации")
    openaiApiKey: str = Field(..., description="API ключ")

class TitleGenerationResponse(BaseModel):
    title: str

# Модели для промптов
class PromptCreateRequest(BaseModel):
    title: str = Field(..., description="Название промпта")
    content: str = Field(..., description="Содержание промпта")

class PromptResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: str

# Модели для документов
class DocumentUploadRequest(BaseModel):
    title: str = Field(..., description="Название документа")
    file: str = Field(..., description="Файл в base64")
    openaiApiKey: str = Field(..., description="API ключ")

class DocumentResponse(BaseModel):
    id: int
    title: str
    created_at: str

# Модели для импорта
class ImportConversation(BaseModel):
    conversation_topic: str
    messages: List[Dict[str, str]]

class ImportRequest(BaseModel):
    imports: List[ImportConversation]

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def enrich_chat_request(
    request_data: dict, 
    request: Request,
    authorization: str = Header(None)
) -> dict:
    """Обогащает запрос контекстом пользователя"""
    
    # Получаем токен
    token = await get_token_from_auth_header_or_cookie(request, authorization)
    
    # Получаем контекст пользователя
    user_context = await get_user_context_from_token(token)
    
    # Создаем обогащенное событие для Kafka
    kafka_message = {
        "message_id": str(uuid.uuid4()),
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            **request_data,
            "user_context": {
                "email": user_context.get("email"),
                "full_name": user_context.get("full_name"),
                "active_org_id": user_context.get("active_org_id"),
                "org_role": user_context.get("org_role"),
                "is_org_owner": user_context.get("is_org_owner", False)
            },
            "request_metadata": {
                "source_ip": request.client.host,
                "user_agent": request.headers.get("user-agent")
            }
        }
    }
    
    return kafka_message

# ═══════════════════════════════════════════════════════════════════
# CONVERSATIONS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.post("/api/chat/conversations/", response_model=ConversationResponse)
async def create_conversation(
    request_data: ConversationCreateRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Создает новый разговор"""
    
    # Используем HTTP проксирование как billing service
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="POST",
        path="/api/chat/conversations/",
        request=request,
        data=request_data.dict()
    )

@router.get("/api/chat/conversations/", response_model=List[ConversationResponse])
async def list_conversations(
    request: Request,
    authorization: str = Header(None)
):
    """Получает список разговоров"""
    
    # Используем HTTP проксирование как billing service
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="GET",
        path="/api/chat/conversations/",
        request=request,
        data={}
    )

@router.get("/api/chat/conversations/{conversation_id}/", response_model=ConversationResponse)
async def get_conversation(
	conversation_id: int,
	request: Request,
	authorization: str = Header(None)
):
	"""Получает конкретный разговор (HTTP proxy)"""
	return await microservice_client.proxy_request(
		service_name="chat_ui",
		method="GET",
		path=f"/api/chat/conversations/{conversation_id}/",
		request=request,
		data={}
	)

@router.put("/api/chat/conversations/{conversation_id}/", response_model=ConversationResponse)
async def update_conversation(
	conversation_id: int,
	request_data: ConversationUpdateRequest,
	request: Request,
	authorization: str = Header(None)
):
	"""Обновляет разговор (HTTP proxy)"""
	return await microservice_client.proxy_request(
		service_name="chat_ui",
		method="PUT",
		path=f"/api/chat/conversations/{conversation_id}/",
		request=request,
		data=request_data.dict()
	)

@router.patch("/api/chat/conversations/{conversation_id}/", response_model=ConversationResponse)
async def partial_update_conversation(
	conversation_id: int,
	request_data: ConversationUpdateRequest,
	request: Request,
	authorization: str = Header(None)
):
	"""Частично обновляет разговор (HTTP proxy)"""
	return await microservice_client.proxy_request(
		service_name="chat_ui",
		method="PATCH",
		path=f"/api/chat/conversations/{conversation_id}/",
		request=request,
		data=request_data.dict()
	)

# DELETE_ALL должен быть ПЕРЕД обычными DELETE роутами
@router.delete("/api/chat/conversations/delete_all/")
async def delete_all_conversations(
	request: Request,
	authorization: str = Header(None)
):
	"""Удаляет все разговоры (HTTP proxy)"""
	return await microservice_client.delete_all_conversations(request)

@router.delete("/api/chat/conversations/{conversation_id}/")
async def delete_conversation(
	conversation_id: int,
	request: Request,
	authorization: str = Header(None)
):
	"""Удаляет разговор (HTTP proxy)"""
	return await microservice_client.proxy_request(
		service_name="chat_ui",
		method="DELETE",
		path=f"/api/chat/conversations/{conversation_id}/",
		request=request,
		data={}
	)

# ═══════════════════════════════════════════════════════════════════
# MESSAGES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/api/chat/messages/", response_model=List[MessageResponse])
async def list_messages(
    conversationId: Optional[int] = Query(None, description="ID разговора для фильтрации"),
    request: Request = None,
    authorization: str = Header(None)
):
    """Получает сообщения (HTTP proxy)"""
    params = {"conversationId": conversationId} if conversationId is not None else None
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="GET",
        path="/api/chat/messages/",
        request=request,
        params=params,
        data={}
    )

@router.post("/api/chat/messages/", response_model=MessageResponse)
async def create_message(
    request_data: MessageCreateRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Создает сообщение (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="POST",
        path="/api/chat/messages/",
        request=request,
        data=request_data.dict()
    )

@router.get("/api/chat/messages/{message_id}/", response_model=MessageResponse)
async def get_message(
    message_id: int,
    request: Request,
    authorization: str = Header(None)
):
    """Получает конкретное сообщение (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="GET",
        path=f"/api/chat/messages/{message_id}/",
        request=request,
        data={}
    )

@router.put("/api/chat/messages/{message_id}/", response_model=MessageResponse)
async def update_message(
    message_id: int,
    request_data: MessageCreateRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Обновляет сообщение (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="PUT",
        path=f"/api/chat/messages/{message_id}/",
        request=request,
        data=request_data.dict()
    )

@router.patch("/api/chat/messages/{message_id}/", response_model=MessageResponse)
async def partial_update_message(
    message_id: int,
    request: Request,
    request_data: MessageCreateRequest,
    authorization: str = Header(None)
):
    """Частично обновляет сообщение (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="PATCH",
        path=f"/api/chat/messages/{message_id}/",
        request=request,
        data=request_data.dict()
    )

# DELETE_ALL должен быть ПЕРЕД обычными DELETE роутами
@router.delete("/api/chat/messages/delete_all/")
async def delete_all_messages(
    request: Request,
    authorization: str = Header(None)
):
    """Удаляет все сообщения конкретной беседы (HTTP proxy)"""
    return await microservice_client.delete_all_messages(request)

@router.delete("/api/chat/messages/{message_id}/")
async def delete_message(
    message_id: int,
    request: Request,
    authorization: str = Header(None)
):
    """Удаляет сообщение (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="DELETE",
        path=f"/api/chat/messages/{message_id}/",
        request=request,
        data={}
    )

# ═══════════════════════════════════════════════════════════════════
# AI CHAT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.post("/api/conversation/")
async def ai_conversation(
    request_data: ConversationAIRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Основной чат с ИИ (streaming)"""
    
    kafka_message = await enrich_chat_request(
        request_data.dict(),
        request, 
        authorization
    )
    kafka_message["operation"] = "ai_conversation"
    
    await send_chat_ui_request(kafka_service.chat_ui_ai_conversation_topic, kafka_message)
    
    try:
        response = await wait_for_chat_response(
            kafka_message["request_id"],
            timeout=120.0  # Увеличенный timeout для AI генерации
        )
        
        if response["status"] == "success":
            return response["payload"]
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("error", "AI conversation failed")
            )
            
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="AI conversation timeout"
        )

@router.post("/api/gen_title/", response_model=TitleGenerationResponse)
async def generate_title(
    request_data: TitleGenerationRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Генерирует заголовок разговора"""
    
    kafka_message = await enrich_chat_request(
        request_data.dict(),
        request, 
        authorization
    )
    kafka_message["operation"] = "generate_title"
    
    await send_chat_ui_request(kafka_service.chat_ui_gen_title_topic, kafka_message)
    
    try:
        response = await wait_for_chat_response(
            kafka_message["request_id"],
            timeout=30.0
        )
        
        if response["status"] == "success":
            return response["payload"]
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("error", "Failed to generate title")
            )
            
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Title generation timeout"
        )

@router.post("/api/upload_conversations/", response_model=List[int])
async def upload_conversations(
    request_data: ImportRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Импортирует разговоры"""
    
    kafka_message = await enrich_chat_request(
        request_data.dict(),
        request, 
        authorization
    )
    kafka_message["operation"] = "upload_conversations"
    
    await send_chat_ui_request(kafka_service.chat_ui_upload_conversations_topic, kafka_message)
    
    try:
        response = await wait_for_chat_response(
            kafka_message["request_id"],
            timeout=30.0
        )
        
        if response["status"] == "success":
            return response["payload"]
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("error", "Failed to upload conversations")
            )
            
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Upload conversations timeout"
        )

# ═══════════════════════════════════════════════════════════════════
# PROMPTS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/api/chat/prompts/", response_model=List[PromptResponse])
async def list_prompts(
    request: Request,
    authorization: str = Header(None)
):
    """Получает промпты (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="GET",
        path="/api/chat/prompts/",
        request=request,
        data={}
    )

@router.post("/api/chat/prompts/", response_model=PromptResponse)
async def create_prompt(
    request_data: PromptCreateRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Создает промпт (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="POST",
        path="/api/chat/prompts/",
        request=request,
        data=request_data.dict()
    )

@router.get("/api/chat/prompts/{prompt_id}/", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int,
    request: Request,
    authorization: str = Header(None)
):
    """Получает конкретный промпт (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="GET",
        path=f"/api/chat/prompts/{prompt_id}/",
        request=request,
        data={}
    )

@router.put("/api/chat/prompts/{prompt_id}/", response_model=PromptResponse)
async def update_prompt(
    prompt_id: int,
    request_data: PromptCreateRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Обновляет промпт (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="PUT",
        path=f"/api/chat/prompts/{prompt_id}/",
        request=request,
        data=request_data.dict()
    )

@router.patch("/api/chat/prompts/{prompt_id}/", response_model=PromptResponse)
async def partial_update_prompt(
    prompt_id: int,
    request_data: PromptCreateRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Частично обновляет промпт (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="PATCH",
        path=f"/api/chat/prompts/{prompt_id}/",
        request=request,
        data=request_data.dict()
    )

# DELETE_ALL должен быть ПЕРЕД обычными DELETE роутами
@router.delete("/api/chat/prompts/delete_all/")
async def delete_all_prompts(
    request: Request,
    authorization: str = Header(None)
):
    """Удаляет все промпты (HTTP proxy)"""
    return await microservice_client.delete_all_prompts(request)

@router.delete("/api/chat/prompts/{prompt_id}/")
async def delete_prompt(
    prompt_id: int,
    request: Request,
    authorization: str = Header(None)
):
    """Удаляет промпт (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="DELETE",
        path=f"/api/chat/prompts/{prompt_id}/",
        request=request,
        data={}
    )

# ═══════════════════════════════════════════════════════════════════
# DOCUMENTS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/api/chat/embedding_document/", response_model=List[DocumentResponse])
async def list_documents(
    request: Request,
    authorization: str = Header(None)
):
    """Получает документы (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="GET",
        path="/api/chat/embedding_document/",
        request=request,
        data={}
    )

@router.post("/api/chat/embedding_document/", response_model=DocumentResponse)
async def upload_document(
    request_data: DocumentUploadRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Загружает документ"""
    
    kafka_message = await enrich_chat_request(
        request_data.dict(),
        request, 
        authorization
    )
    kafka_message["operation"] = "upload_document"
    
    await send_chat_ui_request(kafka_service.chat_ui_documents_topic, kafka_message)
    
    try:
        response = await wait_for_chat_response(
            kafka_message["request_id"],
            timeout=30.0
        )
        
        if response["status"] == "success":
            return response["payload"]
        else:
            raise HTTPException(
                status_code=400,
                detail=response.get("error", "Failed to upload document")
            )
            
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Chat service timeout"
        )

@router.get("/api/chat/embedding_document/{document_id}/", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    request: Request,
    authorization: str = Header(None)
):
    """Получает конкретный документ (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="GET",
        path=f"/api/chat/embedding_document/{document_id}/",
        request=request,
        data={}
    )

@router.put("/api/chat/embedding_document/{document_id}/", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    request_data: DocumentUploadRequest,
    request: Request,
    authorization: str = Header(None)
):
    """Обновляет документ (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="PUT",
        path=f"/api/chat/embedding_document/{document_id}/",
        request=request,
        data=request_data.dict()
    )

# DELETE_ALL должен быть ПЕРЕД обычными DELETE роутами
@router.delete("/api/chat/embedding_document/delete_all/")
async def delete_all_documents(
    request: Request,
    authorization: str = Header(None)
):
    """Удаляет все документы (HTTP proxy)"""
    return await microservice_client.delete_all_documents(request)

@router.delete("/api/chat/embedding_document/{document_id}/")
async def delete_document(
    document_id: int,
    request: Request,
    authorization: str = Header(None)
):
    """Удаляет документ (HTTP proxy)"""
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="DELETE",
        path=f"/api/chat/embedding_document/{document_id}/",
        request=request,
        data={}
    )

# ═══════════════════════════════════════════════════════════════════
# SETTINGS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/api/chat/settings/")
async def get_settings():
    """Получает настройки (не требует аутентификации)"""
    
    # Используем HTTP проксирование как billing service
    return await microservice_client.proxy_request(
        service_name="chat_ui",
        method="GET",
        path="/api/chat/settings/",
        request=Request(scope={"type": "http", "headers": []}),
        data={}
    )

# ═══════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════

@router.get("/chat/health")
async def chat_health():
    """Health check для chat service"""
    return {"status": "ok", "service": "chat-srv"}

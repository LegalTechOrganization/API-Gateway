import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
import os
import logging
import json
from utils.cookie_utils import get_token_from_request

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MicroserviceClient:
    def __init__(self):
        self.base_urls = {
            "billing": "http://host.docker.internal:8001",  # Подключение к внешнему сервису
            "chat_ui": "http://host.docker.internal:8003",  # ChatGPT UI Server
            # Добавь другие микросервисы по мере необходимости
        }
        # Внутренний ключ для аутентификации между сервисами
        self.internal_key = os.getenv("INTERNAL_SERVICE_KEY", "gateway-secret-key-2024")
    
    async def proxy_request(
        self, 
        service_name: str, 
        method: str, 
        path: str, 
        request: Request,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Проксирует запрос к микросервису"""
        if service_name not in self.base_urls:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
        
        url = f"{self.base_urls[service_name]}{path}"
        logger.info(f"Proxying request to: {method} {url}")
        logger.info(f"Request data: {data}")
        logger.info(f"Request params: {params}")
        
        # Добавляем заголовки аутентификации
        request_headers = {
            "Content-Type": "application/json",
            "x-internal-key": self.internal_key
        }
        
        # Добавляем токен пользователя в заголовок X-User-Data для billing сервиса
        if service_name == "billing":
            token = get_token_from_request(request)
            if token:
                user_data = {"jwt_token": token}
                request_headers["X-User-Data"] = json.dumps(user_data)
                logger.info(f"Added X-User-Data header with token for billing service")
            else:
                logger.warning("No token found for billing service request")
        
        # Стандартизированный заголовок аутентификации для chat_ui: X-User-Data (как в billing)
        if service_name == "chat_ui":
            token = get_token_from_request(request)
            if token:
                user_data = {"jwt_token": token}
                request_headers["X-User-Data"] = json.dumps(user_data)
                logger.info("Added X-User-Data header with token for chat UI service")
                # Временная обратная совместимость: добавляем X-User-Id, если удастся извлечь sub
                try:
                    import jwt
                    decoded_token = jwt.decode(token, options={"verify_signature": False})
                    user_id = decoded_token.get("sub")
                    if user_id:
                        request_headers["X-User-Id"] = user_id
                        logger.info(f"Added X-User-Id header (compat) with user_id: {user_id}")
                except Exception as e:
                    logger.warning(f"Skip X-User-Id compat header, decode failed: {e}")
            else:
                logger.warning("No token found for chat UI service request")
        
        if headers:
            request_headers.update(headers)
        
        logger.info(f"Request headers: {request_headers}")
        
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, params=params, headers=request_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, params=params, headers=request_headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, params=params, headers=request_headers)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, json=data, params=params, headers=request_headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, params=params, headers=request_headers)
                else:
                    raise HTTPException(status_code=400, detail=f"Method {method} not supported")
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response body: {response.text}")
                
                response.raise_for_status()
                
                # Обработка пустых ответов (204 No Content)
                if response.status_code == 204:
                    return {"deleted": True, "status": "success"}
                
                # Проверяем, есть ли содержимое в ответе
                if response.text.strip():
                    return response.json()
                else:
                    return {"status": "success", "message": "Operation completed"}
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")

    # ═══════════════════════════════════════════════════════════════════
    # СПЕЦИАЛЬНЫЕ МЕТОДЫ ДЛЯ DELETE_ALL ОПЕРАЦИЙ
    # ═══════════════════════════════════════════════════════════════════
    
    async def delete_all_conversations(self, request: Request) -> Dict[str, Any]:
        """Удалить все беседы пользователя"""
        url = f"{self.base_urls['chat_ui']}/api/chat/conversations/delete_all/"
        return await self._make_request(request, "DELETE", url)
    
    async def delete_all_messages(self, request: Request) -> Dict[str, Any]:
        """Удалить все сообщения конкретной беседы"""
        conversation_id = request.query_params.get('conversationId')
        if not conversation_id:
            raise HTTPException(status_code=400, detail="conversationId parameter is required")
        
        url = f"{self.base_urls['chat_ui']}/api/chat/messages/delete_all/?conversationId={conversation_id}"
        return await self._make_request(request, "DELETE", url)
    
    async def delete_all_prompts(self, request: Request) -> Dict[str, Any]:
        """Удалить все промпты пользователя"""
        url = f"{self.base_urls['chat_ui']}/api/chat/prompts/delete_all/"
        return await self._make_request(request, "DELETE", url)
    
    async def delete_all_documents(self, request: Request) -> Dict[str, Any]:
        """Удалить все документы пользователя"""
        url = f"{self.base_urls['chat_ui']}/api/chat/embedding_document/delete_all/"
        return await self._make_request(request, "DELETE", url)
    
    async def _make_request(self, request: Request, method: str, url: str, data: dict = None) -> Dict[str, Any]:
        """Универсальный метод для запросов к микросервисам"""
        headers = self._prepare_headers(request)
        
        logger.info(f"Making {method} request to: {url}")
        logger.info(f"Request headers: {headers}")
        
        async with httpx.AsyncClient() as client:
            try:
                if method == "DELETE":
                    response = await client.delete(url, headers=headers)
                elif method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response body: {response.text}")
                
                response.raise_for_status()
                return self._process_response(response)
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise HTTPException(status_code=503, detail="Service unavailable")
    
    def _prepare_headers(self, request: Request) -> Dict[str, str]:
        """Подготовка заголовков для запроса"""
        headers = {
            "Content-Type": "application/json",
            "x-internal-key": self.internal_key
        }
        
        # Добавляем токен пользователя в заголовок X-User-Data
        token = get_token_from_request(request)
        if token:
            user_data = {"jwt_token": token}
            headers["X-User-Data"] = json.dumps(user_data)
            logger.info("Added X-User-Data header with token")
            
            # Временная обратная совместимость: добавляем X-User-Id, если удастся извлечь sub
            try:
                import jwt
                decoded_token = jwt.decode(token, options={"verify_signature": False})
                user_id = decoded_token.get("sub")
                if user_id:
                    headers["X-User-Id"] = user_id
                    logger.info(f"Added X-User-Id header (compat) with user_id: {user_id}")
            except Exception as e:
                logger.warning(f"Skip X-User-Id compat header, decode failed: {e}")
        else:
            logger.warning("No token found for request")
        
        return headers
    
    def _process_response(self, response) -> Dict[str, Any]:
        """Обработка ответа от микросервиса"""
        # Обработка пустых ответов (204 No Content)
        if response.status_code == 204:
            return {"deleted": True, "status": "success"}
        
        # Проверяем, есть ли содержимое в ответе
        if response.text.strip():
            return response.json()
        else:
            return {"status": "success", "message": "Operation completed"}

    async def init_user_in_billing(self, access_token: str) -> Dict[str, Any]:
        """Инициализирует пользователя в billing сервисе"""
        url = f"{self.base_urls['billing']}/internal/billing/user/init"
        logger.info(f"Initializing user in billing service: {url}")
        
        # Создаем заголовки с токеном пользователя
        headers = {
            "Content-Type": "application/json",
            "x-internal-key": self.internal_key,
            "X-User-Data": json.dumps({"jwt_token": access_token})
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={}, headers=headers)
            logger.info(f"Billing user init response status: {response.status_code}")
            logger.info(f"Billing user init response body: {response.text}")

            response.raise_for_status()
            return response.json()

# Создаём экземпляр клиента
microservice_client = MicroserviceClient()

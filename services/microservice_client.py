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
                elif method.upper() == "DELETE":
                    response = await client.delete(url, params=params, headers=request_headers)
                else:
                    raise HTTPException(status_code=400, detail=f"Method {method} not supported")
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response body: {response.text}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")

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
            # try:
            #     response = await client.post(url, json={}, headers=headers)
            #     logger.info(f"Billing user init response status: {response.status_code}")
            #     logger.info(f"Billing user init response body: {response.text}")
            #
            #     response.raise_for_status()
            #     return response.json()
            #
            # except httpx.HTTPStatusError as e:
            #     logger.error(f"Billing user init HTTP error: {e.response.status_code} - {e.response.text}")
            #     # Не поднимаем исключение, так как это не критично для регистрации
            #     return {"error": f"Billing service error: {e.response.status_code}"}
            # except httpx.RequestError as e:
            #     logger.error(f"Billing user init request error: {e}")
            #     # Не поднимаем исключение, так как это не критично для регистрации
            #     return {"error": "Billing service unavailable"}

# Создаём экземпляр клиента
microservice_client = MicroserviceClient()

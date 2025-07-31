import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException
import os
import logging

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

# Создаём экземпляр клиента
microservice_client = MicroserviceClient() 
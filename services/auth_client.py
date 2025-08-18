import os
import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException, status


class AuthServiceClient:
    def __init__(self):
        self.base_url = os.getenv("AUTH_SERVICE_URL", "http://host.docker.internal:8000")
        self.timeout = 30.0

    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Выполнение HTTP запроса к auth-service"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, json=data, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Неподдерживаемый HTTP метод: {method}")
                
                response.raise_for_status()
                return response.json() if response.content else {}
                
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Auth service error: {e.response.text} ---- {url}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Auth service unavailable: {str(e)}"
                )

    # Auth endpoints
    async def sign_up(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """Регистрация пользователя"""
        data = {
            "email": email,
            "password": password,
            "full_name": full_name
        }
        return await self._make_request("POST", "/v1/client/sign-up", data)

    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Вход пользователя"""
        data = {
            "email": email,
            "password": password
        }
        return await self._make_request("POST", "/v1/client/sign-in/password", data)

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Обновление токена"""
        data = {"refresh_token": refresh_token}
        return await self._make_request("POST", "/v1/client/refresh_token", data)

    async def logout(self, refresh_token: str) -> None:
        """Выход пользователя"""
        data = {"refresh_token": refresh_token}
        await self._make_request("POST", "/v1/client/logout", data)

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Валидация JWT токена"""
        return await self._make_request("GET", f"/v1/client/validate?token={token}")

    # User endpoints
    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """Получить информацию о пользователе"""
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("GET", "/v1/client/me", headers=headers)

    async def switch_organization(self, org_id: str, token: str) -> Dict[str, Any]:
        """Переключить активную организацию"""
        data = {"org_id": org_id}
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("PATCH", "/v1/client/switch-org", data, headers)

    async def update_user_info(self, full_name: str, token: str) -> Dict[str, Any]:
        """Обновить данные текущего пользователя"""
        data = {"full_name": full_name}
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("PATCH", "/v1/client/update", data, headers)

    async def change_password(self, old_password: str, new_password: str, token: str) -> Dict[str, Any]:
        """Сменить пароль пользователя"""
        data = {"old_password": old_password, "new_password": new_password}
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("POST", "/v1/client/change-password", data, headers)

    # Organization endpoints
    async def create_organization(self, name: str, slug: Optional[str], token: str) -> Dict[str, Any]:
        """Создать организацию"""
        data = {"name": name}
        if slug:
            data["slug"] = slug
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("POST", "/v1/org", data, headers)

    async def get_organization_info(self, org_id: str, token: str) -> Dict[str, Any]:
        """Получить информацию об организации"""
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("GET", f"/v1/org/{org_id}", headers=headers)

    async def get_organization_members(self, org_id: str, token: str) -> Dict[str, Any]:
        """Получить список участников организации"""
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("GET", f"/v1/org/{org_id}/members", headers=headers)

    async def invite_user(self, org_id: str, email: str, role: str, token: str) -> Dict[str, Any]:
        """Пригласить пользователя в организацию"""
        data = {"email": email, "role": role}
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("POST", f"/v1/org/{org_id}/invite", data, headers)

    async def remove_member(self, org_id: str, user_id: str, token: str) -> None:
        """Удалить участника из организации"""
        headers = {"Authorization": f"Bearer {token}"}
        await self._make_request("DELETE", f"/v1/org/{org_id}/member/{user_id}", headers=headers)

    async def update_member_role(self, org_id: str, user_id: str, role: str, token: str) -> Dict[str, Any]:
        """Обновить роль участника"""
        data = {"role": role}
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("PATCH", f"/v1/org/{org_id}/member/{user_id}/role", data, headers)

    # Invite endpoints
    async def accept_invite(self, invite_token: str, token: str) -> Dict[str, Any]:
        """Принять приглашение в организацию"""
        data = {"invite_token": invite_token}
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("POST", "/v1/invite/accept", data, headers)


# Глобальный экземпляр клиента
auth_client = AuthServiceClient()

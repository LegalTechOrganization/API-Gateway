from fastapi import APIRouter, status, Body, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from fastapi.responses import JSONResponse
from services.auth_client import auth_client
from services.kafka_service import send_auth_event, send_user_event, send_organization_event

router = APIRouter()


# --- Pydantic Schemas ---
class User(BaseModel):
    user_id: str = Field(..., example="user-123")
    email: EmailStr
    full_name: Optional[str] = None
    orgs: Optional[List[dict]] = None


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str


class SignUpResponse(BaseModel):
    jwt: str
    refresh_token: str
    user: User


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class SignInResponse(SignUpResponse):
    pass


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    jwt: str
    refresh_token: str


class SwitchOrgRequest(BaseModel):
    org_id: str


class SwitchOrgResponse(BaseModel):
    active_org_id: str


class CreateOrgRequest(BaseModel):
    name: str
    slug: Optional[str] = None


class CreateOrgResponse(BaseModel):
    org_id: str
    name: str


class InviteRequest(BaseModel):
    email: EmailStr
    role: str


class InviteResponse(BaseModel):
    invite_token: str


class AcceptInviteRequest(BaseModel):
    invite_token: str


class AcceptInviteResponse(BaseModel):
    org_id: str
    user_id: str
    role: str


class MemberRoleUpdateRequest(BaseModel):
    role: str


class MemberRoleUpdateResponse(BaseModel):
    user_id: str
    new_role: str


class OrgMember(BaseModel):
    user_id: str
    email: EmailStr
    role: str


# --- Internal Schemas ---
class JWTValidateResponse(BaseModel):
    valid: bool
    sub: str
    email: EmailStr
    exp: int
    roles: List[str]


class OrgRoleInfo(BaseModel):
    org_id: str
    role: str
    is_owner: bool


class OrgDetailInfo(BaseModel):
    id: str
    name: str
    metadata: Optional[dict] = None


class UserDetailInfo(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    active_org_id: Optional[str] = None


class MemberShortInfo(BaseModel):
    user_id: str
    role: str
    email: EmailStr


# --- Public Endpoints ---
@router.post("/v1/client/sign-up", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(data: SignUpRequest):
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.sign_up(data.email, data.password, "")
        
        # Отправляем событие в Kafka
        await send_auth_event("user_registered", {
            "email": data.email
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/v1/client/sign-in/password", response_model=SignInResponse)
async def sign_in(data: SignInRequest):
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.sign_in(data.email, data.password)
        
        # Отправляем событие в Kafka
        await send_auth_event("user_logged_in", {
            "email": data.email
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/v1/client/refresh_token", response_model=RefreshTokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.refresh_token(data.refresh_token)
        
        # Отправляем событие в Kafka
        await send_auth_event("token_refreshed", {
            "refresh_token": data.refresh_token[:10] + "..."  # Логируем только часть токена
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/v1/client/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshTokenRequest):
    try:
        # Проксируем запрос к auth-service
        await auth_client.logout(data.refresh_token)
        
        # Отправляем событие в Kafka
        await send_auth_event("user_logged_out", {
            "refresh_token": data.refresh_token[:10] + "..."  # Логируем только часть токена
        })
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/v1/client/me", response_model=User)
async def get_me(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.get_user_info(token)
        
        # Отправляем событие в Kafka
        await send_user_event("user_info_requested", {
            "user_id": result.get("user_id")
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/v1/client/switch-org", response_model=SwitchOrgResponse)
async def switch_org(data: SwitchOrgRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.switch_organization(data.org_id, token)
        
        # Отправляем событие в Kafka
        await send_user_event("organization_switched", {
            "org_id": data.org_id
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/v1/org", response_model=CreateOrgResponse, status_code=status.HTTP_201_CREATED)
async def create_org(data: CreateOrgRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.create_organization(data.name, data.slug, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("organization_created", {
            "org_id": result.get("org_id"),
            "name": data.name
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/v1/org/{id}/invite", response_model=InviteResponse)
async def invite(id: str, data: InviteRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.invite_user(id, data.email, data.role, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("user_invited", {
            "org_id": id,
            "email": data.email,
            "role": data.role
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/v1/invite/accept", response_model=AcceptInviteResponse)
async def accept_invite(data: AcceptInviteRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.accept_invite(data.invite_token, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("invite_accepted", {
            "org_id": result.get("org_id"),
            "user_id": result.get("user_id"),
            "role": result.get("role")
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/v1/org/{id}/members", response_model=List[OrgMember])
async def org_members(id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.get_organization_members(id, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("members_listed", {
            "org_id": id,
            "member_count": len(result) if isinstance(result, list) else 0
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/v1/org/{id}/member/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(id: str, user_id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        await auth_client.remove_member(id, user_id, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("member_removed", {
            "org_id": id,
            "user_id": user_id
        })
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/v1/org/{id}/member/{user_id}/role", response_model=MemberRoleUpdateResponse)
async def update_member_role(id: str, user_id: str, data: MemberRoleUpdateRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.update_member_role(id, user_id, data.role, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("member_role_updated", {
            "org_id": id,
            "user_id": user_id,
            "new_role": data.role
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# --- Internal Endpoints ---
@router.get("/auth/validate", response_model=JWTValidateResponse)
async def auth_validate(token: str):
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.validate_token(token)
        
        # Отправляем событие в Kafka
        await send_auth_event("token_validated", {
            "valid": result.get("valid", False)
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/auth/user/{id}", response_model=UserDetailInfo)
async def get_user_detail(id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.get_user_info(token)
        
        # Отправляем событие в Kafka
        await send_user_event("user_detail_requested", {
            "user_id": id
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/auth/user/{id}/orgs", response_model=List[OrgRoleInfo])
async def get_user_orgs(id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.get_user_info(token)  # Получаем информацию о пользователе
        
        # Отправляем событие в Kafka
        await send_user_event("user_orgs_requested", {
            "user_id": id
        })
        
        # Возвращаем mock данные, так как в auth-service нет отдельного эндпоинта для orgs
        return [
            {"org_id": "5b1a9904-03d4-4d90-bcbf-8f09c7a8722b", "role": "editor", "is_owner": False},
            {"org_id": "8883b777-7c0b-4784-a7bc-194afc8dd112", "role": "admin", "is_owner": True}
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/auth/org/{id}", response_model=OrgDetailInfo)
async def get_org_detail(id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.get_organization_info(id, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("org_detail_requested", {
            "org_id": id
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/auth/org/{id}/members", response_model=List[MemberShortInfo])
async def get_org_members_internal(id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.get_organization_members(id, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("org_members_requested", {
            "org_id": id
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/auth/org", response_model=CreateOrgResponse, status_code=status.HTTP_201_CREATED)
async def create_org_internal(data: CreateOrgRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.create_organization(data.name, data.slug, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("org_created_internal", {
            "org_id": result.get("org_id"),
            "name": data.name
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/auth/org/{id}/invite", response_model=InviteResponse)
async def invite_internal(id: str, data: InviteRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.invite_user(id, data.email, data.role, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("user_invited_internal", {
            "org_id": id,
            "email": data.email,
            "role": data.role
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/auth/invite/accept", response_model=AcceptInviteResponse)
async def accept_invite_internal(data: AcceptInviteRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.accept_invite(data.invite_token, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("invite_accepted_internal", {
            "org_id": result.get("org_id"),
            "user_id": result.get("user_id"),
            "role": result.get("role")
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/auth/user/{id}/switch-org", response_model=SwitchOrgResponse)
async def switch_org_internal(id: str, data: SwitchOrgRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.switch_organization(data.org_id, token)
        
        # Отправляем событие в Kafka
        await send_user_event("org_switched_internal", {
            "user_id": id,
            "org_id": data.org_id
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/auth/org/{org_id}/member/{user_id}", response_model=MemberRoleUpdateResponse)
async def update_member_role_internal(org_id: str, user_id: str, data: MemberRoleUpdateRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        result = await auth_client.update_member_role(org_id, user_id, data.role, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("member_role_updated_internal", {
            "org_id": org_id,
            "user_id": user_id,
            "new_role": data.role
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/auth/org/{org_id}/member/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_internal(org_id: str, user_id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Проксируем запрос к auth-service
        await auth_client.remove_member(org_id, user_id, token)
        
        # Отправляем событие в Kafka
        await send_organization_event("member_removed_internal", {
            "org_id": org_id,
            "user_id": user_id
        })
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

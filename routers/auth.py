from fastapi import APIRouter, status, Body, Depends, HTTPException, Header, Response, Request
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from fastapi.responses import JSONResponse
from services.auth_client import auth_client
from services.kafka_service import send_auth_event, send_user_event, send_organization_event
from services.microservice_client import microservice_client
from utils.jwt_utils import transform_auth_response, transform_generic_response, extract_user_info_from_token
from utils.cookie_utils import set_auth_cookies, clear_auth_cookies, get_token_from_request, get_refresh_token_from_request

router = APIRouter()


# --- Helper Functions ---
async def get_token_from_auth_header_or_cookie(request: Request, authorization: str = Header(None)) -> str:
    """
    Извлекает токен из заголовка Authorization или из cookie
    
    Args:
        request: FastAPI Request объект
        authorization: Заголовок Authorization
        
    Returns:
        Токен
        
    Raises:
        HTTPException: Если токен не найден
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    else:
        token = get_token_from_request(request)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header or cookie"
        )
    
    return token


# --- Pydantic Schemas ---
class User(BaseModel):
    user_id: str = Field(..., example="user-123")
    email: EmailStr
    full_name: Optional[str] = None
    orgs: Optional[List[dict]] = None


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(..., min_length=1, description="Полное имя пользователя")


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


class UpdateUserRequest(BaseModel):
    full_name: str = Field(..., min_length=1, description="Новое полное имя пользователя")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=1)


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
async def sign_up(data: SignUpRequest, response: Response):
    try:
        # Проксируем запрос к auth-service
        auth_result = await auth_client.sign_up(data.email, data.password, data.full_name)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_auth_response(auth_result, data.email)
        
        # Устанавливаем HTTP-Only cookies
        set_auth_cookies(
            response=response,
            access_token=result["jwt"],
            refresh_token=result["refresh_token"],
            expires_in=auth_result.get("expires_in", 300)
        )

        try:
            await microservice_client.init_user_in_billing(result["jwt"])
        except Exception as billing_error:
            # Логируем ошибку, но не прерываем регистрацию
            print(f"Warning: Failed to initialize user in billing service: {billing_error}")
        
        # Отправляем событие в Kafka
        await send_auth_event("user_registered", {
            "email": data.email,
            "full_name": data.full_name
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
async def sign_in(data: SignInRequest, response: Response):
    try:
        # Проксируем запрос к auth-service
        auth_result = await auth_client.sign_in(data.email, data.password)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_auth_response(auth_result, data.email)
        
        # Устанавливаем HTTP-Only cookies
        set_auth_cookies(
            response=response,
            access_token=result["jwt"],
            refresh_token=result["refresh_token"],
            expires_in=auth_result.get("expires_in", 300)
        )
        
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
async def refresh_token(request: Request, data: RefreshTokenRequest = None, response: Response = None):
    try:
        # Получаем refresh token из тела запроса или из cookie
        refresh_token = None
        if data and data.refresh_token:
            refresh_token = data.refresh_token
        else:
            refresh_token = get_refresh_token_from_request(request)
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token provided"
            )
        
        # Проксируем запрос к auth-service
        auth_result = await auth_client.refresh_token(refresh_token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_auth_response(auth_result)
        
        # Устанавливаем HTTP-Only cookies
        set_auth_cookies(
            response=response,
            access_token=result["jwt"],
            refresh_token=result["refresh_token"],
            expires_in=auth_result.get("expires_in", 300)
        )
        
        # Отправляем событие в Kafka
        await send_auth_event("token_refreshed", {
            "refresh_token": refresh_token[:10] + "..."  # Логируем только часть токена
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
async def logout(request: Request, data: RefreshTokenRequest = None, response: Response = None):
    try:
        # Получаем refresh token из тела запроса или из cookie
        refresh_token = None
        if data and data.refresh_token:
            refresh_token = data.refresh_token
        else:
            refresh_token = get_refresh_token_from_request(request)
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No refresh token provided"
            )
        
        # Проксируем запрос к auth-service
        await auth_client.logout(refresh_token)
        
        # Очищаем cookies
        clear_auth_cookies(response)
        
        # Отправляем событие в Kafka
        await send_auth_event("user_logged_out", {
            "refresh_token": refresh_token[:10] + "..."  # Логируем только часть токена
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
async def get_me(request: Request, authorization: str = Header(None)):
    try:
        # Получаем токен из заголовка Authorization или из cookie
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        
        # Сначала валидируем токен
        validation_result = await auth_client.validate_token(token)
        if not validation_result.get("valid", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Затем получаем информацию о пользователе
        auth_result = await auth_client.get_user_info(token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "user")
        
        # Отправляем событие в Kafka
        await send_user_event("user_info_requested", {
            "user_id": result.get("user_id"),
            "full_name": result.get("full_name")
        })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/v1/client/update", response_model=User)
async def update_user_info(request: Request, data: UpdateUserRequest, authorization: str = Header(None)):
    try:
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        # Проксируем запрос к auth-service
        auth_result = await auth_client.update_user_info(data.full_name, token)

        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "user")

        # Отправляем событие в Kafka
        await send_user_event("user_updated", {
            "user_id": result.get("user_id"),
            "full_name": result.get("full_name")
        })

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/v1/client/change-password", status_code=status.HTTP_200_OK)
async def change_password(request: Request, data: ChangePasswordRequest, authorization: str = Header(None)):
    try:
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        # Проксируем запрос к auth-service
        await auth_client.change_password(data.old_password, data.new_password, token)

        # Отправляем событие в Kafka
        await send_auth_event("password_changed", {
            "message": "Password changed successfully"
        })

        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/v1/client/switch-org", response_model=SwitchOrgResponse)
async def switch_org(request: Request, data: SwitchOrgRequest, authorization: str = Header(None)):
    try:
        # Получаем токен из заголовка Authorization или из cookie
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        
        # Проксируем запрос к auth-service
        auth_result = await auth_client.switch_organization(data.org_id, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "switch_org")
        
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
async def create_org(request: Request, data: CreateOrgRequest, authorization: str = Header(None)):
    try:
        # Получаем токен из заголовка Authorization или из cookie
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        
        # Проксируем запрос к auth-service
        auth_result = await auth_client.create_organization(data.name, data.slug, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "org")
        
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
async def invite(request: Request, id: str, data: InviteRequest, authorization: str = Header(None)):
    try:
        # Получаем токен из заголовка Authorization или из cookie
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        
        # Проксируем запрос к auth-service
        auth_result = await auth_client.invite_user(id, data.email, data.role, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result)
        
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
async def accept_invite(request: Request, data: AcceptInviteRequest, authorization: str = Header(None)):
    try:
        # Получаем токен из заголовка Authorization или из cookie
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        
        # Проксируем запрос к auth-service
        auth_result = await auth_client.accept_invite(data.invite_token, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result)
        
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
async def org_members(request: Request, id: str, authorization: str = Header(None)):
    try:
        # Получаем токен из заголовка Authorization или из cookie
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        
        # Проксируем запрос к auth-service
        auth_result = await auth_client.get_organization_members(id, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "user_list")
        
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
async def remove_member(request: Request, id: str, user_id: str, authorization: str = Header(None)):
    try:
        # Получаем токен из заголовка Authorization или из cookie
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        
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
async def update_member_role(request: Request, id: str, user_id: str, data: MemberRoleUpdateRequest, authorization: str = Header(None)):
    try:
        # Получаем токен из заголовка Authorization или из cookie
        token = await get_token_from_auth_header_or_cookie(request, authorization)
        
        # Проксируем запрос к auth-service
        auth_result = await auth_client.update_member_role(id, user_id, data.role, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result)
        
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


# --- Client Endpoints ---
@router.get("/v1/client/validate", response_model=JWTValidateResponse)
async def validate_token(token: str):
    try:
        # Проксируем запрос к auth-service
        auth_result = await auth_client.validate_token(token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result)
        
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
        auth_result = await auth_client.get_user_info(token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "user")
        
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
        auth_result = await auth_client.get_organization_info(id, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "org")
        
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
        auth_result = await auth_client.get_organization_members(id, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "user_list")
        
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
        auth_result = await auth_client.create_organization(data.name, data.slug, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "org")
        
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
        auth_result = await auth_client.invite_user(id, data.email, data.role, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result)
        
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
        auth_result = await auth_client.accept_invite(data.invite_token, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result)
        
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
        auth_result = await auth_client.switch_organization(data.org_id, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result, "switch_org")
        
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
        auth_result = await auth_client.update_member_role(org_id, user_id, data.role, token)
        
        # Преобразуем ответ от auth сервиса в формат API Gateway
        result = transform_generic_response(auth_result)
        
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

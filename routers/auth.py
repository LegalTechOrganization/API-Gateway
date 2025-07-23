from fastapi import APIRouter, status, Body
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from fastapi.responses import JSONResponse

router = APIRouter()

# --- Pydantic Schemas ---
class User(BaseModel):
    user_id: str = Field(..., example="user-123")
    email: EmailStr
    full_name: str
    orgs: Optional[List[dict]] = None

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

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
    full_name: str
    active_org_id: Optional[str] = None

class MemberShortInfo(BaseModel):
    user_id: str
    role: str
    email: EmailStr

# --- Public Endpoints ---
@router.post("/v1/client/sign-up", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
def sign_up(data: SignUpRequest):
    return {
        "jwt": "mock-jwt",
        "refresh_token": "mock-refresh-token",
        "user": {"user_id": "user-1", "email": data.email, "full_name": data.full_name, "orgs": []}
    }

@router.post("/v1/client/sign-in/password", response_model=SignInResponse)
def sign_in(data: SignInRequest):
    return {
        "jwt": "mock-jwt",
        "refresh_token": "mock-refresh-token",
        "user": {"user_id": "user-1", "email": data.email, "full_name": "Test User", "orgs": []}
    }

@router.post("/v1/client/refresh_token", response_model=RefreshTokenResponse)
def refresh_token(data: RefreshTokenRequest):
    return {"jwt": "mock-jwt", "refresh_token": "mock-refresh-token"}

@router.post("/v1/client/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshTokenRequest):
    return

@router.get("/v1/client/me", response_model=User)
def get_me():
    return {"user_id": "user-1", "email": "user@example.com", "full_name": "Test User", "orgs": [{"org_id": "org-1", "name": "Cyberdyne Systems", "role": "admin"}]}

@router.patch("/v1/client/switch-org", response_model=SwitchOrgResponse)
def switch_org(data: SwitchOrgRequest):
    return {"active_org_id": data.org_id}

@router.post("/v1/org", response_model=CreateOrgResponse, status_code=status.HTTP_201_CREATED)
def create_org(data: CreateOrgRequest):
    return {"org_id": "org-1", "name": data.name}

@router.post("/v1/org/{id}/invite", response_model=InviteResponse)
def invite(id: str, data: InviteRequest):
    return {"invite_token": "mock-invite-token"}

@router.post("/v1/invite/accept", response_model=AcceptInviteResponse)
def accept_invite(data: AcceptInviteRequest):
    return {"org_id": "org-1", "user_id": "user-1", "role": "member"}

@router.get("/v1/org/{id}/members", response_model=List[OrgMember])
def org_members(id: str):
    return [
        {"user_id": "user-1", "email": "user1@example.com", "role": "admin"},
        {"user_id": "user-2", "email": "user2@example.com", "role": "member"}
    ]

@router.delete("/v1/org/{id}/member/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(id: str, user_id: str):
    return

@router.patch("/v1/org/{id}/member/{user_id}/role", response_model=MemberRoleUpdateResponse)
def update_member_role(id: str, user_id: str, data: MemberRoleUpdateRequest):
    return {"user_id": user_id, "new_role": data.role}

# --- Internal Endpoints ---
@router.get("/auth/validate", response_model=JWTValidateResponse)
def auth_validate():
    return {
        "valid": True,
        "sub": "2f40fcac-1de7-48bc-94e4-07c3f110b71a",
        "email": "user@example.com",
        "exp": 1723121231,
        "roles": ["editor", "admin"]
    }

@router.get("/auth/user/{id}", response_model=UserDetailInfo)
def get_user_detail(id: str):
    return {
        "id": id,
        "email": "user@example.com",
        "full_name": "Neo Matrix",
        "active_org_id": "32e40d3e-73aa-4f7d-b7e7-fab87fdd8c1e"
    }

@router.get("/auth/user/{id}/orgs", response_model=List[OrgRoleInfo])
def get_user_orgs(id: str):
    return [
        {"org_id": "5b1a9904-03d4-4d90-bcbf-8f09c7a8722b", "role": "editor", "is_owner": False},
        {"org_id": "8883b777-7c0b-4784-a7bc-194afc8dd112", "role": "admin", "is_owner": True}
    ]

@router.get("/auth/org/{id}", response_model=OrgDetailInfo)
def get_org_detail(id: str):
    return {"id": id, "name": "Cyberdyne Systems", "metadata": {"industry": "AI"}}

@router.get("/auth/org/{id}/members", response_model=List[MemberShortInfo])
def get_org_members_internal(id: str):
    return [
        {"user_id": "user-1", "role": "admin", "email": "user1@example.com"},
        {"user_id": "user-2", "role": "member", "email": "user2@example.com"}
    ]

@router.post("/auth/org", response_model=CreateOrgResponse, status_code=status.HTTP_201_CREATED)
def create_org_internal(data: CreateOrgRequest):
    return {"org_id": "org-1", "name": data.name}

@router.post("/auth/org/{id}/invite", response_model=InviteResponse)
def invite_internal(id: str, data: InviteRequest):
    return {"invite_token": "mock-invite-token"}

@router.post("/auth/invite/accept", response_model=AcceptInviteResponse)
def accept_invite_internal(data: AcceptInviteRequest):
    return {"org_id": "org-1", "user_id": "user-1", "role": "member"}

@router.patch("/auth/user/{id}/switch-org", response_model=SwitchOrgResponse)
def switch_org_internal(id: str, data: SwitchOrgRequest):
    return {"active_org_id": data.org_id}

@router.patch("/auth/org/{org_id}/member/{user_id}", response_model=MemberRoleUpdateResponse)
def update_member_role_internal(org_id: str, user_id: str, data: MemberRoleUpdateRequest):
    return {"user_id": user_id, "new_role": data.role}

@router.delete("/auth/org/{org_id}/member/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member_internal(org_id: str, user_id: str):
    return 
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthUserResponse(BaseModel):
    id: str
    document_id: str
    full_name: str
    email: EmailStr
    role: str
    institution_name: str | None = None
    institution_minerd_code: str | None = None
    institution_regional_code: str | None = None
    institution_district_code: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: AuthUserResponse
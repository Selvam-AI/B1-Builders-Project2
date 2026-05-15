from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MemberRegister(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=1, le=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    preferred_time_slots: list[int] = Field(default_factory=list)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int | None
    email: str | None
    role: str
    preferred_time_slots: list[int]
    is_active: bool

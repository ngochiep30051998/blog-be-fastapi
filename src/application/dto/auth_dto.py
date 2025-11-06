from pydantic import BaseModel, ConfigDict

from src.application.dto.user_dto import UserResponse
from src.core.value_objects.email import Email


class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: Email
    password: str

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    date_of_birth: str | None = None
class RegisterResponse(BaseModel):
    access_token: str
    token_type: str
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
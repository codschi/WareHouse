from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    staff_id: int | None = None
    username: str | None = None
    is_manager: bool = False
    message: str | None = None

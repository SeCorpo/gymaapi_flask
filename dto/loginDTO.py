from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from dto.profileDTO import MyProfileDTO


class LoginDTO(BaseModel, frozen=True):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    trustDevice: bool = Field(False, description="Trust device, set expiration time")


class LoginResponseDTO(BaseModel):
    session_token: str
    myProfileDTO: Optional[MyProfileDTO] = None
    device_trusted: bool = Field(False, description="Trust device, set expiration time")

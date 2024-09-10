import re
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator, model_validator,
)

VALID_PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")


class RegisterDTO(BaseModel, frozen=True):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    password2: str = Field(..., description="Password confirmation")

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        """
        Validates the password against complexity requirements.
        """
        if not VALID_PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password is invalid, must contain 8 characters, 1 uppercase, 1 lowercase, 1 number"
            )
        return v

    @model_validator(mode="before")
    def validate_password2(cls, v: dict) -> dict:
        """
        Validates if passwords are equal.
        """
        if v["password"] != v["password2"]:
            raise ValueError(
                "Passwords do not match"
            )
        return v


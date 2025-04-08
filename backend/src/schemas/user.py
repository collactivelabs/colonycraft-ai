from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str
    full_name: Optional[str] = None

class UserLogin(UserBase):
    id: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    
class ImageRequest(BaseModel):
    model_config = ConfigDict(
        title='Image Generation Request',
        json_schema_extra={
            "example": {
                "prompt": "a beautiful sunset over mountains",
                "n_images": 1,
                "size": "512x512"
            }
        }
    )

    prompt: str = Field(..., min_length=1)
    n_images: int = Field(default=1, ge=1, le=10)
    size: str = Field(default="512x512")

class ImageResponse(BaseModel):
    model_config = ConfigDict(title='Image Generation Response')

    images: list[str]

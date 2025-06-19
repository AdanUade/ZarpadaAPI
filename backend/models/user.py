from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    rol: str  # "final" o "admin"

class UserOut(BaseModel):
    id: str = Field(..., description="ID como string")
    username: str
    email: EmailStr
    rol: str
    profile_image_path: Optional[str] = None
    historial: List[str] = []
    favoritos: List[str] = []

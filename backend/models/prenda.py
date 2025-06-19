from typing import Optional
from pydantic import BaseModel, Field

class PrendaCreate(BaseModel):
    nombre: str
    tipo: str
    descripcion: str
    marca: str

class PrendaOut(BaseModel):
    id: str = Field(..., description="ID como string")
    nombre: str
    tipo: str
    descripcion: str
    marca: str
    image_path: Optional[str] = None

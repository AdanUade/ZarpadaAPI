from typing import Optional
from pydantic import BaseModel

class PrendaCreate(BaseModel):
    nombre: str
    tipo: str
    descripcion: str
    marca: str

class PrendaOut(BaseModel):
    id: str
    nombre: str
    tipo: str
    descripcion: str
    marca: str
    image_path: Optional[str] = None        
    image_public_id: Optional[str] = None   

from pydantic import BaseModel
from datetime import date


class Hurto(BaseModel):
    tipo_hurto: int
    denunciante: str
    direccion: str
    fecha_hurto: date
    
    
class Tipo_hurto(BaseModel):
    nombre: str
    
class UsuarioRegistro(BaseModel):
    username: str
    password: str
    
class Token(BaseModel):
    access_token: str
    token_type: str
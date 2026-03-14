from typing import Optional
from pydantic import BaseModel, EmailStr

class Champion(BaseModel):
    id: Optional[str] = None
    name: str
    email: EmailStr
    hashed_password: str

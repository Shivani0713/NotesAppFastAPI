from pydantic import BaseModel,EmailStr
from datetime import datetime
from typing import Optional


class UserLogin(BaseModel):
    pass

class UserRegister(BaseModel):
    username : str
    email : EmailStr
    password : str
    hash_password : str
    class Config:
        from_attribute = True
        
class UserLogout(BaseModel):
    id : int
    email : EmailStr
    
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
        
class NoteShow(BaseModel):
    id : int
    class Config:
        from_attribute = True
        
class NoteCreate(BaseModel):
    title :str
    create_date : datetime
    description : str
    image_path: Optional[str] = None
    user_id : int
    
    class Config:
        from_attribute = True
        
class NoteDelete(BaseModel):
    id : int
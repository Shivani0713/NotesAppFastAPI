from fastapi import Request, HTTPException, Depends
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models import User
from .db import sessionLocal, get_db
import os


SECRET_KEY = "secret123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 60

pwd_context = CryptContext(schemes=['bcrypt'], deprecated = "auto")
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/login")

def hash_password(password):
    return pwd_context.hash(password)


def verify_password(plain, password):
    return pwd_context.verify(plain,password)

def create_access_token(data:dict, expire_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expire_delta or timedelta(minutes=15))
    to_encode.update({'exp':expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request, db=Depends(get_db)):
    token = request.cookies.get("token")  # ← get from cookie
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
from sqlalchemy.orm import Session
from postgres.config import SessionLocal
from postgres.models import User

from fastapi.security import OAuth2PasswordBearer

from datetime import datetime, timedelta
import os
import uuid

from passlib.context import CryptContext
from jose import JWTError, jwt


db = SessionLocal()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def random_id():
    return str(uuid.uuid4())

def get_user(username: str, fmno: int):
    user  =  db.query(User).filter(User.username == username, User.fmno == fmno).first()
    if user:
        return {
            "id": user.id,
            "username": user.username,
            "fmno": user.fmno,
            "hashedPassword": user.hashedPassword
        }
    return None


def create_user(username: str, fmno:int, password: str):
    user = User(id=random_id(), username=username, fmno=fmno, hashedPassword=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "fmno": user.fmno,
        "hashedPassword": user.hashedPassword
    }


def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(user):
    return jwt.encode(
        {
            "id": user["id"],
            "username": user["username"],
            "fmno": user["fmno"],
            "exp": datetime.now() + timedelta(minutes=int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"]))
        },
        os.environ["SECRET_KEY"],
        algorithm=os.environ["ALGORITHM"]
    )


def authenticate_user(username: str, fmno:str, password: str):
    user = get_user(username, fmno)
    if not user:
        return {
            "message": "User not found"
        }
    if not verify_password(password, user["hashedPassword"]):
        return {
            "message": "Incorrect credentials"
        }
    
    return {
        "message": "Login successful",
        "token": create_jwt_token(user)
    }

def register_user(username: str, fmno: int, password: str):
    user = get_user(username, fmno)
    if user:
        return {
            "message": "User already exists"
        }
    create_user(username, fmno, password)
    return {
        "message": "User created successfully",
        "token": create_jwt_token(get_user(username, fmno))
    }

def validate_token(token: str):
    try:
        payload = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=[os.environ["ALGORITHM"]])
        return {
            "is_valid": True,
            "message": "Token is valid",
            "payload": payload
        }
    except JWTError:
        return {
            "is_valid": False,
            "message": "Token is invalid"
        }
    except Exception as e:
        return {"error": e}

    
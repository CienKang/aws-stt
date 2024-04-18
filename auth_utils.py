
from datetime import datetime, timedelta
import os
import sqlite3
import uuid

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

db = sqlite3.connect("auth-cred.db")

def random_user_id():
    return str(uuid.uuid4())

def get_user(username: str, fmno: int):
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM USERS WHERE username='{username}' AND fmno={fmno}")
    user = cursor.fetchone()
    if user:
        return {
            "user_id": user[0],
            "username": user[1],
            "fmno": user[2],
            "hashedPassword": user[3]
        }
    else :
        return None

def create_user(username: str, fmno:int, password: str):
    cursor = db.cursor()
    hashedPassword = hash_password(password)
    cursor.execute(f"INSERT INTO USERS (user_id, username, fmno, hashedPassword) VALUES ('{random_user_id()}','{username}', {fmno}, '{hashedPassword}')")
    db.commit()



def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(user ):
    return jwt.encode(
        {
            "user_id": user["user_id"],
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
            "message": "Token is valid",
            "payload": payload
        }
    except JWTError:
        return {
            "message": "Token is invalid"
        }
    except Exception as e:
        return {"error": e}

    
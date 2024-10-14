from dotenv import load_dotenv
from passlib.context import CryptContext
import os
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException,status, Depends
from database.models import Users
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import TokenTable, Users
from fastapi.responses import JSONResponse
from typing import List

load_dotenv() #to load env file

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_hashed_password(password):
    return pwd_context.hash(password)

def verify_password(user_password, hashed_password):
    return pwd_context.verify(user_password, hashed_password)

def create_access_token(to_encode: dict):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(to_encode: dict):
    expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = decoded_token.get("sub")
        if not username:
            return None
        return username
    except jwt.PyJWTError:
        return None
    
def decode_token(token):

    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return decoded_token

    
# def role_required(required_roles: List[str]):
#     def role_verifier(token_payload: dict = Depends(verify_token)):
#         verify_role(required_roles, token_payload)
#         return token_payload  # Return payload if role verification passes

#     return role_verifier

# def verify_role(roles: List[str], token_payload: dict):
#     user_roles = token_payload.get("roles", [])
#     # Check if the user has at least one of the required roles
#     if not any(role in user_roles for role in roles):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not enough permissions"
        # )
  
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_token = db.query(TokenTable).filter(TokenTable.access_token == token).first()
    if db_token.is_active==False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login to access",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = verify_token(token)
    if username == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(Users).filter(Users.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

class RoleChecker:
    def __init__(self, required_permissions: list[str]) -> None:
        self.required_permissions = required_permissions

    def __call__(self, user: Users = Depends(get_current_user)) -> bool:
        user_roles = [role.value for role in user.roles]
        for r_perm in self.required_permissions:
            if r_perm not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Access denied'
                )
        return True

 



     

    


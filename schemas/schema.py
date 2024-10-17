from pydantic import BaseModel, EmailStr
from database.db_enum import Roles

from typing import List

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    role: Roles
    password: str

class UserDetails(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    role: Roles

class Token(BaseModel):
    access_token: str
    token_type: str
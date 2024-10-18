from pydantic import BaseModel
from database.db_enum import Roles

from typing import List

class UserCreate(BaseModel):
    username: str
    email: str
    role: Roles
    hashed_password: str

    class Config:
        from_attributes = True

class UserDetails(BaseModel):
    id: int
    username: str
    email: str
    role: Roles

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
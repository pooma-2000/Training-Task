from pydantic import BaseModel, EmailStr
from database.db_enum import Roles
from typing import List

# class User(BaseModel):
#     id: int
#     username: str
#     email: EmailStr

#     class Config:
#         from_attributes = True

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    roles: List[Roles]
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
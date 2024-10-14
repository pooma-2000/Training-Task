from sqlalchemy import Column, Integer, String, DateTime, func, Boolean, ForeignKey, Enum, ARRAY
from database.database import Base
from datetime import datetime
from typing import List
from database.db_enum import Roles

class BaseModel(Base):
    __abstract__ = True

    created_ts = Column(DateTime, default=datetime.now, nullable=False, server_default=func.now())
    updated_ts = Column(DateTime, default=datetime.now, onupdate=datetime.now, server_default=func.now(), server_onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

class Users(BaseModel):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    roles = Column(ARRAY(Enum(Roles)), nullable=False)
    hashed_password = Column(String, nullable=False)

class TokenTable(BaseModel):
    __tablename__ = "token"
    user_id = Column(Integer, ForeignKey(Users.id), nullable=False)
    access_token = Column(String, primary_key=True)
    refresh_token = Column(String, nullable=False)
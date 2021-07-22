from enum import Enum

from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class Role(str, Enum):
    admin = 'admin'
    user = 'user'


class UserBase(BaseModel):
    username: str
    email: str = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: Role = Role.user


class UserUpdate(UserBase):
    password: str


class User(UserBase):
    id: int
    disabled: bool = False

    class Config:
        orm_mode = True

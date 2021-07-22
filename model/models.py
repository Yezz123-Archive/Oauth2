from sqlalchemy import Boolean, Column, Integer, String, Enum

from database.database import Base
from model.schemas import Role


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    otp_secret = Column(String)
    disabled = Column(Boolean, default=False)
    role = Column(Enum(Role))

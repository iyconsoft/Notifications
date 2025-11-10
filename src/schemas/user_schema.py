from typing import List, Optional
from pydantic import BaseModel
from src.core.dbconfig import Base
from sqlalchemy import Column, Integer, String


class IAuth(BaseModel):
    email: Optional[str] = None
    uid: Optional[str] = None
    otp: Optional[str] = None

class IUser(BaseModel):
    uid: Optional[str] = None
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None


class User(Base):
    __tablename__ = f"useraccounts"

    id = Column(Integer, primary_key = True)
    uid = Column(String(100), unique = True)
    email = Column(String(20))
    otp = Column(String(20))
    firstname = Column(String(20))
    lastname = Column(String(20))

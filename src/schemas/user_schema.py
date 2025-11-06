from typing import List, Optional
from pydantic import BaseModel
from src.core.dbconfig import Base
from sqlalchemy import Column, Integer, String


class IAuth(BaseModel):
    email: str

    

class IUser(BaseModel):
    uid: Optional[str] = None




class Authentication(Base):
    __tablename__ = f"authentication"

    id = Column(Integer, primary_key = True)
    uid = Column(String(100), unique = True)
    otp = Column(String(20))
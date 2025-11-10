from typing import Optional
from pydantic import BaseModel



class IMail(BaseModel):
    email: str
    subject: str
    message: str
    sender: Optional[str] = "Iyconsoft Notifications"
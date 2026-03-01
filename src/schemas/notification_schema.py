"""
Notification Schemas - Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ==================== ENUMS ====================
class SMSTypeEnum(str, Enum):
    """SMS Provider Types"""
    LOCAL = "smpp"
    PSI = "pisi"
    EXTERNAL = "external"
    THIRDPARTY = "coroperate"


class EmailTypeEnum(str, Enum):
    """Email Provider Types"""
    ERP = "erp"
    SMTP = "smtp"


# ==================== SMS SCHEMAS ====================
class SMSSingleRequest(BaseModel):
    """Single SMS Request"""
    phone_number: str = Field(..., description="Recipient phone number")
    message: str = Field(..., description="SMS message content")
    realm: SMSTypeEnum = Field(..., description="SMS provider type (smpp, pisi, coroperate)")
    
    class Config:
        example = {
            "phone_number": "+1234567890",
            "message": "Hello, this is a test message",
            "realm": "local"
        }


class SMSBulkRequest(BaseModel):
    """Bulk SMS Request"""
    recipients: List[str] = Field(..., description="List of phone numbers")
    message: str = Field(..., description="SMS message content")
    realm: SMSTypeEnum =  Field(..., description="SMS provider type (smpp, pisi, coroperate)")
    
    class Config:
        example = {
            "recipients": ["+1234567890", "+0987654321"],
            "message": "Bulk message content",
            "realm": "psi"
        }


class SMSResponse(BaseModel):
    """SMS Response"""
    phone_number: str
    status: str
    message_id: Optional[str] = None
    timestamp: str


# ==================== EMAIL SCHEMAS ====================
class EmailSingleRequest(BaseModel):
    """Single Email Request"""
    to_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    html_body: Optional[str] = Field(None, description="HTML email body (optional)")
    template_id: Optional[str] = Field(None, description="Email template id (optional)")
    provider: EmailTypeEnum = Field(..., description="Email provider type (erp, smtp)")
    
    class Config:
        example = {
            "to_email": "user@example.com",
            "subject": "Welcome",
            "body": "Hello user",
            "html_body": "<h1>Hello</h1>",
            "provider": "erp"
        }


class EmailBulkRequest(BaseModel):
    """Bulk Email Request"""
    recipients: List[EmailStr] = Field(..., description="List of email addresses")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    html_body: Optional[str] = Field(None, description="HTML email body (optional)")
    provider: EmailTypeEnum = Field(..., description="Email provider type (erp, smtp)")
    
    class Config:
        example = {
            "recipients": ["user1@example.com", "user2@example.com"],
            "subject": "Notification",
            "body": "This is a bulk email",
            "provider": "erp"
        }


class EmailResponse(BaseModel):
    """Email Response"""
    to_email: str
    status: str
    message_id: Optional[str] = None
    timestamp: str


# ==================== PUSH NOTIFICATION SCHEMAS ====================
class PushNotificationSingleRequest(BaseModel):
    """Single Push Notification Request"""
    device_token: str = Field(..., description="Firebase device token")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data payload")
    
    class Config:
        example = {
            "device_token": "fPZ6y1qW9sL0k3mN5oP8rQ1tU4vW7xY9z",
            "title": "New Message",
            "body": "You have a new message",
            "data": {"message_id": "123", "sender": "admin"}
        }


class PushNotificationBulkRequest(BaseModel):
    """Bulk Push Notification Request"""
    device_tokens: List[str] = Field(..., description="List of Firebase device tokens")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data payload")
    
    class Config:
        example = {
            "device_tokens": ["token1", "token2", "token3"],
            "title": "Broadcast",
            "body": "This is a broadcast notification",
            "data": {"broadcast_id": "456"}
        }


class PushNotificationResponse(BaseModel):
    """Push Notification Response"""
    device_token: str
    status: str
    message_id: Optional[str] = None
    timestamp: str


# ==================== GENERIC RESPONSES ====================
class BulkNotificationResponse(BaseModel):
    """Bulk Notification Response"""
    total: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    timestamp: str

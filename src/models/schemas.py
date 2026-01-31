from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WebhookMessage(BaseModel):
    """Schema for incoming webhook message from Evolution API"""
    event: str
    data: dict


class SessionInfo(BaseModel):
    """Schema for session information"""
    session_id: str
    handler: str
    created_at: str
    last_interaction: str
    message_count: int


class TransferRequest(BaseModel):
    """Schema for transfer to human request"""
    phone: str
    reason: Optional[str] = None


class MessageResponse(BaseModel):
    """Schema for message response"""
    status: str
    phone: str
    message: Optional[str] = None
    needs_transfer: Optional[bool] = False
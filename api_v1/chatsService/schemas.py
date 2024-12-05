import datetime
from pydantic import BaseModel

from core.models import User


class MessageToBroadcast(BaseModel):
    id: int
    sender: User
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    id: int
    last_message_date: datetime.datetime
    last_message_text: str
    username: str

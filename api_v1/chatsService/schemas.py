import datetime
from pydantic import BaseModel


class MessageToBroadcast(BaseModel):
    id: int
    sender_id: int
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    id: int
    last_message_date: datetime.datetime
    last_message_text: str
    username: str

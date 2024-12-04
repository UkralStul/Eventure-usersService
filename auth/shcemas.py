from typing import List, Optional

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    id: int
    username: str
    email: str


class TokenData(BaseModel):
    token: str


class GetUsersByIdsRequest(BaseModel):
    ids: List[int]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    profile_photo: Optional[str] = None
    created_at: datetime
    birth_date: Optional[datetime] = None
    about_me: Optional[str] = None
    last_seen: Optional[datetime] = None
    is_friend: Optional[bool] = None

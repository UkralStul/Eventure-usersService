from typing import List

from datetime import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    username: str
    email: str


class TokenData(BaseModel):
    token: str


class GetUsersByIdsRequest(BaseModel):
    ids: List[int]


class UserResponse(UserBase):
    created_at: datetime
    profile_photo: str
    about_me: str
    last_seen: datetime

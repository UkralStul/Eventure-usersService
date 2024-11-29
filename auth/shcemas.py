from typing import List

from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    username: str
    email: str


class TokenData(BaseModel):
    token: str


class UserResponse(BaseModel):
    id: int
    username: str
    profile_pic: str


class GetUsersByIdsRequest(BaseModel):
    ids: List[int]

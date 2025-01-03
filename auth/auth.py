from datetime import datetime, timedelta
import time
from typing import List

import jwt
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result

from auth.shcemas import UserBase, UserResponse
from core.config import settings
from sqlalchemy import select
from core.models import db_helper, Friendship
from core.models.User import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

#test
async def get_password_hash(password):
    return pwd_context.hash(password)


async def create_access_token(
    data: dict,
    expire_time: int = settings.auth_jwt.ACCESS_TOKEN_EXPIRE_MINUTES,
    algorithm: str = settings.auth_jwt.algorithm,
    secret: str = settings.auth_jwt.secret_key,
) -> str:
    expire_time *= 60
    to_encode = data.copy()
    expire = time.mktime(datetime.now().timetuple()) + expire_time
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)
    return encoded_jwt


async def create_refresh_token(
    data: dict,
    expire_time: int = settings.auth_jwt.REFRESH_TOKEN_EXPIRE_DAYS,
    algorithm: str = settings.auth_jwt.algorithm,
    secret: str = settings.auth_jwt.refresh_secret_key,
) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=expire_time)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)
    return encoded_jwt


async def decode_access_token(
    token: str,
    algorithm: str = settings.auth_jwt.algorithm,
    secret: str = settings.auth_jwt.secret_key,
) -> str:
    if not token:
        raise ValueError("Token is missing")
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("User ID not found in token")
        return user_id
    except jwt.PyJWTError as e:
        if str(e) == "Signature has expired":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        else:
            raise ValueError(str(e))


async def verify_token(
    token: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user_id = await decode_access_token(token)  # Decode the token to get user ID
    stmt = select(User).filter(User.id == user_id)
    result: Result = await session.execute(stmt)
    user = result.scalars().first()
    return user


async def refresh_access_token(
    token: str,
    algorithm: str = settings.auth_jwt.algorithm,
    secret: str = settings.auth_jwt.refresh_secret_key,
) -> str:
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("User ID not found in token")
        new_access_token = await create_access_token({"sub": user_id})
        return new_access_token
    except jwt.PyJWTError:
        raise ValueError("Token is invalid or has expired")


async def authenticate_user(
    username: str,
    password: str,
    session: AsyncSession,
) -> tuple[str, str, UserBase] | None:
    stmt = select(User).filter(User.username == username)
    result: Result = await session.execute(stmt)
    user = result.scalars().first()

    if not user:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    refresh_token = await create_refresh_token({"sub": user.id})
    access_token = await create_access_token({"sub": user.id})
    return access_token, refresh_token, user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(db_helper.session_dependency),
) -> User:
    user_id = await decode_access_token(token)
    stmt = select(User).filter(User.id == user_id)
    result: Result = await session.execute(stmt)
    user = result.scalars().first()
    return user


async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
) -> User:
    hashed_password = await get_password_hash(password)

    new_user = User(username=username, email=email, hashed_password=hashed_password)

    session.add(new_user)

    await session.commit()
    await session.refresh(new_user)

    return new_user


async def get_users_by_ids(
    session: AsyncSession,
    ids: List[int],
) -> List[User]:
    stmt = select(User).filter(User.id.in_(ids))
    result = await session.execute(stmt)
    users = list(result.scalars())
    return users


async def get_user(
    session: AsyncSession,
    user_id: int,
    current_user: int,
) -> UserResponse:
    stmt = select(User).filter(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Проверяем, являются ли пользователи друзьями
    friendship_stmt = (
        select(Friendship)
        .filter(
            ((Friendship.user_id == current_user) & (Friendship.friend_id == user_id))
            | ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user))
        )
        .filter(Friendship.status.in_(["accepted", "pending"]))
    )

    friendship_result = await session.execute(friendship_stmt)
    friendship = friendship_result.scalars().first()

    user_response = UserResponse.model_validate(user)

    # Добавляем информацию о статусе дружбы
    if friendship:
        is_friend = friendship.status
        user_response.friend_request_sent_by = friendship.sent_by
    else:
        is_friend = None

    user_response.is_friend = is_friend  # Добавляем информацию о дружбе

    return user_response

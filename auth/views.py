from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from uvicorn import logging

from core.models import db_helper, User
from . import auth
from .auth import (
    get_current_user,
    oauth2_scheme,
    refresh_access_token,
    verify_token,
    get_users_by_ids,
    get_user,
)
from .shcemas import UserBase, TokenData, UserResponse, GetUsersByIdsRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
async def login_for_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    result = await auth.authenticate_user(
        username=form_data.username,
        password=form_data.password,
        session=session,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    access_token, refresh_token, user = result
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "refresh_token": refresh_token,
    }


@router.post("/createUser")
async def create_user(
    username: str,
    password: str,
    email: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await auth.create_user(
        username=username,
        password=password,
        email=email,
        session=session,
    )


@router.post("/refresh")
async def refresh(
    refresh_token: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    try:
        new_access_token = await refresh_access_token(refresh_token)
        user = await verify_token(token=new_access_token, session=session)
        return {"access_token": new_access_token, "token_type": "bearer", "user": user}

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post("/getUsersByIds")
async def get_users_by_ids_view(
    request: GetUsersByIdsRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    ids = request.ids
    return await get_users_by_ids(ids=ids, session=session)


@router.post("/verifyToken")
async def verify(
    token: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    try:
        user = await verify_token(token=token, session=session)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {"status": "success", "user": user}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/getUser/{user_id}")
async def get_user_view(
    user_id: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
    current_user: User = Depends(get_current_user),
):
    try:
        return await get_user(
            user_id=user_id, session=session, current_user=current_user.id
        )
    except HTTPException as e:
        raise e

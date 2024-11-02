from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import db_helper, User
from auth import get_current_user
from .crud import save_image

router = APIRouter(tags=["images"])


@router.post("/uploadAvatar", status_code=status.HTTP_200_OK)
async def upload_avatar(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(db_helper.session_dependency),
    user: User = Depends(get_current_user),
):
    return await save_image(session=session, user=user, file=file)

from pathlib import Path

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import User

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads/avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_image(
    session: AsyncSession,
    file: UploadFile,
    user: User,
) -> User:
    extension = file.filename.split(".")[-1]
    filename = f"{user.id}_avatar_image.{extension}"
    file_location = UPLOAD_DIR / filename

    try:
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    user.profile_photo = filename
    try:
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not update user: {str(e)}")

    return user

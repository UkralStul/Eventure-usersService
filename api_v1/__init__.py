from fastapi import APIRouter
from .friendsSystem import router as friends_router

router = APIRouter()
router.include_router(router=friends_router)

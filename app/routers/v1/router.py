# app/routers/router.py
from fastapi import APIRouter
from app.routers.v1.user_auth.auth import router as auth_router
from app.routers.v1.user_auth.user import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])


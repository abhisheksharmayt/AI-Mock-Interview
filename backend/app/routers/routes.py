from fastapi import APIRouter
from app.routers.authentication import router as authentication_router
from app.routers.user import router as user_router
from app.routers.resume import router as resume_router
from app.db.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy import text
from app.services.cache import get_cache

router = APIRouter()
rest_routers = [authentication_router, user_router, resume_router]

@router.get("/health")
async def health(db: AsyncSession = Depends(get_db_session)):

    response = {
        "message": "OK",
        "database": "connected",
        "redis": "connected",
        "value": None,
    }

    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        response["database"] = "error"
        response["db_error"] = str(exc)
        response["message"] = "DEGRADED"

    try:
        response["value"] = await get_cache("test")
    except Exception as exc:
        response["redis"] = "error"
        response["redis_error"] = str(exc)
        response["message"] = "DEGRADED"

    return response

for sub_router in rest_routers:
    router.include_router(sub_router)




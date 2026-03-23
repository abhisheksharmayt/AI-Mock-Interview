from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.cache.redis_client import get_redis

app = FastAPI()


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    response = {"message": "OK", "database": "connected", "redis": "connected", "value": None}

    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        response["database"] = "error"
        response["db_error"] = str(exc)
        response["message"] = "DEGRADED"

    try:
        r = get_redis()
        response["value"] = r.get("test")
    except Exception as exc:
        response["redis"] = "error"
        response["redis_error"] = str(exc)
        response["message"] = "DEGRADED"

    return response

from app.schemas.user import UserCreate
from fastapi import FastAPI, Depends, HTTPException, Request, APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.services.cache import get_cache
from app.services.user import UserService
from app.services.authentication import AuthenticationService
from app.schemas.auth import Token, LoginPayload
from app.schemas.user import UserResponse


app = FastAPI()
router = APIRouter(prefix="/api/v1")


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


@router.post("/token")
async def login_for_access_token(
    payload: LoginPayload,
    auth_service: AuthenticationService = Depends(AuthenticationService),
):
    try:
        user = await auth_service.authenticate_user(
            payload.email, payload.password
        )
        access_token = auth_service.create_access_token(data={"email": user.email})

        return Token(access_token=access_token, token_type="bearer")

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while logging in: {e}")


@router.get("/me")
async def get_current_user(
    request: Request,
    auth_service: AuthenticationService = Depends(AuthenticationService),
):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Unauthorized")
        token = auth_header.split(" ")[1]
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user = await auth_service.get_current_user(token)
        return UserResponse(**user.model_dump())
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while getting current user: {e}"
        )

@router.post("/signup")
async def create_user(
    user: UserCreate, user_service: UserService = Depends(UserService)
):
    return await user_service.create_user(user)

app.include_router(router)

from fastapi import APIRouter
from app.services.authentication import AuthenticationService
from app.schemas.auth import LoginPayload
from app.schemas.user import UserCreate
from app.services.user import UserService
from fastapi import Depends, HTTPException
from app.schemas.auth import Token

router = APIRouter(tags=["authentication"])

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

@router.post("/signup")
async def create_user(
    user: UserCreate, user_service: UserService = Depends(UserService)
):
    return await user_service.create_user(user)
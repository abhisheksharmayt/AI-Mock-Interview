from fastapi import APIRouter, Request, Depends, HTTPException
from app.services.authentication import AuthenticationService
from app.schemas.user import UserResponse

router = APIRouter(tags=["user"])

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
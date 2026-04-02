from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me")
async def read_me(user: UserResponse = Depends(get_current_user)):
    try:
        return UserResponse(**user.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while getting current user: {e}"
        )
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.configs import configs
from app.db.database import get_db_session
from app.repositories.user import UserRepository
from app.schemas.auth import TokenData
from app.services.authentication import oauth2_scheme


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, configs.JWT_SECRET_KEY, algorithms=[configs.ALGORITHM])
        email = payload.get("email")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    logger.info(f"User retrieved successfully: {user.email}")
    return user

from app.schemas.user import UserResponse
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from app.schemas.auth import TokenData
from app.db.database import get_db_session
from app.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.configs import configs


password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthenticationService:
    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.password_hash = PasswordHash.recommended()
        self.DUMMY_HASH = self.password_hash.hash("dummypassword")
        self.user_repo = UserRepository(db)  

    def verify_password(self, plain_password, hashed_password):
        return self.password_hash.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.password_hash.hash(password)


    async def authenticate_user(self, email: str, password: str) -> UserResponse:
        try:
            user = await self.user_repo.get_user_by_email(email)
            if not user:
                logger.error(f"User not found: {email}")
                raise HTTPException(status_code=401, detail="Incorrect email or password")
            if not self.verify_password(password, user.password_hash):
                    logger.error(f"Incorrect password: {email}")
                    raise HTTPException(status_code=401, detail="Incorrect email or password")
            return user
        except Exception as e:
            logger.error(f"Error while authenticating user: {e}")
            raise Exception(f"Error while authenticating user: {e}")

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=1)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, configs.JWT_SECRET_KEY, algorithm=configs.ALGORITHM)
        return encoded_jwt

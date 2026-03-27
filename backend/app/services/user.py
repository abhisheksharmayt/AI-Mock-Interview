from app.services.authentication import AuthenticationService
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.db.database import get_db_session
from app.schemas.user import UserCreate
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse
import logging
from fastapi import HTTPException


class UserService:
    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db = db
        self.user_repo = UserRepository(db)
        self.authentication = AuthenticationService(db)

    async def create_user(self, user: UserCreate):
        try:
            logging.info(f"Creating user: {user.email}")
            password_hash = self.authentication.get_password_hash(user.password)
            logging.info(f"Password hash created")
            user = await self.user_repo.create_user(user, password_hash=password_hash, created_by=1, updated_by=1)
            logging.info(f"User created successfully: {user.email}")
            return UserResponse(user)
        except Exception as e:
            logging.error(f"Error while creating user in service: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error while creating user: {e}"
            )

    async def get_user_by_email(self, email: str):
        try:
            user = await self.user_repo.get_user_by_email(email)
            logging.info(f"User retrieved successfully: {user.email}")
            return UserResponse(user)
        except Exception as e:
            logging.error(f"Error while retrieving user in service: {e}")
            raise Exception(f"Error while retrieving user: {e}")

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.schemas.user import UserCreate, UserResponse
from app.models.users import User
from fastapi import HTTPException
from sqlalchemy import select


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: UserCreate, password_hash: str, created_by: int, updated_by: int) -> User:
        try:
            stmt = select(User).where(User.email == user.email)
            existing_user = await self.db.execute(stmt)
            if existing_user.first():
                raise Exception(f"User already exists: {user.email}")
            new_user = User(
                email=user.email,
                password_hash=password_hash,
                full_name=user.full_name,
                created_by=created_by,
                updated_by=updated_by
            )
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            logger.info(f"User created successfully: {new_user.email}")
            return new_user

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise e

    async def get_user_by_id(self, user_id: int):
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                logger.info(f"User retrieved successfully: {user.id}")
                return user
            else:
                raise Exception(f"User not found: {user_id}")

        except Exception as e:
            logger.error(f"Error retrieving user: {e}")
            raise e

    async def get_user_by_email(self, email: str) -> UserResponse:
        try:
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user
            else:
                raise Exception(f"User not found: {email}")
        except Exception as e:
            logger.error(f"Error retrieving user by email: {e}")
            raise e
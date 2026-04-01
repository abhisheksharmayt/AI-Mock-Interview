from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resume import Resume

class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    
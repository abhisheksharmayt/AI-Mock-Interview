
from backend.app.schemas.resume import ResumeUpload
from fastapi import UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from loguru import logger

class ResumeService:
    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db = db
        self.allowed_extensions = [".pdf", ".doc", ".docx"]

    async def upload_resume(self, file: UploadFile):
        try:
            logger.info(f"Uploading resume: {file.filename}")
            

            if not any(file.filename.endswith(extension) for extension in self.allowed_extensions):
                raise HTTPException(status_code=400, detail="Invalid file extension")

            file_content = await file.read();
            file_name = file.filename.split(".")[0];
            file_size = len(file_content);
            file_kind = "resume";
            parse_status = "pending";
            is_default = False;

            resume = ResumeUpload(
                file_name=file_name,
                file_size=file_size,
                file_kind=file_kind,
                parse_status=parse_status,
                is_default=is_default,
            )
            await self.resume_repo.upload_resume(resume, file_content)

        except Exception as e:
            logger.error(f"Error while uploading resume: {e}")
            raise Exception(f"Error while uploading resume: {e}")
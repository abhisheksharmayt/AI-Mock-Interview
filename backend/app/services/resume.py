from io import BytesIO

from app.utils.openai_utils import parse_resume_with_ai
from app.utils.resume_text_extracter import (
    extract_text_from_docx,
    extract_text_from_pdf,
)
from fastapi import Depends, HTTPException, UploadFile, BackgroundTasks
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import FileKind, ParseStatus
from app.core.configs import configs
from app.core.dependencies import get_current_user
from app.db.database import get_db_session, AsyncSessionLocal
from app.models.resume import Resume
from app.repositories.resume import ResumeRepository
from app.schemas.resume import (
    FileUpload,
    JobDescriptionCreate,
    JobDescriptionResponse,
    ResumeUpload,
)
from app.schemas.user import UserResponse
from app.utils.amazon_utils import AmazonUtils
from uuid import UUID


class ResumeService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db_session),
        user: UserResponse = Depends(get_current_user),
    ):
        self.user = user
        self.resume_repo = ResumeRepository(db)
        self.allowed_extensions = [".pdf", ".docx"]
        self.amazon_utils = AmazonUtils()
        self.resume_path = "resumes/"

    async def upload_resume(self, file: UploadFile, background_task: BackgroundTasks) -> Resume:
        logger.info("Uploading resume: {}", file.filename)

        if not any(file.filename.endswith(ext) for ext in self.allowed_extensions):
            raise HTTPException(status_code=400, detail="Invalid file type. Supported types: .pdf, .docx")

        file_content = await file.read()
        file_name = file.filename
        file_size = len(file_content)
        storage_key = f"{self.resume_path}{file_name}"

        resume_data = ResumeUpload(
            user_id=self.user.id,
            file_name=file_name,
            file_size=file_size,
            parse_status=ParseStatus.pending,
            is_default=False,
        )
        file_upload_data = FileUpload(
            user_id=self.user.id,
            kind=FileKind.resume,
            storage_key=storage_key,
            original_filename=file_name,
        )

        bucket = configs.S3_RESUME_BUCKET

        try:
            self.amazon_utils.upload_file_as_object(
                BytesIO(file_content), bucket, storage_key
            )
        except Exception as e:
            logger.exception("Error while uploading resume to object storage")
            raise HTTPException(
                status_code=503,
                detail="Could not store file. Please try again.",
            ) from e

        try:
            resume_record = await self.resume_repo.create_file_and_resume(
                file_upload_data,
                resume_data,
            )
            background_task.add_task(parse_resume_background, resume_record.id)
            return resume_record
        except Exception:
            try:
                self.amazon_utils.delete_object(bucket, storage_key)
            except Exception as del_err:
                logger.warning(
                    "Failed to delete orphan object storage key {}: {}",
                    storage_key,
                    del_err,
                )
            raise

    async def create_jd(self, jd_data: JobDescriptionCreate) -> JobDescriptionResponse:
        try:
            logger.info(f"Creating JD")
            jd_record = await self.resume_repo.create_jd(jd_data, user_id=self.user.id)
            logger.info(f"JD created successfully")
            return JobDescriptionResponse.model_validate(jd_record)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error while creating JD: {e}")


async def parse_resume_background(
    resume_id: UUID,
) -> None:
    async with AsyncSessionLocal() as session:
        resume_repo = ResumeRepository(session)
        amazon_utils = AmazonUtils()
        try:
            resume_record = await resume_repo.get_resume_by_id(resume_id)
            if not resume_record:
                raise Exception(f"Resume not found: {resume_id}")
            if resume_record.parse_status != ParseStatus.pending:
                raise Exception(f"Resume is not pending: {resume_id}")

            file_record = await resume_repo.get_file_by_id(resume_record.file_id)

            await resume_repo.update_resume_parse_status(resume_id, ParseStatus.processing)

            file_content = amazon_utils.download_file_as_bytes(
                key=file_record.storage_key,
                bucket_name=configs.S3_RESUME_BUCKET,
            )
            logger.info(f"Retrieved file content from S3")

            extracted_text = ""

            if resume_record.title.endswith(".pdf"):
                extracted_text = await extract_text_from_pdf(file_content)
            elif resume_record.title.endswith(".docx"):
                extracted_text = await extract_text_from_docx(file_content)
            else:
                raise Exception(f"Unsupported file type: {resume_record.title}")

            logger.info(f"Extracted text: {extracted_text}")

            parsed_resume_data = await parse_resume_with_ai(prompt=extracted_text)

            logger.info(f"Parsed resume data: {parsed_resume_data}")

            parsed_resume_record = await resume_repo.create_parsed_resume(
                resume_id=resume_id,
                full_text=extracted_text,
                parsed_resume_data=parsed_resume_data,
            )
            await resume_repo.update_resume_parse_status(resume_id, ParseStatus.completed)
            logger.info(f"Resume parsed successfully: {resume_id}")

            return parsed_resume_record

        except Exception as e:
            await resume_repo.db.rollback()
            await resume_repo.update_resume_parse_status(resume_id, ParseStatus.failed)
            logger.exception(f"Error while parsing resume {resume_id}")
            raise

from fastapi import UploadFile, File, Depends, APIRouter, HTTPException
from app.services.authentication import AuthenticationService
from app.services.resume import ResumeService
from loguru import logger


router = APIRouter(prefix="/resume", tags=["resume"])

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File,
    auth_service: AuthenticationService = Depends(AuthenticationService),
    resume_service: ResumeService = Depends(ResumeService),
):
    try:
        await resume_service.upload_resume(file)
        logger.info(f"Resume uploaded successfully")
        return {"message": "Resume uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while uploading resume: {e}")
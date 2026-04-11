from app.schemas.resume import JobDescriptionCreate
from fastapi import UploadFile, File, Depends, APIRouter, HTTPException, BackgroundTasks
from app.services.resume import ResumeService
from loguru import logger


router = APIRouter(prefix="/resume", tags=["resume"])

@router.post("/upload")
async def upload_resume(
    background_task: BackgroundTasks,
    file: UploadFile = File(),
    resume_service: ResumeService = Depends(ResumeService),
):
    try:
        logger.info(f"Uploading resume: {file.filename}")
        await resume_service.upload_resume(file, background_task)
        logger.info(f"Resume uploaded successfully")
        return {"message": "Resume uploaded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while uploading resume: {e}")

@router.post("/jd")
async def create_jd(jd_data: JobDescriptionCreate, resume_service: ResumeService = Depends(ResumeService)): 
    try:
        logger.info(f"Creating JD")
        jd_record = await resume_service.create_jd(jd_data)
        logger.info(f"JD created successfully")
        return jd_record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while creating JD: {e}")
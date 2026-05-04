from sys import prefix
from app.schemas.interview import (
    InterviewSessionCreate,
    InterviewSessionStartResponse,
)
from app.services.interveiw import InterviewService
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/start")
async def create_interview_session(
    request: InterviewSessionCreate,
    interview_service: InterviewService = Depends(InterviewService),
) -> InterviewSessionStartResponse:
    session = await interview_service.create_interview_session(request)
    return session


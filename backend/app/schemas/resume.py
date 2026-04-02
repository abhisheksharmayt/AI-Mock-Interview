from uuid import UUID
from app.common.enums import FileKind, ParseStatus
from app.schemas.base import BaseCreate, BaseResponse
from pydantic import BaseModel

class ResumeUpload(BaseModel):
    user_id: UUID
    file_name: str
    file_size: int
    parse_status: ParseStatus
    is_default: bool

class FileUpload(BaseModel):
    user_id: UUID
    kind: FileKind
    storage_key: str
    original_filename: str

class JobDescriptionCreate(BaseCreate):
    title: str
    company_name: str
    raw_text: str

class JobDescriptionResponse(BaseResponse):
    title: str
    company_name: str
    raw_text: str
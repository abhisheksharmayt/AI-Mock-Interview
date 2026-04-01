from pydantic import BaseModel

class ResumeUpload(BaseModel):
    file_name: str
    file_size: int
    file_kind: str
    parse_status: str
    is_default: bool
from enum import Enum

class FileKind(Enum):
    resume = "resume"
    job_description = "job_description"
    audio = "audio"
    report_export = "report_export"

class ParseStatus(Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
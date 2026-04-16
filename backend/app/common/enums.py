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


class InterviewStatus(Enum):
    draft = "draft"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class InterviewMode(Enum):
    voice = "voice"
    text = "text"


class InterviewerType(Enum):
    ai = "ai"
    human = "human"


class SpeakerType(Enum):
    candidate = "candidate"
    interviewer = "interviewer"
    system = "system"


class TurnKind(Enum):
    question = "question"
    answer = "answer"
    system_event = "system_event"
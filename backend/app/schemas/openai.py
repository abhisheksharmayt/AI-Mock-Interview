from pydantic import BaseModel
from typing import List, Optional


class SkillItem(BaseModel):
    name: str
    level: str


class ExperienceItem(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: str
    description: str


class EducationItem(BaseModel):
    institution: str
    degree: str
    field: str
    graduation_year: str


class ProjectItem(BaseModel):
    name: str
    description: str
    tech_stack: List[str]


class CertificationItem(BaseModel):
    name: str
    issuer: str
    year: str


class OpenAIResponse(BaseModel):
    skills_json: List[SkillItem]
    experience_json: List[ExperienceItem]
    education_json: List[EducationItem]
    projects_json: List[ProjectItem]
    certifications_json: List[CertificationItem]
    candidate_summary: str
    total_years_experience: Optional[float] = None
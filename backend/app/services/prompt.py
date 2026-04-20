from pathlib import Path

from app.common.enums import InterviewType
from app.schemas.interview import PromptContext


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PromptRenderer:
    def render(self, interview_type: InterviewType, context: PromptContext) -> str:
        template = (PROMPTS_DIR / f"{interview_type.value}.txt").read_text(encoding="utf-8")

        values = context.model_dump()
        values["key_skills"] = ", ".join(values["key_skills"])

        for key, value in values.items():
            template = template.replace("{{" + key + "}}", str(value))

        if "{{" in template:
            raise ValueError(f"Unfilled placeholders remain in prompt:\n{template}")

        return template 
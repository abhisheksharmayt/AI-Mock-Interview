from app.schemas.openai import OpenAIResponse
from openai import OpenAI
from app.core.configs import configs
from loguru import logger


client = OpenAI(
    api_key=configs.OPENAI_API_KEY,
)

json_generator_prompt = """
You are a resume parser. Extract structured information from the given resume text.

Return ONLY a valid JSON object (no explanation, no extra text).

Follow this exact schema:

{
  "skills_json": [
    { "name": string, "level": string }
  ],
  "experience_json": [
    {
      "company": string,
      "title": string,
      "start_date": string,
      "end_date": string,
      "description": string
    }
  ],
  "education_json": [
    {
      "institution": string,
      "degree": string,
      "field": string,
      "graduation_year": string
    }
  ],
  "projects_json": [
    {
      "name": string,
      "description": string,
      "tech_stack": [string]
    }
  ],
  "certifications_json": [
    {
      "name": string,
      "issuer": string,
      "year": string
    }
  ],
  "candidate_summary": string,
  "total_years_experience": number or null
}

STRICT INSTRUCTIONS:

- DO NOT summarize under any condition.
- DO NOT rewrite, paraphrase, or shorten content.
- COPY the original text for experience and project descriptions as closely as possible.
- Preserve ALL bullet points, responsibilities, achievements, and metrics.
- If multiple bullet points exist:
  - Join them using " | " as separator
  - Keep wording unchanged

- Do NOT remove repeated words or “clean up” sentences.
- Do NOT optimize grammar.
- Do NOT compress information.

- Extract text EXACTLY as written in the resume wherever possible.

- If formatting exists (bullets, line breaks), convert into a single string while preserving full content.

- Skills:
  - Extract all skills explicitly mentioned
  - Infer level only if strongly implied

- Dates:
  - Normalize into "MMM YYYY" or "YYYY" ONLY if clearly available
  - Otherwise keep original

- If any section is missing → return empty array or null

FINAL RULE:
Output MUST be a JSON object and NOTHING else.
If you summarize or omit details, the output is considered incorrect.
"""


def parse_resume_with_ai(prompt: str) -> OpenAIResponse:
    try:
        logger.info(f"Invoking OpenAI API to parse resume with AI")
        response = client.responses.parse(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": json_generator_prompt},
                {"role": "user", "content": prompt},
            ],
            text_format=OpenAIResponse,
        )
        logger.info(f"OpenAI Response: {response}")
        return OpenAIResponse.model_validate_json(response.output_text)
    except Exception:
        logger.exception("Error while parsing resume with AI")
        raise


def generate_interview_question(prompt: str, turns: list[dict]) -> str:
    try:
        logger.info(f"Generating interview question with AI")
        response = client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": prompt},
                *turns,
            ],
        )
        output_text = (response.output_text or "").strip()
        if not output_text:
            raise ValueError("OpenAI returned empty interview question")
        logger.info("Interview question generated")
        return output_text
    except Exception:
        logger.exception("Error while generating interview question")
        raise
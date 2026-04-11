from io import BytesIO
from lxml import etree
import docx
import pdfplumber


WPML = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _para_text(p_element) -> str:
    """Get concatenated text of all <w:t> runs inside a <w:p>."""
    return "".join(
        node.text
        for node in p_element.iter(f"{{{WPML}}}t")
        if node.text
    ).strip()


async def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(BytesIO(file_bytes))
    seen = set()
    chunks = []

    for p in doc.element.body.iter(f"{{{WPML}}}p"):
        text = _para_text(p)
        if text and text not in seen:
            seen.add(text)
            chunks.append(text)

    for section in doc.sections:
        for area in (section.header, section.footer):
            for p in area.paragraphs:
                text = p.text.strip()
                if text and text not in seen:
                    seen.add(text)
                    chunks.append(text)

    return "\n".join(chunks)


async def extract_text_from_pdf(file_bytes: bytes) -> str:
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        parts = []
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(part for part in parts if part).strip()
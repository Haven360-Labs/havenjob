"""Extract raw text from uploaded CV files (PDF, DOCX)."""

from typing import BinaryIO


def extract_text_from_pdf(file: BinaryIO) -> str | None:
    """Extract text from a PDF file. Returns None on failure."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(file)
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n\n".join(parts).strip() or None
    except Exception:
        return None


def extract_text_from_docx(file: BinaryIO) -> str | None:
    """Extract text from a DOCX file. Returns None on failure."""
    try:
        from docx import Document

        doc = Document(file)
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(parts).strip() or None
    except Exception:
        return None


def extract_cv_text(content_type: str, file: BinaryIO) -> str | None:
    """
    Extract raw text from an uploaded CV (PDF or DOCX).
    Returns extracted text or None if unsupported type or extraction fails.
    """
    if content_type == "application/pdf":
        return extract_text_from_pdf(file)
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file)
    return None

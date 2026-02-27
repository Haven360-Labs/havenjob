"""Basic extraction of company, job title, and date from email subject/body (regex)."""

import re
from datetime import datetime
from typing import Any


def extract_job_info(subject: str = "", body: str = "") -> dict[str, Any]:
    """
    Extract company name, job title, and date from email subject and body.
    Returns dict with company_name, job_title, date_applied (None when not found).
    Uses basic regex; EML-04 or later can enhance with LLM.
    """
    text = f"{subject}\n{body}".strip()
    company_name = _extract_company(text)
    job_title = _extract_job_title(text)
    date_applied = _extract_date(text)
    return {
        "company_name": company_name,
        "job_title": job_title,
        "date_applied": date_applied.isoformat() if date_applied else None,
    }


def _extract_company(text: str) -> str | None:
    """Try common patterns: 'at Company', 'Company -', 'company: Company'."""
    if not text:
        return None
    patterns = [
        r"\bat\s+([A-Z][A-Za-z0-9\s&.,\-]+?)(?:\s*[-–—]|\s+for\s|\.|\n|$)",
        r"(?:company|employer)\s*[:\-]\s*([A-Za-z0-9\s&.,\-]+?)(?:\n|$)",
        r"([A-Z][A-Za-z0-9\s&.,\-]+?)\s*[-–—]\s*(?:application|position|role)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) >= 2 and len(candidate) <= 200:
                return candidate
    return None


def _extract_job_title(text: str) -> str | None:
    """Try common patterns: 'position: X', 'role: X', 'job title: X', 'Applied for X'."""
    if not text:
        return None
    patterns = [
        r"(?:position|role|job\s*title|title)\s*[:\-]\s*([A-Za-z0-9\s&.,\-/]+?)(?:\n|$)",
        r"applied\s+for\s+([A-Za-z0-9\s&.,\-/]+?)(?:\s+at|\n|$)",
        r"([A-Za-z0-9\s&.,\-/]+?)\s*[-–—]\s*(?:application|position)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) >= 2 and len(candidate) <= 255:
                return candidate
    return None


def _extract_date(text: str) -> datetime | None:
    """Try ISO date, then 'Jan 15, 2025', '15/01/2025', '2025-01-15'."""
    if not text:
        return None
    # ISO-like
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    # DD/MM/YYYY or MM/DD/YYYY
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        for mo, d in ((a, b), (b, a)):
            if 1 <= mo <= 12 and 1 <= d <= 31:
                try:
                    return datetime(y, mo, d)
                except ValueError:
                    continue
    # Month DD, YYYY
    months = "jan feb mar apr may jun jul aug sep oct nov dec"
    for i, mon in enumerate(months.split(), 1):
        pat = rf"\b{mon}[a-z]*\s+(\d{{1,2}}),?\s+(\d{{4}})\b"
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return datetime(int(m.group(2)), i, int(m.group(1)))
            except ValueError:
                pass
    return None

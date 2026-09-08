"""Bounded parsing for untrusted text and text-bearing PDF uploads."""

import hashlib
import io
import re

from aos_api.errors import ApiError

MAX_BYTES = 1_000_000
MAX_PDF_PAGES = 50
MAX_TEXT_CHARS = 20_000
TEXT_MIME = "text/plain"
PDF_MIME = "application/pdf"
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def parse_document(filename: str, media_type: str | None, content: bytes) -> tuple[str, str, str]:
    if not filename or len(filename) > 255 or not content:
        raise ApiError(422, "DOCUMENT_INVALID", "Upload a non-empty text or PDF document.")
    if len(content) > MAX_BYTES:
        raise ApiError(413, "DOCUMENT_TOO_LARGE", "Document exceeds the 1 MB upload limit.")
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    declared = (media_type or "").lower()
    if suffix == "txt" and declared in {"", TEXT_MIME}:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise ApiError(415, "DOCUMENT_UNSUPPORTED", "Text documents must use UTF-8.") from None
        normalized_type = TEXT_MIME
    elif suffix == "pdf" and declared in {"", PDF_MIME} and content.startswith(b"%PDF-"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content), strict=True)
            if reader.is_encrypted or len(reader.pages) > MAX_PDF_PAGES:
                raise ValueError
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            raise ApiError(
                422, "DOCUMENT_INVALID", "PDF must be readable, unencrypted, and under 50 pages."
            ) from None
        normalized_type = PDF_MIME
    else:
        raise ApiError(
            415, "DOCUMENT_UNSUPPORTED", "Only UTF-8 text and PDF documents are accepted."
        )
    text = _CONTROL.sub("", text).strip()
    if not text:
        raise ApiError(422, "DOCUMENT_INVALID", "The document did not contain readable text.")
    return normalized_type, text[:MAX_TEXT_CHARS], hashlib.sha256(content).hexdigest()

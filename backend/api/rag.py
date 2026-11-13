import re
from pathlib import Path

from docx.opc.exceptions import PackageNotFoundError
from pypdf.errors import PdfReadError, PdfStreamError


class DocumentRetrievalError(Exception):
    """Raised when document text cannot be extracted."""


def _read_document_text(document):
    if not document.file:
        return ""

    suffix = Path(document.original_filename).suffix.lower()
    try:
        document.file.open("rb")
        if suffix == ".pdf":
            from pypdf import PdfReader

            return "\n".join(page.extract_text() or "" for page in PdfReader(document.file).pages)
        if suffix == ".docx":
            from docx import Document as WordDocument

            return "\n".join(paragraph.text for paragraph in WordDocument(document.file).paragraphs)
    except (OSError, ValueError, PackageNotFoundError, PdfReadError, PdfStreamError):
        return ""
    finally:
        document.file.close()
    return ""


def _chunk_text(text, max_chars=1800):
    paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
    chunks = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n{paragraph}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _tokens(text):
    return set(re.findall(r"[^\W_]{3,}", text.lower(), flags=re.UNICODE))


def retrieve_relevant_chunks(chunks, query="", limit=6):
    query_tokens = _tokens(query)
    ranked = sorted(
        enumerate(chunks),
        key=lambda item: (-len(query_tokens & _tokens(item[1])), item[0]),
    )
    return [chunk for _, chunk in ranked[:limit]]


def document_context(document, query="", limit=6):
    chunks = _chunk_text(_read_document_text(document))
    if chunks:
        return "\n\n".join(retrieve_relevant_chunks(chunks, query, limit))
    return (
        f"Dokumento paaiškinimas: {document.simplified_explanation or 'Nėra.'}\n"
        f"Pagrindinės sąlygos: {document.key_conditions or 'Nėra.'}"
    )

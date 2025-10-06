import hashlib
import io
import logging
import mimetypes
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from antgent.clients import s3_client
from antgent.core.text import extract_text_from_bytes
from antgent.models.message import Content
from antgent.utils.pdf import text_to_pdf

logger = logging.getLogger(__name__)


def _process_docx_file(file_bytes: bytes, filename: str) -> tuple[bytes, str, str, io.BytesIO]:
    """Process DOCX file: extract text, convert to PDF."""
    text = extract_text_from_bytes(file_bytes, filename)
    content = text_to_pdf(text)
    new_name = Path(filename).with_suffix(".pdf").name
    return content, new_name, "application/pdf", io.BytesIO(content)


def _process_other_file(
    file_bytes: bytes, filename: str, content_type: str | None, ufile
) -> tuple[bytes, str, str, Any]:
    """Process non-DOCX files."""
    mime = content_type
    if not mime or mime == "application/octet-stream":
        guessed_mime, _ = mimetypes.guess_type(filename)
        if guessed_mime:
            mime = guessed_mime
    mime = mime or "application/octet-stream"
    return file_bytes, filename, mime, ufile.file


def _build_dest_path(s3_prefix: str, year_month: str, filename: str, content_hash: str) -> str:
    """Build S3 destination path."""
    p = Path(filename)
    unique_folder = f"{p.name}-{content_hash}"
    return f"{s3_prefix}{year_month}/{unique_folder}/{p.name}"


async def _process_and_upload_file(ufile: UploadFile, s3, year_month: str) -> Content:
    """Process a single file and upload to S3."""
    file_bytes = await ufile.read()
    await ufile.seek(0)

    filename = ufile.filename
    if not filename:
        filename = "unknown_file"

    if filename.lower().endswith(".docx"):
        content, new_name, mime, file_io = _process_docx_file(file_bytes, filename)
    else:
        content, new_name, mime, file_io = _process_other_file(file_bytes, filename, ufile.content_type, ufile)

    file_hash = hashlib.sha256(content).hexdigest()[:8]
    dest_path = _build_dest_path(s3.prefix, year_month, new_name, file_hash)
    s3_dest = await s3.upload_file_async(file_io, dest=dest_path)
    return Content(mode="url", content=s3_dest.url, mime=mime, title=new_name)


async def _process_and_upload_text(text: str, s3, year_month: str) -> Content:
    """Process a single text and upload to S3."""
    text_bytes = text.encode("utf-8")
    filename = f"text-input-{uuid.uuid4().hex}.txt"
    text_hash = hashlib.sha256(text_bytes).hexdigest()[:8]
    dest_path = _build_dest_path(s3.prefix, year_month, filename, text_hash)
    s3_dest = await s3.upload_file_async(io.BytesIO(text_bytes), dest=dest_path)
    return Content(mode="url", content=s3_dest.url, mime="text/plain", title=filename)


async def prep_contents(
    texts: list[str] | None, files: list[UploadFile | None] | list[UploadFile] | None
) -> list[Content]:
    """Prepares text and file uploads into a list of Content objects, uploading files to S3."""
    documents = []
    s3 = s3_client()
    year_month = datetime.now().strftime("%Y-%m")

    for ufile in files or []:
        if ufile and ufile.filename:
            documents.append(await _process_and_upload_file(ufile, s3, year_month))

    for text in texts or []:
        if text:
            documents.append(await _process_and_upload_text(text, s3, year_month))

    return documents

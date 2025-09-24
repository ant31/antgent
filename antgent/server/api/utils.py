import hashlib
import io
import logging
import mimetypes
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from antgent.clients import s3_client
from antgent.config import config
from antgent.models.message import Content
from antgent.utils.doc import extract_text_from_bytes
from antgent.utils.pdf import text_to_pdf

logger = logging.getLogger(__name__)


def get_workflow_queue() -> str:
    """
    Get the appropriate task queue for workflows.

    It finds the first worker with workflows defined in its configuration.
    If no worker has workflows, it falls back to the first worker's queue.
    """
    for worker in config().temporalio.workers:
        if worker.workflows:
            return worker.queue

    if not config().temporalio.workers:
        raise ValueError("No temporal workers configured.")

    logger.warning("No worker with workflows configured. Falling back to first worker's queue.")
    return config().temporalio.workers[0].queue


async def prep_contents(
    texts: list[str] | None, files: list[UploadFile | None] | list[UploadFile] | None
) -> list[Content]:
    """Prepares text and file uploads into a list of Content objects, uploading files to S3."""
    documents = []
    texts = texts or []
    files = files or []
    s3 = s3_client()
    now = datetime.now()
    year_month = now.strftime("%Y-%m")

    for ufile in files:
        if ufile and ufile.filename:
            file_bytes = await ufile.read()
            await ufile.seek(0)

            if ufile.filename.lower().endswith(".docx"):
                text = extract_text_from_bytes(file_bytes, ufile.filename)
                content_to_upload = text_to_pdf(text)
                new_filename = Path(ufile.filename).with_suffix(".pdf").name
                mime = "application/pdf"
                file_to_upload = io.BytesIO(content_to_upload)
            else:
                content_to_upload = file_bytes
                new_filename = ufile.filename
                mime = ufile.content_type
                if not mime or mime == "application/octet-stream":
                    guessed_mime, _ = mimetypes.guess_type(new_filename)
                    if guessed_mime:
                        mime = guessed_mime
                mime = mime or "application/octet-stream"
                file_to_upload = ufile.file

            file_hash = hashlib.sha256(content_to_upload).hexdigest()[:8]
            p = Path(new_filename)
            unique_folder = f"{p.name}-{file_hash}"
            dest_path = f"{s3.prefix}{year_month}/{unique_folder}/{p.name}"

            s3_dest = s3.upload_file(file_to_upload, dest=dest_path)
            documents.append(Content(mode="url", content=s3_dest.url, mime=mime, title=new_filename))

    for text in texts:
        if text:
            text_bytes = text.encode("utf-8")
            text_io = io.BytesIO(text_bytes)

            filename = f"text-input-{uuid.uuid4().hex}.txt"

            text_hash = hashlib.sha256(text_bytes).hexdigest()[:8]
            unique_folder = f"{filename}-{text_hash}"
            dest_path = f"{s3.prefix}{year_month}/{unique_folder}/{filename}"

            s3_dest = s3.upload_file(text_io, dest=dest_path)
            documents.append(Content(mode="url", content=s3_dest.url, mime="text/plain", title=filename))

    return documents

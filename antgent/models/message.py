import base64
import io
from typing import Literal
from urllib.parse import urlparse

from agents import (
    TResponseInputItem,
)
from openai.types.responses import EasyInputMessageParam
from openai.types.responses.response_input_file_param import ResponseInputFileParam
from pydantic import BaseModel, Field

from antgent.core.text import extract_text_from_bytes


class Content(BaseModel):
    mode: Literal["bytes", "string", "b64", "url"] = Field(
        default="string",
        description=(
            "Mode of the content: 'bytes' for binary data, 'string' for text, "
            "'b64' for base64 encoded data, 'url' for a URL to the content"
        ),
    )
    mime: str = Field(default="", description="MIME type of the content, e.g., 'application/pdf' for PDF files")
    content: str | bytes = Field(..., description="Content of the document as a string, bytes or URL")
    title: str = Field(default="", description="Title of the document")

    async def _process_url_content(self, content_url: str) -> tuple[str | bytes, str, str]:
        """Process URL content by downloading and converting if needed.

        Returns: (processed_content, mode, mime_type)
        """
        from antgent.clients import filedl_client  # noqa: PLC0415

        dl_client = filedl_client()
        output = io.BytesIO()

        parsed_url = urlparse(content_url)
        if parsed_url.scheme == "s3":
            file_info = await dl_client.download_s3(source=content_url, output=output)
        else:
            file_info = await dl_client.download(content_url, output=output)

        output.seek(0)
        file_bytes = output.read()

        if file_info.filename:
            self.title = self.title or file_info.filename

        mime_type = self.mime
        if mime_type in (
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ) or (self.title and self.title.endswith((".txt", ".docx"))):
            content = extract_text_from_bytes(file_bytes, self.title)
            mode = "string"
        else:
            content = file_bytes
            mode = "bytes"
            if file_info.metadata and "content-type" in file_info.metadata:
                mime_type = file_info.metadata["content-type"]

        return content, mode, mime_type

    async def to_messages(
        self, role: Literal["user", "assistant", "developer", "system"] = "user", with_title: bool = True
    ) -> list[TResponseInputItem]:
        res = []
        content_to_process = self.content
        mime_type = self.mime
        mode = self.mode

        if mode == "url" and isinstance(content_to_process, str):
            content_to_process, mode, mime_type = await self._process_url_content(content_to_process)

        # Add title message after URL processing (title may be set from filename)
        if not self.title:
            self.title = "input_file"
        if with_title and self.title:
            res.insert(0, EasyInputMessageParam(role=role, content=f"## {self.title}:\n"))

        if mode == "string":
            res.append(EasyInputMessageParam(role=role, content=str(content_to_process) + "\n"))
        else:
            content_b64 = ""
            if mode == "bytes" and isinstance(content_to_process, bytes):
                content_b64 = base64.b64encode(content_to_process).decode("utf-8")
            elif mode == "b64" and isinstance(content_to_process, str):
                content_b64 = content_to_process

            res.append(
                EasyInputMessageParam(
                    role=role,
                    content=[
                        ResponseInputFileParam(
                            type="input_file", file_data=f"data:{mime_type};base64,{content_b64}", filename=self.title
                        )
                    ],
                )
            )
        return res

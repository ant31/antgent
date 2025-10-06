import io

import docx


def extract_text_from_bytes(content: bytes, filename: str) -> str:
    """Extract text from bytes, supporting docx and plain text."""
    if filename.endswith(".docx"):
        document = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in document.paragraphs)
    # For other types like text/plain, just decode bytes
    return content.decode("utf-8")

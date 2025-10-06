import mimetypes
from pathlib import Path

from antgent.core.text import extract_text_from_bytes
from antgent.models.message import Content

# Comprehensive MIME type mappings for common file extensions
MIME_TYPE_MAP = {
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".odp": "application/vnd.oasis.opendocument.presentation",
    # Text formats
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".xml": "application/xml",
    ".html": "text/html",
    ".htm": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".ts": "application/typescript",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
    ".toml": "application/toml",
    ".ini": "text/plain",
    ".cfg": "text/plain",
    ".conf": "text/plain",
    ".log": "text/plain",
    # Images
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    # Audio
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    # Video
    ".mp4": "video/mp4",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".wmv": "video/x-ms-wmv",
    ".flv": "video/x-flv",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    # Archives
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".bz2": "application/x-bzip2",
    ".7z": "application/x-7z-compressed",
    ".rar": "application/vnd.rar",
    # Programming
    ".py": "text/x-python",
    ".java": "text/x-java-source",
    ".c": "text/x-c",
    ".cpp": "text/x-c++",
    ".h": "text/x-c",
    ".hpp": "text/x-c++",
    ".rs": "text/x-rust",
    ".go": "text/x-go",
    ".rb": "text/x-ruby",
    ".php": "text/x-php",
    ".sh": "application/x-sh",
    ".bat": "application/x-bat",
    ".ps1": "application/x-powershell",
}


def load_file_to_content(file_path: str | Path, title: str | None = None) -> Content:
    """
    Load a file from the filesystem and convert it to a Content object.

    This utility reads a local file, detects its MIME type, and creates a Content
    object that can be easily converted to messages for agent input.

    Text files (.txt, .md, .csv, .json, .yaml) are loaded as strings.
    DOCX files are converted to plain text by extracting their content.
    Other files (PDFs, images, etc.) are loaded as bytes.

    Args:
        file_path: Path to the file to load (can be string or Path object)
        title: Optional title for the content. If not provided, uses the filename.

    Returns:
        Content object ready to be converted to messages via .to_messages()

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the path is not a file

    Example:
        >>> # Load a PDF file
        >>> content = load_file_to_content("document.pdf")
        >>> messages = await content.to_messages()
        >>>
        >>> # Load a text file with custom title
        >>> content = load_file_to_content("notes.txt", title="Meeting Notes")
        >>> messages = await content.to_messages(role="user")
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Read file content
    file_bytes = path.read_bytes()

    # Get filename for title
    filename = title or path.name

    # Get MIME type from explicit mapping first, then fall back to mimetypes
    suffix = path.suffix.lower()
    mime_type = MIME_TYPE_MAP.get(suffix)

    if not mime_type:
        # Fall back to mimetypes library
        mime_type, _ = mimetypes.guess_type(str(path))

    # Final fallback
    mime_type = mime_type or "application/octet-stream"

    # Handle text files specially - decode to string
    if mime_type.startswith("text/") or path.suffix.lower() in [".txt", ".md", ".csv", ".json", ".yaml", ".yml"]:
        try:
            text_content = file_bytes.decode("utf-8")
            return Content(mode="string", mime=mime_type, content=text_content, title=filename)
        except UnicodeDecodeError:
            # If decoding fails, treat as binary
            pass

    # Handle docx - extract text content
    if path.suffix.lower() == ".docx":
        text_content = extract_text_from_bytes(file_bytes, filename)
        return Content(mode="string", mime="text/plain", content=text_content, title=filename)

    # For binary files (PDFs, images, etc.), use bytes mode
    return Content(mode="bytes", mime=mime_type, content=file_bytes, title=filename)

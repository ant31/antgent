import base64
import logging
import pathlib
import tempfile
from typing import Literal

from fpdf import FPDF  # type: ignore
from openai.types.responses import EasyInputMessageParam, ResponseInputFileParam

logger = logging.getLogger(__name__)
logging.getLogger("fontTools.subset").level = logging.WARN


def text_to_pdf(text: str) -> bytes:
    """
    Converts a string of text (plain or Markdown) to a PDF.

    Args:
        text: The input text.
        is_markdown: Whether to interpret the text as Markdown.

    Returns:
        The PDF content as bytes.
    """
    pdf = FPDF()
    pdf.add_page()

    font_path = pathlib.Path(__file__).parent.parent.resolve().joinpath("files/DejaVuSans.ttf")
    pdf.add_font("dejavu-sans", style="", fname=str(font_path))
    pdf.set_font(family="dejavu-sans", style="", size=8)

    pdf.multi_cell(w=0, h=5, text=text)

    return bytes(pdf.output())


def text_to_pdf_message(
    text: str, role: Literal["user", "assistant", "developer", "system"] = "user", filename: str = ""
) -> EasyInputMessageParam:
    """
    Converts a string of text (plain or Markdown) to a PDF and wraps it in an EasyInputMessageParam.

    Args:
        text: The input text.
        is_markdown: Whether to interpret the text as Markdown.
        role: The role of the message (user, assistant, developer, system).
    Returns:
        An EasyInputMessageParam containing the PDF as a base64-encoded input file.
    """

    byte_content = text_to_pdf(text)
    content_b64 = base64.b64encode(byte_content).decode("utf-8")
    if not filename:
        filename = "file.pdf"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, delete_on_close=False) as temp_file:
        temp_file.write(byte_content)
        logger.info("PDF file created at %s", temp_file.name)
    return EasyInputMessageParam(
        role=role,
        content=[
            ResponseInputFileParam(
                type="input_file", file_data=f"data:application/pdf;base64,{content_b64}", filename=filename
            )
        ],
    )

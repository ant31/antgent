import io
from typing import Any

from docx import Document
from htmldocx import HtmlToDocx
from markdown_it import MarkdownIt


def markdown_to_docx_bytes(
    main_content_md: str,
    metadata_sections: dict[str, str] | None = None,
    tables: dict[str, list[dict[str, Any]]] | None = None,
    main_content_title: str = "Content",
    metadata_title: str = "Details",
) -> bytes:
    """
    Converts markdown text, metadata, and tables into a DOCX file as bytes.

    Args:
        main_content_md: The main content in Markdown format.
        metadata_sections: A dictionary where keys are titles for metadata sections
                           and values are their string content.
        tables: A dictionary where keys are titles for tables and values are a
                list of dictionaries representing rows.
        main_content_title: The main title for the markdown content section.
        metadata_title: The main title for the metadata/tables page.

    Returns:
        The generated DOCX file as bytes.
    """
    document = Document()

    if metadata_sections or tables:
        document.add_heading(metadata_title, level=1)

        if metadata_sections:
            for title, content in metadata_sections.items():
                document.add_heading(title, level=2)
                document.add_paragraph(content)

        if tables:
            for title, table_data in tables.items():
                if not table_data:
                    continue
                document.add_heading(title, level=2)

                headers = list(table_data[0].keys())
                table = document.add_table(rows=1, cols=len(headers))
                table.style = "Table Grid"

                hdr_cells = table.rows[0].cells
                for i, header in enumerate(headers):
                    cell = hdr_cells[i]
                    cell.text = header
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.bold = True

                for row_data in table_data:
                    row_cells = table.add_row().cells
                    for i, header in enumerate(headers):
                        cell_value = row_data.get(header, "")
                        row_cells[i].text = str(cell_value)

        document.add_page_break()

    document.add_heading(main_content_title, level=1)

    md = MarkdownIt()
    html_content = md.render(main_content_md)

    parser = HtmlToDocx()
    parser.add_html_to_document(html_content, document)

    doc_io = io.BytesIO()
    document.save(doc_io)
    doc_io.seek(0)
    return doc_io.getvalue()

# Generating Reports (PDF/DOCX)

Some workflows need to generate downloadable reports, such as PDFs or DOCX files, from the results of an agent's analysis. This guide covers the patterns and utilities we use for creating these reports.

## PDF Report Generation

For generating PDF reports, we use the [`fpdf2`](https://pyfpdf.github.io/fpdf2/) library, which provides a flexible way to programmatically create PDF documents.

A utility for this is located in `antgent/utils/pdf.py`.

### Core Logic

The `text_to_pdf` function takes a string of text and converts it into a PDF, returning the raw `bytes`. It handles basic text and layout, and includes font support for broader character sets.

### Integration into a Workflow

Report generation logic is typically wrapped in a Temporal **Activity**. This is because it can be a computationally intensive operation. The activity can then take the data from a workflow, generate the PDF bytes, upload it to a service like S3, and return a URL.

## DOCX Report Generation

For generating DOCX files, especially from structured markdown content, we use the `python-docx` and `htmldocx` libraries. This is particularly useful for converting agent-generated markdown into a formal document.

The utility function is located in `antgent/utils/reporting.py`.

### Core Logic

The `markdown_to_docx_bytes` function takes markdown content, optional metadata, and tables, and performs these steps:
1.  Creates a new DOCX `Document`.
2.  Adds metadata and tables to the first page, if provided.
3.  Adds a page break.
4.  Converts the main markdown content to HTML using `markdown-it-py`.
5.  Uses `HtmlToDocx` to parse the HTML and add it to the DOCX `Document`.
6.  Saves the document to an in-memory byte buffer and returns the bytes.

This approach allows us to leverage the simplicity of Markdown for the LLM's output while still being able to produce a professionally formatted DOCX file. The integration into a workflow follows the same pattern as PDF generation: wrap the logic in an activity that generates the file and uploads it to S3.

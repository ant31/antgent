import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from antgent.server.api.utils import prep_contents


@pytest.mark.asyncio
class TestPrepContents:
    """Tests for prep_contents() with async S3 operations."""

    @patch("antgent.services.s3_uploader.s3_client")
    async def test_prep_contents_with_text(self, mock_s3_client):
        """Test preparing text content uploads to S3."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.prefix = "uploads/"
        mock_s3_client.return_value = mock_s3

        # Mock the async upload
        mock_s3_dest = MagicMock()
        mock_s3_dest.url = "s3://bucket/uploads/2025-10/text-input-abc123/text-input-abc123.txt"
        mock_s3.upload_file_async = AsyncMock(return_value=mock_s3_dest)

        # Prepare text content
        texts = ["This is test content"]
        with patch("antgent.services.s3_uploader.uuid") as mock_uuid:
            mock_uuid.uuid4.return_value.hex = "abc123"
            with patch("antgent.services.s3_uploader.datetime") as mock_datetime:
                mock_now = MagicMock()
                mock_now.strftime.return_value = "2025-10"
                mock_datetime.now.return_value = mock_now

                results = await prep_contents(texts=texts, files=None)

        # Verify async upload was called
        mock_s3.upload_file_async.assert_awaited_once()
        call_args = mock_s3.upload_file_async.call_args

        # Check that the first argument is a BytesIO object
        assert isinstance(call_args[0][0], io.BytesIO)

        # Check the destination path
        assert "2025-10" in call_args[1]["dest"]
        assert "text-input-abc123" in call_args[1]["dest"]

        # Verify results
        assert len(results) == 1
        assert results[0].mode == "url"
        assert results[0].content == mock_s3_dest.url
        assert results[0].mime == "text/plain"

    @patch("antgent.services.s3_uploader.s3_client")
    async def test_prep_contents_with_pdf_file(self, mock_s3_client):
        """Test preparing PDF file uploads to S3."""
        mock_s3 = MagicMock()
        mock_s3.prefix = "uploads/"
        mock_s3_client.return_value = mock_s3

        mock_s3_dest = MagicMock()
        mock_s3_dest.url = "s3://bucket/uploads/2025-10/test.pdf-hash123/test.pdf"
        mock_s3.upload_file_async = AsyncMock(return_value=mock_s3_dest)

        # Create a mock PDF file upload
        pdf_content = b"%PDF-1.4 fake pdf content"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=pdf_content)
        mock_file.seek = AsyncMock()
        mock_file.file = io.BytesIO(pdf_content)

        with patch("antgent.services.s3_uploader.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.strftime.return_value = "2025-10"
            mock_datetime.now.return_value = mock_now

            results = await prep_contents(texts=None, files=[mock_file])

        # Verify async upload was called
        mock_s3.upload_file_async.assert_awaited_once()

        # Verify results
        assert len(results) == 1
        assert results[0].mode == "url"
        assert results[0].content == mock_s3_dest.url
        assert results[0].mime == "application/pdf"
        assert results[0].title == "test.pdf"

    @patch("antgent.services.s3_uploader.s3_client")
    @patch("antgent.services.s3_uploader.extract_text_from_bytes")
    @patch("antgent.services.s3_uploader.text_to_pdf")
    async def test_prep_contents_with_docx_file(self, mock_text_to_pdf, mock_extract_text, mock_s3_client):
        """Test preparing DOCX file (converted to PDF) uploads to S3."""
        mock_s3 = MagicMock()
        mock_s3.prefix = "uploads/"
        mock_s3_client.return_value = mock_s3

        mock_s3_dest = MagicMock()
        mock_s3_dest.url = "s3://bucket/uploads/2025-10/document.pdf-hash456/document.pdf"
        mock_s3.upload_file_async = AsyncMock(return_value=mock_s3_dest)

        # Mock text extraction and PDF conversion
        mock_extract_text.return_value = "Extracted text from DOCX"
        mock_text_to_pdf.return_value = b"%PDF-1.4 converted pdf"

        # Create a mock DOCX file upload
        docx_content = b"fake docx binary content"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "document.docx"
        mock_file.content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        mock_file.read = AsyncMock(return_value=docx_content)
        mock_file.seek = AsyncMock()
        mock_file.file = io.BytesIO(docx_content)

        with patch("antgent.services.s3_uploader.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.strftime.return_value = "2025-10"
            mock_datetime.now.return_value = mock_now

            results = await prep_contents(texts=None, files=[mock_file])

        # Verify text extraction and PDF conversion happened
        mock_extract_text.assert_called_once_with(docx_content, "document.docx")
        mock_text_to_pdf.assert_called_once_with("Extracted text from DOCX")

        # Verify async upload was called
        mock_s3.upload_file_async.assert_awaited_once()

        # Verify results show PDF conversion
        assert len(results) == 1
        assert results[0].mime == "application/pdf"
        assert results[0].title == "document.pdf"  # Extension changed to .pdf

    @patch("antgent.services.s3_uploader.s3_client")
    async def test_prep_contents_with_multiple_files_and_texts(self, mock_s3_client):
        """Test preparing multiple texts and files."""
        mock_s3 = MagicMock()
        mock_s3.prefix = "uploads/"
        mock_s3_client.return_value = mock_s3

        # Mock different S3 destinations for each upload
        upload_count = [0]

        async def mock_upload_side_effect(*args, **kwargs):
            upload_count[0] += 1
            mock_dest = MagicMock()
            mock_dest.url = f"s3://bucket/uploads/file-{upload_count[0]}"
            return mock_dest

        mock_s3.upload_file_async = AsyncMock(side_effect=mock_upload_side_effect)

        # Prepare multiple texts and files
        texts = ["Text 1", "Text 2"]
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"pdf content")
        mock_file.seek = AsyncMock()
        mock_file.file = io.BytesIO(b"pdf content")

        with patch("antgent.services.s3_uploader.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.strftime.return_value = "2025-10"
            mock_datetime.now.return_value = mock_now

            results = await prep_contents(texts=texts, files=[mock_file])

        # Should have uploaded 1 file + 2 texts = 3 uploads
        assert mock_s3.upload_file_async.await_count == 3
        assert len(results) == 3

    @patch("antgent.services.s3_uploader.s3_client")
    async def test_prep_contents_empty_inputs(self, mock_s3_client):
        """Test with empty or None inputs."""
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        results = await prep_contents(texts=None, files=None)
        assert len(results) == 0

        results = await prep_contents(texts=[], files=[])
        assert len(results) == 0

    @patch("antgent.services.s3_uploader.s3_client")
    async def test_prep_contents_filters_none_files(self, mock_s3_client):
        """Test that None entries in files list are filtered out."""
        mock_s3 = MagicMock()
        mock_s3.prefix = "uploads/"
        mock_s3_client.return_value = mock_s3

        mock_s3_dest = MagicMock()
        mock_s3_dest.url = "s3://bucket/uploads/test.pdf"
        mock_s3.upload_file_async = AsyncMock(return_value=mock_s3_dest)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"pdf")
        mock_file.seek = AsyncMock()
        mock_file.file = io.BytesIO(b"pdf")

        with patch("antgent.services.s3_uploader.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.strftime.return_value = "2025-10"
            mock_datetime.now.return_value = mock_now

            # Mix of None and valid files
            results = await prep_contents(texts=None, files=[None, mock_file, None])

        # Should only process the one valid file
        assert len(results) == 1
        assert mock_s3.upload_file_async.await_count == 1

    @patch("antgent.services.s3_uploader.s3_client")
    async def test_prep_contents_mime_type_guessing(self, mock_s3_client):
        """Test MIME type guessing for files without content_type."""
        mock_s3 = MagicMock()
        mock_s3.prefix = "uploads/"
        mock_s3_client.return_value = mock_s3

        mock_s3_dest = MagicMock()
        mock_s3_dest.url = "s3://bucket/uploads/test.txt"
        mock_s3.upload_file_async = AsyncMock(return_value=mock_s3_dest)

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = None  # No content type provided
        mock_file.read = AsyncMock(return_value=b"text content")
        mock_file.seek = AsyncMock()
        mock_file.file = io.BytesIO(b"text content")

        with patch("antgent.services.s3_uploader.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.strftime.return_value = "2025-10"
            mock_datetime.now.return_value = mock_now

            results = await prep_contents(texts=None, files=[mock_file])

        # Should guess MIME type from filename
        assert results[0].mime == "text/plain"

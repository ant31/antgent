from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from antgent.models.message import Content


@pytest.mark.asyncio
class TestContentToMessages:
    """Tests for Content.to_messages() with async S3 operations."""

    async def test_string_content(self):
        """Test converting string content to messages."""
        content = Content(mode="string", content="Hello, world!", title="Test")
        messages = await content.to_messages(role="user", with_title=True)

        assert len(messages) == 2
        assert messages[0]["content"] == "## Test:\n"
        assert messages[1]["content"] == "Hello, world!\n"

    async def test_string_content_without_title(self):
        """Test converting string content without title."""
        content = Content(mode="string", content="Hello, world!")
        messages = await content.to_messages(role="user", with_title=False)

        assert len(messages) == 1
        assert messages[0]["content"] == "Hello, world!\n"

    async def test_bytes_content(self):
        """Test converting bytes content to messages."""
        content = Content(mode="bytes", content=b"binary data", mime="application/pdf", title="Document")
        messages = await content.to_messages(role="user")

        assert len(messages) == 2
        assert messages[0]["content"] == "## Document:\n"
        assert messages[1]["role"] == "user"
        # Check that it contains the base64 encoded data
        assert "input_file" in messages[1]["content"][0]["type"]

    async def test_b64_content(self):
        """Test converting base64 content to messages."""
        import base64

        test_bytes = b"test data"
        b64_string = base64.b64encode(test_bytes).decode("utf-8")

        content = Content(mode="b64", content=b64_string, mime="application/pdf")
        messages = await content.to_messages(role="user", with_title=False)

        assert len(messages) == 1
        assert "input_file" in messages[0]["content"][0]["type"]

    @patch("antgent.models.message.filedl_client")
    async def test_url_content_with_s3_pdf(self, mock_filedl_client):
        """Test converting S3 URL content (PDF) to messages."""
        # Mock the file download client
        mock_client = MagicMock()
        mock_filedl_client.return_value = mock_client

        # Mock the download_s3 method to return file info
        mock_file_info = MagicMock()
        mock_file_info.filename = "test.pdf"
        mock_file_info.metadata = {"content-type": "application/pdf"}

        # Create an async mock for download_s3
        mock_client.download_s3 = AsyncMock(return_value=mock_file_info)

        # Mock the output BytesIO to return PDF bytes
        with patch("io.BytesIO") as mock_bytesio:
            mock_output = MagicMock()
            mock_output.read.return_value = b"%PDF-1.4 fake pdf data"
            mock_output.seek = MagicMock()
            mock_bytesio.return_value = mock_output

            content = Content(
                mode="url", content="s3://bucket/path/test.pdf", mime="application/pdf", title="Test Document"
            )
            messages = await content.to_messages(role="user")

            # Verify download_s3 was called (not wrapped in asyncio.to_thread)
            mock_client.download_s3.assert_awaited_once()
            call_args = mock_client.download_s3.call_args
            assert call_args[1]["source"] == "s3://bucket/path/test.pdf"

            # Should have title + PDF content
            assert len(messages) == 2
            assert messages[0]["content"] == "## Test Document:\n"

    @patch("antgent.models.message.filedl_client")
    async def test_url_content_with_s3_text(self, mock_filedl_client):
        """Test converting S3 URL content (text file) to messages."""
        mock_client = MagicMock()
        mock_filedl_client.return_value = mock_client

        mock_file_info = MagicMock()
        mock_file_info.filename = "test.txt"
        mock_file_info.metadata = {"content-type": "text/plain"}

        mock_client.download_s3 = AsyncMock(return_value=mock_file_info)

        with patch("io.BytesIO") as mock_bytesio:
            mock_output = MagicMock()
            mock_output.read.return_value = b"This is text content"
            mock_output.seek = MagicMock()
            mock_bytesio.return_value = mock_output

            content = Content(mode="url", content="s3://bucket/path/test.txt", mime="text/plain", title="")
            messages = await content.to_messages(role="user", with_title=True)

            # Verify async call
            mock_client.download_s3.assert_awaited_once()

            # Should extract text and return as string
            # Title should be set from filename during download
            assert len(messages) == 2
            assert messages[0]["content"] == "## test.txt:\n"
            assert messages[1]["content"] == "This is text content\n"

    @patch("antgent.models.message.filedl_client")
    async def test_url_content_with_http(self, mock_filedl_client):
        """Test converting HTTP URL content to messages."""
        mock_client = MagicMock()
        mock_filedl_client.return_value = mock_client

        mock_file_info = MagicMock()
        mock_file_info.filename = "document.pdf"
        mock_file_info.metadata = {"content-type": "application/pdf"}

        # For HTTP URLs, it should use download() not download_s3()
        mock_client.download = AsyncMock(return_value=mock_file_info)

        with patch("io.BytesIO") as mock_bytesio:
            mock_output = MagicMock()
            mock_output.read.return_value = b"%PDF-1.4 fake pdf"
            mock_output.seek = MagicMock()
            mock_bytesio.return_value = mock_output

            content = Content(mode="url", content="https://example.com/doc.pdf", mime="application/pdf")
            messages = await content.to_messages(role="user")

            # Should use download, not download_s3
            mock_client.download.assert_awaited_once()
            mock_client.download_s3.assert_not_called()
            
            # Should return messages with the document
            assert len(messages) > 0

    @patch("antgent.models.message.filedl_client")
    @patch("antgent.models.message.extract_text_from_bytes")
    async def test_url_content_with_docx(self, mock_extract_text, mock_filedl_client):
        """Test converting S3 URL content (DOCX) to messages."""
        mock_client = MagicMock()
        mock_filedl_client.return_value = mock_client

        mock_file_info = MagicMock()
        mock_file_info.filename = "document.docx"
        mock_file_info.metadata = {
            "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }

        mock_client.download_s3 = AsyncMock(return_value=mock_file_info)
        mock_extract_text.return_value = "Extracted text from DOCX"

        with patch("io.BytesIO") as mock_bytesio:
            mock_output = MagicMock()
            mock_output.read.return_value = b"fake docx binary data"
            mock_output.seek = MagicMock()
            mock_bytesio.return_value = mock_output

            content = Content(
                mode="url",
                content="s3://bucket/doc.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            messages = await content.to_messages(role="user")

            # Should extract text and return as string
            mock_extract_text.assert_called_once()
            assert "Extracted text from DOCX" in messages[-1]["content"]

    async def test_multiple_roles(self):
        """Test that different roles are properly set."""
        for role in ["user", "assistant", "developer", "system"]:
            content = Content(mode="string", content="Test")
            messages = await content.to_messages(role=role, with_title=False)
            assert messages[0]["role"] == role

"""
Documents resource for the Burki SDK (RAG).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from burki.resources.base import BaseResource
from burki.models.document import Document, DocumentStatus


class DocumentsResource(BaseResource):
    """
    Resource for managing documents (RAG knowledge base).

    Example:
        ```python
        # Upload a document
        document = client.documents.upload(
            assistant_id=123,
            file_path="knowledge.pdf"
        )

        # List documents
        documents = client.documents.list(assistant_id=123)

        # Check processing status
        status = client.documents.get_status(document_id=456)
        ```
    """

    def list(self, assistant_id: int) -> List[Document]:
        """
        List all documents for an assistant.

        Args:
            assistant_id: The ID of the assistant.

        Returns:
            List of Document objects.
        """
        response = self._http.get(f"/api/v1/assistants/{assistant_id}/documents")

        if isinstance(response, list):
            return [Document.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [Document.model_validate(item) for item in response["items"]]
        return []

    async def list_async(self, assistant_id: int) -> List[Document]:
        """
        Async version of list().
        """
        response = await self._http.get_async(
            f"/api/v1/assistants/{assistant_id}/documents"
        )

        if isinstance(response, list):
            return [Document.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [Document.model_validate(item) for item in response["items"]]
        return []

    def upload(
        self,
        assistant_id: int,
        file_path: Union[str, Path],
        auto_process: bool = True,
    ) -> Document:
        """
        Upload a document to an assistant's knowledge base.

        Args:
            assistant_id: The ID of the assistant.
            file_path: Path to the file to upload.
            auto_process: Whether to automatically process the document.

        Returns:
            The uploaded Document object.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, self._get_content_type(file_path))}
            data = {"auto_process": str(auto_process).lower()}

            response = self._http.request(
                "POST",
                f"/api/v1/assistants/{assistant_id}/documents",
                files=files,
                data=data,
            )

        return Document.model_validate(response)

    async def upload_async(
        self,
        assistant_id: int,
        file_path: Union[str, Path],
        auto_process: bool = True,
    ) -> Document:
        """
        Async version of upload().
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, self._get_content_type(file_path))}
            data = {"auto_process": str(auto_process).lower()}

            response = await self._http.request_async(
                "POST",
                f"/api/v1/assistants/{assistant_id}/documents",
                files=files,
                data=data,
            )

        return Document.model_validate(response)

    def upload_from_url(
        self,
        assistant_id: int,
        url: str,
        filename: Optional[str] = None,
        auto_process: bool = True,
    ) -> Document:
        """
        Upload a document from a URL.

        Args:
            assistant_id: The ID of the assistant.
            url: URL of the document to fetch and upload.
            filename: Optional filename for the document.
            auto_process: Whether to automatically process the document.

        Returns:
            The uploaded Document object.
        """
        data: Dict[str, Any] = {
            "url": url,
            "auto_process": auto_process,
        }

        if filename:
            data["filename"] = filename

        response = self._http.post(
            f"/api/v1/assistants/{assistant_id}/documents/url", json=data
        )
        return Document.model_validate(response)

    async def upload_from_url_async(
        self,
        assistant_id: int,
        url: str,
        filename: Optional[str] = None,
        auto_process: bool = True,
    ) -> Document:
        """
        Async version of upload_from_url().
        """
        data: Dict[str, Any] = {
            "url": url,
            "auto_process": auto_process,
        }

        if filename:
            data["filename"] = filename

        response = await self._http.post_async(
            f"/api/v1/assistants/{assistant_id}/documents/url", json=data
        )
        return Document.model_validate(response)

    def get_status(self, document_id: int) -> DocumentStatus:
        """
        Get the processing status of a document.

        Args:
            document_id: The ID of the document.

        Returns:
            The DocumentStatus object.
        """
        response = self._http.get(f"/api/v1/assistants/documents/{document_id}/status")
        return DocumentStatus.model_validate(response)

    async def get_status_async(self, document_id: int) -> DocumentStatus:
        """
        Async version of get_status().
        """
        response = await self._http.get_async(
            f"/api/v1/assistants/documents/{document_id}/status"
        )
        return DocumentStatus.model_validate(response)

    def delete(self, document_id: int) -> bool:
        """
        Delete a document.

        Args:
            document_id: The ID of the document.

        Returns:
            True if deleted successfully.
        """
        self._http.delete(f"/api/v1/assistants/documents/{document_id}")
        return True

    async def delete_async(self, document_id: int) -> bool:
        """
        Async version of delete().
        """
        await self._http.delete_async(f"/api/v1/assistants/documents/{document_id}")
        return True

    def reprocess(self, document_id: int) -> Document:
        """
        Reprocess a document.

        Args:
            document_id: The ID of the document.

        Returns:
            The updated Document object.
        """
        response = self._http.post(
            f"/api/v1/assistants/documents/{document_id}/reprocess"
        )
        return Document.model_validate(response)

    async def reprocess_async(self, document_id: int) -> Document:
        """
        Async version of reprocess().
        """
        response = await self._http.post_async(
            f"/api/v1/assistants/documents/{document_id}/reprocess"
        )
        return Document.model_validate(response)

    @staticmethod
    def _get_content_type(file_path: Path) -> str:
        """Get content type based on file extension."""
        content_types = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".csv": "text/csv",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        return content_types.get(file_path.suffix.lower(), "application/octet-stream")

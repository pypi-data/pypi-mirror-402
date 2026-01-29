"""PandaDoc API client."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from pandadoc_cli.config import get_config

BASE_URL = "https://api.pandadoc.com/public/v1"
RATE_LIMIT_DELAY = 0.6  # 100 req/min = 1.67 req/sec, use 0.6s to be safe


class PandaDocError(Exception):
    """Base PandaDoc API error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize with message and optional status code."""
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(PandaDocError):
    """Authentication failed."""

    pass


class NotFoundError(PandaDocError):
    """Resource not found."""

    pass


class ConflictError(PandaDocError):
    """Conflict - cannot modify resource in current state."""

    pass


@dataclass
class Document:
    """PandaDoc document."""

    id: str
    name: str
    status: str
    date_created: str
    date_modified: str
    expiration_date: str | None = None
    version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "date_created": self.date_created,
            "date_modified": self.date_modified,
            "expiration_date": self.expiration_date,
            "version": self.version,
        }


@dataclass
class Template:
    """PandaDoc template."""

    id: str
    name: str
    date_created: str
    date_modified: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "date_created": self.date_created,
            "date_modified": self.date_modified,
        }


@dataclass
class Contact:
    """PandaDoc contact."""

    id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company": self.company,
        }


class PandaDocClient:
    """PandaDoc API client."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize with API key."""
        if api_key is None:
            config = get_config()
            config.validate_pandadoc()
            api_key = config.pandadoc_api_key

        self._api_key = api_key
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"API-Key {api_key}"},
            timeout=30.0,
        )
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request with rate limiting and error handling."""
        self._rate_limit()

        response = self._client.request(method, path, json=json, params=params)

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key", 401)
        if response.status_code == 404:
            raise NotFoundError("Resource not found", 404)
        if response.status_code == 409:
            raise ConflictError("Cannot modify resource in current state", 409)
        if response.status_code >= 400:
            msg = response.text or f"HTTP {response.status_code}"
            raise PandaDocError(msg, response.status_code)

        if response.status_code == 204:
            return {}

        return response.json()  # type: ignore[no-any-return]

    # Documents

    def list_documents(
        self,
        status: str | None = None,
        template_id: str | None = None,
        page: int = 1,
        count: int = 50,
    ) -> list[Document]:
        """List documents with optional filters."""
        params: dict[str, Any] = {"page": page, "count": count}
        if status:
            params["status"] = status
        if template_id:
            params["template_id"] = template_id

        data = self._request("GET", "/documents", params=params)
        results = data.get("results", [])

        return [
            Document(
                id=d["id"],
                name=d.get("name", ""),
                status=d.get("status", ""),
                date_created=d.get("date_created", ""),
                date_modified=d.get("date_modified", ""),
                expiration_date=d.get("expiration_date"),
                version=d.get("version"),
            )
            for d in results
        ]

    def get_document(self, doc_id: str) -> dict[str, Any]:
        """Get document details."""
        return self._request("GET", f"/documents/{doc_id}/details")

    def get_document_status(self, doc_id: str) -> str:
        """Get document status."""
        data = self._request("GET", f"/documents/{doc_id}")
        return data.get("status", "unknown")  # type: ignore[no-any-return]

    def create_document(
        self,
        template_id: str,
        name: str,
        recipients: list[dict[str, str]] | None = None,
        fields: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a document from a template. Returns document ID."""
        payload: dict[str, Any] = {
            "template_uuid": template_id,
            "name": name,
            "recipients": recipients or [],
        }

        if fields:
            payload["fields"] = fields
        if metadata:
            payload["metadata"] = metadata

        data = self._request("POST", "/documents", json=payload)
        return data["id"]  # type: ignore[no-any-return]

    def update_document(self, doc_id: str, fields: dict[str, Any]) -> None:
        """Update document fields."""
        self._request("PATCH", f"/documents/{doc_id}", json={"fields": fields})

    def delete_document(self, doc_id: str) -> None:
        """Delete a document."""
        self._request("DELETE", f"/documents/{doc_id}")

    def send_document(
        self,
        doc_id: str,
        subject: str | None = None,
        message: str | None = None,
        silent: bool = False,
    ) -> None:
        """Send document for signature."""
        payload: dict[str, Any] = {"silent": silent}
        if subject:
            payload["subject"] = subject
        if message:
            payload["message"] = message

        self._request("POST", f"/documents/{doc_id}/send", json=payload)

    def remind_document(self, doc_id: str, message: str | None = None) -> None:
        """Send a reminder for a document."""
        payload: dict[str, Any] = {}
        if message:
            payload["message"] = message
        self._request("POST", f"/documents/{doc_id}/remind", json=payload)

    def void_document(self, doc_id: str, reason: str | None = None) -> None:
        """Void a sent document."""
        payload: dict[str, Any] = {}
        if reason:
            payload["reason"] = reason
        self._request("POST", f"/documents/{doc_id}/void", json=payload)

    def download_document(self, doc_id: str) -> bytes:
        """Download document as PDF."""
        self._rate_limit()
        response = self._client.get(f"/documents/{doc_id}/download")
        if response.status_code != 200:
            raise PandaDocError(
                f"Download failed: {response.status_code}", response.status_code
            )
        return response.content

    def get_document_link(self, doc_id: str) -> str:
        """Get shareable link for a document."""
        data = self._request("POST", f"/documents/{doc_id}/session")
        return data.get("link", data.get("id", ""))  # type: ignore[no-any-return]

    # Templates

    def list_templates(self, folder_id: str | None = None) -> list[Template]:
        """List templates."""
        params: dict[str, Any] = {}
        if folder_id:
            params["folder_uuid"] = folder_id

        data = self._request("GET", "/templates", params=params)
        results = data.get("results", [])

        return [
            Template(
                id=t["id"],
                name=t.get("name", ""),
                date_created=t.get("date_created", ""),
                date_modified=t.get("date_modified", ""),
            )
            for t in results
        ]

    def get_template(self, template_id: str) -> dict[str, Any]:
        """Get template details."""
        return self._request("GET", f"/templates/{template_id}/details")

    # Contacts

    def list_contacts(self, email: str | None = None) -> list[Contact]:
        """List contacts."""
        params: dict[str, Any] = {}
        if email:
            params["email"] = email

        data = self._request("GET", "/contacts", params=params)
        results = data.get("results", [])

        return [
            Contact(
                id=c["id"],
                email=c.get("email", ""),
                first_name=c.get("first_name"),
                last_name=c.get("last_name"),
                company=c.get("company"),
            )
            for c in results
        ]

    def get_contact(self, contact_id: str) -> Contact:
        """Get contact details."""
        data = self._request("GET", f"/contacts/{contact_id}")
        return Contact(
            id=data["id"],
            email=data.get("email", ""),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            company=data.get("company"),
        )

    def create_contact(
        self,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        company: str | None = None,
    ) -> str:
        """Create a contact. Returns contact ID."""
        payload: dict[str, Any] = {"email": email}
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if company:
            payload["company"] = company

        data = self._request("POST", "/contacts", json=payload)
        return data["id"]  # type: ignore[no-any-return]

    def update_contact(
        self,
        contact_id: str,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        company: str | None = None,
    ) -> None:
        """Update a contact."""
        payload: dict[str, Any] = {}
        if email:
            payload["email"] = email
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if company:
            payload["company"] = company

        self._request("PATCH", f"/contacts/{contact_id}", json=payload)

    def delete_contact(self, contact_id: str) -> None:
        """Delete a contact."""
        self._request("DELETE", f"/contacts/{contact_id}")

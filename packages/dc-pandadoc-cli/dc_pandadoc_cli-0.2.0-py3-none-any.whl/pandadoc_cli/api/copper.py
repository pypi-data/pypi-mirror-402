"""Copper CRM API client."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from pandadoc_cli.config import get_config

BASE_URL = "https://api.copper.com/developer_api/v1"
RATE_LIMIT_DELAY = 0.2  # 600 req/min = 10 req/sec


class CopperError(Exception):
    """Base Copper API error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize with message and optional status code."""
        super().__init__(message)
        self.status_code = status_code


class CopperAuthError(CopperError):
    """Authentication failed."""

    pass


class CopperNotFoundError(CopperError):
    """Resource not found."""

    pass


@dataclass
class Opportunity:
    """Copper opportunity."""

    id: int
    name: str
    company_id: int | None = None
    company_name: str | None = None
    monetary_value: float | None = None
    close_date: str | None = None
    status: str | None = None
    pipeline_id: int | None = None
    pipeline_stage_id: int | None = None
    primary_contact_id: int | None = None
    custom_fields: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "monetary_value": self.monetary_value,
            "close_date": self.close_date,
            "status": self.status,
            "pipeline_id": self.pipeline_id,
            "pipeline_stage_id": self.pipeline_stage_id,
            "primary_contact_id": self.primary_contact_id,
            "custom_fields": self.custom_fields,
        }


@dataclass
class Person:
    """Copper person/contact."""

    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    company_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company_id": self.company_id,
        }


@dataclass
class Company:
    """Copper company."""

    id: int
    name: str
    email_domain: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email_domain": self.email_domain,
        }


class CopperClient:
    """Copper CRM API client."""

    def __init__(
        self, api_key: str | None = None, user_email: str | None = None
    ) -> None:
        """Initialize with API key and user email."""
        if api_key is None or user_email is None:
            config = get_config()
            config.validate_copper()
            api_key = api_key or config.copper.api_key
            user_email = user_email or config.copper.user_email

        self._api_key = api_key
        self._user_email = user_email
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={
                "X-PW-AccessToken": api_key,
                "X-PW-UserEmail": user_email,
                "X-PW-Application": "developer_api",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        self._last_request_time = 0.0
        self._custom_field_cache: dict[int, str] | None = None

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
        json: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make an API request with rate limiting and error handling."""
        self._rate_limit()

        response = self._client.request(method, path, json=json)

        if response.status_code == 401:
            raise CopperAuthError("Invalid API key or user email", 401)
        if response.status_code == 404:
            raise CopperNotFoundError("Resource not found", 404)
        if response.status_code >= 400:
            msg = response.text or f"HTTP {response.status_code}"
            raise CopperError(msg, response.status_code)

        if response.status_code == 204:
            return {}

        return response.json()  # type: ignore[no-any-return]

    def _get_custom_field_definitions(self) -> dict[int, str]:
        """Get custom field definitions (id -> name mapping)."""
        if self._custom_field_cache is not None:
            return self._custom_field_cache

        data = self._request("GET", "/custom_field_definitions")
        if isinstance(data, list):
            self._custom_field_cache = {f["id"]: f["name"] for f in data}
        else:
            self._custom_field_cache = {}
        return self._custom_field_cache

    def _parse_custom_fields(
        self, custom_fields: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Parse custom fields to name -> value mapping."""
        definitions = self._get_custom_field_definitions()
        result: dict[str, Any] = {}
        for field in custom_fields:
            field_id = field.get("custom_field_definition_id")
            if field_id and field_id in definitions:
                result[definitions[field_id]] = field.get("value")
        return result

    # Opportunities

    def get_opportunity(self, opp_id: int) -> Opportunity:
        """Get opportunity details."""
        data = self._request("GET", f"/opportunities/{opp_id}")
        if not isinstance(data, dict):
            raise CopperError("Invalid response format")

        custom_fields = self._parse_custom_fields(data.get("custom_fields", []))

        return Opportunity(
            id=data["id"],
            name=data.get("name", ""),
            company_id=data.get("company_id"),
            company_name=data.get("company_name"),
            monetary_value=data.get("monetary_value"),
            close_date=data.get("close_date"),
            status=data.get("status"),
            pipeline_id=data.get("pipeline_id"),
            pipeline_stage_id=data.get("pipeline_stage_id"),
            primary_contact_id=data.get("primary_contact_id"),
            custom_fields=custom_fields,
        )

    def update_opportunity(
        self,
        opp_id: int,
        custom_fields: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Update opportunity fields."""
        payload: dict[str, Any] = dict(kwargs)

        if custom_fields:
            definitions = self._get_custom_field_definitions()
            # Reverse lookup: name -> id
            name_to_id = {v: k for k, v in definitions.items()}
            cf_list = []
            for name, value in custom_fields.items():
                if name in name_to_id:
                    cf_list.append(
                        {"custom_field_definition_id": name_to_id[name], "value": value}
                    )
            if cf_list:
                payload["custom_fields"] = cf_list

        self._request("PUT", f"/opportunities/{opp_id}", json=payload)

    def create_activity(
        self,
        parent_type: str,
        parent_id: int,
        activity_type: str,
        details: str,
    ) -> int:
        """Create an activity log entry."""
        payload = {
            "parent": {"type": parent_type, "id": parent_id},
            "type": {"category": "user", "id": activity_type},
            "details": details,
        }
        data = self._request("POST", "/activities", json=payload)
        if isinstance(data, dict):
            activity_id = data.get("id")
            return activity_id if isinstance(activity_id, int) else 0
        return 0

    # People

    def get_person(self, person_id: int) -> Person:
        """Get person details."""
        data = self._request("GET", f"/people/{person_id}")
        if not isinstance(data, dict):
            raise CopperError("Invalid response format")

        email = None
        emails = data.get("emails", [])
        if emails:
            email = emails[0].get("email")

        phone = None
        phones = data.get("phone_numbers", [])
        if phones:
            phone = phones[0].get("number")

        return Person(
            id=data["id"],
            name=data.get("name", ""),
            email=email,
            phone=phone,
            company_id=data.get("company_id"),
        )

    # Companies

    def get_company(self, company_id: int) -> Company:
        """Get company details."""
        data = self._request("GET", f"/companies/{company_id}")
        if not isinstance(data, dict):
            raise CopperError("Invalid response format")

        return Company(
            id=data["id"],
            name=data.get("name", ""),
            email_domain=data.get("email_domain"),
        )

    # Field discovery

    def get_available_fields(self) -> list[str]:
        """Get list of available field paths for mapping."""
        fields = [
            # Opportunity fields
            "opportunity.name",
            "opportunity.company_name",
            "opportunity.monetary_value",
            "opportunity.close_date",
            "opportunity.status",
            # Primary contact fields
            "primary_contact.name",
            "primary_contact.email",
            "primary_contact.phone",
            # Company fields
            "company.name",
            "company.email_domain",
        ]

        # Add custom fields
        definitions = self._get_custom_field_definitions()
        for name in definitions.values():
            fields.append(f"custom_fields.{name}")

        return sorted(fields)

    def resolve_field_value(
        self,
        opp: Opportunity,
        field_path: str,
        person_cache: dict[int, Person] | None = None,
        company_cache: dict[int, Company] | None = None,
    ) -> Any:
        """Resolve a field path to its value for an opportunity."""
        if person_cache is None:
            person_cache = {}
        if company_cache is None:
            company_cache = {}

        parts = field_path.split(".", 1)
        if len(parts) != 2:
            return None

        prefix, field = parts

        if prefix == "opportunity":
            return getattr(opp, field, None)

        if prefix == "custom_fields" and opp.custom_fields:
            return opp.custom_fields.get(field)

        if prefix == "primary_contact" and opp.primary_contact_id:
            if opp.primary_contact_id not in person_cache:
                person_cache[opp.primary_contact_id] = self.get_person(
                    opp.primary_contact_id
                )
            person = person_cache[opp.primary_contact_id]
            return getattr(person, field, None)

        if prefix == "company" and opp.company_id:
            if opp.company_id not in company_cache:
                company_cache[opp.company_id] = self.get_company(opp.company_id)
            company = company_cache[opp.company_id]
            return getattr(company, field, None)

        return None

"""Main client implementation for ParcelTracker Recipient/Tenant API."""

import logging
from typing import Any, Dict, List, Optional, Type

import requests
from requests.exceptions import RequestException

from .errors import APIError, AuthenticationError, NotFoundError, ValidationError
from .models import PagedRecipientResponse, RecipientCreate, RecipientResponse, RecipientUpdate
from .services.recipients_service import RecipientsService


class ParcelTrackerClient:
    """Main client for interacting with the ParcelTracker public API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.parceltracker.com/api/public",
        timeout: int = 30,
    ):
        """Initialize the ParcelTracker client.

        Args:
            api_key: Your ParcelTracker API key. Use the value *without* the
                ``ApiKey `` prefix; it will be added automatically.
            base_url: Base URL for the public API
                (default: https://api.parceltracker.com/api/public)
            timeout: Request timeout in seconds (default: 30)

        Raises:
            ValidationError: If ``api_key`` is not provided.
        """
        if not api_key:
            raise ValidationError("API key must be provided")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"ApiKey {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        # Initialize services
        self.recipients = RecipientsService(self)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        expected_status: Optional[List[int]] = None,
    ) -> Any:
        """Perform an HTTP request and handle common error cases."""

        logger = logging.getLogger(__name__)
        url = f"{self.base_url}{path}"
        expected_status = expected_status or list(range(200, 300))

        try:
            logger.debug(
                "ParcelTracker request: %s %s params=%s",
                method,
                url,
                params,
            )
            response = self.session.request(
                method,
                url,
                params=params,
                json=json_body,
                timeout=self.timeout,
            )
        except RequestException as exc:
            logger.error("ParcelTracker request failed: %s %s", method, url)
            raise APIError(f"Request to {url} failed: {exc}") from exc

        logger.debug(
            "ParcelTracker response: %s %s status=%s",
            method,
            url,
            response.status_code,
        )
        if response.status_code not in expected_status:
            if response.status_code in (401, 403):
                raise AuthenticationError("Authentication failed " f"({response.status_code}): {response.text}")
            if response.status_code == 404:
                raise NotFoundError(f"Resource not found at {url}")

            raise APIError("Unexpected response " f"({response.status_code}) from {url}: {response.text}")

        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:  # JSON decode error
            raise APIError(f"Invalid JSON in response from {url}: {exc}") from exc

    # ------------------------------------------------------------------
    # Recipient (Tenant) endpoints
    # ------------------------------------------------------------------

    def create_recipient(self, recipient_data: RecipientCreate) -> RecipientResponse:
        """Create a new recipient (POST /tenants).

        This method delegates to :class:`RecipientsService` to keep the client
        surface area small while allowing the library to grow.
        """

        return self.recipients.create_recipient(recipient_data)

    def get_recipient(self, recipient_id: str) -> RecipientResponse:
        """Get a recipient by ID (GET /tenants/{id})."""

        return self.recipients.get_recipient(recipient_id)

    def update_recipient(self, recipient_id: str, recipient_data: RecipientUpdate) -> RecipientResponse:
        """Update an existing recipient (PUT /tenants/{id})."""

        return self.recipients.update_recipient(recipient_id, recipient_data)

    def delete_recipient(self, recipient_id: str) -> bool:
        """Delete a recipient (DELETE /tenants/{id})."""

        return self.recipients.delete_recipient(recipient_id)

    def list_recipients(
        self,
        development_id: int,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> PagedRecipientResponse:
        """List recipients with optional filtering (GET /tenants).

        This is a thin wrapper around :meth:`RecipientsService.list_recipients`.
        """

        return self.recipients.list_recipients(
            development_id=development_id,
            page=page,
            page_size=page_size,
        )

    def get_all_recipients(
        self,
        development_id: int,
        *,
        page_size: int = 100,
    ) -> List[RecipientResponse]:
        """Retrieve *all* recipients for a development by paging through
        results."""

        return self.recipients.get_all_recipients(
            development_id=development_id,
            page_size=page_size,
        )

    def sync_recipients(
        self,
        recipients: List[RecipientCreate],
        development_id: int,
    ) -> None:
        """Sync a list of recipients for a development.

        This is a thin wrapper around
        :meth:`RecipientsService.sync_recipients`, which will:

        * create recipients that do not yet exist (based on ``external_id``)
        * update recipients whose details have changed
        * delete recipients that exist remotely but are not in the provided list
        """

        self.recipients.sync_recipients(recipients=recipients, development_id=development_id)

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self) -> "ParcelTrackerClient":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Context manager exit."""
        self.close()

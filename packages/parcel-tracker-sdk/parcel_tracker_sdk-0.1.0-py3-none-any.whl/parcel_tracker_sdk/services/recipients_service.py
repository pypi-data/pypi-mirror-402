"""Recipients service handling Tenant/Recipient operations."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..errors import ValidationError
from ..models import PagedRecipientResponse, RecipientCreate, RecipientResponse, RecipientUpdate

logger = logging.getLogger(__name__)


class RecipientsService:
    """Service class encapsulating recipient-related operations.

    This is intended to be used by :class:`parcel_tracker_sdk.client.ParcelTrackerClient`.
    It expects the client instance to provide a ``_request`` method compatible with
    :meth:`parcel_tracker_sdk.client.ParcelTrackerClient._request`.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_recipient_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        import re

        from ..errors import ValidationError  # local import to avoid cycles

        errors: List[str] = []

        def require_str_field(field_name: str, label: str, *, min_len: int) -> None:
            if field_name not in payload or payload[field_name] is None:
                errors.append(f"{label} is required")
                return
            value = payload[field_name]
            if not isinstance(value, str):
                errors.append(f"{label} must be a string")
                return
            if len(value.strip()) < min_len:
                errors.append(f"{label} must be at least {min_len} character(s)")

        def require_str_field_allow_empty(field_name: str, label: str) -> None:
            if field_name not in payload or payload[field_name] is None:
                errors.append(f"{label} is required")
                return
            if not isinstance(payload[field_name], str):
                errors.append(f"{label} must be a string")

        # Id2 (ExternalId) optional non-empty
        if "Id2" in payload:
            if payload["Id2"] is None:
                payload.pop("Id2", None)
            elif not isinstance(payload["Id2"], str):
                errors.append("Id2 must be a string when provided")
            elif payload["Id2"].strip() == "":
                errors.append("Id2 must not be empty when provided")

        # FirstName mandatory length >= 1
        require_str_field("FirstName", "FirstName", min_len=1)

        # LastName mandatory length >= 0 (required, may be empty)
        require_str_field_allow_empty("LastName", "LastName")

        # Email mandatory validated for format
        if "Email" not in payload or payload["Email"] is None:
            errors.append("Email is required")
        elif not isinstance(payload["Email"], str):
            errors.append("Email must be a string")
        else:
            email_value = payload["Email"].strip()
            import re as _re

            if not _re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_value):
                errors.append("Email must be a valid email address")

        # Phone optional; normalize to digits if needed
        if "Phone" in payload:
            if payload["Phone"] is None:
                payload.pop("Phone", None)
            else:
                phone_value = str(payload["Phone"]).strip()
                if phone_value == "":
                    payload.pop("Phone", None)
                elif not phone_value.isdigit():
                    digits_only = re.sub(r"\D", "", phone_value)
                    if digits_only == "":
                        errors.append("Phone must contain digits when provided")
                    else:
                        payload["Phone"] = digits_only

        # Room (Location) mandatory length > 0
        require_str_field("Room", "Room", min_len=1)

        # Alias optional: no validation rules

        # DevelopmentId integer mandatory
        if "DevelopmentId" not in payload or payload["DevelopmentId"] is None:
            errors.append("DevelopmentId is required")
        elif not isinstance(payload["DevelopmentId"], int) or isinstance(payload["DevelopmentId"], bool):
            errors.append("DevelopmentId must be an integer")

        if errors:
            raise ValidationError("Validation error(s): " + "; ".join(errors))

        return payload

    # ------------------------------------------------------------------
    # Public recipient methods
    # ------------------------------------------------------------------

    def create_recipient(self, recipient_data: RecipientCreate) -> RecipientResponse:
        """Create a new recipient (POST /tenants)."""

        try:
            if hasattr(recipient_data, "dict"):
                payload = recipient_data.dict(by_alias=True)
            else:
                raise ValidationError("recipient_data must be a RecipientRequest instance")

            payload = self._validate_recipient_payload(payload)
            data = self._client._request(
                "POST",
                "/tenants",
                json_body=payload,
                expected_status=[201],
            )
            recipient = RecipientResponse(**data)
            logger.info("Created recipient id=%s external_id=%s", recipient.id, recipient.external_id)
            return recipient
        except Exception:
            logger.error(
                "Failed to create recipient external_id=%s",
                getattr(recipient_data, "external_id", None),
            )
            raise

    def get_recipient(self, recipient_id: str) -> RecipientResponse:
        """Get a recipient by ID or Id2 (GET /tenants/{id})."""

        try:
            data = self._client._request("GET", f"/tenants/{recipient_id}")
            recipient = RecipientResponse(**data)
            logger.info("Fetched recipient id=%s external_id=%s", recipient.id, recipient.external_id)
            return recipient
        except Exception:
            logger.error("Failed to fetch recipient id=%s", recipient_id)
            raise

    def update_recipient(self, recipient_id: str, recipient_data: RecipientUpdate) -> RecipientResponse:
        """Update an existing recipient (PUT /tenants/{id})."""

        try:
            if recipient_data.id != recipient_id:
                recipient_data.id = recipient_id

            if hasattr(recipient_data, "dict"):
                payload = recipient_data.model_dump(by_alias=True)
            else:
                raise ValidationError("recipient_data must be a RecipientRequest instance")

            payload = self._validate_recipient_payload(payload)
            data = self._client._request(
                "PUT",
                f"/tenants/{recipient_id}",
                json_body=payload,
            )
            recipient = RecipientResponse(**data)
            logger.info("Updated recipient id=%s external_id=%s", recipient.id, recipient.external_id)
            return recipient
        except Exception:
            logger.error("Failed to update recipient id=%s", recipient_id)
            raise

    def delete_recipient(self, recipient_id: str) -> bool:
        """Delete a recipient (DELETE /tenants/{id})."""

        try:
            self._client._request(
                "DELETE",
                f"/tenants/{recipient_id}",
                expected_status=[200],
            )
            logger.info("Deleted recipient id=%s", recipient_id)
            return True
        except Exception:
            logger.error("Failed to delete recipient id=%s", recipient_id)
            raise

    def list_recipients(
        self,
        development_id: int,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> PagedRecipientResponse:
        """List recipients with optional filtering (GET /tenants)."""

        try:
            params: Dict[str, Any] = {"development_id": development_id}
            if page is not None:
                params["page"] = page
            if page_size is not None:
                params["page_size"] = page_size

            data = self._client._request("GET", "/tenants", params=params)
            page_response = PagedRecipientResponse(**data)
            logger.info(
                "Listed recipients development_id=%s page=%s page_size=%s total_results=%s",
                development_id,
                page_response.page,
                page_response.page_size,
                page_response.total_results,
            )
            return page_response
        except Exception:
            logger.error("Failed to list recipients development_id=%s", development_id)
            raise

    def get_all_recipients(
        self,
        development_id: int,
        *,
        page_size: int = 100,
    ) -> List[RecipientResponse]:
        """Retrieve *all* recipients for a development by paging through results."""

        try:
            all_recipients: List[RecipientResponse] = []
            page = 1

            while True:
                page_response = self.list_recipients(
                    development_id=development_id,
                    page=page,
                    page_size=page_size,
                )
                all_recipients.extend(page_response.elements)

                if page >= page_response.total_pages:
                    break
                page += 1

            logger.info(
                "Fetched all recipients development_id=%s count=%s",
                development_id,
                len(all_recipients),
            )
            return all_recipients
        except Exception:
            logger.error("Failed to fetch all recipients development_id=%s", development_id)
            raise

    def sync_recipients(
        self, recipients: List[RecipientCreate], development_id: int, stop_on_failure: bool = False
    ) -> None:
        """Sync a list of recipients: create or update as needed."""

        try:
            if not self._ensure_external_id_defined(recipients):
                logger.error("Sync recipients failed: one or more recipients missing external_id")
                raise ValidationError(
                    "The sync functionality relies on `external_id` to determine changes, creations and deletions. "
                    "At least one supplied recipient is missing the external_id field"
                )

            existing_recipients = self.get_all_recipients(development_id=development_id)
            existing_recipients_map = {r.external_id: r for r in existing_recipients if r.external_id}
            recipients_to_delete = self._get_recipients_to_delete(recipients, existing_recipients)

            created = 0
            updated = 0
            deleted = len(recipients_to_delete)

            for recipient in recipients:
                if recipient.external_id not in existing_recipients_map:
                    try:
                        self.create_recipient(recipient)
                        created += 1
                    except Exception:
                        if stop_on_failure:
                            raise
                    continue

                existing = existing_recipients_map[recipient.external_id]

                if not (
                    existing.first_name == recipient.first_name
                    and existing.last_name == recipient.last_name
                    and existing.alias == recipient.alias
                    and existing.email == recipient.email
                    and existing.phone == recipient.phone
                    and existing.development_id == recipient.development_id
                ):
                    try:
                        self.update_recipient(existing.id, recipient)
                        updated += 1
                    except Exception:
                        if stop_on_failure:
                            raise

            for recipient2 in recipients_to_delete:
                try:
                    self.delete_recipient(recipient2.id)
                except Exception:
                    if stop_on_failure:
                        raise

            logger.info(
                "Synced recipients development_id=%s created=%s updated=%s deleted=%s",
                development_id,
                created,
                updated,
                deleted,
            )
        except Exception:
            logger.error("Failed to sync recipients development_id=%s", development_id)
            raise

    def _get_recipients_to_delete(
        self, new_recipients: List[RecipientCreate], existing_recipients: List[RecipientResponse]
    ) -> List[RecipientResponse]:
        """Determine which recipients need to be deleted."""

        new_external_ids = {r.external_id for r in new_recipients if r.external_id}
        recipients_to_delete = [r for r in existing_recipients if r.external_id not in new_external_ids]
        return recipients_to_delete

    def _ensure_external_id_defined(self, new_recipients: List[RecipientCreate]) -> bool:
        for recipient in new_recipients:
            if recipient.external_id is None:
                return False

        return True

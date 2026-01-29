"""Models package for parcel_tracker_sdk.

Currently this package exposes recipient-related models from
``recipient_models``. As the SDK grows, additional model groups can live in
separate modules within this package.
"""

from .recipient_models import (
    BaseModelMixin,
    PagedRecipientResponse,
    RecipientCreate,
    RecipientListResponse,
    RecipientRequest,
    RecipientResponse,
    RecipientUpdate,
)

__all__ = [
    "BaseModelMixin",
    "RecipientResponse",
    "RecipientRequest",
    "PagedRecipientResponse",
    "RecipientCreate",
    "RecipientUpdate",
    "RecipientListResponse",
]

"""Pydantic models for ParcelTracker Recipient API."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, cast

from pydantic import BaseModel, Field


class BaseModelMixin:
    """Common mixin for Pydantic models used in this SDK.

    By default, ``dict()`` excludes unset fields, which is helpful when
    serialising request payloads. ``json()`` builds on top of that behaviour.
    """

    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("exclude_unset", True)
        data = cast(Any, self).model_dump(*args, **kwargs)
        return cast(Dict[str, Any], data)

    def json(self, *args: Any, **kwargs: Any) -> str:
        return json.dumps(self.dict(), *args, **kwargs)


class RecipientResponse(BaseModel, BaseModelMixin):
    """Recipient model matching the public API schema."""

    id: str = Field(..., alias="Id", description="Recipient ID (UUID)")
    external_id: Optional[str] = Field(None, alias="Id2", description="External ID (integration key)")
    first_name: str = Field(..., alias="FirstName", description="First name")
    last_name: str = Field(..., alias="LastName", description="Last name")
    alias: Optional[str] = Field(None, alias="Alias", description="Alias/Nickname")
    email: str = Field(..., alias="Email", description="Email address")
    phone: Optional[str] = Field(None, alias="Phone", description="Phone number")
    location: str = Field(..., alias="Room", description="Location / room / unit identifier")
    development_id: int = Field(..., alias="DevelopmentId", description="Development ID")

    class Config:
        populate_by_name = True


class RecipientRequest(BaseModel, BaseModelMixin):
    """Request payload for creating/updating a recipient."""

    id: Optional[str] = Field(None, alias="Id", description="Recipient ID (UUID)")
    external_id: Optional[str] = Field(None, alias="Id2", description="External ID (integration key)")
    first_name: str = Field(..., alias="FirstName", description="First name")
    last_name: str = Field(..., alias="LastName", description="Last name")
    alias: Optional[str] = Field(None, alias="Alias", description="Alias/Nickname")
    email: str = Field(..., alias="Email", description="Email address")
    phone: Optional[str] = Field(None, alias="Phone", description="Phone number")
    location: str = Field(..., alias="Room", description="Location / room / unit identifier")
    development_id: int = Field(..., alias="DevelopmentId", description="Development ID")

    class Config:
        populate_by_name = True


class PagedRecipientResponse(BaseModel, BaseModelMixin):
    """Response model for paged recipient lists."""

    page: int = Field(..., alias="Page", description="Current page number")
    page_size: int = Field(..., alias="PageSize", description="Page size")
    total_pages: int = Field(..., alias="TotalPages", description="Total pages")
    total_results: int = Field(..., alias="TotalResults", description="Total number of recipients")
    elements: List[RecipientResponse] = Field(
        default_factory=list,
        alias="Elements",
        description="Recipients on the current page",
    )

    class Config:
        populate_by_name = True


# Backwards-compatible aliases used by existing tests/examples
RecipientCreate = RecipientRequest
RecipientUpdate = RecipientRequest
RecipientListResponse = PagedRecipientResponse

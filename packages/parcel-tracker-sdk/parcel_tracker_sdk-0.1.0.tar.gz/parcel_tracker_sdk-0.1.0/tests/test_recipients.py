"""Tests for recipient (formerly tenant) functionality against models/client.
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from parcel_tracker_sdk import (
    ParcelTrackerClient,
    RecipientCreate,
    RecipientListResponse,
    RecipientResponse,
    RecipientUpdate,
)


class TestRecipientModels:
    """Test recipient data models."""

    def test_recipient_create_model(self):
        """Test RecipientCreate (alias of RecipientRequest) model."""
        recipient_data = RecipientCreate(
            external_id="1234567890",
            first_name="James",
            last_name="Williams",
            alias="Jay",
            email="test@test.test",
            phone=None,
            location="Flat 704",
            development_id=1001,
        )
        assert recipient_data.external_id == "1234567890"
        assert recipient_data.first_name == "James"
        assert recipient_data.last_name == "Williams"
        assert recipient_data.alias == "Jay"
        assert recipient_data.email == "test@test.test"
        assert recipient_data.phone is None
        assert recipient_data.location == "Flat 704"

    def test_recipient_update_model(self):
        """Test RecipientUpdate (alias of RecipientRequest) model."""
        update_data = RecipientUpdate(
            id="b99d41d5-d697-45be-af9d-b5fc092abc8c",
            first_name="Updated First Name",
            last_name="Updated Last Name",
            email="new-email@test.com",
            location="Updated Room",
            development_id=2002,
        )
        assert update_data.first_name == "Updated First Name"
        assert update_data.last_name == "Updated Last Name"
        assert update_data.email == "new-email@test.com"

    def test_recipient_model(self):
        """Test Recipient model mapping from wire-format fields."""
        recipient = RecipientResponse(
            Id="b99d41d5-d697-45be-af9d-b5fc092abc8c",
            Id2="1234567890",
            FirstName="James",
            LastName="Williams",
            Alias="Jay",
            Email="test@test.test",
            Phone=None,
            Room="Flat 704",
            DevelopmentId=2002,
        )
        assert recipient.id == "b99d41d5-d697-45be-af9d-b5fc092abc8c"
        assert recipient.external_id == "1234567890"
        assert recipient.first_name == "James"
        assert recipient.last_name == "Williams"
        assert recipient.alias == "Jay"
        assert recipient.email == "test@test.test"
        assert recipient.phone is None
        assert recipient.location == "Flat 704"
        assert recipient.development_id == 2002

    def test_recipient_list_response(self):
        """Test RecipientListResponse (PagedRecipientResponse) model."""
        response = RecipientListResponse(
            Page=1,
            PageSize=20,
            TotalPages=3,
            TotalResults=42,
            Elements=[],
        )
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 3
        assert response.total_results == 42
        assert isinstance(response.elements, list)


class TestRecipientClientMethods:
    """Test recipient client methods exist and are callable."""

    def test_client_initialization(self):
        """Test client initialization with API key."""
        client = ParcelTrackerClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_create_recipient_method_exists(self):
        client = ParcelTrackerClient(api_key="test-key")
        assert hasattr(client, "create_recipient")
        assert callable(client.create_recipient)

    def test_get_recipient_method_exists(self):
        client = ParcelTrackerClient(api_key="test-key")
        assert hasattr(client, "get_recipient")
        assert callable(client.get_recipient)

    def test_update_recipient_method_exists(self):
        client = ParcelTrackerClient(api_key="test-key")
        assert hasattr(client, "update_recipient")
        assert callable(client.update_recipient)

    def test_delete_recipient_method_exists(self):
        client = ParcelTrackerClient(api_key="test-key")
        assert hasattr(client, "delete_recipient")
        assert callable(client.delete_recipient)

    def test_list_recipients_method_exists(self):
        client = ParcelTrackerClient(api_key="test-key")
        assert hasattr(client, "list_recipients")
        assert callable(client.list_recipients)

    def test_get_all_recipients_method_exists(self):
        client = ParcelTrackerClient(api_key="test-key")
        assert hasattr(client, "get_all_recipients")
        assert callable(client.get_all_recipients)


class TestRecipientModelValidation:
    """Test recipient model validation rules."""

    def test_recipient_create_requires_core_fields(self):
        """RecipientCreate should require core required fields."""
        with pytest.raises(PydanticValidationError):
            RecipientCreate()  # type: ignore[call-arg]

        # Valid when required fields are present
        data = RecipientCreate(
            first_name="A",
            last_name="B",
            email="a@b.com",
            location="Room 1",
            development_id=3003,
        )
        assert data.first_name == "A"
        assert data.last_name == "B"
        assert data.email == "a@b.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

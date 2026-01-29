#!/usr/bin/env python3
"""Examples for recipient (formerly tenant) functionality using v2 API."""

import logging
import uuid

import polars as pl

from parcel_tracker_sdk import ParcelTrackerClient, RecipientCreate, RecipientUpdate

# Configure logging for the SDK
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("parcel_tracker_sdk.log"),
    ],
)

# Optionally set specific log levels for different modules
logging.getLogger("parcel_tracker_sdk").setLevel(logging.INFO)
logging.getLogger("parcel_tracker_sdk.services.recipients_service").setLevel(logging.INFO)
logging.getLogger("parcel_tracker_sdk.client").setLevel(logging.INFO)

API_KEY = "kBUqTxxDtP8neqxoVzFgRA8msl8aS5ZaMI0mVgV8HE8="
DEVELOPMENT_ID = 2928
BASE_URL = "https://parcel-tracker-api-dev.azurewebsites.net/api/public"

new_recipient_id = None


def example_create_recipient():
    """Example: Create a new recipient (tenant)."""
    print("=== Create Recipient ===")

    client = ParcelTrackerClient(api_key=API_KEY, base_url=BASE_URL)

    recipient_data = RecipientCreate(
        external_id=str(uuid.uuid4()),
        first_name="James",
        last_name="Williams",
        alias="Jay",
        email="test@test.test",
        phone=None,
        location="Flat 704",
        development_id=DEVELOPMENT_ID,
    )

    try:
        recipient = client.create_recipient(recipient_data)
        print(f"Created recipient: {recipient.first_name} {recipient.last_name}")
        print(f"Recipient ID: {recipient.id}")
        print(f"Email: {recipient.email}")
        print(f"Location: {recipient.location}")

        global new_recipient_id
        new_recipient_id = recipient.id
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


def example_get_recipient():
    """Example: Get recipient by ID or ExternalId."""
    print("\n=== Get Recipient by ID ===")

    client = ParcelTrackerClient(api_key=API_KEY, base_url=BASE_URL)

    try:
        recipient = client.get_recipient(new_recipient_id)
        print(f"Recipient: {recipient.first_name} {recipient.last_name}")
        print(f"ID: {recipient.id}")
        print(f"Email: {recipient.email}")
        print(f"Phone: {recipient.phone}")
        print(f"Location: {recipient.location}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


def example_update_recipient():
    """Example: Update recipient information."""
    print("\n=== Update Recipient ===")

    client = ParcelTrackerClient(api_key=API_KEY, base_url=BASE_URL)

    update_data = RecipientUpdate(
        id=new_recipient_id,
        first_name="James Updated",
        last_name="Williams Updated",
        email="new-email@test.com",
        location="Flat 705",
        development_id=DEVELOPMENT_ID,
    )

    try:
        recipient = client.update_recipient(new_recipient_id, update_data)
        print(f"Updated recipient: {recipient.first_name} {recipient.last_name}")
        print(f"New email: {recipient.email}")
        print(f"New location: {recipient.location}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


def example_list_recipients():
    """Example: List recipients with pagination."""
    print("\n=== List Recipients ===")

    client = ParcelTrackerClient(api_key=API_KEY, base_url=BASE_URL)
    development_id = DEVELOPMENT_ID  # Replace with actual development ID

    try:
        response = client.list_recipients(development_id=development_id, page=1, page_size=10)
        print(f"Page: {response.page} / {response.total_pages}")
        print(f"Total recipients: {response.total_results}")
        print(f"Showing {len(response.elements)} recipients:")

        for recipient in response.elements:
            print(f"  - {recipient.first_name} {recipient.last_name} ({recipient.id})")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


def example_delete_recipient():
    """Example: Delete recipient."""
    print("\n=== Delete Recipient ===")

    client = ParcelTrackerClient(api_key=API_KEY, base_url=BASE_URL)

    recipient_id = new_recipient_id

    try:
        success = client.delete_recipient(recipient_id)
        if success:
            print(f"Successfully deleted recipient: {recipient_id}")
        else:
            print(f"Failed to delete recipient: {recipient_id}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


def example_get_all_recipients():
    """Example: Get all recipients by iterating through all pages."""
    print("\n=== Get All Recipients ===")

    client = ParcelTrackerClient(api_key=API_KEY, base_url=BASE_URL)
    development_id = DEVELOPMENT_ID  # Replace with actual development ID

    try:
        all_recipients = client.get_all_recipients(development_id=development_id)

        print(f"Retrieved {len(all_recipients)} recipients")
        for i, recipient in enumerate(all_recipients[:5], 1):  # Show first 5
            print(f"{i}. {recipient.first_name} {recipient.last_name} - {recipient.location}")

        if len(all_recipients) > 5:
            print(f"... and {len(all_recipients) - 5} more recipients")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


def example_context_manager():
    """Example: Using client with context manager."""
    print("\n=== Using Context Manager ===")

    with ParcelTrackerClient(api_key=API_KEY, base_url=BASE_URL) as client:
        recipient_data = RecipientCreate(
            first_name="Test",
            last_name="Recipient",
            email="test@example.com",
            location="Front desk",
            development_id=DEVELOPMENT_ID,
        )

        try:
            recipient = client.create_recipient(recipient_data)
            print(f"Created recipient: {recipient.first_name} " f"{recipient.last_name} (ID: {recipient.id})")
        except Exception as e:
            print(f"Error: {e}")

    print("Client session closed automatically")


def example_list_processing():
    data_df = pl.read_csv("./examples/recipients_list.csv", has_header=True)
    recipients_to_sync = []

    for row in data_df.iter_rows(named=True):
        recipients_to_sync.append(
            RecipientCreate(
                external_id=row["sso_username"],
                first_name=row["firstname"],
                last_name=row["lastname"],
                alias=row["known_as"],
                email=row["oxford_email"],
                location=row["university_card_type"],
                development_id=DEVELOPMENT_ID,
            )
        )

    with ParcelTrackerClient(api_key=API_KEY, base_url=BASE_URL) as client:
        # create a sample recipient that will need to be deleted as part of the sync process
        random_id2 = "deleteme"
        recipient = RecipientCreate(
            external_id=random_id2,
            first_name="Test",
            last_name="Recipient",
            email="test@example.com",
            location="Front desk",
            development_id=DEVELOPMENT_ID,
        )
        client.create_recipient(recipient)

        # perform the sync process
        client.sync_recipients(recipients_to_sync, DEVELOPMENT_ID)

        # check that all recipients have been created and the one created above has been deleted
        recipients = client.list_recipients(development_id=DEVELOPMENT_ID).elements
        valid_ext_ids = 0
        for r in recipients:
            if r.external_id is not None and r.external_id != random_id2:
                valid_ext_ids += 1
            elif r.external_id != random_id2:
                raise Exception("Deletion did not work as expected")

        assert valid_ext_ids == len(data_df)


if __name__ == "__main__":
    print("ParcelTracker SDK - Recipient Usage Examples\n")

    example_create_recipient()
    example_get_recipient()
    example_update_recipient()
    example_list_recipients()
    example_get_all_recipients()
    example_delete_recipient()
    example_context_manager()
    example_list_processing()

    print("\n=== Recipient Examples Complete ===")

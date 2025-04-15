from litepolis_database_default.Actor import DatabaseActor
import pytest
from typing import Optional

def test_create_user():
    # Use the generic BaseManager.create method
    user_data = {
        "email": "test@example.com",
        "auth_token": "test-token"
    }
    user = DatabaseActor.create_user(user_data)
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.auth_token == "test-token"

def test_get_user():
    # Create a test user using the generic method
    user_data = {
        "email": "get_user@example.com", # Use unique email for isolation
        "auth_token": "get-token"
    }
    user = DatabaseActor.create_user(user_data)

    # Retrieve the user using the generic BaseManager.read method
    retrieved_user = DatabaseActor.read_user(user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == "get_user@example.com"

def test_update_user():
    # Create a test user
    user_data = {
        "email": "update_user@example.com", # Unique email
        "auth_token": "update-token"
    }
    user = DatabaseActor.create_user(user_data)

    # Update the user using the generic BaseManager.update method
    updated_email = "updated@example.com"
    update_data = {"email": updated_email}
    updated_user = DatabaseActor.update_user(user.id, update_data)

    # Retrieve and verify
    retrieved_user = DatabaseActor.read_user(user.id)
    assert retrieved_user is not None
    assert retrieved_user.email == updated_email

def test_delete_user():
    # Create a test user
    user_data = {
        "email": "delete_user@example.com", # Unique email
        "auth_token": "delete-token"
    }
    user = DatabaseActor.create_user(user_data)

    # Delete the user using the generic BaseManager.delete method
    DatabaseActor.delete_user(user.id)

    # Verify deletion
    retrieved_user = DatabaseActor.read_user(user.id)
    assert retrieved_user is None
from litepolis_database_default.Actor import DatabaseActor
import pytest
from typing import Optional


def test_create_conversation():
    # Create a test user
    user_data = {
        "email": "conv_create_user@example.com",
        "auth_token": "conv-create-token"
    }
    user = DatabaseActor.create_user(user_data)
    
    # Create conversation
    conversation_data = {
        "title": "Test Conversation",
        "description": "This is a test conversation",
        "user_id": user.id
    }
    conversation = DatabaseActor.create_conversation(conversation_data)
    
    assert conversation.id is not None
    assert conversation.title == "Test Conversation"
    assert conversation.description == "This is a test conversation"

def test_get_conversation():
    # Create user
    user_data = {
        "email": "conv_get_user@example.com",
        "auth_token": "conv-get-token"
    }
    user = DatabaseActor.create_user(user_data)
    
    # Create conversation
    conversation_data = {
        "title": "Get Test Conversation",
        "description": "Getting this one",
        "user_id": user.id
    }
    conversation = DatabaseActor.create_conversation(conversation_data)
    
    # Retrieve conversation
    retrieved_conversation = DatabaseActor.read_conversation(conversation.id)
    assert retrieved_conversation.id == conversation.id
    assert retrieved_conversation.title == "Get Test Conversation"

def test_update_conversation():
    # Create user
    user_data = {
        "email": "conv_update_user@example.com",
        "auth_token": "conv-update-token"
    }
    user = DatabaseActor.create_user(user_data)
    
    # Create conversation
    conversation_data = {
        "title": "Update Test Conversation",
        "description": "Updating this one",
        "user_id": user.id
    }
    conversation = DatabaseActor.create_conversation(conversation_data)
    
    updated_title = "Updated Conversation"
    # Update conversation
    update_data = {"title": updated_title}
    updated_conversation = DatabaseActor.update_conversation(conversation.id, update_data)
    
    # Verify update
    retrieved_conversation = DatabaseActor.read_conversation(conversation.id)
    assert retrieved_conversation.title == updated_title

def test_delete_conversation():
    # Create user
    user_data = {
        "email": "conv_delete_user@example.com",
        "auth_token": "conv-delete-token"
    }
    user = DatabaseActor.create_user(user_data)
    
    # Create conversation
    conversation_data = {
        "title": "Delete Test Conversation",
        "description": "Deleting this one",
        "user_id": user.id
    }
    conversation = DatabaseActor.create_conversation(conversation_data)
    
    # Delete conversation
    deleted = DatabaseActor.delete_conversation(conversation.id)
    assert deleted is True
    
    # Verify deletion
    retrieved_conversation = DatabaseActor.read_conversation(conversation.id)
    assert retrieved_conversation is None
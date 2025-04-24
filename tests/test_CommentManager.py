from litepolis_database_default.Actor import DatabaseActor
import pytest
from typing import Optional

def test_create_comment():
    # Create test user
    user = DatabaseActor.create_user({
        "email": "comment_test1@example.com",
        "auth_token": "comment-token"
    })
    
    # Create test conversation
    conversation = DatabaseActor.create_conversation({
        "title": "Test Conversation",
        "description": "Test description",
        "user_id": user.id
    })
    
    # Create comment
    comment = DatabaseActor.create_comment({
        "text_field": "Test comment",
        "user_id": user.id,
        "conversation_id": conversation.id
    })
    
    assert comment.id is not None
    assert comment.text_field == "Test comment"
    assert comment.user_id == user.id
    assert comment.conversation_id == conversation.id

    assert DatabaseActor.delete_user(user.id)
    assert DatabaseActor.delete_conversation(conversation.id)
    assert DatabaseActor.delete_comment(comment.id)

def test_get_comment():
    # Create test user
    user = DatabaseActor.create_user({
        "email": "comment_test2@example.com",
        "auth_token": "comment-token"
    })
    
    # Create test conversation
    conversation = DatabaseActor.create_conversation({
        "title": "Test Conversation",
        "description": "Test description",
        "user_id": user.id
    })
    
    # Create comment
    comment = DatabaseActor.create_comment({
        "text_field": "Test comment",
        "user_id": user.id,
        "conversation_id": conversation.id
    })
    
    # Retrieve comment
    retrieved_comment = DatabaseActor.read_comment(comment.id)
    assert retrieved_comment.id == comment.id
    assert retrieved_comment.text_field == "Test comment"

    assert DatabaseActor.delete_user(user.id)
    assert DatabaseActor.delete_conversation(conversation.id)
    assert DatabaseActor.delete_comment(comment.id)

def test_update_comment():
    # Create test user
    user = DatabaseActor.create_user({
        "email": "comment_test3@example.com",
        "auth_token": "comment-token"
    })
    
    # Create test conversation
    conversation = DatabaseActor.create_conversation({
        "title": "Test Conversation",
        "description": "Test description",
        "user_id": user.id
    })
    
    # Create comment
    comment = DatabaseActor.create_comment({
        "text_field": "Test comment",
        "user_id": user.id,
        "conversation_id": conversation.id
    })
    
    # Update comment
    updated_text = "Updated comment"
    DatabaseActor.update_comment(comment.id, {"text_field": updated_text})
    
    # Verify update
    retrieved_comment = DatabaseActor.read_comment(comment.id)
    assert retrieved_comment.text_field == updated_text

    assert DatabaseActor.delete_user(user.id)
    assert DatabaseActor.delete_conversation(conversation.id)
    assert DatabaseActor.delete_comment(comment.id)

def test_delete_comment():
    # Create test user
    user = DatabaseActor.create_user({
        "email": "comment_test4@example.com",
        "auth_token": "comment-token"
    })
    
    # Create test conversation
    conversation = DatabaseActor.create_conversation({
        "title": "Test Conversation",
        "description": "Test description",
        "user_id": user.id
    })
    
    # Create comment
    comment = DatabaseActor.create_comment({
        "text_field": "Test comment",
        "user_id": user.id,
        "conversation_id": conversation.id
    })
    
    # Delete comment
    DatabaseActor.delete_comment(comment.id)
    
    # Verify deletion
    retrieved_comment = DatabaseActor.read_comment(comment.id)
    assert retrieved_comment is None

    assert DatabaseActor.delete_user(user.id)
    assert DatabaseActor.delete_conversation(conversation.id)
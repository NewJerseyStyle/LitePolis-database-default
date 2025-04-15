from litepolis_database_default.Comments import CommentManager, Comment
from litepolis_database_default.Conversations import ConversationManager
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
    conversation = ConversationManager.create_conversation({
        "title": "Test Conversation",
        "description": "Test description",
        "user_id": user.id
    })
    
    # Create comment
    CommentManager.create_comment({
        "text": "Test comment",
        "user_id": user.id,
        "conversation_id": conversation.id
    })

    result = CommentManager.list_comments_by_conversation_id(conversation.id)
    for comment in result:
        if comment.user_id == user.id:
            if comment.text_field == "Test comment":
                break
    
    assert comment.id is not None
    assert comment.text_field == "Test comment"
    assert comment.user_id == user.id
    assert comment.conversation_id == conversation.id

    DatabaseActor.delete_user(user.id)
    ConversationManager.delete_conversation(conversation.id)
    CommentManager.delete_comment(comment.id)

def test_get_comment():
    # Create test user
    user = DatabaseActor.create_user({
        "email": "comment_test2@example.com",
        "auth_token": "comment-token"
    })
    
    # Create test conversation
    conversation = ConversationManager.create_conversation({
        "title": "Test Conversation",
        "description": "Test description",
        "user_id": user.id
    })
    
    # Create comment
    CommentManager.create_comment({
        "text": "Test comment",
        "user_id": user.id,
        "conversation_id": conversation.id
    })

    result = CommentManager.list_comments_by_conversation_id(conversation.id)
    for comment in result:
        if comment.user_id == user.id:
            if comment.text_field == "Test comment":
                break

    # Retrieve comment
    retrieved_comment = CommentManager.read_comment(comment.id)
    assert retrieved_comment.id == comment.id
    assert retrieved_comment.text_field == "Test comment"

    DatabaseActor.delete_user(user.id)
    ConversationManager.delete_conversation(conversation.id)
    CommentManager.delete_comment(comment.id)

def test_update_comment():
    # Create test user
    user = DatabaseActor.create_user({
        "email": "comment_test3@example.com",
        "auth_token": "comment-token"
    })
    
    # Create test conversation
    conversation = ConversationManager.create_conversation({
        "title": "Test Conversation",
        "description": "Test description",
        "user_id": user.id
    })
    
    # Create comment
    CommentManager.create_comment({
        "text": "Test comment",
        "user_id": user.id,
        "conversation_id": conversation.id
    })
    
    result = CommentManager.list_comments_by_conversation_id(conversation.id)
    for comment in result:
        if comment.user_id == user.id:
            if comment.text_field == "Test comment":
                break

    # Update comment
    updated_text = "Updated comment"
    CommentManager.update_comment(comment.id, {"text": updated_text})
    
    # Verify update
    retrieved_comment = CommentManager.read_comment(comment.id)
    assert retrieved_comment.text_field == updated_text

    DatabaseActor.delete_user(user.id)
    ConversationManager.delete_conversation(conversation.id)
    CommentManager.delete_comment(comment.id)

def test_delete_comment():
    # Create test user
    user = DatabaseActor.create_user({
        "email": "comment_test4@example.com",
        "auth_token": "comment-token"
    })
    
    # Create test conversation
    conversation = ConversationManager.create_conversation({
        "title": "Test Conversation",
        "description": "Test description",
        "user_id": user.id
    })
    
    # Create comment
    CommentManager.create_comment({
        "text": "Test comment",
        "user_id": user.id,
        "conversation_id": conversation.id
    })
    
    result = CommentManager.list_comments_by_conversation_id(conversation.id)
    for comment in result:
        if comment.user_id == user.id:
            if comment.text_field == "Test comment":
                break
    # Delete comment
    CommentManager.delete_comment(comment.id)
    
    # Verify deletion
    retrieved_comment = CommentManager.read_comment(comment.id)
    assert retrieved_comment is None

    DatabaseActor.delete_user(user.id)
    ConversationManager.delete_conversation(conversation.id)
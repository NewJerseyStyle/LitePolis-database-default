from litepolis_database_default.Actor import DatabaseActor
import pytest
from typing import Optional

def test_create_vote():
    # Create test DatabaseActor
    user = DatabaseActor.create_user({
        "email": "vote_test1@example.com",
        "auth_token": "vote-token"
    })
    
    # Create test comment
    comment = DatabaseActor.create_comment({
        "text_field": "Test comment",
        "user_id": user.id,
        "conversation_id": 1
    })
    
    # Create vote
    vote = DatabaseActor.create_vote({
        "user_id": user.id,
        "comment_id": comment.id,
        "value": 1
    })
    
    assert vote.id is not None
    assert vote.user_id == user.id
    assert vote.comment_id == comment.id
    assert vote.value == 1

    assert DatabaseActor.delete_user(user.id)
    assert DatabaseActor.delete_comment(comment.id)
    assert DatabaseActor.delete_vote(vote.id)

def test_get_vote():
    # Create test DatabaseActor
    user = DatabaseActor.create_user({
        "email": "vote_test2@example.com",
        "auth_token": "vote-token"
    })
    
    # Create test comment
    comment = DatabaseActor.create_comment({
        "text_field": "Test comment",
        "user_id": user.id,
        "conversation_id": 1
    })
    
    # Create vote
    vote = DatabaseActor.create_vote({
        "user_id": user.id,
        "comment_id": comment.id,
        "value": 1
    })
    
    # Retrieve vote
    retrieved_vote = DatabaseActor.read_vote(vote.id)
    assert retrieved_vote.id == vote.id
    assert retrieved_vote.user_id == user.id

    assert DatabaseActor.delete_user(user.id)
    assert DatabaseActor.delete_comment(comment.id)
    assert DatabaseActor.delete_vote(vote.id)

def test_update_vote():
    # Create test DatabaseActor
    user = DatabaseActor.create_user({
        "email": "vote_test3@example.com",
        "auth_token": "vote-token"
    })
    
    # Create test comment
    comment = DatabaseActor.create_comment({
        "text_field": "Test comment",
        "user_id": user.id,
        "conversation_id": 1
    })
    
    # Create vote
    vote = DatabaseActor.create_vote({
        "user_id": user.id,
        "comment_id": comment.id,
        "value": 1
    })
    
    # Update vote
    DatabaseActor.update_vote(vote.id, {"value": -1})
    
    # Verify update
    retrieved_vote = DatabaseActor.read_vote(vote.id)
    assert retrieved_vote.value == -1

    assert DatabaseActor.delete_user(user.id)
    assert DatabaseActor.delete_comment(comment.id)
    assert DatabaseActor.delete_vote(vote.id)

def test_delete_vote():
    # Create test DatabaseActor
    user = DatabaseActor.create_user({
        "email": "vote_test4@example.com",
        "auth_token": "vote-token"
    })
    
    # Create test comment
    comment = DatabaseActor.create_comment({
        "text_field": "Test comment",
        "user_id": user.id,
        "conversation_id": 1
    })
    
    # Create vote
    vote = DatabaseActor.create_vote({
        "user_id": user.id,
        "comment_id": comment.id,
        "value": 1
    })
    
    # Delete vote
    DatabaseActor.delete_vote(vote.id)
    
    # Verify deletion
    retrieved_vote = DatabaseActor.read_vote(vote.id)
    assert retrieved_vote is None

    assert DatabaseActor.delete_user(user.id)
    assert DatabaseActor.delete_comment(comment.id)
from litepolis_database_default.Vote import VoteManager, Vote
from litepolis_database_default.Comments import CommentManager
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
    CommentManager.create_comment({
        "text": "Test comment",
        "user_id": user.id,
        "conversation_id": 1
    })

    result = CommentManager.list_comments_by_user_id(user.id)
    for comment in result:
        if comment.conversation_id == 1:
            break
    
    # Create vote
    vote = VoteManager.create_vote({
        "user_id": user.id,
        "comment_id": comment.id,
        "value": 1
    })
    
    assert vote.id is not None
    assert vote.user_id == user.id
    assert vote.comment_id == comment.id
    assert vote.value == 1

    DatabaseActor.delete_user(user.id)
    CommentManager.delete_comment(comment.id)
    VoteManager.delete_vote(vote.id)

def test_get_vote():
    # Create test DatabaseActor
    user = DatabaseActor.create_user({
        "email": "vote_test2@example.com",
        "auth_token": "vote-token"
    })
    
    # Create test comment
    CommentManager.create_comment({
        "text": "Test comment",
        "user_id": user.id,
        "conversation_id": 1
    })

    result = CommentManager.list_comments_by_user_id(user.id)
    for comment in result:
        if comment.conversation_id == 1:
            break
    
    # Create vote
    vote = VoteManager.create_vote({
        "user_id": user.id,
        "comment_id": comment.id,
        "value": 1
    })
    
    # Retrieve vote
    retrieved_vote = VoteManager.read_vote(vote.id)
    assert retrieved_vote.id == vote.id
    assert retrieved_vote.user_id == user.id

    DatabaseActor.delete_user(user.id)
    CommentManager.delete_comment(comment.id)
    VoteManager.delete_vote(vote.id)

def test_update_vote():
    # Create test DatabaseActor
    user = DatabaseActor.create_user({
        "email": "vote_test3@example.com",
        "auth_token": "vote-token"
    })
    
    # Create test comment
    CommentManager.create_comment({
        "text": "Test comment",
        "user_id": user.id,
        "conversation_id": 1
    })

    result = CommentManager.list_comments_by_user_id(user.id)
    for comment in result:
        if comment.conversation_id == 1:
            break
    
    # Create vote
    VoteManager.create_vote({
        "user_id": user.id,
        "comment_id": comment.id,
        "value": 1
    })

    result = VoteManager.list_votes_by_comment_id(comment.id)
    for vote in result:
        if vote.user_id == user.id:
            break
    
    # Update vote
    VoteManager.update_vote(vote.id, {"value": 4})
    
    # Verify update
    retrieved_vote = VoteManager.read_vote(vote.id)
    assert retrieved_vote.value == 4

    DatabaseActor.delete_user(user.id)
    CommentManager.delete_comment(comment.id)
    VoteManager.delete_vote(vote.id)

def test_delete_vote():
    # Create test DatabaseActor
    user = DatabaseActor.create_user({
        "email": "vote_test4@example.com",
        "auth_token": "vote-token"
    })
    
    # Create test comment
    CommentManager.create_comment({
        "text": "Test comment",
        "user_id": user.id,
        "conversation_id": 1
    })

    result = CommentManager.list_comments_by_user_id(user.id)
    for comment in result:
        if comment.conversation_id == 1:
            break
    
    # Create vote
    VoteManager.create_vote({
        "user_id": user.id,
        "comment_id": comment.id,
        "value": 1
    })
    
    # Delete vote
    result = VoteManager.list_votes_by_comment_id(comment.id)
    for vote in result:
        if vote.user_id == user.id:
            break
    VoteManager.delete_vote(vote.id)
    
    # Verify deletion
    retrieved_vote = VoteManager.read_vote(vote.id)
    assert retrieved_vote is None

    DatabaseActor.delete_user(user.id)
    CommentManager.delete_comment(comment.id)
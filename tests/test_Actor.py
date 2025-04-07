from litepolis_database_default import DatabaseActor


def test_actor_create_user_and_conversation():
    user_data = {
        "email": "actor_test@example.com",
        "auth_token": "password"
    }
    user = DatabaseActor.create_user(user_data)
    creator_id = user.id
    
    conversation_data = {
        "title": "Actor Test Title",
        "description": "Actor Test Description",
        "user_id": creator_id
    }
    conversation = DatabaseActor.create_conversation(conversation_data)
    assert conversation.title == "Actor Test Title"
    
    # Cleanup
    DatabaseActor.delete_conversation(conversation.id)
    DatabaseActor.delete_user(creator_id)
from litepolis_database_default.Actor import DatabaseActor
import pytest

def test_create_conversation():
    data = {
        "title": "Test Conversation",
        "description": "This is a test conversation."
    }
    conversation = DatabaseActor.create_conversation(data)
    assert conversation.title == data["title"]
    assert conversation.description == data["description"]
    assert conversation.is_archived == False
    assert conversation.settings == {} # Assert default settings
    conversation_id = conversation.id

    # Clean up
    assert DatabaseActor.delete_conversation(conversation_id)


def test_read_conversation():
    # Create a conversation first
    data = {
        "title": "Test Conversation",
        "description": "This is a test conversation."
    }
    conversation = DatabaseActor.create_conversation(data)
    conversation_id = conversation.id

    read_conversation = DatabaseActor.read_conversation(conversation_id)
    assert read_conversation.title == data["title"]
    assert read_conversation.description == data["description"]
    assert read_conversation.is_archived == False

    # Clean up
    assert DatabaseActor.delete_conversation(conversation_id)


def test_read_conversation():
    # Create some conversations first
    data1 = {
        "title": "Test Conversation 1",
        "description": "This is a test conversation 1."
    }
    DatabaseActor.create_conversation(data1)
    data2 = {
        "title": "Test Conversation 2",
        "description": "This is a test conversation 2."
    }
    DatabaseActor.create_conversation(data2)

    conversations = DatabaseActor.list_conversations()
    assert isinstance(conversations, list)
    assert len(conversations) >= 2  # Assuming there are no other conversations in the database

    # Clean up (very basic, assumes the last two created)
    assert DatabaseActor.delete_conversation(conversations[-1].id)
    assert DatabaseActor.delete_conversation(conversations[-2].id)


def test_update_conversation():
    # Create a conversation first
    data = {
        "title": "Test Conversation",
        "description": "This is a test conversation."
    }
    conversation = DatabaseActor.create_conversation(data)
    conversation_id = conversation.id

    # Update the conversation
    updated_data = {
        "title": "Updated Title",
        "description": "Updated description",
        "is_archived": True,
        "settings": {"Participants can see visualization": True}
    }
    updated_conversation = DatabaseActor.update_conversation(conversation_id, updated_data)
    assert updated_conversation.title == updated_data["title"]
    assert updated_conversation.description == updated_data["description"]
    assert updated_conversation.is_archived == updated_data["is_archived"]
    assert updated_conversation.settings == updated_data["settings"]

    # Clean up
    assert DatabaseActor.delete_conversation(conversation_id)


def test_delete_conversation():
    # Create a conversation first
    data = {
        "title": "Test Conversation",
        "description": "This is a test conversation."
    }
    conversation = DatabaseActor.create_conversation(data)
    conversation_id = conversation.id

    # Delete the conversation
    assert DatabaseActor.delete_conversation(conversation_id)

    # Try to get the deleted conversation (should return None)
    deleted_conversation = DatabaseActor.read_conversation(conversation_id)
    assert deleted_conversation is None

from litepolis_database_default.Actor import DatabaseActor


def test_create_user():
    user = DatabaseActor.create_user({
        "email": "test1@example.com",
        "auth_token": "auth_token",
    })
    assert user.email == "test1@example.com"
    assert user.id is not None

    # Clean up
    assert DatabaseActor.delete_user(user.id)


def test_read_user():
    # Create a DatabaseActor first
    user = DatabaseActor.create_user({
        "email": "test2@example.com",
        "auth_token": "auth_token",
    })
    user_id = user.id

    read_user = DatabaseActor.read_user(user_id)
    assert read_user.email == "test2@example.com"

    # Clean up
    assert DatabaseActor.delete_user(user_id)


def test_read_users():
    # Create some DatabaseActors first
    DatabaseActor.create_user({
        "email": "test01@example.com",
        "auth_token": "auth_token",
    })
    DatabaseActor.create_user({
        "email": "test02@example.com",
        "auth_token": "auth_token",
        "is_admin": 1
    })

    DatabaseActors = DatabaseActor.list_users()
    assert isinstance(DatabaseActors, list)
    assert len(DatabaseActors) >= 2

    # Clean up (very basic, assumes the last two created)
    assert DatabaseActor.delete_user(DatabaseActors[-1].id)
    assert DatabaseActor.delete_user(DatabaseActors[-2].id)


def test_update_user():
    # Create a DatabaseActor first
    user = DatabaseActor.create_user({
        "email": "test3@example.com",
        "auth_token": "auth_token",
    })
    user_id = user.id

    # Update the DatabaseActor
    updated_user = DatabaseActor.update_user(
        user_id,
        {
            "email": "test3@example.com",
            "auth_token": "auth_token",
            "is_admin": 1
        }
    )
    assert updated_user.is_admin == 1

    # Clean up
    assert DatabaseActor.delete_user(user_id)


def test_delete_user():
    # Create a DatabaseActor first
    user = DatabaseActor.create_user({
        "email": "test4@example.com",
        "auth_token": "auth_token",
    })
    user_id = user.id

    assert DatabaseActor.delete_user(user_id)

    # Try to get the deleted DatabaseActor (should return None)
    deleted_user = DatabaseActor.read_user(user_id)
    assert deleted_user is None

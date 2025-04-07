from litepolis_database_default.Users import UserManager


def test_create_user():
    user = UserManager.create_user({
        "email": "test@example.com",
        "auth_token": "auth_token",
    })
    assert user.email == "test@example.com"
    assert user.id is not None

    # Clean up
    assert UserManager.delete_user(user.id)


def test_read_user():
    # Create a user first
    user = UserManager.create_user({
        "email": "test@example.com",
        "auth_token": "auth_token",
    })
    user_id = user.id

    read_user = UserManager.read_user(user_id)
    assert read_user.email == "test@example.com"

    # Clean up
    assert UserManager.delete_user(user_id)


def test_read_users():
    # Create some users first
    UserManager.create_user({
        "email": "test1@example.com",
        "auth_token": "auth_token",
    })
    UserManager.create_user({
        "email": "test2@example.com",
        "auth_token": "auth_token",
        "is_admin": 1
    })

    users = UserManager.list_users()
    assert isinstance(users, list)
    assert len(users) >= 2

    # Clean up (very basic, assumes the last two created)
    assert UserManager.delete_user(users[-1].id)
    assert UserManager.delete_user(users[-2].id)


def test_update_user():
    # Create a user first
    user = UserManager.create_user({
        "email": "test@example.com",
        "auth_token": "auth_token",
    })
    user_id = user.id

    # Update the user
    updated_user = UserManager.update_user(
        user_id,
        {
            "email": "test@example.com",
            "auth_token": "auth_token",
            "is_admin": 1
        }
    )
    assert updated_user.is_admin == 1

    # Clean up
    assert UserManager.delete_user(user_id)


def test_delete_user():
    # Create a user first
    user = UserManager.create_user({
        "email": "test@example.com",
        "auth_token": "auth_token",
    })
    user_id = user.id

    assert UserManager.delete_user(user_id)

    # Try to get the deleted user (should return None)
    deleted_user = UserManager.read_user(user_id)
    assert deleted_user is None

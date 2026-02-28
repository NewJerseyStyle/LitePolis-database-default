"""
This module defines the User model and UserManager class for interacting with the 'users' table in the database.

The 'users' table stores information about users, including their email, authentication token, and admin status.
It also includes timestamps for creation and modification. The table supports both standard SQL databases and StarRocks,
with some specific handling for StarRocks (e.g., unique constraints and primary keys).

.. list-table:: Table Schema
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - id
     - INTEGER
     - Unique identifier for the user.
   * - email
     - VARCHAR
     - User's email address. Must be unique.
   * - auth_token
     - VARCHAR
     - Authentication token for the user.
   * - is_admin
     - BOOLEAN
     - Indicates whether the user is an administrator.
   * - created
     - DATETIME
     - Timestamp indicating when the user was created.
   * - modified
     - DATETIME
     - Timestamp indicating when the user was last modified.

.. list-table:: Relationships

    * - Comment
      - One-to-many.
    * - Vote
      - One-to-many.
    * - Conversation
      - One-to-many.

The UserManager class provides static methods for interacting with the 'users' table, including CRUD operations,
searching, listing with pagination, and counting.

To use the methods in this module, import DatabaseActor.  For example::

    from litepolis_database_default import DatabaseActor

    user = DatabaseActor.create_user({
        "email": "test@example.com",
        "auth_token": "auth_token",
    })
"""

from sqlalchemy import DDL, text
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlmodel import Index, UniqueConstraint, Session, select
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, timezone

from .utils import get_session, is_starrocks_engine

from .utils_StarRocks import register_table

@register_table(distributed_by="HASH(id)")
class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        Index("ix_user_created", "created"),
        Index("ix_user_is_admin", "is_admin"),
    ) if not is_starrocks_engine() else None
    
    id: Optional[int] = Field(primary_key=True)
    email: str = Field(nullable=False, unique=not is_starrocks_engine())
    auth_token: str = Field(nullable=False)
    is_admin: bool = Field(default=False)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    comments: List["Comment"] = Relationship(back_populates="user")
    votes: List["Vote"] = Relationship(back_populates="user")
    conversation: List["Conversation"] = Relationship(back_populates="user")


class UserManager:
    @staticmethod
    def create_user(data: Dict[str, Any]) -> Optional[User]:
        """Creates a new User record.

        Handles checking for existing email before creation, especially for StarRocks.

        Args:
            data: A dictionary containing user data (e.g., "email", "auth_token").

        Returns:
            The created User object, or None if a user with the same email already exists.

        To use this method, import DatabaseActor.  For example::

            from litepolis_database_default import DatabaseActor

            user = DatabaseActor.create_user({
                "email": "test@example.com",
                "auth_token": "auth_token",
            })
        """
        if is_starrocks_engine():
            with get_session() as session:
                # Select only the ID to check for existence, potentially simpler for StarRocks analyzer
                existing_id = session.exec(
                    select(User.id).where(User.email == data["email"])
                ).first()

            if existing_id is not None:
                print("Email already exists")
                return None

        user = User(**data)
        with get_session() as session:
            session.add(user)
            session.commit()
            # StarRocks might not return the ID immediately on commit,
            # so we fetch the created user explicitly.
            if is_starrocks_engine():
                return session.exec(
                    select(User).where(User.email == data["email"])
                ).first()
            session.refresh(user)
            return user

    @staticmethod
    def read_user(user_id: int) -> Optional[User]:
        """Reads a User record by ID.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            The User object if found, otherwise None.

        To use this method, import DatabaseActor.  For example::

            from litepolis_database_default import DatabaseActor

            user = DatabaseActor.read_user(user_id=1)
        """
        with get_session() as session:
            return session.get(User, user_id)

    @staticmethod
    def read_user_by_email(email: str) -> Optional[User]:
        """Reads a User record by email address.

        Args:
            email: The email address of the user.

        Returns:
            The User object if found, otherwise None.

        To use this method, import DatabaseActor.  For example::

            from litepolis_database_default import DatabaseActor

            user = DatabaseActor.read_user_by_email(email="test@example.com")
        """
        with get_session() as session:
            return session.exec(select(User).where(User.email == email)).first()


    @staticmethod
    def list_users(page: int = 1, page_size: int = 10) -> List[User]:
        """Lists User records with pagination.

        Args:
            page: The page number (1-based). Defaults to 1.
            page_size: The number of records per page. Defaults to 10.

        Returns:
            A list of User objects for the specified page.

        To use this method, import DatabaseActor.  For example::

            from litepolis_database_default import DatabaseActor

            users = DatabaseActor.list_users(page=1, page_size=10)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        with get_session() as session:
            return session.exec(select(User).offset(offset).limit(page_size)).all()


    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """Updates a User record by ID with the provided data.

        Args:
            user_id: The unique identifier of the user to update.
            data: A dictionary containing the fields and new values to update.

        Returns:
            The updated User object if found and updated, otherwise None.

        To use this method, import DatabaseActor.  For example::

            from litepolis_database_default import DatabaseActor

            user = DatabaseActor.update_user(user_id=1, data={"email": "new_email@example.com"})
        """
        with get_session() as session:
            user_instance = session.get(User, user_id)
            if not user_instance:
                return None
            for key, value in data.items():
                setattr(user_instance, key, value)
            session.add(user_instance)
            session.commit()
            if is_starrocks_engine():
                return session.exec(
                    select(User).where(User.id == user_id)
                ).first()
            session.refresh(user_instance)
            return user_instance

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Deletes a User record by ID.

        Args:
            user_id: The unique identifier of the user to delete.

        Returns:
            True if the user was found and deleted, False otherwise.

        To use this method, import DatabaseActor.  For example::

            from litepolis_database_default import DatabaseActor

            success = DatabaseActor.delete_user(user_id=1)
        """
        with get_session() as session:
            user_instance = session.get(User, user_id)
            if not user_instance:
                return False
            session.delete(user_instance)
            session.commit()
            return True
            
    @staticmethod
    def search_users_by_email(query: str) -> List[User]:
        """Searches for users whose email address contains the specified query string.

        Args:
            query: The string to search for within email addresses.

        Returns:
            A list of User objects matching the search query.

        To use this method, import DatabaseActor.  For example::

            from litepolis_database_default import DatabaseActor

            users = DatabaseActor.search_users_by_email(query="example.com")
        """
        with get_session() as session:
            return session.exec(select(User).where(User.email.contains(query))).all()

    @staticmethod
    def list_users_by_admin_status(is_admin: bool) -> List[User]:
        """Lists users based on their admin status.

        Args:
            is_admin: A boolean indicating whether to list administrators (True) or non-administrators (False).

        Returns:
            A list of User objects matching the specified admin status.

        To use this method, import DatabaseActor.  For example::

            from litepolis_database_default import DatabaseActor

            users = DatabaseActor.list_users_by_admin_status(is_admin=True)
        """
        with get_session() as session:
            return session.exec(select(User).where(User.is_admin == is_admin)).all()

    @staticmethod
    def list_users_created_in_date_range(start_date: datetime, end_date: datetime) -> List[User]:
        """Lists users created within a specified date range (inclusive).

        Args:
            start_date: The start of the date range.
            end_date: The end of the date range.

        Returns:
            A list of User objects created within the specified range.

        To use this method, import DatabaseActor.  For example::

            from litepolis_database_default import DatabaseActor

            users = DatabaseActor.list_users_created_in_date_range(start_date=datetime(2023, 1, 1), end_date=datetime(2023, 12, 31))
        """
        with get_session() as session:
            return session.exec(
                select(User).where(User.created >= start_date, User.created <= end_date)
            ).all()

    @staticmethod
    def count_users() -> int:
        """Counts the total number of User records in the database.

        Returns:
            The total count of users.

        To use this method, import DatabaseActor.  For example:

            from litepolis_database_default import DatabaseActor

            count = DatabaseActor.count_users()
        """
        from sqlalchemy import func
        with get_session() as session:
            return session.scalar(select(func.count(User.id))) or 0
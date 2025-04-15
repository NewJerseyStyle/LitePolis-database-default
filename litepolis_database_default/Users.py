"""
This module defines the User type hint and UserManager class for interacting
with the 'users' table in the database using SQLAlchemy Core API.

The 'users' table stores information about users, including their email,
authentication token, and admin status. It also includes timestamps for
creation and modification.

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

    * - Report
      - One-to-many. (Handled manually)
    * - Comment
      - One-to-many. (Handled manually)
    * - Vote
      - One-to-many. (Handled manually)

The UserManager class provides static methods for performing CRUD operations
on the 'users' table using SQLAlchemy Core API.

To use the methods in this module, import DatabaseActor.  For example::

    from litepolis_database_default import DatabaseActor

    user_data = DatabaseActor.create_user({
        "email": "test@example.com",
        "auth_token": "auth_token",
    })
"""

from sqlalchemy import (
    Table, Column, Integer, String, DateTime, Boolean, MetaData, Index,
    UniqueConstraint, select, insert, update, delete, func,
    DDL
)
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC

from .utils import get_session, engine, metadata

class BaseModel:
    id: int
    created: datetime
    modified: datetime

    def __init__(self, id: int, created: datetime, modified: datetime):
        self.id = id
        self.created = created
        self.modified = modified


user_table = Table(
    "users",
    metadata, # Consider using a shared MetaData object from utils
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("auth_token", String(2048), nullable=False),
    Column("is_admin", Boolean, default=False),
    Column("created", DateTime(timezone=True), default=datetime.now(UTC)),
    Column("modified", DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC)), # Add onupdate
    UniqueConstraint("email", name="uq_user_email"),
    Index("ix_user_created", "created"),
    Index("ix_user_is_admin", "is_admin"),
)


expected_keys = [column.key for column in user_table.columns]

class User(BaseModel): # Keep the User class for type hinting
    email: str
    auth_token: str
    is_admin: bool = False
    # Note: Relationships like reports, comments, votes need manual handling

    def __init__(self, id: int, created: datetime, modified: datetime, email: str, auth_token: str, is_admin: bool = False):
        super().__init__(id=id, created=created, modified=modified)
        self.email = email
        self.auth_token = auth_token
        self.is_admin = is_admin

class UserManager:
    @staticmethod
    def _row_to_user(row) -> Optional[User]:
        """Converts a SQLAlchemy Row object to a User type hint object."""
        if row is None:
            return None
        return User(
            id=row.id,
            created=row.created,
            modified=row.modified,
            email=row.email,
            auth_token=row.auth_token,
            is_admin=row.is_admin
        )

    @staticmethod
    def create_user(data: Dict[str, Any]) -> Optional[User]:
        """Creates a new User record using Core API."""
        data = {k: v for k, v in data.items() if k in expected_keys}
        stmt = insert(user_table).values(**data)
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()                
                return UserManager.read_user_by_email(data["email"])
            except Exception as e:
                session.rollback()
                print(f"Error creating user: {e}")
                return None

    @staticmethod
    def read_user(user_id: int) -> Optional[User]:
        """Reads a User record by ID using Core API."""
        stmt = select(user_table).where(user_table.c.id == user_id)
        with get_session() as session:
            result = session.execute(stmt)
            row = result.first()
            return UserManager._row_to_user(row)

    @staticmethod
    def read_user_by_email(email: str) -> Optional[User]:
        """Reads a User record by email using Core API."""
        stmt = select(user_table).where(user_table.c.email == email)
        with get_session() as session:
            result = session.execute(stmt)
            row = result.first()
            return UserManager._row_to_user(row)


    @staticmethod
    def list_users(page: int = 1, page_size: int = 10) -> List[User]:
        """Lists User records with pagination using Core API."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        stmt = select(user_table).offset(offset).limit(page_size)
        users = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 user = UserManager._row_to_user(row)
                 if user:
                    users.append(user)
        return users


    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """Updates a User record by ID using Core API."""
        data = {k: v for k, v in data.items() if k in expected_keys + ['modified']}
        if 'modified' not in data: # Ensure 'modified' timestamp is updated
             data['modified'] = datetime.now(UTC)
        
        row = UserManager.read_user(user_id)
        for k, v in vars(row).items():
            if k not in data:
                data[k] = v
        UserManager.delete_user(user_id)
        return UserManager.create_user(data)

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Deletes a User record by ID using Core API."""
        stmt = delete(user_table).where(user_table.c.id == user_id)
        with get_session() as session:
            try:
                result = session.execute(stmt)
                session.commit()
                return result.rowcount > 0
            except Exception as e:
                session.rollback()
                print(f"Error deleting user {user_id}: {e}")
                return False

    @staticmethod
    def search_users_by_email(query: str) -> List[User]:
        """Search users by email using Core API."""
        search_term = f"%{query}%" # Assuming partial match search
        stmt = select(user_table).where(user_table.c.email.like(search_term))
        users = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 user = UserManager._row_to_user(row)
                 if user:
                    users.append(user)
        return users

    @staticmethod
    def list_users_by_admin_status(is_admin: bool) -> List[User]:
        """List users by admin status using Core API."""
        stmt = select(user_table).where(user_table.c.is_admin == is_admin)
        users = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 user = UserManager._row_to_user(row)
                 if user:
                    users.append(user)
        return users

    @staticmethod
    def list_users_created_in_date_range(start_date: datetime, end_date: datetime) -> List[User]:
        """List users created in a date range using Core API."""
        stmt = select(user_table).where(
            user_table.c.created >= start_date,
            user_table.c.created <= end_date
        )
        users = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 user = UserManager._row_to_user(row)
                 if user:
                    users.append(user)
        return users

    @staticmethod
    def count_users() -> int:
        """Counts all User records using Core API."""
        stmt = select(func.count(user_table.c.id))
        with get_session() as session:
            result = session.execute(stmt)
            count = result.scalar()
            return count if count is not None else 0
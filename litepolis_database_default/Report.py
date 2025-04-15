"""
This module defines the database schema for reports, including the `Report` type hint,
`ReportStatus` enum, and `ReportManager` class for managing reports using SQLAlchemy Core API.

The database schema includes tables for users, comments, and reports,
with relationships defined between them. The `report_table` object represents the
reports table storing information about individual reports.

.. list-table:: Table Schemas
    :header-rows: 1

    * - Table Name
        - Description
    * - users
        - Stores user information (id, email, auth_token, etc.).
    * - comments
        - Stores comment information (id, text, user_id, conversation_id, parent_comment_id, created, modified).
    * - reports
        - Stores report information (id, reporter_id, target_comment_id, reason, status, created, modified, resolved_at, resolution_notes).

.. list-table:: Reports Table Details
    :header-rows: 1

    * - Column Name
        - Description
    * - id (int)
        - Primary key for the report.
    * - reporter_id (int, optional)
        - Foreign key referencing the user who created the report.
    * - target_comment_id (int, optional)
        - Foreign key referencing the comment being reported.
    * - reason (str)
        - The reason for the report.
    * - status (ReportStatus)
        - The status of the report (pending, resolved, escalated).
    * - created (datetime)
        - Timestamp of when the report was created.
    * - modified (datetime)
        - Timestamp of when the report was last modified.
    * - resolved_at (datetime, optional)
        - Timestamp of when the report was resolved.
    * - resolution_notes (str, optional)
        - Notes about the resolution of the report.

.. list-table:: Classes
    :header-rows: 1

    * - Class Name
        - Description
    * - BaseModel
        - Base class for type hinting common fields like `id`, `created`, and `modified`.
    * - ReportStatus
        - Enum representing the status of a report (pending, resolved, escalated).
    * - Report
        - Type hint class representing a report record.
    * - ReportManager
        - Provides static methods for managing reports using SQLAlchemy Core API.

To use the methods in this module, import `DatabaseActor` from
`litepolis_database_default`. For example:

.. code-block:: py

    from litepolis_database_default import DatabaseActor

    report_data = DatabaseActor.create_report({
        "reporter_id": 1,
        "target_comment_id": 2,
        "reason": "Inappropriate content",
        "status": "pending" # or ReportStatus.pending
    })
"""


from sqlalchemy import (
    Table, Column, Integer, String, DateTime, ForeignKey, Enum, MetaData, Index,
    ForeignKeyConstraint, select, insert, update, delete, func, asc, desc
)
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC
import enum

from .utils import get_session, engine, metadata


class BaseModel:
    def __init__(self, id: int, created: datetime, modified: datetime):
        self.id = id
        self.created = created
        self.modified = modified

class ReportStatus(str, enum.Enum):
    pending = "pending"
    resolved = "resolved"
    escalated = "escalated"


report_table = Table(
    "reports",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("reporter_id", Integer, ForeignKey("users.id"), nullable=True),
    Column("target_comment_id", Integer, ForeignKey("comments.id"), nullable=True),
    Column("reason", String(16_000), nullable=False),
    Column("status", String(10), default=ReportStatus.pending, nullable=False),
    Column("created", DateTime(timezone=True), default=datetime.now(UTC)),
    Column("modified", DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC)), # Add onupdate
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("resolution_notes", String(16_000), nullable=True),
    Index("ix_report_status", "status"),
    Index("ix_report_reporter_id", "reporter_id"),
    Index("ix_report_target_comment_id", "target_comment_id"),
    Index("ix_report_created", "created"),
    ForeignKeyConstraint(['reporter_id'], ['users.id'], name='fk_report_reporter_id'),
    ForeignKeyConstraint(['target_comment_id'], ['comments.id'], name='fk_report_target_comment_id'),
    starrocks_key_desc='PRIMARY KEY(id)',
    starrocks_distribution_desc='DISTRIBUTED BY HASH(id)',
)

class Report(BaseModel): # Keep the Report class for type hinting
    reporter_id: Optional[int] = None
    target_comment_id: Optional[int] = None
    reason: str
    status: ReportStatus
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    def __init__(self, id: int, created: datetime, modified: datetime, reporter_id: Optional[int] = None, target_comment_id: Optional[int] = None, reason: str = "", status: ReportStatus = ReportStatus.pending, resolved_at: Optional[datetime] = None, resolution_notes: Optional[str] = None):
        super().__init__(id=id, created=created, modified=modified)
        self.reporter_id = reporter_id
        self.target_comment_id = target_comment_id
        self.reason = reason
        self.status = status
        self.resolved_at = resolved_at
        self.resolution_notes = resolution_notes
    # Note: Relationships like reporter, target_comment need manual handling

class ReportManager:
    @staticmethod
    def _row_to_report(row) -> Optional[Report]:
        """Converts a SQLAlchemy Row object to a Report type hint object."""
        if row is None:
            return None
        return Report(
            id=row.id,
            created=row.created,
            modified=row.modified,
            reporter_id=row.reporter_id,
            target_comment_id=row.target_comment_id,
            reason=row.reason,
            status=row.status, # Enum should be handled correctly by SQLAlchemy
            resolved_at=row.resolved_at,
            resolution_notes=row.resolution_notes
        )

    @staticmethod
    def create_report(data: Dict[str, Any]) -> Optional[Report]:
        """Creates a new Report record using Core API."""
        # Ensure status is the enum value if a string is passed
        if isinstance(data.get("status"), str):
            data["status"] = ReportStatus(data["status"])

        stmt = insert(report_table).values(**data)
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
                result = ReportManager.list_reports_by_reporter_id(data["reporter_id"])
                for report in result:
                    if report.target_comment_id == data["target_comment_id"]:
                        return report
            except Exception as e:
                session.rollback()
                print(f"Error creating report: {e}")
                return None

    @staticmethod
    def read_report(report_id: int) -> Optional[Report]:
        """Reads a Report record by ID using Core API."""
        stmt = select(report_table).where(report_table.c.id == report_id)
        with get_session() as session:
            result = session.execute(stmt)
            row = result.first()
            return ReportManager._row_to_report(row)

    @staticmethod
    def list_reports_by_status(status: ReportStatus, page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "desc") -> List[Report]:
        """Lists Report records by status with pagination and sorting using Core API."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size

        sort_column = report_table.c.get(order_by, report_table.c.created)
        sort_func = desc if order_direction.lower() == "desc" else asc
        stmt = (
            select(report_table)
            .where(report_table.c.status == status)
            .order_by(sort_func(sort_column))
            .offset(offset)
            .limit(page_size)
        )
        reports = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                report = ReportManager._row_to_report(row)
                if report:
                    reports.append(report)
        return reports


    @staticmethod
    def update_report(report_id: int, data: Dict[str, Any]) -> Optional[Report]:
        """Updates a Report record by ID using Core API."""
        if 'modified' not in data: # Ensure 'modified' timestamp is updated
             data['modified'] = datetime.now(UTC)
        # Ensure status is the enum value if a string is passed
        if isinstance(data.get("status"), str):
            data["status"] = ReportStatus(data["status"])

        row = ReportManager.read_report(report_id)
        for k, v in vars(row).items():
            if k not in data:
                data[k] = v
        ReportManager.delete_report(report_id)
        return ReportManager.create_report(data)

    @staticmethod
    def delete_report(report_id: int) -> bool:
        """Deletes a Report record by ID using Core API."""
        stmt = delete(report_table).where(report_table.c.id == report_id)
        with get_session() as session:
            try:
                result = session.execute(stmt)
                session.commit()
                return result.rowcount > 0
            except Exception as e:
                session.rollback()
                print(f"Error deleting report {report_id}: {e}")
                return False

    @staticmethod
    def search_reports_by_reason(query: str) -> List[Report]:
        """Search reports by reason text using Core API."""
        search_term = f"%{query}%"
        stmt = select(report_table).where(report_table.c.reason.like(search_term))
        reports = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 report = ReportManager._row_to_report(row)
                 if report:
                    reports.append(report)
        return reports

    @staticmethod
    def list_reports_by_reporter_id(reporter_id: int, page: int = 1, page_size: int = 10) -> List[Report]:
        """List reports by reporter id with pagination using Core API."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        stmt = (
            select(report_table)
            .where(report_table.c.reporter_id == reporter_id)
            .offset(offset)
            .limit(page_size)
        )
        reports = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 report = ReportManager._row_to_report(row)
                 if report:
                    reports.append(report)
        return reports

    @staticmethod
    def list_reports_created_in_date_range(start_date: datetime, end_date: datetime) -> List[Report]:
        """List reports created in date range using Core API."""
        stmt = select(report_table).where(
            report_table.c.created >= start_date,
            report_table.c.created <= end_date
        )
        reports = []
        with get_session() as session:
            result = session.execute(stmt)
            for row in result:
                 report = ReportManager._row_to_report(row)
                 if report:
                    reports.append(report)
        return reports

    @staticmethod
    def count_reports_by_status(status: ReportStatus) -> int:
        """Counts reports by status using Core API."""
        stmt = select(func.count(report_table.c.id)).where(report_table.c.status == status)
        with get_session() as session:
            result = session.execute(stmt)
            count = result.scalar()
            return count if count is not None else 0

    @staticmethod
    def resolve_report(report_id: int, resolution_notes: str) -> Optional[Report]:
        """Resolves a report using Core API."""
        update_data = {
            "status": ReportStatus.resolved,
            "resolved_at": datetime.now(UTC),
            "resolution_notes": resolution_notes,
            "modified": datetime.now(UTC) # Also update modified time
        }
        stmt = (
            update(report_table)
            .where(report_table.c.id == report_id)
            .values(**update_data)
        )
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
                return ReportManager.read_report(data["id"])
            except Exception as e:
                session.rollback()
                print(f"Error resolving report {report_id}: {e}")
                return None

    @staticmethod
    def escalate_report(report_id: int, resolution_notes: str) -> Optional[Report]:
        """Escalates a report using Core API."""
        update_data = {
            "status": ReportStatus.escalated,
            "resolved_at": datetime.now(UTC), # Consider if resolved_at should be set on escalation
            "resolution_notes": resolution_notes,
            "modified": datetime.now(UTC) # Also update modified time
        }
        stmt = (
            update(report_table)
            .where(report_table.c.id == report_id)
            .values(**update_data)
        )
        with get_session() as session:
            try:
                session.execute(stmt)
                session.commit()
                return ReportManager.read_report(data["id"])
            except Exception as e:
                session.rollback()
                print(f"Error escalating report {report_id}: {e}")
                return None
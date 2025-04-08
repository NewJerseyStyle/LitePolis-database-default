    """
    This module defines the database schema for reports, including the `Report` model,
    `ReportStatus` enum, and `ReportManager` class for managing reports.

    The database schema includes tables for users, comments, and reports,
    with relationships defined between them. The `Report` table stores information
    about individual reports, including the reporter, target comment, reason,
    status, and resolution details.

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
         - Base class for all database models, providing common fields like `id`, `created`, and `modified`.
       * - ReportStatus
         - Enum representing the status of a report (pending, resolved, escalated).
       * - Report
         - SQLModel class representing the `reports` table.
       * - ReportManager
         - Provides static methods for managing reports.

    To use the methods in this module, import `DatabaseActor` from
    `litepolis_database_default`. For example:

    .. code-block:: py

        from litepolis_database_default import DatabaseActor

        report = DatabaseActor.create_report({
            "reporter_id": 1,
            "target_comment_id": 2,
            "reason": "Inappropriate content",
            "status": "pending"
        })
    """


from sqlalchemy import ForeignKeyConstraint
from sqlmodel import SQLModel, Field, Relationship, Column, Index, ForeignKey, Enum
from sqlmodel import select
from typing import Optional, List, Type, Any, Dict, Generator
from datetime import datetime, UTC
import enum

from .utils import get_session


class BaseModel(SQLModel):
    id: int = Field(primary_key=True)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReportStatus(str, enum.Enum):
    pending = "pending"
    resolved = "resolved"
    escalated = "escalated"


class Report(BaseModel, table=True):
    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_report_status", "status"),
        Index("ix_report_reporter_id", "reporter_id"),
        Index("ix_report_target_comment_id", "target_comment_id"),
        Index("ix_report_created", "created"),
        ForeignKeyConstraint(['reporter_id'], ['users.id'], name='fk_report_reporter_id'),
        ForeignKeyConstraint(['target_comment_id'], ['comments.id'], name='fk_report_target_comment_id')
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    reporter_id: Optional[int] = Field(default=None, foreign_key="users.id")
    target_comment_id: Optional[int] = Field(default=None, foreign_key="comments.id")
    reason: str = Field(nullable=False)
    status: ReportStatus = Field(sa_column=Column(Enum(ReportStatus), default=ReportStatus.pending, nullable=False, index=True))  # Keep index here as it's defined in sa_column
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: Optional[datetime] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)

    reporter: Optional["User"] = Relationship(back_populates="reports")
    # target_comment: Optional["Comment"] = Relationship(back_populates="reports")


class ReportManager:
    @staticmethod
    def create_report(data: Dict[str, Any]) -> Report:
        """Creates a new Report record.

        Args:
            data (Dict[str, Any]): A dictionary containing the data for the new Report.

        Returns:
            Report: The newly created Report instance.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                report = DatabaseActor.create_report({
                    "reporter_id": 1,
                    "target_comment_id": 2,
                    "reason": "Inappropriate content",
                    "status": "pending"
                })
        """
        with get_session() as session:
            report_instance = Report(**data)
            session.add(report_instance)
            session.commit()
            session.refresh(report_instance)
            return report_instance

    @staticmethod
    def read_report(report_id: int) -> Optional[Report]:
        """Reads a Report record by ID.

        Args:
            report_id (int): The ID of the Report to read.

        Returns:
            Optional[Report]: The Report instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                report = DatabaseActor.read_report(report_id=1)
        """
        with get_session() as session:
            return session.get(Report, report_id)

    @staticmethod
    def list_reports_by_status(status: ReportStatus, page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "desc") -> List[Report]:
        """Lists Report records by status with pagination and sorting.

        Args:
            status (ReportStatus): The status of the reports to list.
            page (int): The page number for pagination.
            page_size (int): The number of reports per page.
            order_by (str): The field to order the reports by.
            order_direction (str): The direction to order the reports in ("asc" or "desc").

        Returns:
            List[Report]: A list of Report instances matching the criteria.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor
                from litepolis_database_default.Report import ReportStatus

                reports = DatabaseActor.list_reports_by_status(status=ReportStatus.pending, page=1, page_size=10, order_by="created", order_direction="desc")
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        order_column = getattr(Report, order_by, Report.created)  # Default to created
        direction = "desc" if order_direction.lower() == "desc" else "asc"
        sort_order = order_column.desc() if direction == "desc" else order_column.asc()


        with get_session() as session:
            return session.exec(
                select(Report)
                .where(Report.status == status)
                .order_by(sort_order)
                .offset(offset)
                .limit(page_size)
            ).all()



    @staticmethod
    def update_report(report_id: int, data: Dict[str, Any]) -> Optional[Report]:
        """Updates a Report record by ID.

        Args:
            report_id (int): The ID of the Report to update.
            data (Dict[str, Any]): A dictionary containing the data to update.

        Returns:
            Optional[Report]: The updated Report instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                updated_report = DatabaseActor.update_report(report_id=1, data={"status": "resolved"})
        """
        with get_session() as session:
            report_instance = session.get(Report, report_id)
            if not report_instance:
                return None
            for key, value in data.items():
                setattr(report_instance, key, value)
            session.add(report_instance)
            session.commit()
            session.refresh(report_instance)
            return report_instance

    @staticmethod
    def delete_report(report_id: int) -> bool:
        """Deletes a Report record by ID.

        Args:
            report_id (int): The ID of the Report to delete.

        Returns:
            bool: True if the Report was deleted successfully, False otherwise.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                success = DatabaseActor.delete_report(report_id=1)
        """
        with get_session() as session:
            report_instance = session.get(Report, report_id)
            if not report_instance:
                return False
            session.delete(report_instance)
            session.commit()
            return True
            
    @staticmethod
    def search_reports_by_reason(query: str) -> List[Report]:
        """Search reports by reason text.

        Args:
            query (str): The search query.

        Returns:
            List[Report]: A list of Report instances matching the search query.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                reports = DatabaseActor.search_reports_by_reason(query="inappropriate")
        """
        search_term = f"%{query}%"
        with get_session() as session:
            return session.exec(
                select(Report).where(Report.reason.like(search_term))
            ).all()
            
    @staticmethod
    def list_reports_by_reporter_id(reporter_id: int, page: int = 1, page_size: int = 10) -> List[Report]:
        """List reports by reporter id with pagination.

        Args:
            reporter_id (int): The ID of the reporter.
            page (int): The page number for pagination.
            page_size (int): The number of reports per page.

        Returns:
            List[Report]: A list of Report instances matching the criteria.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                reports = DatabaseActor.list_reports_by_reporter_id(reporter_id=1, page=1, page_size=10)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        offset = (page - 1) * page_size
        with get_session() as session:
            return session.exec(
                select(Report).where(Report.reporter_id == reporter_id).offset(offset).limit(page_size)
            ).all()
            
    @staticmethod
    def list_reports_created_in_date_range(start_date: datetime, end_date: datetime) -> List[Report]:
        """List reports created in date range.

        Args:
            start_date (datetime): The start date of the range.
            end_date (datetime): The end date of the range.

        Returns:
            List[Report]: A list of Report instances created within the date range.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor
                from datetime import datetime

                start = datetime(2023, 1, 1)
                end = datetime(2023, 1, 31)
                reports = DatabaseActor.list_reports_created_in_date_range(start_date=start, end_date=end)
        """
        with get_session() as session:
            return session.exec(
                select(Report).where(
                    Report.created >= start_date, Report.created <= end_date
                )
            ).all()
            
    @staticmethod
    def count_reports_by_status(status: ReportStatus) -> int:
        """Counts reports by status.

        Args:
            status (ReportStatus): The status to count reports by.

        Returns:
            int: The number of reports with the given status.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor
                from litepolis_database_default.Report import ReportStatus

                count = DatabaseActor.count_reports_by_status(status=ReportStatus.pending)
        """
        with get_session() as session:
            return session.scalar(
                select(Report).where(Report.status == status).count()
            ) or 0
            
    @staticmethod
    def resolve_report(report_id: int, resolution_notes: str) -> Optional[Report]:
        """Resolves a report.

        Args:
            report_id (int): The ID of the report to resolve.
            resolution_notes (str): Notes about the resolution.

        Returns:
            Optional[Report]: The resolved Report instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                resolved_report = DatabaseActor.resolve_report(report_id=1, resolution_notes="Resolved after review.")
        """
        with get_session() as session:
            report_instance = session.get(Report, report_id)
            if not report_instance:
                return None
            report_instance.status = ReportStatus.resolved
            report_instance.resolved_at = datetime.now(UTC)
            report_instance.resolution_notes = resolution_notes
            session.add(report_instance)
            session.commit()
            session.refresh(report_instance)
            return report_instance
            
    @staticmethod
    def escalate_report(report_id: int, resolution_notes: str) -> Optional[Report]:
        """Escalates a report.

        Args:
            report_id (int): The ID of the report to escalate.
            resolution_notes (str): Notes about the escalation.

        Returns:
            Optional[Report]: The escalated Report instance if found, otherwise None.

        Example:
            .. code-block:: python

                from litepolis_database_default import DatabaseActor

                escalated_report = DatabaseActor.escalate_report(report_id=1, resolution_notes="Escalated for further review.")
        """
        with get_session() as session:
            report_instance = session.get(Report, report_id)
            if not report_instance:
                return None
            report_instance.status = ReportStatus.escalated
            report_instance.resolved_at = datetime.now(UTC)
            report_instance.resolution_notes = resolution_notes
            session.add(report_instance)
            session.commit()
            session.refresh(report_instance)
            return report_instance
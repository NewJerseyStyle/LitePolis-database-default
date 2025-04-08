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
        """Creates a new Report record."""
        with get_session() as session:
            report_instance = Report(**data)
            session.add(report_instance)
            session.commit()
            session.refresh(report_instance)
            return report_instance

    @staticmethod
    def read_report(report_id: int) -> Optional[Report]:
        """Reads a Report record by ID."""
        with get_session() as session:
            return session.get(Report, report_id)

    @staticmethod
    def list_reports_by_status(status: ReportStatus, page: int = 1, page_size: int = 10, order_by: str = "created", order_direction: str = "desc") -> List[Report]:
        """Lists Report records by status with pagination and sorting."""
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
        """Updates a Report record by ID."""
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
        """Deletes a Report record by ID."""
        with get_session() as session:
            report_instance = session.get(Report, report_id)
            if not report_instance:
                return False
            session.delete(report_instance)
            session.commit()
            return True
            
    @staticmethod
    def search_reports_by_reason(query: str) -> List[Report]:
        """Search reports by reason text."""
        search_term = f"%{query}%"
        with get_session() as session:
            return session.exec(
                select(Report).where(Report.reason.like(search_term))
            ).all()
            
    @staticmethod
    def list_reports_by_reporter_id(reporter_id: int, page: int = 1, page_size: int = 10) -> List[Report]:
        """List reports by reporter id with pagination."""
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
        """List reports created in date range."""
        with get_session() as session:
            return session.exec(
                select(Report).where(
                    Report.created >= start_date, Report.created <= end_date
                )
            ).all()
            
    @staticmethod
    def count_reports_by_status(status: ReportStatus) -> int:
        """Counts reports by status."""
        with get_session() as session:
            return session.scalar(
                select(Report).where(Report.status == status).count()
            ) or 0
            
    @staticmethod
    def resolve_report(report_id: int, resolution_notes: str) -> Optional[Report]:
        """Resolves a report."""
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
        """Escalates a report."""
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
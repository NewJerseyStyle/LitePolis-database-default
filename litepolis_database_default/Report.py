from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Type, Any, Dict
from datetime import datetime, UTC

# Removed BaseManager import
from .utils import create_db_and_tables, get_session # Import get_session
from sqlmodel import Session, select # Import Session and select

class BaseModel(SQLModel):
    id: int = Field(primary_key=True)
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified: datetime = Field(default_factory=lambda: datetime.now(UTC))

class Report(BaseModel, table=True):
    __tablename__ = "reports"
    reporter_id: int = Field(foreign_key="users.id")
    target_comment_id: int = Field(foreign_key="comments.id")
    reason: str
    status: str = Field(default="pending")  # pending/resolved

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
            report_instance = session.get(Report, report_id)
            return report_instance

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
    def list_reports() -> List[Report]:
        """Lists all Report records."""
        with get_session() as session:
            report_instances = session.exec(select(Report)).all()
            return report_instances

    @staticmethod
    def update_report_status(report_id: int, status: str) -> Optional[Report]:
        """Specific method to update only the report status."""
        with get_session() as session:
            report_instance = session.get(Report, report_id)
            if not report_instance:
                return None
            report_instance.status = status # type: ignore
            session.add(report_instance)
            session.commit()
            session.refresh(report_instance)
            return report_instance


create_db_and_tables()
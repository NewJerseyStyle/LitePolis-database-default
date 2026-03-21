"""
Participant model and ParticipantManager for managing conversation participants.

In Polis, participants are users who have joined a conversation. Each participant
has a unique pid per (zid, uid) combination.

.. list-table:: Table Schema
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - pid
     - INTEGER
     - Unique participant ID (primary key)
   * - zid
     - INTEGER
     - Foreign key to conversation
   * - uid
     - INTEGER
     - Foreign key to user
   * - created
     - DATETIME
     - When participant joined
   * - modified
     - DATETIME
     - Last modification time
   * - vote_count
     - INTEGER
     - Number of votes cast
   * - mod
     - INTEGER
     - Moderation status (0=active)

To use this module::

    from litepolis_database_default import DatabaseActor

    participant = DatabaseActor.create_participant({
        "zid": 1,
        "uid": 1
    })
"""

from sqlalchemy import DDL, UniqueConstraint, ForeignKeyConstraint, Index
from sqlmodel import SQLModel, Field, Relationship, Column, select
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .utils import get_session, is_starrocks_engine
from .utils_StarRocks import register_table


@register_table(distributed_by="HASH(pid)")
class Participant(SQLModel, table=True):
    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("zid", "uid", name="uq_participant_zid_uid"),
        Index("ix_participant_zid", "zid"),
        Index("ix_participant_uid", "uid"),
        ForeignKeyConstraint(['zid'], ['conversations.id'], name='fk_participant_zid'),
        ForeignKeyConstraint(['uid'], ['users.id'], name='fk_participant_uid'),
    )

    pid: Optional[int] = Field(default=None, primary_key=True)
    zid: int = Field(nullable=False)
    uid: int = Field(nullable=False)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    vote_count: int = Field(default=0)
    mod: int = Field(default=0)


class ParticipantManager:
    @staticmethod
    def create_participant(data: Dict[str, Any]) -> Participant:
        """Creates a new Participant record.

        Args:
            data: Must include 'zid' and 'uid'.

        Returns:
            The created Participant instance.

        Example:
            from litepolis_database_default import DatabaseActor
            participant = DatabaseActor.create_participant({"zid": 1, "uid": 1})
        """
        with get_session() as session:
            participant = Participant(**data)
            session.add(participant)
            session.commit()
            if is_starrocks_engine():
                return session.exec(
                    select(Participant).where(
                        Participant.zid == data["zid"],
                        Participant.uid == data["uid"]
                    )
                ).first()
            session.refresh(participant)
            return participant

    @staticmethod
    def read_participant(pid: int) -> Optional[Participant]:
        """Reads a Participant by ID."""
        with get_session() as session:
            return session.get(Participant, pid)

    @staticmethod
    def get_participant_by_zid_uid(zid: int, uid: int) -> Optional[Participant]:
        """Gets participant by conversation and user IDs."""
        with get_session() as session:
            return session.exec(
                select(Participant).where(
                    Participant.zid == zid,
                    Participant.uid == uid
                )
            ).first()

    @staticmethod
    def get_or_create_participant(zid: int, uid: int) -> Participant:
        """Gets existing participant or creates new one."""
        participant = ParticipantManager.get_participant_by_zid_uid(zid, uid)
        if participant:
            return participant
        return ParticipantManager.create_participant({"zid": zid, "uid": uid})

    @staticmethod
    def list_participants_by_zid(zid: int, page: int = 1, page_size: int = 100) -> List[Participant]:
        """Lists participants in a conversation with pagination."""
        if page < 1:
            page = 1
        offset = (page - 1) * page_size
        with get_session() as session:
            return session.exec(
                select(Participant)
                .where(Participant.zid == zid)
                .offset(offset)
                .limit(page_size)
            ).all()

    @staticmethod
    def count_participants(zid: int) -> int:
        """Counts participants in a conversation."""
        with get_session() as session:
            from sqlalchemy import func
            return session.scalar(
                select(func.count(Participant.pid)).where(Participant.zid == zid)
            ) or 0

    @staticmethod
    def update_participant(pid: int, data: Dict[str, Any]) -> Optional[Participant]:
        """Updates a Participant record."""
        with get_session() as session:
            participant = session.get(Participant, pid)
            if not participant:
                return None
            for key, value in data.items():
                if hasattr(participant, key):
                    setattr(participant, key, value)
            session.add(participant)
            session.commit()
            if is_starrocks_engine():
                return session.get(Participant, pid)
            session.refresh(participant)
            return participant

    @staticmethod
    def increment_vote_count(pid: int) -> Optional[Participant]:
        """Increments vote count for a participant."""
        with get_session() as session:
            participant = session.get(Participant, pid)
            if not participant:
                return None
            participant.vote_count += 1
            participant.modified = datetime.now(timezone.utc)
            session.add(participant)
            session.commit()
            if is_starrocks_engine():
                return session.get(Participant, pid)
            session.refresh(participant)
            return participant

    @staticmethod
    def delete_participant(pid: int) -> bool:
        """Deletes a Participant record."""
        with get_session() as session:
            participant = session.get(Participant, pid)
            if not participant:
                return False
            session.delete(participant)
            session.commit()
            return True

    @staticmethod
    def get_or_create_anonymous_participant(zid: int, pc_token: str) -> Participant:
        """Gets or creates an anonymous participant using a pc token.
        
        Uses negative UIDs derived from hash of pc_token to distinguish anonymous users.
        """
        import hashlib
        uid = -abs(int(hashlib.md5(pc_token.encode()).hexdigest()[:8], 16))
        
        participant = ParticipantManager.get_participant_by_zid_uid(zid, uid)
        if participant:
            return participant
        return ParticipantManager.create_participant({"zid": zid, "uid": uid})

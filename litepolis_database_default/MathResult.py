"""
MathResult model for caching mathematical computation results.

Stores PCA, clustering, and repness computation results for conversations.
Each record is keyed by (zid, math_tick) where math_tick increments on each update.

.. list-table:: Table Schema
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - zid
     - INTEGER
     - Foreign key to conversation (part of composite PK)
   * - math_tick
     - INTEGER
     - Computation version number (part of composite PK)
   * - data
     - JSON
     - Computation results (pca, clusters, repness, etc.)
   * - created
     - DATETIME
     - When computation was performed

To use this module::

    from litepolis_database_default import DatabaseActor

    # Store math results
    result = DatabaseActor.create_math_result({
        "zid": 1,
        "math_tick": 1,
        "data": {"n": 10, "n-cmts": 5, ...}
    })

    # Retrieve latest results
    result = DatabaseActor.get_latest_math_result(1)
"""

from sqlalchemy import DDL, ForeignKeyConstraint, Index, Column, Text
from sqlmodel import SQLModel, Field, select
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json

from .utils import get_session, is_starrocks_engine
from .utils_StarRocks import register_table


@register_table(distributed_by="HASH(zid)")
class MathResult(SQLModel, table=True):
    __tablename__ = "math_results"
    __table_args__ = (
        Index("ix_math_results_zid", "zid"),
        ForeignKeyConstraint(['zid'], ['conversations.id'], name='fk_math_result_zid'),
    )

    zid: int = Field(nullable=False, primary_key=True)
    math_tick: int = Field(nullable=False, primary_key=True, default=1)
    data: str = Field(default="{}", sa_column=Column(Text))
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_data(self) -> Dict[str, Any]:
        """Parse JSON data field."""
        return json.loads(self.data) if self.data else {}

    def set_data(self, data: Dict[str, Any]):
        """Serialize data to JSON."""
        self.data = json.dumps(data, default=str)


class MathResultManager:
    @staticmethod
    def create_math_result(data: Dict[str, Any]) -> MathResult:
        """Creates a new MathResult record.

        Args:
            data: Must include 'zid', 'math_tick'. 'data' should be a dict.

        Returns:
            The created MathResult instance.
        """
        with get_session() as session:
            # Serialize data dict to JSON string
            result_data = data.copy()
            if 'data' in result_data and isinstance(result_data['data'], dict):
                result_data['data'] = json.dumps(result_data['data'], default=str)

            math_result = MathResult(**result_data)
            session.add(math_result)
            session.commit()
            if is_starrocks_engine():
                return session.exec(
                    select(MathResult).where(
                        MathResult.zid == result_data["zid"],
                        MathResult.math_tick == result_data["math_tick"]
                    )
                ).first()
            session.refresh(math_result)
            return math_result

    @staticmethod
    def get_math_result(zid: int, math_tick: int) -> Optional[MathResult]:
        """Gets a specific MathResult by zid and math_tick."""
        with get_session() as session:
            return session.exec(
                select(MathResult).where(
                    MathResult.zid == zid,
                    MathResult.math_tick == math_tick
                )
            ).first()

    @staticmethod
    def get_latest_math_result(zid: int) -> Optional[MathResult]:
        """Gets the latest (highest math_tick) MathResult for a conversation."""
        with get_session() as session:
            results = session.exec(
                select(MathResult)
                .where(MathResult.zid == zid)
                .order_by(MathResult.math_tick.desc())
            ).all()
            return results[0] if results else None

    @staticmethod
    def get_latest_data(zid: int) -> Optional[Dict[str, Any]]:
        """Gets the data dict from the latest MathResult."""
        result = MathResultManager.get_latest_math_result(zid)
        if result:
            return result.get_data()
        return None

    @staticmethod
    def get_current_tick(zid: int) -> int:
        """Gets the current math_tick for a conversation (0 if none)."""
        result = MathResultManager.get_latest_math_result(zid)
        return result.math_tick if result else 0

    @staticmethod
    def store_result(zid: int, data: Dict[str, Any]) -> MathResult:
        """Store computation results, incrementing math_tick automatically.

        Args:
            zid: Conversation ID
            data: Computation results dict

        Returns:
            The created MathResult with new math_tick
        """
        current_tick = MathResultManager.get_current_tick(zid)
        new_tick = current_tick + 1

        # Ensure math_tick is in the data
        data_with_tick = data.copy()
        data_with_tick['math_tick'] = new_tick

        return MathResultManager.create_math_result({
            "zid": zid,
            "math_tick": new_tick,
            "data": data_with_tick
        })

    @staticmethod
    def delete_math_results(zid: int) -> int:
        """Deletes all MathResults for a conversation. Returns count deleted."""
        with get_session() as session:
            results = session.exec(
                select(MathResult).where(MathResult.zid == zid)
            ).all()
            count = len(results)
            for r in results:
                session.delete(r)
            session.commit()
            return count

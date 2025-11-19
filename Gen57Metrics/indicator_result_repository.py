"""
Indicator result persistence layer.

This module owns the logic that persists the 57 indicator outputs into
PostgreSQL. The repository follows SOLID guidelines:
- Single Responsibility: only handles DB persistence for indicator results.
- Open/Closed: table name and payload schema are configurable.
- Dependency Inversion: depends on connect() abstraction from utils_database_manager.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    from psycopg2.extras import execute_values, Json as PsycopgJson
except ImportError:  # pragma: no cover - handled at runtime when psycopg2 missing
    execute_values = None  # type: ignore
    PsycopgJson = None  # type: ignore

from Gen57Metrics.utils_database_manager import connect


@dataclass(frozen=True)
class IndicatorResultRow:
    """Value object representing a json_raw payload per stock-period."""

    stock: str
    year: int
    quarter: int
    json_raw: Dict[str, Any]

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "IndicatorResultRow":
        if not payload:
            raise ValueError("payload is required")
        stock = str(payload.get("stock", "")).strip().upper()
        if not stock:
            raise ValueError("payload.stock is required")
        year = int(payload.get("year"))
        quarter_value = payload.get("quarter")
        if quarter_value is None:
            raise ValueError("payload.quarter is required")
        quarter = int(quarter_value)
        json_raw = payload.get("json_raw")
        if json_raw is None:
            raise ValueError("payload.json_raw is required")
        if not isinstance(json_raw, dict):
            raise ValueError("payload.json_raw must be a dict")
        return cls(stock=stock, year=year, quarter=quarter, json_raw=json_raw)

    def as_tuple(self) -> tuple:
        return (
            self.stock,
            self.year,
            self.quarter,
            PsycopgJson(self.json_raw) if PsycopgJson else self.json_raw,
        )


class IndicatorResultRepository:
    """Repository that persists indicator outputs."""

    DEFAULT_TABLE = "indicator_57"

    def __init__(self, table_name: Optional[str] = None):
        if execute_values is None or PsycopgJson is None:
            raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
        self.table_name = table_name or self.DEFAULT_TABLE

    def _ensure_table(self, cursor) -> None:
        """Create the table and supporting indexes if needed."""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS "{self.table_name}" (
            id SERIAL PRIMARY KEY,
            stock VARCHAR(10) NOT NULL,
            year INTEGER NOT NULL,
            quarter SMALLINT NOT NULL,
            json_raw JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock, year, quarter)
        );
        """
        cursor.execute(create_table_sql)

    def save_row(self, payload: Dict[str, Any]) -> int:
        """
        Persist a single json_raw payload for a stock/period.

        Args:
            payload: Dict with keys stock, year, quarter, json_raw.

        Returns:
            Number of rows written (1 or 0).
        """
        row = IndicatorResultRow.from_payload(payload)

        insert_sql = f"""
        INSERT INTO "{self.table_name}"
            (stock, year, quarter, json_raw)
        VALUES %s
        ON CONFLICT (stock, year, quarter)
        DO UPDATE SET
            json_raw = EXCLUDED.json_raw,
            updated_at = CURRENT_TIMESTAMP;
        """

        conn = connect()
        try:
            with conn:
                with conn.cursor() as cursor:
                    self._ensure_table(cursor)
                    execute_values(cursor, insert_sql, [row.as_tuple()])
            return 1
        finally:
            conn.close()


def save_indicator_result_payload(result_payload: Dict[str, Any], table_name: Optional[str] = None) -> int:
    """
    Convenience helper that saves the standard calculator payload.

    Args:
        result_payload: Output from IndicatorCalculator.calculate_all().
        table_name: Optional override table name.

    Returns:
        Number of rows written.
    """
    repository = IndicatorResultRepository(table_name=table_name)
    return repository.save_row(result_payload)


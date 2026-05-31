"""Helpers for reading Snowflake transfer SQL files."""

from __future__ import annotations

from pathlib import Path


SQL_DIR = Path("sql/snowflake")


def available_sql_templates(sql_dir: Path = SQL_DIR) -> list[str]:
    """List v2 Snowflake SQL templates."""

    if not sql_dir.exists():
        return []
    return sorted(path.name for path in sql_dir.glob("*.sql"))


def load_sql_template(name: str, sql_dir: Path = SQL_DIR) -> str:
    """Read a named SQL template."""

    path = sql_dir / name
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")

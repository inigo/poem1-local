import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "poems.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS poems (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                time_str  TEXT NOT NULL,
                poem      TEXT NOT NULL,
                date_used TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_poems_time_str ON poems(time_str);

            CREATE TABLE IF NOT EXISTS tags (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS poem_tags (
                poem_id INTEGER NOT NULL REFERENCES poems(id),
                tag_id  INTEGER NOT NULL REFERENCES tags(id),
                PRIMARY KEY (poem_id, tag_id)
            );

            CREATE INDEX IF NOT EXISTS idx_poem_tags_poem ON poem_tags(poem_id);
            CREATE INDEX IF NOT EXISTS idx_poem_tags_tag  ON poem_tags(tag_id);
        """)


def _get_or_create_tag(conn: sqlite3.Connection, tag: str) -> int:
    conn.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (tag,))
    row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()
    return row["id"]


def insert_poem(time_str: str, poem: str, tags: list[str], db_path: Path = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO poems(time_str, poem) VALUES (?, ?)",
            (time_str, poem),
        )
        poem_id = cur.lastrowid
        for tag in tags:
            tag_id = _get_or_create_tag(conn, tag.strip().lower())
            conn.execute(
                "INSERT OR IGNORE INTO poem_tags(poem_id, tag_id) VALUES (?, ?)",
                (poem_id, tag_id),
            )
        return poem_id


def find_poems(time_str: Optional[str] = None, tags: Optional[list[str]] = None,
               db_path: Path = DB_PATH) -> list[sqlite3.Row]:
    """Return poems matching time_str and/or all given tags."""
    conditions = []
    params: list = []

    if time_str:
        conditions.append("p.time_str = ?")
        params.append(time_str)

    if tags:
        for tag in tags:
            conditions.append("""
                p.id IN (
                    SELECT pt.poem_id FROM poem_tags pt
                    JOIN tags t ON t.id = pt.tag_id
                    WHERE t.name = ?
                )
            """)
            params.append(tag.strip().lower())

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    query = f"SELECT p.* FROM poems p {where} ORDER BY p.time_str, p.id"

    with get_connection(db_path) as conn:
        return conn.execute(query, params).fetchall()


def mark_used(poem_id: int, date_used: str, db_path: Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("UPDATE poems SET date_used = ? WHERE id = ?", (date_used, poem_id))

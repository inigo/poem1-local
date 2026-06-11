import sqlite3
import tempfile
from pathlib import Path

import pytest

from database import find_poems, init_db, insert_poem, mark_used


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test_poems.db"
    init_db(db)
    return db


def test_init_creates_tables(tmp_db):
    with sqlite3.connect(tmp_db) as conn:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    assert {"poems", "tags", "poem_tags"}.issubset(tables)


def test_insert_and_find_by_time(tmp_db):
    insert_poem("17:00", "The hour strikes softly", ["rain"], db_path=tmp_db)
    rows = find_poems(time_str="17:00", db_path=tmp_db)
    assert len(rows) == 1
    assert rows[0]["poem"] == "The hour strikes softly"


def test_insert_with_multiple_tags(tmp_db):
    insert_poem("08:30", "Half past eight, the sun climbs", ["sun", "morning"], db_path=tmp_db)
    rows = find_poems(time_str="08:30", tags=["sun"], db_path=tmp_db)
    assert len(rows) == 1
    rows2 = find_poems(tags=["morning"], db_path=tmp_db)
    assert len(rows2) == 1


def test_find_by_tag_only(tmp_db):
    insert_poem("06:00", "Dawn breaks", ["sun"], db_path=tmp_db)
    insert_poem("18:00", "Dusk falls", ["rain"], db_path=tmp_db)
    sun_rows = find_poems(tags=["sun"], db_path=tmp_db)
    assert len(sun_rows) == 1
    assert sun_rows[0]["time_str"] == "06:00"


def test_find_by_time_and_tag(tmp_db):
    insert_poem("12:00", "Noon, bright and clear", ["sun"], db_path=tmp_db)
    insert_poem("12:00", "Noon, grey and wet", ["rain"], db_path=tmp_db)
    rows = find_poems(time_str="12:00", tags=["sun"], db_path=tmp_db)
    assert len(rows) == 1
    assert "bright" in rows[0]["poem"]


def test_find_by_multiple_tags_requires_all(tmp_db):
    insert_poem("15:00", "Warm rain", ["rain", "warm"], db_path=tmp_db)
    insert_poem("15:01", "Just rain", ["rain"], db_path=tmp_db)
    rows = find_poems(tags=["rain", "warm"], db_path=tmp_db)
    assert len(rows) == 1
    assert rows[0]["time_str"] == "15:00"


def test_date_used_initially_null(tmp_db):
    pid = insert_poem("09:00", "Morning haze", [], db_path=tmp_db)
    rows = find_poems(time_str="09:00", db_path=tmp_db)
    assert rows[0]["date_used"] is None


def test_mark_used(tmp_db):
    pid = insert_poem("09:00", "Morning haze", [], db_path=tmp_db)
    mark_used(pid, "2026-06-11", db_path=tmp_db)
    rows = find_poems(time_str="09:00", db_path=tmp_db)
    assert rows[0]["date_used"] == "2026-06-11"


def test_tags_normalised_to_lowercase(tmp_db):
    insert_poem("10:00", "Mid-morning", ["Rain", "WIND"], db_path=tmp_db)
    rows = find_poems(tags=["rain"], db_path=tmp_db)
    assert len(rows) == 1


def test_shared_tags_deduped(tmp_db):
    insert_poem("11:00", "Poem A", ["rain"], db_path=tmp_db)
    insert_poem("11:01", "Poem B", ["rain"], db_path=tmp_db)
    with sqlite3.connect(tmp_db) as conn:
        tag_count = conn.execute("SELECT COUNT(*) FROM tags WHERE name='rain'").fetchone()[0]
    assert tag_count == 1


def test_no_filters_returns_all(tmp_db):
    insert_poem("00:00", "Midnight", ["moon"], db_path=tmp_db)
    insert_poem("12:00", "Noon", ["sun"], db_path=tmp_db)
    rows = find_poems(db_path=tmp_db)
    assert len(rows) == 2

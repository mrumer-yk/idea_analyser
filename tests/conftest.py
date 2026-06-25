import pytest

from backend import db
from backend.config import get_settings


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point every test at a fresh, isolated SQLite file."""
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    get_settings.cache_clear()
    db.init_db()
    yield
    get_settings.cache_clear()

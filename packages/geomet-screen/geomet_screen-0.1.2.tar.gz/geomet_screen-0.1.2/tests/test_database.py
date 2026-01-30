import tempfile
from pathlib import Path

from geomet.screen.database import DatabaseConnection, ExcelLoader  # adjust to actual exports


def test_database_connection_memory():
    db = DatabaseConnection()
    db.create_tables()

    session = db.get_session()
    assert session is not None

    session.close()
    db.close()


def test_database_connection_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DatabaseConnection(str(db_path))
        db.create_tables()

        assert db_path.exists()

        session = db.get_session()
        assert session is not None

        session.close()
        db.close()

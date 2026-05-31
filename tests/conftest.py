import os
import tempfile
import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Mock the database path to use a temporary database for testing
@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    temp_dir = tempfile.mkdtemp()
    test_db_path = Path(temp_dir) / "test_database.db"
    
    import app.database
    # Override the DB_PATH
    app.database.DB_PATH = test_db_path
    app.database.init_db() # re-init on the new path
    
    yield test_db_path
    
    # Cleanup
    if test_db_path.exists():
        os.remove(test_db_path)
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

@pytest.fixture(scope="module")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def clear_db():
    """Clear users table before each test to ensure a clean slate."""
    import app.database
    conn = sqlite3.connect(app.database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()

import sys
import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import Base
from app.models import User
from app.core.security import hash_password
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import get_db

# Store test database in local temp directory to prevent OneDrive file lock contention
TEST_DB_FILE = os.path.join(tempfile.gettempdir(), f"test_hl_{os.getpid()}.db").replace(os.sep, "/")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        farmer = User(
            name="Kumar",
            email="kumar@test.org",
            hashed_password=hash_password("farmer123"),
            role="farmer",
            phone="+91-9876543210",
            preferred_language="ta"
        )
        buyer_a = User(
            name="Restaurant A",
            email="rest_a@test.org",
            hashed_password=hash_password("buyer123"),
            role="buyer",
            phone="+91-9876543211",
            preferred_language="en"
        )
        buyer_b = User(
            name="Supermarket B",
            email="super_b@test.org",
            hashed_password=hash_password("buyer123"),
            role="buyer",
            phone="+91-9876543212",
            preferred_language="en"
        )
        buyer_c = User(
            name="Food Processor C",
            email="proc_c@test.org",
            hashed_password=hash_password("buyer123"),
            role="buyer",
            phone="+91-9876543213",
            preferred_language="en"
        )
        operator = User(
            name="Selvi",
            email="selvi@test.org",
            hashed_password=hash_password("operator123"),
            role="operator",
            phone="+91-9876543214",
            preferred_language="ta"
        )
        session.add_all([farmer, buyer_a, buyer_b, buyer_c, operator])
        session.commit()
        
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        if os.path.exists(TEST_DB_FILE):
            try:
                os.remove(TEST_DB_FILE)
            except Exception:
                pass

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=True)
    yield test_client
    app.dependency_overrides.clear()


import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database

# Create an in-memory SQLite database for tests only.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Make main.py use the test engine when it initializes the app.
database.engine = test_engine

from models import Base, User, Event, Booking
from database import get_db
from main import app, get_current_user


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_user(db_session):
    user = User(
        username="review_tester",
        email="review_tester@example.com",
        hashed_password="test-password-hash",
        role="USER"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def completed_event(db_session, test_user):
    event = Event(
        title="Review Test Event",
        description="Event for isolated review tests",
        category="Tech",
        location="Kalaburagi",
        event_date=__import__("datetime").datetime(2026, 10, 1, 10, 0),
        ticket_price=100,
        total_tickets=10,
        organizer_id=None,
        event_status="COMPLETED"
    )

    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    booking = Booking(
        user_id=test_user.id,
        event_id=event.id,
        ticket_quantity=1,
        total_price=100,
        coupon_id=None,
        discount_amount=0,
        final_amount=100,
        booking_status="CONFIRMED"
    )

    db_session.add(booking)
    db_session.commit()

    return event


@pytest.fixture
def client(db_session, test_user):
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )

    # Prevent the real application's startup background task
    # from opening a session against the production database.
    app.router.on_startup = []

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

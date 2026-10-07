# Import necessary SQLAlchemy components
from sqlalchemy import Column, Integer, String, DateTime,Float,Boolean
from datetime import datetime

# This is the parent class that all ORM models inherit from
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(150),
        nullable=False,
        index=True
    )

    description = Column(
        String(1000),
        nullable=False
    )

    category = Column(
        String(50),
        nullable=False,
        index=True
    )

    location = Column(
        String(200),
        nullable=False
    )

    event_date = Column(
        DateTime,
        nullable=False
    )
    

    ticket_price = Column(
        Float,
        nullable=False
    )

    banner_image = Column(
        String(500),
        nullable=True
    )
    
    total_tickets = Column(
        Integer,
        nullable=False,
        default=100
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)

    event_id = Column(Integer, nullable=False)

    ticket_quantity = Column(Integer, nullable=False)

    total_price = Column(Float, nullable=False)

    booking_status = Column(
        String(20),
        default="PENDING",
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    
class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(Integer, nullable=False)

    ticket_code = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    qr_code_url = Column(
        String(500),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    title = Column(
        String(200),
        nullable=False
    )

    message = Column(
        String(1000),
        nullable=False
    )

    type = Column(
        String(20),
        nullable=False
    )

    is_read = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
# ============================================================
# models.py
# SmartEvent Database Models
# ============================================================

# Import SQLAlchemy components
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean
)

from datetime import datetime

# Import Base class
from database import Base


# ============================================================
# USER MODEL
# ============================================================

class User(Base):

    __tablename__ = "users"

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Username
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    # Email
    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # Hashed password
    hashed_password = Column(
        String(255),
        nullable=False
    )

    # User role
    # USER / ORGANIZER / ADMIN
    role = Column(
        String(20),
        default="USER",
        nullable=False
    )

    # Account creation date
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# EVENT MODEL
# ============================================================

class Event(Base):

    __tablename__ = "events"

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Event title
    title = Column(
        String(150),
        nullable=False,
        index=True
    )

    # Event description
    description = Column(
        String(1000),
        nullable=False
    )

    # Event category
    # Music / Tech / Sports / Business
    category = Column(
        String(50),
        nullable=False,
        index=True
    )

    # Event location
    location = Column(
        String(200),
        nullable=False
    )

    # Event date and time
    event_date = Column(
        DateTime,
        nullable=False
    )

    # Ticket price
    ticket_price = Column(
        Float,
        nullable=False
    )

    # Event banner image
    banner_image = Column(
        String(500),
        nullable=True
    )

    # Total number of tickets
    total_tickets = Column(
        Integer,
        nullable=False,
        default=100
    )

    # Organizer who created this event
    #
    # nullable=True is kept because older events
    # may not have an organizer_id.
    organizer_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    # Event status
    #
    # ACTIVE
    # CANCELLED
    # COMPLETED
    event_status = Column(
        String(20),
        default="ACTIVE",
        nullable=False
    )

    # Event creation date
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# BOOKING MODEL
# ============================================================

class Booking(Base):

    __tablename__ = "bookings"

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # User who made booking
    user_id = Column(
        Integer,
        nullable=False
    )

    # Event being booked
    event_id = Column(
        Integer,
        nullable=False
    )

    # Number of tickets
    ticket_quantity = Column(
        Integer,
        nullable=False
    )

    # Total booking amount
    total_price = Column(
        Float,
        nullable=False
    )

    # Booking status
    #
    # PENDING
    # CONFIRMED
    # CANCELLED
    booking_status = Column(
        String(20),
        default="PENDING",
        nullable=False
    )

    # Booking creation date
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# TICKET MODEL
# ============================================================

class Ticket(Base):

    __tablename__ = "tickets"

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Related booking
    booking_id = Column(
        Integer,
        nullable=False
    )

    # Unique ticket code
    ticket_code = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # QR code image URL
    qr_code_url = Column(
        String(500),
        nullable=True
    )

    # Ticket creation date
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# NOTIFICATION MODEL
# ============================================================

class Notification(Base):

    __tablename__ = "notifications"

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # User who receives notification
    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    # Notification title
    title = Column(
        String(200),
        nullable=False
    )

    # Notification message
    message = Column(
        String(1000),
        nullable=False
    )

    # Notification type
    #
    # EVENT
    # BOOKING
    # SYSTEM
    type = Column(
        String(20),
        nullable=False
    )

    # Read/unread status
    is_read = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # Notification creation date
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
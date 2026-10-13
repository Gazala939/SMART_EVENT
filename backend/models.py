
# ============================================================
# models.py
# SmartEvent Database Models - Modules 1 to 13
# ============================================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    ForeignKey
)
from datetime import datetime
from database import Base


# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="USER", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# EVENT MODEL
# ============================================================

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False, index=True)
    description = Column(String(1000), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    location = Column(String(200), nullable=False)
    event_date = Column(DateTime, nullable=False)
    ticket_price = Column(Float, nullable=False)
    banner_image = Column(String(500), nullable=True)
    total_tickets = Column(Integer, nullable=False, default=100)
    organizer_id = Column(Integer, nullable=True, index=True)
    event_status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# COUPON MODEL - MODULE 13
# ============================================================

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)

    # Coupon codes are stored in uppercase.
    coupon_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    # PERCENTAGE or FIXED
    discount_type = Column(String(20), nullable=False)

    # For example: 10 means 10%, or ₹100 for FIXED.
    discount_value = Column(Float, nullable=False)

    # Minimum booking total required to use the coupon.
    minimum_booking_amount = Column(Float, default=0, nullable=False)

    # Last date/time when the coupon can be used.
    expiry_date = Column(DateTime, nullable=False)

    # Maximum number of successful uses.
    usage_limit = Column(Integer, nullable=False)

    # Tracks successful coupon uses.
    usage_count = Column(Integer, default=0, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================
# BOOKING MODEL - MODULE 13 UPDATES
# ============================================================

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=False)
    ticket_quantity = Column(Integer, nullable=False)

    # Original price before discounts.
    total_price = Column(Float, nullable=False)

    # Coupon used for this booking, if any.
    coupon_id = Column(
        Integer,
        ForeignKey("coupons.id"),
        nullable=True
    )

    # Amount subtracted from the original price.
    discount_amount = Column(Float, default=0, nullable=False)

    # Amount the customer must pay.
    final_amount = Column(Float, default=0, nullable=False)

    booking_status = Column(
        String(20),
        default="PENDING",
        nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# TICKET MODEL
# ============================================================

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
    qr_code_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)




# ============================================================
# NOTIFICATION MODEL
# ============================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    title = Column(String(200), nullable=False)

    message = Column(String(1000), nullable=False)

    # Keep the old database column working
    type = Column(
        String(20),
        nullable=False,
        default="SYSTEM"
    )

    # New field used by the application
    notification_type = Column(
        String(20),
        nullable=False,
        default="SYSTEM"
    )

    is_read = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )



# ============================================================
# PAYMENT MODEL - MODULE 12
# ============================================================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, nullable=False, index=True)
    payment_method = Column(
        String(40),
        default="SIMULATED",
        nullable=False
    )
    payment_status = Column(
        String(20),
        default="PENDING",
        nullable=False
    )
    transaction_id = Column(
        String(120),
        nullable=True,
        unique=True
    )
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)



# ============================================================
# REVIEW MODEL - MODULE 14
# ============================================================

class Review(Base):
    __tablename__ = "reviews"

    # Unique ID for each review
    id = Column(Integer, primary_key=True, index=True)

    # User who submitted the review
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Event being reviewed
    event_id = Column(
        Integer,
        ForeignKey("events.id"),
        nullable=False,
        index=True
    )

    # Rating must be between 1 and 5.
    # Backend API validation will enforce this range.
    rating = Column(Integer, nullable=False)

    # Written feedback from the user
    review_text = Column(String(2000), nullable=True)

    # Review creation time
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

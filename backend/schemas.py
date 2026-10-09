# ============================================================
# schemas.py
# SmartEvent Pydantic Schemas
# ============================================================

# Import Pydantic components
from pydantic import BaseModel, EmailStr, Field

# Import datetime
from datetime import datetime


# ============================================================
# USER SCHEMAS
# ============================================================

# User Registration
class UserRegister(BaseModel):

    username: str = Field(
        min_length=3,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=72
    )


# User Login
class UserLogin(BaseModel):

    email: EmailStr

    password: str


# User Response
class UserResponse(BaseModel):

    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# Token Response
class TokenResponse(BaseModel):

    access_token: str
    token_type: str


# ============================================================
# EVENT SCHEMAS
# ============================================================

# Create / Update Event
class EventCreate(BaseModel):

    title: str = Field(
        min_length=3,
        max_length=150
    )

    description: str = Field(
        min_length=5,
        max_length=1000
    )

    category: str

    location: str = Field(
        min_length=2,
        max_length=200
    )

    event_date: datetime

    ticket_price: float = Field(
        ge=0
    )

    # Total tickets available for this event
    total_tickets: int = Field(
        gt=0
    )

    # Optional banner image
    banner_image: str | None = None


# Event Response
class EventResponse(BaseModel):

    id: int
    title: str
    description: str
    category: str
    location: str
    event_date: datetime
    ticket_price: float
    banner_image: str | None

    # Module 8 fields
    total_tickets: int
    organizer_id: int | None
    event_status: str

    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# BOOKING SCHEMAS
# ============================================================

# Create Booking
class BookingCreate(BaseModel):

    event_id: int = Field(
        gt=0
    )

    ticket_quantity: int = Field(
        gt=0,
        le=10
    )


# Booking Response
class BookingResponse(BaseModel):

    id: int
    user_id: int
    event_id: int
    ticket_quantity: int
    total_price: float
    booking_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# TICKET SCHEMAS
# ============================================================

# Event information inside ticket
class TicketEventResponse(BaseModel):

    id: int
    title: str
    location: str
    event_date: datetime

    class Config:
        from_attributes = True


# Ticket Response
class TicketResponse(BaseModel):

    id: int
    booking_id: int
    ticket_code: str
    qr_code_url: str | None
    created_at: datetime

    event: TicketEventResponse

    class Config:
        from_attributes = True


# Booking with Ticket
class BookingWithTicketResponse(BaseModel):

    id: int
    user_id: int
    event_id: int
    ticket_quantity: int
    total_price: float
    booking_status: str
    created_at: datetime

    ticket: TicketResponse

    class Config:
        from_attributes = True


# ============================================================
# NOTIFICATION SCHEMA
# ============================================================

class NotificationResponse(BaseModel):

    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# ADMIN - CHANGE USER ROLE
# ============================================================

class RoleUpdate(BaseModel):

    role: str
# ============================================================
# schemas.py
# SmartEvent Pydantic Schemas
# ============================================================

# Import Pydantic components
from pydantic import BaseModel, EmailStr, Field


from typing import Literal

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
    
    profile_picture: str | None = None
    location: str | None = None

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

    # Original booking amount
    total_price: float

    # Module 13 - Coupon and discount fields
    coupon_id: int | None = None
    discount_amount: float = 0
    final_amount: float = 0

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
    

# ============================================================
# MODULE 12 - PAYMENT SCHEMAS
# ============================================================



class PaymentCreate(BaseModel):
    booking_id: int = Field(gt=0)
    payment_method: Literal["SIMULATED"] = "SIMULATED"
    simulate_status: Literal["SUCCESS", "FAILED"] = "SUCCESS"


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    payment_method: str
    payment_status: str
    transaction_id: str | None
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True
        

# ============================================================
# COUPON SCHEMAS - MODULE 13
# ============================================================

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class CouponCreate(BaseModel):
    coupon_code: str = Field(min_length=3, max_length=50)
    discount_type: Literal["PERCENTAGE", "FIXED"]
    discount_value: float = Field(gt=0)
    minimum_booking_amount: float = Field(default=0, ge=0)
    expiry_date: datetime
    usage_limit: int = Field(gt=0)
    is_active: bool = True


class CouponApply(BaseModel):
    coupon_code: str = Field(min_length=3, max_length=50)
    booking_id: int = Field(gt=0)


class CouponResponse(BaseModel):
    id: int
    coupon_code: str
    discount_type: str
    discount_value: float
    minimum_booking_amount: float
    expiry_date: datetime
    usage_limit: int
    usage_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CouponValidationResponse(BaseModel):
    valid: bool
    message: str
    coupon_code: str | None = None
    original_amount: float | None = None
    discount_amount: float | None = None
    final_amount: float | None = None



# ============================================================
# MODULE 14 - EVENT REVIEW & RATING SCHEMAS
# ============================================================

# Submit a new review or update an existing review
class ReviewCreate(BaseModel):

    # Rating must be between 1 and 5
    rating: int = Field(
        ge=1,
        le=5
    )

    # Review text is optional
    review_text: str | None = Field(
        default=None,
        max_length=2000
    )


# Response for a single review
class ReviewResponse(BaseModel):

    id: int
    user_id: int
    event_id: int
    rating: int
    review_text: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# Response containing event reviews and average rating
class ReviewListResponse(BaseModel):

    event_id: int
    average_rating: float
    total_reviews: int
    reviews: list[ReviewResponse]


# ============================================================
# MODULE 20 - WISHLIST SCHEMAS
# ============================================================

class WishlistCreate(BaseModel):
    event_id: int = Field(gt=0)


class WishlistResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# MODULE 21 - EVENT UPDATE SCHEMAS
# ============================================================

class EventUpdateCreate(BaseModel):
    message: str = Field(min_length=3, max_length=2000)
    is_important: bool = False


class EventUpdateResponse(BaseModel):
    id: int
    event_id: int
    message: str
    is_important: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# MODULE 22 - PROFILE SCHEMAS
# ============================================================

class ProfileUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50
    )

    email: EmailStr | None = None

    profile_picture: str | None = Field(
        default=None,
        max_length=500
    )
    
    location: str | None = Field(
        default=None,
        max_length=200
    )


class ProfileSummaryResponse(BaseModel):
    total_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    total_tickets: int
    total_spent: float


# ============================================================
# MODULE 24 - CHATBOT SCHEMAS
# ============================================================

class ChatbotRequest(BaseModel):
    message: str = Field(
        min_length=2,
        max_length=1000
    )


class ChatbotResponse(BaseModel):
    answer: str
    intent: str = "general"
    events: list[EventResponse] = Field(default_factory=list)

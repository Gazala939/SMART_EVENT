# Import Pydantic components:
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# User_Resigster
class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

# User_Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# User_Response
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: object

    class Config:
        from_attributes = True

# Token
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    
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

    banner_image: str | None = None


class EventResponse(BaseModel):

    id: int
    title: str
    description: str
    category: str
    location: str
    event_date: datetime
    ticket_price: float
    banner_image: str | None
    created_at: datetime

    class Config:
        from_attributes = True
        
# BOOKING SCHEMAS

class BookingCreate(BaseModel):
    event_id: int = Field(gt=0)
    ticket_quantity: int = Field(gt=0, le=10)


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
        
class TicketEventResponse(BaseModel):
    id: int
    title: str
    location: str
    event_date: datetime

    class Config:
        from_attributes = True


class TicketResponse(BaseModel):
    id: int
    booking_id: int
    ticket_code: str
    qr_code_url: str | None
    created_at: datetime
    event: TicketEventResponse

    class Config:
        from_attributes = True
        
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
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles

import os
import uuid
import qrcode
import asyncio
from datetime import datetime, timedelta

from database import engine, Base, get_db,SessionLocal
from models import User, Event, Booking, Ticket, Notification
from schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    EventCreate,
    EventResponse,
    BookingCreate,
    BookingResponse,
    TicketResponse,
    TicketEventResponse,
    BookingWithTicketResponse,
    NotificationResponse
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SmartEvent API",
    description="SmartEvent Event Discovery and Ticket Booking System",
    version="1.0.0"
)

@app.on_event("startup")
async def start_reminder_checker():
    asyncio.create_task(event_reminder_checker())


app.mount(
    "/qr_codes",
    StaticFiles(directory="qr_codes"),
    name="qr_codes"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# USER REGISTRATION
@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):

    existing_email = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_email:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )


    existing_username = db.query(User).filter(
        User.username == user_data.username
    ).first()

    if existing_username:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )


    hashed_password = hash_password(
        user_data.password
    )


    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )


    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    return new_user

# USER LOGIN
@app.post(
    "/auth/login",
    response_model=TokenResponse
)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == user_data.email
    ).first()


    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


    password_correct = verify_password(
        user_data.password,
        user.hashed_password
    )


    if not password_correct:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


    access_token = create_access_token(
        data={
            "sub": str(user.id)
        }
    )


    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# USER PROFILE
@app.get(
    "/auth/profile",
    response_model=UserResponse
)
def get_profile(
    current_user: User = Depends(get_current_user)
):

    return current_user

# ============================================================
# EVENT DISCOVERY
# ============================================================

# CREATE EVENT

@app.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED
)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db)
):

    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        category=event_data.category,
        location=event_data.location,
        event_date=event_data.event_date,
        ticket_price=event_data.ticket_price,
        banner_image=event_data.banner_image
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event


# GET ALL EVENTS

@app.get(
    "/events",
    response_model=list[EventResponse]
)
def get_all_events(
    db: Session = Depends(get_db)
):

    events = db.query(Event).all()

    return events


# GET EVENTS BY CATEGORY

@app.get(
    "/events/category/{category}",
    response_model=list[EventResponse]
)
def get_events_by_category(
    category: str,
    db: Session = Depends(get_db)
):

    events = db.query(Event).filter(
        Event.category.ilike(category)
    ).all()

    return events


# SEARCH EVENTS BY TITLE

@app.get(
    "/events/search",
    response_model=list[EventResponse]
)
def search_events(
    title: str,
    db: Session = Depends(get_db)
):

    events = db.query(Event).filter(
        Event.title.ilike(f"%{title}%")
    ).all()

    return events


# GET SINGLE EVENT
# KEEP THIS ROUTE LAST

@app.get(
    "/events/{event_id}",
    response_model=EventResponse
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):

    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    return event

@app.put(
    "/events/{event_id}",
    response_model=EventResponse
)
def update_event(
    event_id: int,
    event_data: EventCreate,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    event.title = event_data.title
    event.description = event_data.description
    event.category = event_data.category
    event.location = event_data.location
    event.event_date = event_data.event_date
    event.ticket_price = event_data.ticket_price
    event.banner_image = event_data.banner_image

    db.commit()
    db.refresh(event)

    return event

# CREATE BOOKING
@app.post(
    "/bookings",
    response_model=BookingWithTicketResponse,
    status_code=status.HTTP_201_CREATED
)
def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the event
    event = db.query(Event).filter(
        Event.id == booking_data.event_id
    ).first()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check already booked tickets
    booked_tickets = db.query(Booking).filter(
        Booking.event_id == event.id,
        Booking.booking_status != "CANCELLED"
    ).all()

    total_booked = sum(
        booking.ticket_quantity
        for booking in booked_tickets
    )

    # Calculate available tickets
    available_tickets = (
        event.total_tickets - total_booked
    )

    # Check availability
    if booking_data.ticket_quantity > available_tickets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {available_tickets} tickets are available"
        )

    # Calculate total price
    total_price = (
        event.ticket_price *
        booking_data.ticket_quantity
    )

    # Create booking
    new_booking = Booking(
        user_id=current_user.id,
        event_id=event.id,
        ticket_quantity=booking_data.ticket_quantity,
        total_price=total_price,
        booking_status="CONFIRMED"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # Generate unique ticket code
    ticket_code = f"TKT-{uuid.uuid4().hex[:8].upper()}"

    # Generate QR code
    qr_code_url = generate_ticket_qr(ticket_code)

    # Create ticket
    new_ticket = Ticket(
        booking_id=new_booking.id,
        ticket_code=ticket_code,
        qr_code_url=qr_code_url
    )

    db.add(new_ticket)
    db.commit()
    
    # Create booking confirmation notification
    notification = Notification(
        user_id=current_user.id,
        title="Booking Confirmed",
        message=f"Your ticket for {event.title} has been successfully booked.",
        type="BOOKING",
        is_read=False
    )

    db.add(notification)
    db.commit()

    return {
    "id": new_booking.id,
    "user_id": new_booking.user_id,
    "event_id": new_booking.event_id,
    "ticket_quantity": new_booking.ticket_quantity,
    "total_price": new_booking.total_price,
    "booking_status": new_booking.booking_status,
    "created_at": new_booking.created_at,
    "ticket": {
        "id": new_ticket.id,
        "booking_id": new_ticket.booking_id,
        "ticket_code": new_ticket.ticket_code,
        "qr_code_url": new_ticket.qr_code_url,
        "created_at": new_ticket.created_at,
        "event": {
            "id": event.id,
            "title": event.title,
            "location": event.location,
            "event_date": event.event_date
        }
    }
}
    
    

# GET MY BOOKINGS
@app.get(
    "/bookings/my-bookings",
    response_model=list[BookingResponse]
)
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id
    ).all()

    return bookings

# CANCEL MY BOOKING
@app.put(
    "/bookings/{booking_id}/cancel",
    response_model=BookingResponse
)
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own booking"
        )

    if booking.booking_status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled"
        )

    booking.booking_status = "CANCELLED"

    db.commit()
    db.refresh(booking)

    return booking

def generate_ticket_qr(ticket_code: str):
    qr = qrcode.make(ticket_code)

    file_name = f"{ticket_code}.png"

    qr_folder = os.path.join(
        os.path.dirname(__file__),
        "qr_codes"
    )

    os.makedirs(
        qr_folder,
        exist_ok=True
    )

    file_path = os.path.join(
        qr_folder,
        file_name
    )

    qr.save(file_path)

    return f"/qr_codes/{file_name}"

@app.get(
    "/tickets/my-tickets",
    response_model=list[TicketResponse]
)
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tickets = (
        db.query(Ticket, Event)
        .join(
            Booking,
            Ticket.booking_id == Booking.id
        )
        .join(
            Event,
            Booking.event_id == Event.id
        )
        .filter(
            Booking.user_id == current_user.id
        )
        .all()
    )

    result = []

    for ticket, event in tickets:
        result.append({
            "id": ticket.id,
            "booking_id": ticket.booking_id,
            "ticket_code": ticket.ticket_code,
            "qr_code_url": ticket.qr_code_url,
            "created_at": ticket.created_at,
            "event": {
                "id": event.id,
                "title": event.title,
                "location": event.location,
                "event_date": event.event_date
            }
        })

    return result

@app.get("/tickets/verify/{ticket_code}")
def verify_ticket(
    ticket_code: str,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.ticket_code == ticket_code
    ).first()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid ticket"
        )

    booking = db.query(Booking).filter(
        Booking.id == ticket.booking_id
    ).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking.booking_status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket is cancelled"
        )

    return {
        "message": "Ticket is valid",
        "ticket_code": ticket.ticket_code,
        "booking_id": booking.id,
        "event_id": booking.event_id,
        "ticket_quantity": booking.ticket_quantity,
        "booking_status": booking.booking_status
    }
    
@app.get(
    "/notifications",
    response_model=list[NotificationResponse]
)
def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id
        )
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )

    return notifications

async def event_reminder_checker():
    while True:

        db = SessionLocal()

        try:
            now = datetime.utcnow()

            reminder_start = now + timedelta(hours=23)
            reminder_end = now + timedelta(hours=25)

            upcoming_events = db.query(Event).filter(
                Event.event_date >= reminder_start,
                Event.event_date <= reminder_end
            ).all()

            for event in upcoming_events:

                bookings = db.query(Booking).filter(
                    Booking.event_id == event.id,
                    Booking.booking_status == "CONFIRMED"
                ).all()

                for booking in bookings:

                    existing_notification = db.query(
                        Notification
                    ).filter(
                        Notification.user_id == booking.user_id,
                        Notification.title == "Event Reminder",
                        Notification.message.contains(event.title)
                    ).first()

                    if existing_notification is None:

                        notification = Notification(
                            user_id=booking.user_id,
                            title="Event Reminder",
                            message=f'Your event "{event.title}" is coming up soon.',
                            type="EVENT",
                            is_read=False
                        )

                        db.add(notification)

            db.commit()

        except Exception as error:
            print("Reminder checker error:", error)

        finally:
            db.close()

        await asyncio.sleep(3600)
        
@app.put("/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return {
        "message": "Notification marked as read",
        "notification": notification
    }
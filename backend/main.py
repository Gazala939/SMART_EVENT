
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import uuid
import qrcode
import asyncio

from datetime import date, datetime, time, timedelta

from database import engine, Base, get_db, SessionLocal

from models import User, Event, Booking, Ticket, Notification

from schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    RoleUpdate,
    EventCreate,
    EventResponse,
    BookingCreate,
    BookingResponse,
    TicketResponse,
    BookingWithTicketResponse,
    NotificationResponse
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role
)


# ============================================================
# DATABASE AND APPLICATION
# ============================================================

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartEvent API",
    description="SmartEvent Event Discovery and Ticket Booking System",
    version="1.0.0"
)

os.makedirs("qr_codes", exist_ok=True)

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
    allow_headers=["*"]
)


# ============================================================
# MODULE 10 - AUTOMATIC EVENT STATUS
# ============================================================

def refresh_event_status(event):
    """
    Status rules:
    Future event              -> UPCOMING
    Event starts today        -> ONGOING
    Event date has passed     -> COMPLETED
    Cancelled event           -> remains CANCELLED
    Manually completed event  -> remains COMPLETED

    This project currently stores a start date/time only.
    Therefore, an event is considered completed the next day.
    """

    if event.event_status in ("CANCELLED", "COMPLETED"):
        return False

    now = datetime.utcnow()
    event_date = event.event_date

    # Handle timezone-aware dates by normalizing them to naive
    # UTC values for comparison with this project's UTC clock.
    if event_date.tzinfo is not None:
        event_date = event_date.astimezone(
            datetime.now().astimezone().tzinfo
        ).replace(tzinfo=None)

    if event_date.date() < now.date():
        new_status = "COMPLETED"

    elif event_date <= now:
        new_status = "ONGOING"

    else:
        new_status = "UPCOMING"

    if event.event_status != new_status:
        event.event_status = new_status
        return True

    return False


def refresh_event_statuses(db, events):
    """Refresh event statuses and save changes."""

    changed = False

    for event in events:
        if refresh_event_status(event):
            changed = True

    if changed:
        db.commit()


# ============================================================
# MODULE 10 - NOTIFY CONFIRMED BOOKERS
# ============================================================

def notify_confirmed_bookers(
    db,
    event,
    notification_title,
    notification_message
):
    """Create a notification for each user with a confirmed booking."""

    bookings = db.query(Booking).filter(
        Booking.event_id == event.id,
        Booking.booking_status == "CONFIRMED"
    ).all()

    # A user receives only one notification per update,
    # even if they have multiple confirmed bookings.
    user_ids = {
        booking.user_id for booking in bookings
    }

    for user_id in user_ids:
        notification = Notification(
            user_id=user_id,
            title=notification_title,
            message=notification_message,
            type="EVENT",
            is_read=False
        )
        db.add(notification)


# ============================================================
# BACKGROUND TASK STARTUP
# ============================================================

@app.on_event("startup")
async def start_reminder_checker():
    asyncio.create_task(event_reminder_checker())


# ============================================================
# AUTHENTICATION - REGISTER
# ============================================================

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    if db.query(User).filter(
        User.email == user_data.email
    ).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    if db.query(User).filter(
        User.username == user_data.username
    ).first():
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ============================================================
# AUTHENTICATION - LOGIN
# ============================================================

@app.post("/auth/login", response_model=TokenResponse)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if user is None or not verify_password(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ============================================================
# AUTHENTICATION - PROFILE
# ============================================================

@app.get("/auth/profile", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


# ============================================================
# ADMIN - USER MANAGEMENT
# ============================================================

@app.get("/admin/users", response_model=list[UserResponse])
def get_all_users(
    current_user: User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    return db.query(User).all()


@app.put("/admin/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if role_data.role not in ["USER", "ORGANIZER", "ADMIN"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user.role = role_data.role
    db.commit()
    db.refresh(user)

    return user


@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if db.query(Booking).filter(Booking.user_id == user_id).first():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete user with existing bookings"
        )

    if db.query(Event).filter(Event.organizer_id == user_id).first():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete organizer with existing events"
        )

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


# ============================================================
# EVENTS - CREATE
# ============================================================

@app.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED
)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ORGANIZER"))
):
    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        category=event_data.category,
        location=event_data.location,
        event_date=event_data.event_date,
        ticket_price=event_data.ticket_price,
        total_tickets=event_data.total_tickets,
        banner_image=event_data.banner_image,
        organizer_id=current_user.id,
        event_status="UPCOMING"
    )

    # Set the correct status immediately if the submitted date
    # is today or already in the past.
    refresh_event_status(new_event)

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event


# ============================================================
# EVENTS - ORGANIZER'S EVENTS
# ============================================================

@app.get("/organizer/events", response_model=list[EventResponse])
def get_my_events(
    current_user: User = Depends(require_role("ORGANIZER")),
    db: Session = Depends(get_db)
):
    events = db.query(Event).filter(
        Event.organizer_id == current_user.id
    ).all()

    refresh_event_statuses(db, events)

    return events


# ============================================================
# EVENTS - GET ALL
# ============================================================

@app.get("/events", response_model=list[EventResponse])
def get_all_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()

    refresh_event_statuses(db, events)

    return events


# ============================================================
# EVENTS - CATEGORY SEARCH
# ============================================================

@app.get("/events/category/{category}", response_model=list[EventResponse])
def get_events_by_category(
    category: str,
    db: Session = Depends(get_db)
):
    events = db.query(Event).filter(
        Event.category.ilike(category)
    ).all()

    refresh_event_statuses(db, events)

    return events


# ============================================================
# EVENTS - TITLE SEARCH
# Keep this before /events/{event_id}
# ============================================================

@app.get("/events/search", response_model=list[EventResponse])
def search_events(
    title: str,
    db: Session = Depends(get_db)
):
    events = db.query(Event).filter(
        Event.title.ilike(f"%{title}%")
    ).all()

    refresh_event_statuses(db, events)

    return events


# ============================================================
# EVENTS - GET ONE
# ============================================================

@app.get("/events/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    refresh_event_statuses(db, [event])
    db.refresh(event)

    return event



# ============================================================
# EVENTS - UPDATE
# ORGANIZER CAN UPDATE OWN EVENTS; ADMIN CAN UPDATE ANY
# ============================================================

@app.put("/events/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("ORGANIZER", "ADMIN")
    )
):
    # 1. Find the event
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # 2. Check ownership
    if (
        current_user.role == "ORGANIZER"
        and event.organizer_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can update only your own events"
        )

    # 3. Prevent updates to cancelled events
    if event.event_status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Cancelled events cannot be updated"
        )

    # 4. Update event details
    event.title = event_data.title
    event.description = event_data.description
    event.category = event_data.category
    event.location = event_data.location
    event.event_date = event_data.event_date
    event.ticket_price = event_data.ticket_price
    event.total_tickets = event_data.total_tickets
    event.banner_image = event_data.banner_image

    # 5. Refresh the status after changing the event date
    if event.event_status != "COMPLETED":
        event.event_status = "UPCOMING"
        refresh_event_status(event)

    # 6. Notify users who have confirmed bookings
    notify_confirmed_bookers(
        db,
        event,
        "Event Updated",
        (
            f'The event "{event.title}" has been updated. '
            "Please check the latest event details."
        )
    )

    # 7. Save the event and its notifications
    db.commit()
    db.refresh(event)

    # 8. Return the updated event
    return event

# ============================================================
# EVENTS - DELETE
# ============================================================

@app.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("ORGANIZER", "ADMIN")
    )
):
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if (
        current_user.role == "ORGANIZER"
        and event.organizer_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can delete only your own events"
        )

    # Keep the existing delete endpoint for compatibility.
    db.delete(event)
    db.commit()

    return {"message": "Event deleted successfully"}


# ============================================================
# EVENTS - CANCEL
# ============================================================

@app.put("/organizer/events/{event_id}/cancel")
def cancel_event(
    event_id: int,
    current_user: User = Depends(require_role("ORGANIZER")),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can cancel only your own events"
        )

    if event.event_status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Event is already cancelled"
        )

    event.event_status = "CANCELLED"

    notify_confirmed_bookers(
        db,
        event,
        "Event Cancelled",
        (
            f'The event "{event.title}" has been cancelled. '
            "Please do not attend this event."
        )
    )

    db.commit()
    db.refresh(event)

    return {
        "message": "Event cancelled successfully",
        "event_id": event.id,
        "event_status": event.event_status
    }


# ============================================================
# EVENTS - MANUALLY COMPLETE
# ============================================================

@app.put("/organizer/events/{event_id}/complete")
def complete_event(
    event_id: int,
    current_user: User = Depends(require_role("ORGANIZER")),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can complete only your own events"
        )

    if event.event_status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Cancelled event cannot be completed"
        )

    if event.event_status == "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Event is already completed"
        )

    event.event_status = "COMPLETED"
    db.commit()
    db.refresh(event)

    return {
        "message": "Event marked as completed successfully",
        "event_id": event.id,
        "event_status": event.event_status
    }


# ============================================================
# ORGANIZER - BOOKINGS FOR OWN EVENT
# ============================================================

@app.get(
    "/organizer/events/{event_id}/bookings",
    response_model=list[BookingResponse]
)
def get_event_bookings(
    event_id: int,
    current_user: User = Depends(require_role("ORGANIZER")),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.organizer_id is None:
        raise HTTPException(
            status_code=400,
            detail="This event has no organizer assigned"
        )

    if event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can view bookings only for your own events"
        )

    return db.query(Booking).filter(
        Booking.event_id == event_id
    ).all()


# ============================================================
# ORGANIZER - ANALYTICS FOR ALL OWN EVENTS
# ============================================================

@app.get("/organizer/analytics")
def get_organizer_analytics(
    current_user: User = Depends(require_role("ORGANIZER")),
    db: Session = Depends(get_db)
):
    events = db.query(Event).filter(
        Event.organizer_id == current_user.id
    ).all()

    refresh_event_statuses(db, events)

    event_analytics = []
    total_tickets_sold = 0
    total_remaining_tickets = 0
    total_revenue = 0
    total_booking_count = 0

    for event in events:
        bookings = db.query(Booking).filter(
            Booking.event_id == event.id
        ).all()

        confirmed = [
            booking for booking in bookings
            if booking.booking_status == "CONFIRMED"
        ]

        tickets_sold = sum(
            booking.ticket_quantity for booking in confirmed
        )
        remaining = max(event.total_tickets - tickets_sold, 0)
        revenue = sum(booking.total_price for booking in confirmed)
        booking_count = len(confirmed)

        total_tickets_sold += tickets_sold
        total_remaining_tickets += remaining
        total_revenue += revenue
        total_booking_count += booking_count

        event_analytics.append({
            "event_id": event.id,
            "event_title": event.title,
            "event_status": event.event_status,
            "total_tickets": event.total_tickets,
            "tickets_sold": tickets_sold,
            "remaining_tickets": remaining,
            "total_revenue": revenue,
            "booking_count": booking_count
        })

    return {
        "total_events": len(events),
        "total_tickets_sold": total_tickets_sold,
        "total_remaining_tickets": total_remaining_tickets,
        "total_revenue": total_revenue,
        "total_booking_count": total_booking_count,
        "events": event_analytics
    }


# ============================================================
# ORGANIZER - ANALYTICS FOR ONE EVENT
# ============================================================

@app.get("/organizer/events/{event_id}/analytics")
def get_single_event_analytics(
    event_id: int,
    current_user: User = Depends(require_role("ORGANIZER")),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can view analytics only for your own events"
        )

    refresh_event_statuses(db, [event])

    bookings = db.query(Booking).filter(
        Booking.event_id == event.id
    ).all()

    confirmed = [
        booking for booking in bookings
        if booking.booking_status == "CONFIRMED"
    ]

    tickets_sold = sum(
        booking.ticket_quantity for booking in confirmed
    )

    return {
        "event_id": event.id,
        "event_title": event.title,
        "event_status": event.event_status,
        "total_tickets": event.total_tickets,
        "tickets_sold": tickets_sold,
        "remaining_tickets": max(
            event.total_tickets - tickets_sold, 0
        ),
        "total_revenue": sum(
            booking.total_price for booking in confirmed
        ),
        "booking_count": len(confirmed)
    }


# ============================================================
# ADMIN - ALL BOOKINGS
# ============================================================

@app.get("/admin/bookings", response_model=list[BookingResponse])
def get_all_bookings(
    current_user: User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    return db.query(Booking).all()


# ============================================================
# ADMIN - ANALYTICS
# ============================================================

@app.get("/admin/analytics")
def admin_analytics(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be later than end date",
        )

    # Support either booking quantity column name.
    quantity_col = getattr(Booking, "ticket_quantity", None)

    if quantity_col is None:
        quantity_col = getattr(Booking, "quantity", None)

    status_col = getattr(Booking, "status", None)

    if status_col is None:
        status_col = getattr(Booking, "booking_status", None)

    created_col = getattr(Booking, "created_at", None)
    amount_col = getattr(Booking, "total_price", None)

    if quantity_col is None or status_col is None:
        raise HTTPException(
            status_code=500,
            detail="Check the Booking model's quantity and status fields",
        )

    if created_col is None or amount_col is None:
        raise HTTPException(
            status_code=500,
            detail="Check the Booking model's created_at and total_price fields",
        )

    # Apply date filters to booking-based statistics.
    def filtered_bookings():
        query = db.query(Booking)

        if start_date:
            query = query.filter(
                created_col >= datetime.combine(start_date, time.min)
            )

        if end_date:
            query = query.filter(
                created_col <= datetime.combine(end_date, time.max)
            )

        return query

    def confirmed_bookings_query():
        return filtered_bookings().filter(
            func.upper(status_col) == "CONFIRMED"
        )

    # Summary counts.
    total_users = db.query(User).count()
    total_events = db.query(Event).count()
    total_bookings = filtered_bookings().count()

    confirmed_count = confirmed_bookings_query().count()

    cancelled_count = filtered_bookings().filter(
        func.upper(status_col) == "CANCELLED"
    ).count()
    

    total_revenue = (
        confirmed_bookings_query()
        .with_entities(
            func.coalesce(func.sum(amount_col), 0)
        )
        .scalar()
        or 0
    )

    total_tickets_sold = (
        confirmed_bookings_query()
        .with_entities(func.coalesce(func.sum(quantity_col), 0))
        .scalar()
        or 0
    )

    # 1. Daily ticket sales: confirmed bookings grouped by date.
    daily_rows = (
        confirmed_bookings_query()
        .filter(created_col.isnot(None))
        .with_entities(
            func.date(created_col).label("sale_date"),
            func.coalesce(func.sum(quantity_col), 0).label("tickets_sold"),
        )
        .group_by(func.date(created_col))
        .order_by(func.date(created_col))
        .all()
    )

    daily_ticket_sales = [
        {
            "date": str(row.sale_date),
            "tickets_sold": int(row.tickets_sold or 0),
        }
        for row in daily_rows
    ]

    # 2. Monthly booking trends: all booking statuses.
    month_expression = func.strftime("%Y-%m", created_col)

    monthly_rows = (
        filtered_bookings()
        .filter(created_col.isnot(None))
        .with_entities(
            month_expression.label("month"),
            func.count(Booking.id).label("total_bookings"),
        )
        .group_by(month_expression)
        .order_by(month_expression)
        .all()
    )

    monthly_booking_trends = [
        {
            "month": str(row.month),
            "total_bookings": int(row.total_bookings or 0),
        }
        for row in monthly_rows
    ]

    # 3. Most popular events, ranked by tickets sold.
    popular_rows = (
        confirmed_bookings_query()
        .join(Event, Booking.event_id == Event.id)
        .with_entities(
            Event.id.label("event_id"),
            Event.title.label("event_title"),
            func.count(Booking.id).label("booking_count"),
            func.coalesce(func.sum(quantity_col), 0).label("tickets_sold"),
        )
        .group_by(Event.id, Event.title)
        .order_by(func.sum(quantity_col).desc())
        .limit(5)
        .all()
    )

    most_popular_events = [
        {
            "event_id": row.event_id,
            "event_title": row.event_title,
            "booking_count": int(row.booking_count or 0),
            "tickets_sold": int(row.tickets_sold or 0),
        }
        for row in popular_rows
    ]

    # 4. Top revenue-generating events.
    revenue_rows = (
        confirmed_bookings_query()
        .join(Event, Booking.event_id == Event.id)
        .with_entities(
            Event.id.label("event_id"),
            Event.title.label("event_title"),
            func.coalesce(func.sum(amount_col), 0).label("revenue"),
        )
        .group_by(Event.id, Event.title)
        .order_by(func.sum(amount_col).desc())
        .limit(5)
        .all()
    )

    top_revenue_events = [
        {
            "event_id": row.event_id,
            "event_title": row.event_title,
            "revenue": float(row.revenue or 0),
        }
        for row in revenue_rows
    ]

    return {
        "total_users": total_users,
        "total_events": total_events,
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_count,
        "cancelled_bookings": cancelled_count,
        "total_revenue": float(total_revenue),
        "total_tickets_sold": int(total_tickets_sold),
        "daily_ticket_sales": daily_ticket_sales,
        "monthly_booking_trends": monthly_booking_trends,
        "most_popular_events": most_popular_events,
        "top_revenue_events": top_revenue_events,
    }

# ============================================================
# BOOKINGS - CREATE
# ============================================================

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
    event = db.query(Event).filter(
        Event.id == booking_data.event_id
    ).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    refresh_event_status(event)

    if event.event_status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Cannot book a cancelled event"
        )

    if event.event_status in ("ONGOING", "COMPLETED"):
        raise HTTPException(
            status_code=400,
            detail="Bookings are not available for this event"
        )

    booked = db.query(Booking).filter(
        Booking.event_id == event.id,
        Booking.booking_status != "CANCELLED"
    ).all()

    total_booked = sum(
        booking.ticket_quantity for booking in booked
    )
    available = event.total_tickets - total_booked

    if booking_data.ticket_quantity > available:
        raise HTTPException(
            status_code=400,
            detail=f"Only {available} tickets are available"
        )

    total_price = event.ticket_price * booking_data.ticket_quantity

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

    ticket_code = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    qr_code_url = generate_ticket_qr(ticket_code)

    new_ticket = Ticket(
        booking_id=new_booking.id,
        ticket_code=ticket_code,
        qr_code_url=qr_code_url
    )

    db.add(new_ticket)

    db.add(Notification(
        user_id=current_user.id,
        title="Booking Confirmed",
        message=f"Your ticket for {event.title} has been successfully booked.",
        type="BOOKING",
        is_read=False
    ))

    db.commit()
    db.refresh(new_ticket)

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


# ============================================================
# BOOKINGS - MY BOOKINGS
# ============================================================

@app.get("/bookings/my-bookings", response_model=list[BookingResponse])
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Booking).filter(
        Booking.user_id == current_user.id
    ).all()


# ============================================================
# BOOKINGS - CANCEL MY BOOKING
# ============================================================

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
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only cancel your own booking"
        )

    if booking.booking_status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Booking is already cancelled"
        )

    booking.booking_status = "CANCELLED"
    db.commit()
    db.refresh(booking)

    return booking


# ============================================================
# QR CODE GENERATION
# ============================================================

def generate_ticket_qr(ticket_code: str):
    qr = qrcode.make(ticket_code)

    qr_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "qr_codes"
    )
    os.makedirs(qr_folder, exist_ok=True)

    file_name = f"{ticket_code}.png"
    file_path = os.path.join(qr_folder, file_name)

    qr.save(file_path)

    return f"/qr_codes/{file_name}"


# ============================================================
# TICKETS - MY TICKETS
# ============================================================

@app.get("/tickets/my-tickets", response_model=list[TicketResponse])
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Ticket, Event)
        .join(Booking, Ticket.booking_id == Booking.id)
        .join(Event, Booking.event_id == Event.id)
        .filter(Booking.user_id == current_user.id)
        .all()
    )

    result = []

    for ticket, event in rows:
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


# ============================================================
# TICKETS - VERIFY
# ============================================================

@app.get("/tickets/verify/{ticket_code}")
def verify_ticket(
    ticket_code: str,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.ticket_code == ticket_code
    ).first()

    if ticket is None:
        raise HTTPException(status_code=404, detail="Invalid ticket")

    booking = db.query(Booking).filter(
        Booking.id == ticket.booking_id
    ).first()

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.booking_status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Ticket is cancelled")

    event = db.query(Event).filter(
        Event.id == booking.event_id
    ).first()

    if event is not None and event.event_status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="The event has been cancelled"
        )

    return {
        "message": "Ticket is valid",
        "ticket_code": ticket.ticket_code,
        "booking_id": booking.id,
        "event_id": booking.event_id,
        "ticket_quantity": booking.ticket_quantity,
        "booking_status": booking.booking_status
    }


# ============================================================
# NOTIFICATIONS - MY NOTIFICATIONS
# ============================================================

@app.get("/notifications", response_model=list[NotificationResponse])
def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()


# ============================================================
# BACKGROUND CHECKER - STATUS + EVENT REMINDERS
# ============================================================

async def event_reminder_checker():
    while True:
        db = SessionLocal()

        try:
            now = datetime.utcnow()

            # 1. Automatically refresh all event statuses.
            all_events = db.query(Event).all()

            for event in all_events:
                refresh_event_status(event)

            db.commit()

            # 2. Send reminders for events about 24 hours away.
            reminder_start = now + timedelta(hours=23)
            reminder_end = now + timedelta(hours=25)

            upcoming_events = db.query(Event).filter(
                Event.event_date >= reminder_start,
                Event.event_date <= reminder_end,
                Event.event_status != "CANCELLED"
            ).all()

            for event in upcoming_events:
                bookings = db.query(Booking).filter(
                    Booking.event_id == event.id,
                    Booking.booking_status == "CONFIRMED"
                ).all()

                for booking in bookings:
                    existing = db.query(Notification).filter(
                        Notification.user_id == booking.user_id,
                        Notification.title == "Event Reminder",
                        Notification.message.contains(event.title)
                    ).first()

                    if existing is None:
                        db.add(Notification(
                            user_id=booking.user_id,
                            title="Event Reminder",
                            message=(
                                f'Your event "{event.title}" '
                                "is coming up soon."
                            ),
                            type="EVENT",
                            is_read=False
                        ))

            db.commit()

        except Exception as error:
            db.rollback()
            print("Event checker error:", error)

        finally:
            db.close()

        await asyncio.sleep(3600)


# ============================================================
# NOTIFICATIONS - MARK AS READ
# ============================================================

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
            status_code=404,
            detail="Notification not found"
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return {
        "message": "Notification marked as read",
        "notification": notification
    }
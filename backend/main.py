
# ============================================================
# SmartEvent - Main FastAPI Application
# ============================================================

from fastapi import FastAPI, Depends, HTTPException, status,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func

import os
import uuid
import qrcode
import asyncio

from datetime import date, datetime, time, timedelta
from typing import Optional


from database import engine, Base, get_db, SessionLocal

from models import (
    User,
    Event,
    Booking,
    Ticket,
    Notification,
    Payment,
    Coupon,
    Review
)

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
    NotificationResponse,
    PaymentCreate,
    PaymentResponse,
    CouponCreate,
    CouponApply,
    CouponResponse,
    CouponValidationResponse,
    ReviewCreate,
    ReviewResponse,
    ReviewListResponse,
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QR_FOLDER = os.path.join(BASE_DIR, "qr_codes")

os.makedirs(QR_FOLDER, exist_ok=True)

app.mount(
    "/qr_codes",
    StaticFiles(directory=QR_FOLDER),
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
    if event.event_status in ("CANCELLED", "COMPLETED"):
        return False

    now = datetime.utcnow()
    event_date = event.event_date

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
    bookings = db.query(Booking).filter(
        Booking.event_id == event.id,
        Booking.booking_status == "CONFIRMED"
    ).all()

    user_ids = {booking.user_id for booking in bookings}

    for user_id in user_ids:
        db.add(Notification(
            user_id=user_id,
            title=notification_title,
            message=notification_message,
            notification_type="EVENT",
            is_read=False
        ))


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
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if role_data.role not in ["USER", "ORGANIZER", "ADMIN"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

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
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if db.query(Booking).filter(
        Booking.user_id == user_id
    ).first():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete user with existing bookings"
        )

    if db.query(Event).filter(
        Event.organizer_id == user_id
    ).first():
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
# Keep before /events/{event_id}
# ============================================================

@app.get("/events/search", response_model=list[EventResponse])
def search_events(
    title: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    sort_by: str = Query(default="date"),
    sort_order: str = Query(default="asc"),
    db: Session = Depends(get_db),
):
    # Validate sorting options
    allowed_sort_fields = {"date", "popularity", "price"}

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail="sort_by must be date, popularity, or price"
        )

    if sort_order not in {"asc", "desc"}:
        raise HTTPException(
            status_code=400,
            detail="sort_order must be asc or desc"
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date"
        )

    # Start with all events
    query = db.query(Event)

    # Search by event name
    if title and title.strip():
        query = query.filter(
            Event.title.ilike(f"%{title.strip()}%")
        )

    # Filter by category
    if category and category.strip():
        query = query.filter(
            Event.category.ilike(f"%{category.strip()}%")
        )

    # Filter by location
    if location and location.strip():
        query = query.filter(
            Event.location.ilike(f"%{location.strip()}%")
        )

    # Filter by date range
    if start_date:
        query = query.filter(
            Event.event_date >= datetime.combine(
                start_date, time.min
            )
        )

    if end_date:
        query = query.filter(
            Event.event_date <= datetime.combine(
                end_date, time.max
            )
        )

    # Sort events
    if sort_by == "date":
        sort_column = Event.event_date

    elif sort_by == "price":
        sort_column = Event.ticket_price

    else:
        # Popularity = total tickets in confirmed bookings
        popularity_subquery = (
            db.query(
                Booking.event_id.label("event_id"),
                func.sum(
                    Booking.ticket_quantity
                ).label("ticket_count")
            )
            .filter(Booking.booking_status == "CONFIRMED")
            .group_by(Booking.event_id)
            .subquery()
        )

        query = query.outerjoin(
            popularity_subquery,
            Event.id == popularity_subquery.c.event_id
        )

        popularity_column = func.coalesce(
            popularity_subquery.c.ticket_count, 0
        )

        sort_column = popularity_column

    if sort_order == "asc":
        query = query.order_by(sort_column.asc(), Event.id.asc())
    else:
        query = query.order_by(sort_column.desc(), Event.id.asc())

    events = query.all()

    # Keep existing event-status refresh behavior
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
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    refresh_event_status(event)
    db.refresh(event)

    return event


# ============================================================
# EVENTS - UPDATE
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
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    if (
        current_user.role == "ORGANIZER"
        and event.organizer_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can update only your own events"
        )

    if event.event_status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Cancelled events cannot be updated"
        )

    event.title = event_data.title
    event.description = event_data.description
    event.category = event_data.category
    event.location = event_data.location
    event.event_date = event_data.event_date
    event.ticket_price = event_data.ticket_price
    event.total_tickets = event_data.total_tickets
    event.banner_image = event_data.banner_image

    if event.event_status != "COMPLETED":
        event.event_status = "UPCOMING"
        refresh_event_status(event)

    notify_confirmed_bookers(
        db,
        event,
        "Event Updated",
        f'The event "{event.title}" has been updated. '
        "Please check the latest event details."
    )

    db.commit()
    db.refresh(event)

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
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    if (
        current_user.role == "ORGANIZER"
        and event.organizer_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can delete only your own events"
        )

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
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

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
        f'The event "{event.title}" has been cancelled. '
        "Please do not attend this event."
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
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

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
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

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

        revenue = sum(
            (
                booking.final_amount
                if booking.final_amount is not None
                else booking.total_price
            )
            for booking in confirmed
        )

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
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

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
            (
                booking.final_amount
                if booking.final_amount is not None
                else booking.total_price
            )
            for booking in confirmed
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
    current_user: User = Depends(require_role("ADMIN"))
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be later than end date"
        )

    quantity_col = getattr(Booking, "ticket_quantity", None)
    if quantity_col is None:
        quantity_col = getattr(Booking, "quantity", None)

    status_col = getattr(Booking, "booking_status", None)
    if status_col is None:
        status_col = getattr(Booking, "status", None)

    created_col = getattr(Booking, "created_at", None)

    if quantity_col is None or status_col is None:
        raise HTTPException(
            status_code=500,
            detail="Check Booking quantity and status fields"
        )

    if created_col is None:
        raise HTTPException(
            status_code=500,
            detail="Check Booking created_at field"
        )

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

    total_users = db.query(User).count()
    total_events = db.query(Event).count()
    total_bookings = filtered_bookings().count()
    confirmed_count = confirmed_bookings_query().count()

    cancelled_count = filtered_bookings().filter(
        func.upper(status_col) == "CANCELLED"
    ).count()

    revenue_expression = func.coalesce(
        func.sum(
            func.coalesce(Booking.final_amount, Booking.total_price)
        ),
        0
    )

    total_revenue = (
        confirmed_bookings_query()
        .with_entities(revenue_expression)
        .scalar() or 0
    )

    total_tickets_sold = (
        confirmed_bookings_query()
        .with_entities(func.coalesce(func.sum(quantity_col), 0))
        .scalar() or 0
    )

    daily_rows = (
        confirmed_bookings_query()
        .filter(created_col.isnot(None))
        .with_entities(
            func.date(created_col).label("sale_date"),
            func.coalesce(func.sum(quantity_col), 0).label("tickets_sold")
        )
        .group_by(func.date(created_col))
        .order_by(func.date(created_col))
        .all()
    )

    daily_ticket_sales = [
        {
            "date": str(row.sale_date),
            "tickets_sold": int(row.tickets_sold or 0)
        }
        for row in daily_rows
    ]

    month_expression = func.strftime("%Y-%m", created_col)

    monthly_rows = (
        filtered_bookings()
        .filter(created_col.isnot(None))
        .with_entities(
            month_expression.label("month"),
            func.count(Booking.id).label("total_bookings")
        )
        .group_by(month_expression)
        .order_by(month_expression)
        .all()
    )

    monthly_booking_trends = [
        {
            "month": str(row.month),
            "total_bookings": int(row.total_bookings or 0)
        }
        for row in monthly_rows
    ]

    popular_rows = (
        confirmed_bookings_query()
        .join(Event, Booking.event_id == Event.id)
        .with_entities(
            Event.id.label("event_id"),
            Event.title.label("event_title"),
            func.count(Booking.id).label("booking_count"),
            func.coalesce(func.sum(quantity_col), 0).label("tickets_sold")
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
            "tickets_sold": int(row.tickets_sold or 0)
        }
        for row in popular_rows
    ]

    revenue_rows = (
        confirmed_bookings_query()
        .join(Event, Booking.event_id == Event.id)
        .with_entities(
            Event.id.label("event_id"),
            Event.title.label("event_title"),
            func.coalesce(
                func.sum(
                    func.coalesce(
                        Booking.final_amount,
                        Booking.total_price
                    )
                ),
                0
            ).label("revenue")
        )
        .group_by(Event.id, Event.title)
        .order_by(func.sum(
            func.coalesce(Booking.final_amount, Booking.total_price)
        ).desc())
        .limit(5)
        .all()
    )

    top_revenue_events = [
        {
            "event_id": row.event_id,
            "event_title": row.event_title,
            "revenue": float(row.revenue or 0)
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
        "top_revenue_events": top_revenue_events
    }


# ============================================================
# HELPER - GENERATE TICKET QR
# ============================================================

def generate_ticket_qr(ticket_code: str):
    qr = qrcode.make(ticket_code)

    os.makedirs(QR_FOLDER, exist_ok=True)

    file_name = f"{ticket_code}.png"
    file_path = os.path.join(QR_FOLDER, file_name)

    qr.save(file_path)

    return f"/qr_codes/{file_name}"


# ============================================================
# MODULE 13 - CREATE COUPON (ADMIN ONLY)
# ============================================================

@app.post(
    "/coupons",
    response_model=CouponResponse,
    status_code=status.HTTP_201_CREATED
)
def create_coupon(
    coupon_data: CouponCreate,
    current_user: User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    coupon_code = coupon_data.coupon_code.strip().upper()

    if coupon_data.discount_type == "PERCENTAGE":
        if coupon_data.discount_value > 100:
            raise HTTPException(
                status_code=400,
                detail="Percentage discount cannot exceed 100%"
            )

    if coupon_data.expiry_date <= datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Coupon expiry date must be in the future"
        )

    existing_coupon = db.query(Coupon).filter(
        func.upper(Coupon.coupon_code) == coupon_code
    ).first()

    if existing_coupon:
        raise HTTPException(
            status_code=400,
            detail="Coupon code already exists"
        )

    new_coupon = Coupon(
        coupon_code=coupon_code,
        discount_type=coupon_data.discount_type,
        discount_value=coupon_data.discount_value,
        minimum_booking_amount=coupon_data.minimum_booking_amount,
        expiry_date=coupon_data.expiry_date,
        usage_limit=coupon_data.usage_limit,
        usage_count=0,
        is_active=coupon_data.is_active
    )

    db.add(new_coupon)
    db.commit()
    db.refresh(new_coupon)

    return new_coupon


# ============================================================
# MODULE 13 - LIST COUPONS (ADMIN ONLY)
# ============================================================

@app.get("/coupons", response_model=list[CouponResponse])
def get_coupons(
    current_user: User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


# ============================================================
# MODULE 13 - APPLY COUPON TO A PENDING BOOKING
# ============================================================

@app.post(
    "/coupons/apply",
    response_model=CouponValidationResponse
)
def apply_coupon(
    coupon_data: CouponApply,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(
        Booking.id == coupon_data.booking_id
    ).first()

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can apply a coupon only to your own booking"
        )

    if booking.booking_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Coupon can only be applied to a pending booking"
        )

    # Do not allow the price to change after payment has started.
    existing_payment = db.query(Payment).filter(
        Payment.booking_id == booking.id,
        Payment.payment_status == "SUCCESS"
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=400,
            detail="This booking has already been paid"
        )

    coupon_code = coupon_data.coupon_code.strip().upper()

    coupon = db.query(Coupon).filter(
        func.upper(Coupon.coupon_code) == coupon_code
    ).first()

    if coupon is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid coupon code"
        )

    if not coupon.is_active:
        raise HTTPException(
            status_code=400,
            detail="This coupon is inactive"
        )

    if coupon.expiry_date <= datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="This coupon has expired"
        )

    if coupon.usage_count >= coupon.usage_limit:
        raise HTTPException(
            status_code=400,
            detail="Coupon usage limit has been reached"
        )

    if booking.total_price < coupon.minimum_booking_amount:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Minimum booking amount is "
                f"₹{coupon.minimum_booking_amount:.2f}"
            )
        )

    if coupon.discount_type == "PERCENTAGE":
        discount = booking.total_price * coupon.discount_value / 100
    elif coupon.discount_type == "FIXED":
        discount = coupon.discount_value
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported coupon discount type"
        )

    discount = min(discount, booking.total_price)

    booking.coupon_id = coupon.id
    booking.discount_amount = round(discount, 2)
    booking.final_amount = round(
        booking.total_price - discount,
        2
    )

    db.commit()
    db.refresh(booking)

    return {
        "valid": True,
        "message": "Coupon applied successfully",
        "coupon_code": coupon.coupon_code,
        "original_amount": round(booking.total_price, 2),
        "discount_amount": booking.discount_amount,
        "final_amount": booking.final_amount
    }


# ============================================================
# BOOKINGS - CREATE PENDING BOOKING
# ============================================================

@app.post(
    "/bookings",
    response_model=BookingResponse,
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
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

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

    if booking_data.ticket_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Ticket quantity must be greater than zero"
        )

    active_bookings = db.query(Booking).filter(
        Booking.event_id == event.id,
        Booking.booking_status.in_(["PENDING", "CONFIRMED"])
    ).all()

    total_booked = sum(
        booking.ticket_quantity for booking in active_bookings
    )

    available = max(event.total_tickets - total_booked, 0)

    if booking_data.ticket_quantity > available:
        raise HTTPException(
            status_code=400,
            detail=f"Only {available} tickets are available"
        )

    total_price = round(
        event.ticket_price * booking_data.ticket_quantity,
        2
    )

    new_booking = Booking(
        user_id=current_user.id,
        event_id=event.id,
        ticket_quantity=booking_data.ticket_quantity,
        total_price=total_price,
        coupon_id=None,
        discount_amount=0,
        final_amount=total_price,
        booking_status="PENDING"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking



# ============================================================
# MODULE 12 + 13 - PROCESS SIMULATED PAYMENT
# ============================================================

@app.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED
)
def process_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(
        Booking.id == payment_data.booking_id
    ).first()

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can pay only for your own booking"
        )

    if booking.booking_status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Cannot pay for a cancelled booking"
        )

    if booking.booking_status == "CONFIRMED":
        raise HTTPException(
            status_code=400,
            detail="Booking is already confirmed"
        )

    existing_success = db.query(Payment).filter(
        Payment.booking_id == booking.id,
        Payment.payment_status == "SUCCESS"
    ).first()

    if existing_success:
        raise HTTPException(
            status_code=400,
            detail="This booking has already been paid"
        )

    coupon = None

    if booking.coupon_id is not None:
        coupon = db.query(Coupon).filter(
            Coupon.id == booking.coupon_id
        ).with_for_update().first()

        if coupon is None or not coupon.is_active:
            raise HTTPException(
                status_code=400,
                detail="The applied coupon is no longer available"
            )

        if coupon.expiry_date <= datetime.utcnow():
            raise HTTPException(
                status_code=400,
                detail="The applied coupon has expired"
            )

        if coupon.usage_count >= coupon.usage_limit:
            raise HTTPException(
                status_code=400,
                detail="Coupon usage limit has been reached"
            )

        if booking.total_price < coupon.minimum_booking_amount:
            raise HTTPException(
                status_code=400,
                detail="Booking no longer meets coupon minimum amount"
            )

        if coupon.discount_type == "PERCENTAGE":
            discount = (
                booking.total_price * coupon.discount_value / 100
            )
        else:
            discount = coupon.discount_value

        discount = min(discount, booking.total_price)

        booking.discount_amount = round(discount, 2)
        booking.final_amount = round(
            booking.total_price - discount,
            2
        )
    else:
        booking.discount_amount = 0
        booking.final_amount = booking.total_price

    payable_amount = round(booking.final_amount, 2)

    payment = Payment(
        booking_id=booking.id,
        payment_method=payment_data.payment_method,
        payment_status="PENDING",
        amount=payable_amount
    )

    db.add(payment)
    db.flush()

    # Simulated failed payment
    if payment_data.simulate_status == "FAILED":
        payment.payment_status = "FAILED"

        db.add(Notification(
            user_id=current_user.id,
            title="Payment Failed",
            message=(
                f"Payment of ₹{payable_amount:.2f} for booking "
                f"{booking.id} failed. Please try again."
            ),
            notification_type="PAYMENT",
            type="PAYMENT",
            is_read=False
        ))

        try:
            db.commit()
            db.refresh(payment)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Unable to save payment failure"
            )

        return payment

    # Simulated successful payment
    payment.payment_status = "SUCCESS"
    payment.transaction_id = f"DEMO-{uuid.uuid4().hex.upper()}"

    booking.booking_status = "CONFIRMED"

    if coupon is not None:
        coupon.usage_count += 1

    ticket = db.query(Ticket).filter(
        Ticket.booking_id == booking.id
    ).first()

    if ticket is None:
        ticket_code = f"TKT-{uuid.uuid4().hex[:8].upper()}"

        ticket = Ticket(
            booking_id=booking.id,
            ticket_code=ticket_code,
            qr_code_url=generate_ticket_qr(ticket_code)
        )

        db.add(ticket)

    event = db.query(Event).filter(
        Event.id == booking.event_id
    ).first()

    event_title = event.title if event else "your event"

    message = (
        f"Payment of ₹{payable_amount:.2f} for booking "
        f"{booking.id} was successful. "
        f"Your booking for {event_title} is confirmed."
    )

    if booking.discount_amount > 0:
        message += (
            f" You saved ₹{booking.discount_amount:.2f} "
            "with your coupon."
        )

    db.add(Notification(
        user_id=current_user.id,
        title="Payment Successful",
        message=message,
        type="PAYMENT",
        notification_type="PAYMENT",
        is_read=False
    ))

    
    try:
        db.commit()
        db.refresh(payment)
    except Exception as e:
        print("PAYMENT COMMIT ERROR:", repr(e))
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                "Payment processing failed. "
                "Check the backend terminal for the actual error."
            )
        )

    return payment




# ============================================================
# BOOKINGS - MY BOOKINGS
# ============================================================

@app.get(
    "/bookings/my-bookings",
    response_model=list[BookingResponse]
)
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
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

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

    event = db.query(Event).filter(
        Event.id == booking.event_id
    ).first()

    if event and event.event_status == "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="A completed event booking cannot be cancelled"
        )

    booking.booking_status = "CANCELLED"

    try:
        db.commit()
        db.refresh(booking)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to cancel booking"
        )

    return booking


# ============================================================
# TICKETS - MY TICKETS
# ============================================================

@app.get(
    "/tickets/my-tickets",
    response_model=list[TicketResponse]
)
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Ticket, Event)
        .join(Booking, Ticket.booking_id == Booking.id)
        .join(Event, Booking.event_id == Event.id)
        .filter(
            Booking.user_id == current_user.id,
            Booking.booking_status == "CONFIRMED"
        )
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
        raise HTTPException(
            status_code=404,
            detail="Invalid ticket"
        )

    booking = db.query(Booking).filter(
        Booking.id == ticket.booking_id
    ).first()

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.booking_status != "CONFIRMED":
        raise HTTPException(
            status_code=400,
            detail="Ticket is not confirmed"
        )

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

@app.get(
    "/notifications",
    response_model=list[NotificationResponse]
)
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
# NOTIFICATIONS - UNREAD COUNT
# ============================================================

@app.get("/notifications/unread-count")
def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return {"unread_count": count}


# ============================================================
# BACKGROUND CHECKER - STATUS + EVENT REMINDERS
# ============================================================

async def event_reminder_checker():
    while True:
        db = SessionLocal()

        try:
            now = datetime.utcnow()

            all_events = db.query(Event).all()

            for event in all_events:
                refresh_event_status(event)

            db.commit()

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
                            notification_type="EVENT",
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



# ============================================================
# NOTIFICATIONS - MARK ALL AS READ
# ============================================================

@app.put("/notifications/read-all")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update(
        {Notification.is_read: True},
        synchronize_session=False
    )

    db.commit()

    return {
        "message": "All notifications marked as read",
        "updated_count": updated_count
    }


# ============================================================
# MODULE 14 - EVENT FEEDBACK & RATINGS
# ============================================================

from sqlalchemy import func
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from models import Review
from schemas import ReviewCreate, ReviewResponse, ReviewListResponse


# ------------------------------------------------------------
# SUBMIT A REVIEW
# POST /events/{event_id}/reviews
# ------------------------------------------------------------

@app.post("/events/{event_id}/reviews", response_model=ReviewResponse)
def create_event_review(
    event_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check whether the event exists
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # The user must have a confirmed booking
    booking = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.event_id == event_id,
        Booking.booking_status == "CONFIRMED"
    ).first()

    if not booking:
        raise HTTPException(
            status_code=403,
            detail="You must have a confirmed booking to review this event"
        )

    # Reviews are allowed only after the event has finished
    if event.event_status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="You can review this event only after it is completed"
        )

    # Allow only one review per user for each event
    existing_review = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.event_id == event_id
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=400,
            detail="You have already reviewed this event. You can edit your existing review."
        )

    new_review = Review(
        user_id=current_user.id,
        event_id=event_id,
        rating=review_data.rating,
        review_text=review_data.review_text
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review


# ------------------------------------------------------------
# FETCH REVIEWS AND AVERAGE RATING
# GET /events/{event_id}/reviews
# ------------------------------------------------------------

@app.get(
    "/events/{event_id}/reviews",
    response_model=ReviewListResponse
)
def get_event_reviews(
    event_id: int,
    db: Session = Depends(get_db)
):
    # Check whether the event exists
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    reviews = db.query(Review).filter(
        Review.event_id == event_id
    ).order_by(Review.created_at.desc()).all()

    average_rating = db.query(
        func.avg(Review.rating)
    ).filter(
        Review.event_id == event_id
    ).scalar()

    return {
        "event_id": event_id,
        "average_rating": round(float(average_rating), 2) if average_rating is not None else 0.0,
        "total_reviews": len(reviews),
        "reviews": reviews
    }


# ------------------------------------------------------------
# EDIT YOUR OWN REVIEW
# PUT /reviews/{review_id}
# ------------------------------------------------------------

@app.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_event_review(
    review_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = db.query(Review).filter(
        Review.id == review_id
    ).first()

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    # Users can edit only their own reviews
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can edit only your own reviews"
        )

    review.rating = review_data.rating
    review.review_text = review_data.review_text

    db.commit()
    db.refresh(review)

    return review


# ------------------------------------------------------------
# DELETE YOUR OWN REVIEW
# DELETE /reviews/{review_id}
# ------------------------------------------------------------

@app.delete("/reviews/{review_id}")
def delete_event_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = db.query(Review).filter(
        Review.id == review_id
    ).first()

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    # Users can delete only their own reviews
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can delete only your own reviews"
        )

    db.delete(review)
    db.commit()

    return {
        "message": "Review deleted successfully"
    }

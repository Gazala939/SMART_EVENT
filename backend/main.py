
# ============================================================
# SmartEvent - Main FastAPI Application
# ============================================================

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Query,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func,text,inspect

import os
import uuid
import qrcode
import asyncio
import shutil

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
    Review,
    Wishlist,
    ViewedEvent,
    EventUpdate as EventUpdateModel,
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
    WishlistCreate,
    WishlistResponse,
    EventUpdateCreate,
    EventUpdateResponse,
    ProfileUpdate,
    ProfileSummaryResponse,
    ChatbotRequest,
    ChatbotResponse,
    )

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role
)



# ==========================================
# MODULE 18: PENDING BOOKING EXPIRY
# ==========================================

RESERVATION_HOLD_MINUTES = 15


def release_expired_bookings(db: Session, event_id=None):
    """
    Release ticket reservations for abandoned bookings.

    Pending bookings older than 15 minutes are cancelled.
    Payment history is preserved.
    """
    expiry_time = datetime.utcnow() - timedelta(
        minutes=RESERVATION_HOLD_MINUTES
    )

    query = db.query(Booking).filter(
        Booking.booking_status == "PENDING",
        Booking.created_at <= expiry_time
    )

    if event_id is not None:
        query = query.filter(Booking.event_id == event_id)

    expired_bookings = query.update(
        {"booking_status": "CANCELLED"},
        synchronize_session=False
    )

    return expired_bookings



# ============================================================
# DATABASE AND APPLICATION
# ============================================================

Base.metadata.create_all(bind=engine)
# Add new profile field to an existing SQLite database if needed.
# This preserves existing users and their data.
with engine.begin() as connection:
    if engine.dialect.name == "sqlite":
        user_columns = {
            column["name"]
            for column in inspect(connection).get_columns("users")
        }

        if "profile_picture" not in user_columns:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN profile_picture VARCHAR(500)"
                )
            )
            
        if "location" not in user_columns:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN location VARCHAR(200)"
                )
            )

app = FastAPI(
    title="SmartEvent API",
    description="SmartEvent Event Discovery and Ticket Booking System",
    version="1.0.0"
)
# ============================================================
# MODULE 18 - LIVE TICKET AVAILABILITY WEBSOCKET
# ============================================================

class AvailabilityConnectionManager:
    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    async def connect(self, event_id: int, websocket: WebSocket):
        await websocket.accept()

        if event_id not in self.connections:
            self.connections[event_id] = []

        self.connections[event_id].append(websocket)

    def disconnect(self, event_id: int, websocket: WebSocket):
        if event_id in self.connections:
            if websocket in self.connections[event_id]:
                self.connections[event_id].remove(websocket)

            if not self.connections[event_id]:
                del self.connections[event_id]

    async def broadcast(self, event_id: int, data: dict):
        disconnected = []

        for websocket in self.connections.get(event_id, []):
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(event_id, websocket)


availability_manager = AvailabilityConnectionManager()

# ============================================================
# MODULE 18 - BROADCAST UPDATED TICKET AVAILABILITY
# ============================================================

async def broadcast_event_availability(event_id: int):
    db = SessionLocal()

    try:
        event = db.query(Event).filter(
            Event.id == event_id
        ).first()

        if not event:
            return

        reserved_tickets = (
            db.query(
                func.coalesce(
                    func.sum(Booking.ticket_quantity), 0
                )
            )
            .filter(
                Booking.event_id == event_id,
                Booking.booking_status.in_(
                    ["PENDING", "CONFIRMED"]
                ),
            )
            .scalar()
        ) or 0

        availability_data = {
            "event_id": event_id,
            "total_tickets": event.total_tickets,
            "reserved_tickets": int(reserved_tickets),
            "available_tickets": max(
                event.total_tickets - int(reserved_tickets),
                0,
            ),
            "event_status": event.event_status,
        }

    finally:
        db.close()

    await availability_manager.broadcast(
        event_id,
        availability_data,
    )


@app.websocket("/ws/events/{event_id}/availability")
async def event_availability_websocket(
    websocket: WebSocket,
    event_id: int,
):
    print(f"WebSocket endpoint reached for event_id={event_id}")

    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            await websocket.close(code=1008, reason="Event not found")
            return

        await availability_manager.connect(event_id, websocket)

        reserved_tickets = (
            db.query(func.coalesce(func.sum(Booking.ticket_quantity), 0))
            .filter(
                Booking.event_id == event_id,
                Booking.booking_status.in_(["PENDING", "CONFIRMED"]),
            )
            .scalar()
        ) or 0

        await websocket.send_json({
            "event_id": event_id,
            "total_tickets": event.total_tickets,
            "reserved_tickets": int(reserved_tickets),
            "available_tickets": max(
                event.total_tickets - int(reserved_tickets), 0
            ),
            "event_status": event.event_status,
        })

        while True:
            # Keep the connection alive and detect disconnected clients.
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass

    finally:
        availability_manager.disconnect(event_id, websocket)
        db.close()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QR_FOLDER = os.path.join(BASE_DIR, "qr_codes")

os.makedirs(QR_FOLDER, exist_ok=True)

app.mount(
    "/qr_codes",
    StaticFiles(directory=QR_FOLDER),
    name="qr_codes"
)

PROFILE_FOLDER = os.path.join(BASE_DIR, "profile_pictures")
os.makedirs(PROFILE_FOLDER, exist_ok=True)

app.mount(
    "/profile_pictures",
    StaticFiles(directory=PROFILE_FOLDER),
    name="profile_pictures"
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
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
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
        
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=400,
            detail="min_price cannot be greater than max_price"
        )

    # Start with all events
    query = db.query(Event)
    
    # Filter by minimum ticket price
    if min_price is not None:
        query = query.filter(Event.ticket_price >= min_price)

    # Filter by maximum ticket price
    if max_price is not None:
        query = query.filter(Event.ticket_price <= max_price)

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


# MODULE 19: Record an event view
@app.post("/events/{event_id}/view")
def record_event_view(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the event
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # Save the user's view
    view_record = ViewedEvent(
        user_id=current_user.id,
        event_id=event_id
    )

    db.add(view_record)
    db.commit()

    return {
        "message": "Event view recorded successfully",
        "event_id": event_id
    }


# TEMPORARY TEST: Check saved event views
@app.get("/debug/my-event-views")
def debug_my_event_views(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = db.query(ViewedEvent).filter(
        ViewedEvent.user_id == current_user.id
    ).order_by(
        ViewedEvent.viewed_at.desc()
    ).limit(20).all()

    return [
        {
            "event_id": record.event_id,
            "viewed_at": record.viewed_at
        }
        for record in records
    ]


# TEMPORARY DEBUG: Inspect personalized recommendation inputs
@app.get("/debug/recommendation-check")
def debug_recommendation_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    views = db.query(ViewedEvent).filter(
        ViewedEvent.user_id == current_user.id
    ).all()

    viewed_ids = list({view.event_id for view in views})

    viewed_events = db.query(Event).filter(
        Event.id.in_(viewed_ids)
    ).all() if viewed_ids else []

    candidates = db.query(Event).filter(
        Event.event_status.notin_(
            ["CANCELLED", "COMPLETED", "ONGOING"]
        ),
        Event.event_date >= datetime.utcnow()
    ).all()

    return {
        "viewed_events": [
            {
                "id": event.id,
                "title": event.title,
                "category": event.category,
                "status": event.event_status,
                "event_date": event.event_date
            }
            for event in viewed_events
        ],
        "eligible_candidates": [
            {
                "id": event.id,
                "title": event.title,
                "category": event.category,
                "status": event.event_status,
                "event_date": event.event_date
            }
            for event in candidates
        ]
    }

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
# GET /events/{event_id}/availability
# ============================================================


@app.get("/events/{event_id}/availability")
def get_ticket_availability(
    event_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        event = db.query(Event).filter(
            Event.id == event_id
        ).first()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        # Release expired reservations.
        expired_count = release_expired_bookings(
            db,
            event_id=event.id
        )

        refresh_event_status(event)

        reserved = db.query(
            func.coalesce(
                func.sum(Booking.ticket_quantity), 0
            )
        ).filter(
            Booking.event_id == event.id,
            Booking.booking_status.in_(
                ["PENDING", "CONFIRMED"]
            )
        ).scalar()

        reserved = int(reserved or 0)
        available = max(
            event.total_tickets - reserved, 0
        )

        if event.event_status in (
            "CANCELLED", "COMPLETED", "ONGOING"
        ):
            available = 0

        db.commit()

        # Broadcast after committing if expired bookings were released.
        if expired_count > 0:
            background_tasks.add_task(
                broadcast_event_availability,
                event.id
            )

        return {
            "event_id": event.id,
            "total_tickets": event.total_tickets,
            "reserved_tickets": reserved,
            "available_tickets": available,
            "event_status": event.event_status,
            "sold_out": available == 0
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        print("AVAILABILITY ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve ticket availability"
        )



# ============================================================
#  CREATE PENDING BOOKING SAFELY
# ============================================================
@app.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED
)
def create_booking(
    booking_data: BookingCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Acquire SQLite write lock before checking availability.
        db.rollback()
        db.execute(text("BEGIN IMMEDIATE"))

        event = db.query(Event).filter(
            Event.id == booking_data.event_id
        ).first()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        # Release expired reservations.
        release_expired_bookings(db, event_id=event.id)
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

        quantity = booking_data.ticket_quantity

        if quantity <= 0 or quantity > 10:
            raise HTTPException(
                status_code=400,
                detail="Ticket quantity must be between 1 and 10"
            )

        reserved = db.query(
            func.coalesce(
                func.sum(Booking.ticket_quantity), 0
            )
        ).filter(
            Booking.event_id == event.id,
            Booking.booking_status.in_(
                ["PENDING", "CONFIRMED"]
            )
        ).scalar()

        reserved = int(reserved or 0)
        available = max(event.total_tickets - reserved, 0)

        if quantity > available:
            raise HTTPException(
                status_code=400,
                detail=f"Only {available} tickets are available"
            )

        total_price = round(
            event.ticket_price * quantity, 2
        )

        new_booking = Booking(
            user_id=current_user.id,
            event_id=event.id,
            ticket_quantity=quantity,
            total_price=total_price,
            coupon_id=None,
            discount_amount=0,
            final_amount=total_price,
            booking_status="PENDING"
        )

        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        # Broadcast only after the booking has been committed.
        background_tasks.add_task(
            broadcast_event_availability,
            event.id
        )

        return new_booking

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        print("BOOKING CREATION ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to create booking. Please try again."
        )



# ============================================================
#  PROCESS SIMULATED PAYMENT
# ============================================================


# ============================================================
# PROCESS PAYMENT API
# ============================================================

@app.post("/payments", response_model=PaymentResponse, status_code=201)
def process_payment(
    payment_data: PaymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # ----------------------------------------------------
        # 1. Start a protected database transaction
        # ----------------------------------------------------
        db.rollback()
        db.execute(text("BEGIN IMMEDIATE"))

        # ----------------------------------------------------
        # 2. Find the booking
        # ----------------------------------------------------
        booking = (
            db.query(Booking)
            .filter(Booking.id == payment_data.booking_id)
            .first()
        )

        if booking is None:
            raise HTTPException(
                status_code=404,
                detail="Booking not found"
            )

        # ----------------------------------------------------
        # 3. Verify booking ownership
        # ----------------------------------------------------
        if booking.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only pay for your own bookings"
            )

        # ----------------------------------------------------
        # 4. Check whether the reservation has expired
        # Reservation hold time: 15 minutes
        # ----------------------------------------------------
        if (
            booking.booking_status == "PENDING"
            and booking.created_at is not None
            and booking.created_at
            <= datetime.utcnow()
            - timedelta(minutes=RESERVATION_HOLD_MINUTES)
        ):
            booking.booking_status = "CANCELLED"
            db.commit()

            raise HTTPException(
                status_code=400,
                detail=(
                    "This reservation has expired. "
                    "Please create a new booking."
                )
            )

        # ----------------------------------------------------
        # 5. Validate booking status
        # ----------------------------------------------------
        if booking.booking_status == "CANCELLED":
            raise HTTPException(
                status_code=400,
                detail="This booking has been cancelled"
            )

        if booking.booking_status == "CONFIRMED":
            raise HTTPException(
                status_code=400,
                detail="This booking has already been paid"
            )

        # ----------------------------------------------------
        # 6. Prevent duplicate successful payments
        # ----------------------------------------------------
        existing_success = (
            db.query(Payment)
            .filter(
                Payment.booking_id == booking.id,
                Payment.payment_status == "SUCCESS"
            )
            .first()
        )

        if existing_success:
            raise HTTPException(
                status_code=400,
                detail="A successful payment already exists"
            )

        # ----------------------------------------------------
        # 7. Validate the payment method
        # ----------------------------------------------------
        if payment_data.payment_method != "SIMULATED":
            raise HTTPException(
                status_code=400,
                detail="Unsupported payment method"
            )

        # ----------------------------------------------------
        # 8. Validate the event and ticket availability
        # ----------------------------------------------------
        event = (
            db.query(Event)
            .filter(Event.id == booking.event_id)
            .first()
        )

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        release_expired_bookings(db, event_id=event.id)
        refresh_event_status(event)

        if event.event_status in (
            "CANCELLED",
            "COMPLETED",
            "ONGOING"
        ):
            raise HTTPException(
                status_code=400,
                detail="Tickets cannot be purchased for this event"
            )

        # Recalculate availability while the transaction is active.
        reserved_tickets = (
            db.query(
                func.coalesce(
                    func.sum(Booking.ticket_quantity),
                    0
                )
            )
            .filter(
                Booking.event_id == event.id,
                Booking.booking_status.in_(
                    ["PENDING", "CONFIRMED"]
                )
            )
            .scalar()
        )

        reserved_tickets = int(reserved_tickets or 0)

        other_reserved_tickets = max(
            reserved_tickets - booking.ticket_quantity,
            0
        )

        available_for_this_booking = max(
            event.total_tickets - other_reserved_tickets,
            0
        )

        if booking.ticket_quantity > available_for_this_booking:
            raise HTTPException(
                status_code=400,
                detail="Not enough tickets are available to complete payment."
            )

        # ----------------------------------------------------
        # 9. Calculate coupon discount, if one was applied
        # ----------------------------------------------------
        discount_amount = 0.0
        final_amount = float(booking.total_price or 0)

        if booking.coupon_id is not None:
            coupon = (
                db.query(Coupon)
                .filter(Coupon.id == booking.coupon_id)
                .first()
            )

            if coupon is None:
                raise HTTPException(
                    status_code=400,
                    detail="The applied coupon no longer exists"
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
                    detail="This coupon has reached its usage limit"
                )

            if (
                booking.total_price
                < coupon.minimum_booking_amount
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Booking amount does not meet the "
                        "coupon's minimum requirement"
                    )
                )

            if coupon.discount_type.upper() in (
                "PERCENTAGE",
                "PERCENT"
            ):
                discount_amount = (
                    float(booking.total_price)
                    * float(coupon.discount_value)
                    / 100
                )
            elif coupon.discount_type.upper() in (
                "FIXED",
                "FLAT"
            ):
                discount_amount = float(coupon.discount_value)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported coupon discount type"
                )

            # Never allow a discount greater than the booking amount.
            discount_amount = min(
                max(discount_amount, 0.0),
                float(booking.total_price)
            )

            final_amount = max(
                float(booking.total_price) - discount_amount,
                0.0
            )

        # Save the calculated amounts on the booking.
        booking.discount_amount = discount_amount
        booking.final_amount = final_amount

        # ----------------------------------------------------
        # 10. Create the payment record
        # ----------------------------------------------------
        payment = Payment(
            booking_id=booking.id,
            payment_method=payment_data.payment_method,
            payment_status="PENDING",
            transaction_id=None,
            amount=final_amount
        )

        db.add(payment)
        db.flush()

        # ----------------------------------------------------
        # 11. Handle simulated payment failure
        # ----------------------------------------------------
        if payment_data.simulate_status == "FAILED":
            payment.payment_status = "FAILED"
            booking.booking_status = "CANCELLED"

            failure_notification = Notification(
                user_id=current_user.id,
                title="Payment Failed",
                message=(
                    f"Payment for event '{event.title}' failed. "
                    "Please create a new booking to try again."
                ),
                type="PAYMENT",
                notification_type="PAYMENT",
                is_read=False
            )

            db.add(failure_notification)
            db.commit()
            db.refresh(payment)

            background_tasks.add_task(
                broadcast_event_availability,
                event.id
            )

            return payment
        

        # ----------------------------------------------------
        # 12. Handle successful simulated payment
        # ----------------------------------------------------
        payment.payment_status = "SUCCESS"
        payment.transaction_id = str(uuid.uuid4())

        booking.booking_status = "CONFIRMED"

        # Increase coupon usage only after successful payment.
        if booking.coupon_id is not None:
            coupon.usage_count += 1

        # ----------------------------------------------------
        # 13. Create a ticket and QR code
        # ----------------------------------------------------
        existing_ticket = (
            db.query(Ticket)
            .filter(Ticket.booking_id == booking.id)
            .first()
        )

        if existing_ticket is None:
            ticket_code = str(uuid.uuid4())

            # Ensure the QR-code directory exists.
            os.makedirs(QR_FOLDER, exist_ok=True)

            qr_filename = f"ticket_{ticket_code}.png"
            qr_filepath = os.path.join(
                QR_FOLDER,
                qr_filename
            )

            # Generate the QR code containing the ticket code.
            qr_image = qrcode.make(ticket_code)
            qr_image.save(qr_filepath)

            new_ticket = Ticket(
                booking_id=booking.id,
                ticket_code=ticket_code,
                qr_code_url=f"/qr_codes/{qr_filename}"
            )

            db.add(new_ticket)

        # ----------------------------------------------------
        # 14. Create a payment success notification
        # ----------------------------------------------------
        success_notification = Notification(
            user_id=current_user.id,
            title="Payment Successful",
            message=(
                f"Your payment for '{event.title}' was successful. "
                "Your booking is confirmed and your ticket is ready."
            ),
            type="PAYMENT",
            notification_type="PAYMENT",
            is_read=False
        )

        db.add(success_notification)

        # ----------------------------------------------------
        # 15. Commit all successful payment changes
        # ----------------------------------------------------
        db.commit()
        db.refresh(payment)

        return payment

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()

        print(
            "PAYMENT PROCESSING ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the payment"
        )

    




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

@app.put(
    "/bookings/{booking_id}/cancel",
    response_model=BookingResponse
)
def cancel_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
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

    if booking.booking_status == "CONFIRMED":
        raise HTTPException(
            status_code=400,
            detail="A confirmed booking cannot be cancelled here"
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

        if event:
            background_tasks.add_task(
                broadcast_event_availability,
                event.id
            )

    except Exception as error:
        db.rollback()
        print("BOOKING CANCELLATION ERROR:", repr(error))

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


# ============================================================
# MODULE 19: TRENDING EVENTS AND PERSONALIZED RECOMMENDATIONS
# ============================================================
# MODULE 19: Trending events based on confirmed ticket sales
@app.get(
    "/recommendations/trending",
    response_model=list[EventResponse]
)
def get_trending_events(
    db: Session = Depends(get_db)
):
    # Count tickets sold for each event using confirmed bookings.
    popularity_subquery = (
        db.query(
            Booking.event_id.label("event_id"),
            func.sum(
                Booking.ticket_quantity
            ).label("tickets_sold")
        )
        .filter(Booking.booking_status == "CONFIRMED")
        .group_by(Booking.event_id)
        .subquery()
    )

    # Select upcoming events and include their popularity.
    events = (
        db.query(Event)
        .outerjoin(
            popularity_subquery,
            Event.id == popularity_subquery.c.event_id
        )
        .filter(
            Event.event_status.notin_(
                ["CANCELLED", "COMPLETED", "ONGOING"]
            ),
            Event.event_date >= datetime.utcnow()
        )
        .order_by(
            func.coalesce(
                popularity_subquery.c.tickets_sold, 0
            ).desc(),
            Event.event_date.asc()
        )
        .limit(10)
        .all()
    )

    refresh_event_statuses(db, events)

    return events
# MODULE 19: Track events viewed by a user
@app.post("/events/{event_id}/view")
def track_event_view(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check whether the event exists.
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Find an existing view record for this user and event.
    viewed = db.query(ViewedEvent).filter(
        ViewedEvent.user_id == current_user.id,
        ViewedEvent.event_id == event_id
    ).first()

    if viewed:
        # Refresh the viewing time instead of creating duplicates.
        viewed.viewed_at = datetime.utcnow()
    else:
        viewed = ViewedEvent(
            user_id=current_user.id,
            event_id=event_id
        )
        db.add(viewed)

    db.commit()

    return {"message": "Event view tracked successfully"}




# MODULE 19: Personalized recommendations
@app.get(
    "/recommendations/for-me",
    response_model=list[EventResponse]
)
def get_personalized_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Find the user's confirmed bookings.
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.booking_status == "CONFIRMED"
    ).all()

    booked_event_ids = {
        booking.event_id for booking in bookings
    }

    # 2. Find the categories of events the user booked.
    booked_events = []

    if booked_event_ids:
        booked_events = db.query(Event).filter(
            Event.id.in_(booked_event_ids)
        ).all()

    booked_categories = {
        event.category for event in booked_events
    }

    # 3. Find the user's recently viewed events.
    viewed_records = db.query(ViewedEvent).filter(
        ViewedEvent.user_id == current_user.id
    ).order_by(
        ViewedEvent.viewed_at.desc()
    ).limit(20).all()

    viewed_event_ids = {
        record.event_id for record in viewed_records
    }

    viewed_events = []

    if viewed_event_ids:
        viewed_events = db.query(Event).filter(
            Event.id.in_(viewed_event_ids)
        ).all()

    viewed_categories = {
        event.category for event in viewed_events
    }

    # 4. Combine categories from bookings and views.
    preferred_categories = (
        booked_categories | viewed_categories
    )

    # 5. Get future events that are available for discovery.
    query = db.query(Event).filter(
        Event.event_status.notin_(
            ["CANCELLED", "COMPLETED", "ONGOING"]
        ),
        Event.event_date >= datetime.utcnow()
    )

    # Do not recommend events the user has already booked.
    if booked_event_ids:
        query = query.filter(
            ~Event.id.in_(booked_event_ids)
        )

    candidate_events = query.all()

    # 6. Rank events by category and preferred location.
    preferred_location = (
        (current_user.location or "").strip().casefold()
    )

    
    def recommendation_score(event):
        event_location = (
            (event.location or "").strip().casefold()
        )

        event_category = (
            (event.category or "").strip().casefold()
        )

        normalized_booked_categories = {
            category.strip().casefold()
            for category in booked_categories
            if category
        }

        normalized_preferred_categories = {
            category.strip().casefold()
            for category in preferred_categories
            if category
        }

        location_match = (
            bool(preferred_location)
            and bool(event_location)
            and (
                preferred_location in event_location
                or event_location in preferred_location
            )
        )

        booked_category_match = (
            event_category in normalized_booked_categories
        )

        preferred_category_match = (
            event_category in normalized_preferred_categories
        )

        return (
            not booked_category_match,
            not preferred_category_match,
            not location_match,
            event.event_date
        )
        
    # Sort events by personalized recommendation score   
    candidate_events.sort(key=recommendation_score)
    print("DEBUG - Candidate count:", len(candidate_events))
    print("DEBUG - Sorted candidates:", [
        (event.id, event.title, event.category)
        for event in candidate_events
    ])
   
    # Refresh event statuses before returning results
    refresh_event_statuses(db, candidate_events)

    # Return up to 10 personalized events
    return candidate_events[:10]


# ============================================================
# MODULE 20: WISHLIST
# ============================================================

@app.post(
    "/wishlist",
    response_model=WishlistResponse,
    status_code=status.HTTP_201_CREATED
)
def add_to_wishlist(
    data: WishlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == data.event_id
    ).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.event_id == data.event_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Event is already in your wishlist"
        )

    item = Wishlist(
        user_id=current_user.id,
        event_id=data.event_id
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/wishlist", response_model=list[WishlistResponse])
def get_my_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return (
        db.query(Wishlist)
        .filter(Wishlist.user_id == current_user.id)
        .order_by(Wishlist.created_at.desc())
        .all()
    )


@app.get("/wishlist/events", response_model=list[EventResponse])
def get_my_wishlist_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return (
        db.query(Event)
        .join(Wishlist, Wishlist.event_id == Event.id)
        .filter(Wishlist.user_id == current_user.id)
        .order_by(Wishlist.created_at.desc())
        .all()
    )


@app.delete("/wishlist/{event_id}")
def remove_from_wishlist(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(Wishlist).filter(
        Wishlist.event_id == event_id,
        Wishlist.user_id == current_user.id
    ).first()

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found in your wishlist"
        )

    db.delete(item)
    db.commit()
    return {"message": "Event removed from wishlist"}




# ============================================================
# MODULE 21: EVENT UPDATES AND ANNOUNCEMENTS
# ============================================================

@app.post(
    "/events/{event_id}/updates",
    response_model=EventUpdateResponse,
    status_code=status.HTTP_201_CREATED
)
def create_event_update(
    event_id: int,
    data: EventUpdateCreate,
    current_user: User = Depends(
        require_role("ORGANIZER", "ADMIN")
    ),
    db: Session = Depends(get_db)
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
            detail="You can post updates only for your own events"
        )

    update = EventUpdateModel(
        event_id=event.id,
        message=data.message.strip(),
        is_important=data.is_important
    )
    db.add(update)

    # Notify users with confirmed bookings.
    notify_confirmed_bookers(
        db,
        event,
        "Important Event Update" if data.is_important else "Event Update",
        f"{event.title}: {data.message.strip()}"
    )

    db.commit()
    db.refresh(update)
    return update


@app.get(
    "/events/{event_id}/updates",
    response_model=list[EventUpdateResponse]
)
def get_event_updates(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return (
        db.query(EventUpdateModel)
        .filter(EventUpdateModel.event_id == event_id)
        .order_by(
            EventUpdateModel.is_important.desc(),
            EventUpdateModel.created_at.desc()
        )
        .all()
    )


# ============================================================
# MODULE 22: EDIT PROFILE
# ============================================================

@app.put("/auth/profile", response_model=UserResponse)
def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.username is not None:
        username = data.username.strip()
        if not username:
            raise HTTPException(
                status_code=400,
                detail="Username cannot be empty"
            )

        existing = db.query(User).filter(
            User.username == username,
            User.id != current_user.id
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )
        current_user.username = username

    if data.email is not None:
        existing = db.query(User).filter(
            User.email == data.email,
            User.id != current_user.id
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )
        current_user.email = data.email

    if data.profile_picture is not None:
        current_user.profile_picture = data.profile_picture
        
    if data.location is not None:
        current_user.location = data.location.strip()

    db.commit()
    db.refresh(current_user)
    return current_user


@app.post("/auth/profile/picture", response_model=UserResponse)
def upload_profile_picture(
    picture: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp"
    }

    extension = allowed_types.get(picture.content_type)
    if extension is None:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, PNG, or WEBP image"
        )

    # Limit uploads to 5 MB.
    contents = picture.file.read(5 * 1024 * 1024 + 1)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Profile picture must be 5 MB or smaller"
        )

    filename = f"user_{current_user.id}_{uuid.uuid4().hex}{extension}"
    path = os.path.join(PROFILE_FOLDER, filename)

    with open(path, "wb") as image_file:
        image_file.write(contents)

    current_user.profile_picture = f"/profile_pictures/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user


@app.get("/auth/profile/summary", response_model=ProfileSummaryResponse)
def get_profile_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id
    ).all()

    confirmed = [
        booking for booking in bookings
        if booking.booking_status == "CONFIRMED"
    ]
    cancelled = [
        booking for booking in bookings
        if booking.booking_status == "CANCELLED"
    ]

    return {
        "total_bookings": len(bookings),
        "confirmed_bookings": len(confirmed),
        "cancelled_bookings": len(cancelled),
        "total_tickets": sum(
            booking.ticket_quantity for booking in confirmed
        ),
        "total_spent": round(sum(
            float(
                booking.final_amount
                if booking.final_amount is not None
                else booking.total_price
            )
            for booking in confirmed
        ), 2)
    }


# ============================================================
# MODULE 24: EVENT AND BOOKING CHATBOT
# Rule-based assistant; no external AI credentials required.
# ============================================================

@app.post("/chatbot", response_model=ChatbotResponse)
def chatbot(
    data: ChatbotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    message = data.message.strip().lower()

    if any(word in message for word in ["my booking", "my bookings", "booking history"]):
        bookings = db.query(Booking).filter(
            Booking.user_id == current_user.id
        ).order_by(Booking.created_at.desc()).limit(10).all()

        lines = []
        for booking in bookings:
            event = db.query(Event).filter(
                Event.id == booking.event_id
            ).first()
            event_name = event.title if event else f"Event #{booking.event_id}"
            lines.append(
                f"{event_name}: {booking.booking_status}, "
                f"{booking.ticket_quantity} ticket(s)"
            )

        return {
            "answer": "\n".join(lines) if lines else "You have no bookings yet.",
            "intent": "bookings",
            "events": []
        }
        
    
    # Ticket support
    if any(phrase in message for phrase in [
        "get my ticket",
        "get ticket",
        "my ticket",
        "find my ticket",
        "download ticket",
        "where is my ticket",
        "ticket qr",
        "qr code",
        "ticket support"
    ]):
        return {
            "answer": (
                "To get your ticket, open My Tickets after booking. "
                "Find your confirmed booking and open its ticket to view "
                "the QR code. If your ticket is missing, check My Bookings "
                "to confirm your booking status. If payment or booking failed, "
                "please contact support with your booking details."
            ),
            "intent": "ticket_support",
            "events": []
        }


    if any(word in message for word in ["ticket issue", "payment issue", "problem", "help"]):
        return {
            "answer": (
                "For ticket help, open My Tickets to check your confirmed tickets "
                "and QR codes. For a payment issue, check My Bookings and your "
                "payment status. You can also revisit the event and booking details."
            ),
            "intent": "support",
            "events": []
        }

    query = db.query(Event).filter(
        Event.event_status.notin_(["CANCELLED", "COMPLETED"]),
        Event.event_date >= datetime.utcnow()
    )

    category_words = ["music", "tech", "technology", "sports", "business"]
    category = next(
        (word for word in category_words if word in message),
        None
    )

    if category:
        if category == "technology":
            category = "tech"
        query = query.filter(Event.category.ilike(f"%{category}%"))

    if "near me" in message or "nearby" in message:
        return {
            "answer": (
                "I can filter events by location, but I do not have your "
                "current location in this chat. Please tell me your city "
                "or use the event search location filter."
            ),
            "intent": "location_help",
            "events": []
        }

    if "weekend" in message:
        today = datetime.utcnow().date()
        days_until_saturday = (5 - today.weekday()) % 7
        saturday = today + timedelta(days=days_until_saturday)
        sunday = saturday + timedelta(days=1)
        query = query.filter(
            Event.event_date >= datetime.combine(saturday, time.min),
            Event.event_date <= datetime.combine(sunday, time.max)
        )

    events = query.order_by(Event.event_date.asc()).limit(10).all()

    if events:
        names = ", ".join(event.title for event in events[:5])
        answer = f"Here are some events you may like: {names}."
        intent = "event_recommendations"
    else:
        answer = (
            "I couldn't find matching upcoming events. Try another category, "
            "date, or location."
        )
        intent = "event_search"

    return {
        "answer": answer,
        "intent": intent,
        "events": events
    }

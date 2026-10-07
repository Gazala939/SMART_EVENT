# SmartEvent – Event Discovery & Ticket Booking Platform

SmartEvent is a full-stack event discovery and ticket booking platform built using **FastAPI** for the backend and **React.js with Vite** for the frontend.

The application allows users to register and log in securely, discover events, search and filter events, book tickets, receive QR-based digital tickets, view booking history, and receive event and booking notifications.

---

## 🚀 Features

### 1. User Authentication

* User registration
* User login
* JWT-based authentication
* Bcrypt password hashing
* Protected routes
* User profile
* Logout
* JWT stored in browser localStorage

### 2. Event Discovery

* View all available events
* View individual event details
* Search events by title
* Filter events by category
* Supported categories:

  * Music
  * Tech
  * Sports
  * Business
* Event banner images
* Event date and time
* Event location
* Ticket price

### 3. Ticket Booking

* Authenticated users can book tickets
* Select ticket quantity
* Maximum 10 tickets per booking
* Automatic total price calculation
* Ticket availability checking
* Sold-out prevention
* Booking confirmation
* Booking history
* Users can cancel their own bookings

### 4. QR Code Ticket System

* Unique ticket code generated for every booking
* QR code automatically generated after booking
* QR code stored on the backend
* Digital ticket display
* Event details displayed with the ticket
* Download QR ticket
* Ticket verification endpoint
* Cancelled tickets cannot be verified as valid

### 5. Notifications

* Booking confirmation notification
* Event reminder notification
* Notification bell
* Unread notification count
* Notification dropdown
* Mark notification as read
* View all notifications

### 6. React Frontend

The frontend contains:

* Register page
* Login page
* Home page
* Event details page
* Booking confirmation page
* Booking history page
* Tickets page
* Notifications page
* Profile page

Reusable components include:

* Navbar
* ProtectedRoute
* EventCard
* TicketCard
* NotificationDropdown

---

## 🛠️ Technology Stack

### Backend

* Python 3.13
* FastAPI
* SQLAlchemy
* SQLite
* Pydantic
* JWT
* Bcrypt
* QR Code
* Uvicorn
* Python-dotenv

### Frontend

* React.js
* Vite
* JavaScript
* Axios
* React Router DOM
* CSS

### Database

* SQLite

Database file:

```text
smartevent.db
```

---



# ⚙️ Backend Setup

## 1. Open the backend folder

```text
cd C:\SmartEvent\backend
```

## 2. Create virtual environment

```text
python -m venv venv
```

## 3. Activate virtual environment

```text
venv\Scripts\activate
```

## 4. Install dependencies

```text
pip install -r requirements.txt
```

## 5. Configure environment variables

Create a `.env` file inside the backend folder:

```text
SECRET_KEY=smartevent_secret_key_123456
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 6. Start the FastAPI server

```text
python -m uvicorn main:app --reload
```

Backend will run at:

```text
http://127.0.0.1:8000
```

---

# 📖 API Documentation

FastAPI automatically provides Swagger documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

The API documentation can be used to test all backend endpoints.

---

# 💻 Frontend Setup

Open a new terminal.

## 1. Go to frontend folder

```text
cd C:\SmartEvent\frontend
```

## 2. Install dependencies

```text
npm.cmd install
```

If `npm` works normally on your system, you can also use:

```text
npm install
```

## 3. Start React development server

```text
npm.cmd run dev
```

The frontend will normally run at:

```text
http://localhost:5173
```

---

# 🔐 Authentication Flow

The authentication process works as follows:

```text
User
  ↓
Register
  ↓
Backend validates data
  ↓
Password is hashed using Bcrypt
  ↓
User stored in SQLite
  ↓
Login
  ↓
JWT token generated
  ↓
Token stored in localStorage
  ↓
Protected API requests use Bearer Token
```

Example authorization header:

```text
Authorization: Bearer <JWT_TOKEN>
```

---

# 🎟️ Booking Workflow

The ticket booking process is:

```text
Login
  ↓
Home Page
  ↓
Select Event
  ↓
View Event Details
  ↓
Select Ticket Quantity
  ↓
Book Tickets
  ↓
Check Ticket Availability
  ↓
Calculate Total Price
  ↓
Create Booking
  ↓
Generate Unique Ticket Code
  ↓
Generate QR Code
  ↓
Create Booking Notification
  ↓
Booking Confirmation
```

---

# 📱 Digital Ticket

After successful booking, the system generates:

* Booking ID
* Unique ticket code
* QR code
* Event title
* Event location
* Event date
* Ticket information

The QR code can also be downloaded from the Tickets page.

---

# 🔎 Ticket Verification

Tickets can be verified using the ticket code.

API endpoint:

```text
GET /tickets/verify/{ticket_code}
```

The system checks whether:

* The ticket exists
* The booking exists
* The booking has not been cancelled

---

# 🔔 Notification System

SmartEvent supports:

### Booking Notification

A notification is automatically created after a successful booking.

Example:

```text
Booking Confirmed

Your ticket has been successfully booked.
```

### Event Reminder

The backend checks upcoming events and creates a reminder notification for users who have confirmed bookings.

### Notification Management

Users can:

* View notifications
* See unread notification count
* Open notification dropdown
* Mark notifications as read
* View all notifications

---

# 📡 API Endpoints

## Authentication

```text
POST /auth/register
POST /auth/login
GET  /auth/profile
```

## Events

```text
POST /events
GET  /events
GET  /events/{event_id}
GET  /events/category/{category}
GET  /events/search
PUT  /events/{event_id}
```

## Bookings

```text
POST /bookings
GET  /bookings/my-bookings
PUT  /bookings/{booking_id}/cancel
```

## Tickets

```text
GET /tickets/my-tickets
GET /tickets/verify/{ticket_code}
```

## Notifications

```text
GET /notifications
PUT /notifications/{notification_id}/read
```

---

# 🗄️ Database Tables

The SQLite database contains the following tables:

### Users

Stores registered user information.

```text
id
username
email
hashed_password
created_at
```

### Events

Stores event information.

```text
id
title
description
category
location
event_date
ticket_price
banner_image
total_tickets
created_at
```

### Bookings

Stores ticket booking information.

```text
id
user_id
event_id
ticket_quantity
total_price
booking_status
created_at
```

### Tickets

Stores digital ticket information.

```text
id
booking_id
ticket_code
qr_code_url
created_at
```

### Notifications

Stores user notifications.

```text
id
user_id
title
message
type
is_read
created_at
```

---

# 🔒 Security

The application implements:

* JWT authentication
* Bcrypt password hashing
* Protected booking routes
* Protected profile route
* Protected ticket routes
* Protected notification routes
* User-specific booking history
* Ownership validation when cancelling bookings
* Pydantic input validation
* Ticket verification
* Cancelled booking validation

---

# 🧪 Testing

The application can be tested using:

### Backend

FastAPI Swagger:

```text
http://127.0.0.1:8000/docs
```

### Frontend

React application:

```text
http://localhost:5173
```

The complete workflow can be tested using:

```text
Register
→ Login
→ Discover Events
→ Search / Filter
→ View Event
→ Book Tickets
→ Booking Confirmation
→ View QR Ticket
→ View Booking History
→ View Notifications
→ Mark Notification as Read
```

---

# 🎯 Project Objective

The objective of SmartEvent is to provide a complete event discovery and digital ticket booking platform where users can discover events, securely book tickets, receive QR-based digital tickets, and receive notifications about their bookings and upcoming events.

---


# 👩‍💻 Project

**Project Name:** SmartEvent

**Type:** Full-Stack Event Discovery & Ticket Booking Platform

**Backend:** FastAPI

**Frontend:** React.js + Vite

**Database:** SQLite

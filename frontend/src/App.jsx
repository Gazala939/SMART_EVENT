
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import Home from "./pages/Home";
import EventDetails from "./pages/EventDetails";
import BookingConfirmation from "./pages/BookingConfirmation";
import BookingHistory from "./pages/BookingHistory";
import Notifications from "./pages/Notifications";
import Tickets from "./pages/Tickets";

import CreateEvent from "./pages/CreateEvent";
import ManageEvents from "./pages/ManageEvents";
import EditEvent from "./pages/EditEvent";
import EventBookings from "./pages/EventBookings";
import OrganizerDashboard from "./pages/OrganizerDashboard";

import AdminDashboard from "./pages/AdminDashboard";
import PlatformAnalytics from "./pages/PlatformAnalytics";
import UsersOverview from "./pages/UsersOverview";
import EventsOverview from "./pages/EventsOverview";
import BookingsOverview from "./pages/BookingsOverview";

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        {/* PUBLIC PAGES */}
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* AUTHENTICATED USER PAGES */}
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />

        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />

        <Route
          path="/events/:event_id"
          element={
            <ProtectedRoute>
              <EventDetails />
            </ProtectedRoute>
          }
        />

        <Route
          path="/booking-confirmation"
          element={
            <ProtectedRoute>
              <BookingConfirmation />
            </ProtectedRoute>
          }
        />

        <Route
          path="/booking-history"
          element={
            <ProtectedRoute>
              <BookingHistory />
            </ProtectedRoute>
          }
        />

        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <Notifications />
            </ProtectedRoute>
          }
        />

        <Route
          path="/tickets"
          element={
            <ProtectedRoute>
              <Tickets />
            </ProtectedRoute>
          }
        />

        {/* ORGANIZER PAGES */}
        <Route
          path="/create-event"
          element={
            <ProtectedRoute allowedRoles={["ORGANIZER"]}>
              <CreateEvent />
            </ProtectedRoute>
          }
        />

        <Route
          path="/manage-events"
          element={
            <ProtectedRoute allowedRoles={["ORGANIZER"]}>
              <ManageEvents />
            </ProtectedRoute>
          }
        />
        {/* ORGANIZER EVENT BOOKINGS */}
        <Route
          path="/organizer/event-bookings/:event_id"
          element={
            <ProtectedRoute allowedRoles={["ORGANIZER"]}>
              <EventBookings />
            </ProtectedRoute>
          }
        />

        <Route
          path="/organizer/events/edit/:eventId"
          element={
            <ProtectedRoute allowedRoles={["ORGANIZER"]}>
              <EditEvent />
            </ProtectedRoute>
          }
        />

        {/* Event bookings: keep this path for existing navigation */}
        <Route
          path="/event-bookings/:event_id"
          element={
            <ProtectedRoute allowedRoles={["ORGANIZER"]}>
              <EventBookings />
            </ProtectedRoute>
          }
        />

        {/* Alternative URL for event bookings */}
        <Route
          path="/organizer/events/:event_id/bookings"
          element={
            <ProtectedRoute allowedRoles={["ORGANIZER"]}>
              <EventBookings />
            </ProtectedRoute>
          }
        />

        <Route
          path="/organizer/dashboard"
          element={
            <ProtectedRoute allowedRoles={["ORGANIZER"]}>
              <OrganizerDashboard />
            </ProtectedRoute>
          }
        />

        {/* ADMIN PAGES */}
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={["ADMIN"]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/analytics"
          element={
            <ProtectedRoute allowedRoles={["ADMIN"]}>
              <PlatformAnalytics />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/users"
          element={
            <ProtectedRoute allowedRoles={["ADMIN"]}>
              <UsersOverview />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/events"
          element={
            <ProtectedRoute allowedRoles={["ADMIN"]}>
              <EventsOverview />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/bookings"
          element={
            <ProtectedRoute allowedRoles={["ADMIN"]}>
              <BookingsOverview />
            </ProtectedRoute>
          }
        />

        {/* FALLBACK */}
        <Route
          path="*"
          element={
            <div style={{ padding: "24px" }}>
              <h2>Page not found</h2>
              <button onClick={() => (window.location.href = "/home")}>
                Go to Home
              </button>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
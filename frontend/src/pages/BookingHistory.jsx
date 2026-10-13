
import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./BookingHistory.css";

function BookingHistory() {
  const [bookings, setBookings] = useState([]);
  const [events, setEvents] = useState({});
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  // Fetch the logged-in user's bookings
  const getBookings = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Please login first.");
      navigate("/login");
      setLoading(false);
      return;
    }

    try {
      const bookingResponse = await axios.get(
        "http://127.0.0.1:8000/bookings/my-bookings",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const bookingData = bookingResponse.data;
      setBookings(bookingData);

      // Fetch event details for each booking
      const eventData = {};

      await Promise.all(
        bookingData.map(async (booking) => {
          try {
            const eventResponse = await axios.get(
              `http://127.0.0.1:8000/events/${booking.event_id}`
            );

            eventData[booking.event_id] = eventResponse.data;
          } catch (error) {
            console.error(
              `Could not load event ${booking.event_id}:`,
              error
            );
          }
        })
      );

      setEvents(eventData);
    } catch (error) {
      console.error("Error loading booking history:", error);

      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/login");
      } else {
        alert(
          error.response?.data?.detail ||
            "Unable to load booking history."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getBookings();
  }, []);

  // Cancel a booking
  const cancelBooking = async (bookingId) => {
    const token = localStorage.getItem("token");

    if (!token) {
      navigate("/login");
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to cancel this booking?"
    );

    if (!confirmed) return;

    try {
      await axios.put(
        `http://127.0.0.1:8000/bookings/${bookingId}/cancel`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      alert("Booking cancelled successfully!");
      setLoading(true);
      await getBookings();
    } catch (error) {
      console.error("Error cancelling booking:", error);

      alert(
        error.response?.data?.detail ||
          "Unable to cancel booking."
      );
    }
  };

  // Loading screen
  if (loading) {
    return (
      <div className="booking-history-container">
        <h2>Loading booking history...</h2>
      </div>
    );
  }

  return (
    <div className="booking-history-container">
      <header className="booking-history-header">
        <h1>SmartEvent</h1>
        <h2>My Booking History</h2>

        <button
          type="button"
          className="booking-back-button"
          onClick={() => navigate("/home")}
        >
          ← Back to Events
        </button>
      </header>

      {bookings.length === 0 ? (
        <div className="booking-empty">
          <h3>No bookings found</h3>
          <p>You haven't booked any events yet.</p>

          <button
            type="button"
            onClick={() => navigate("/home")}
          >
            Browse Events
          </button>
        </div>
      ) : (
        <div className="booking-list">
          {bookings.map((booking) => {
            const event = events[booking.event_id];

            return (
              <article className="booking-card" key={booking.id}>
                {event?.banner_image ? (
                  <img
                    src={event.banner_image}
                    alt={event.title || "Event"}
                    className="booking-image"
                  />
                ) : (
                  <div className="booking-image booking-image-placeholder">
                    Event Image
                  </div>
                )}

                <div className="booking-content">
                  <h3>{event?.title || "Event details unavailable"}</h3>

                  <p>
                    <strong>Booking ID:</strong> {booking.id}
                  </p>

                  <p>
                    <strong>Location:</strong>{" "}
                    {event?.location || "N/A"}
                  </p>

                  <p>
                    <strong>Event Date:</strong>{" "}
                    {event?.event_date
                      ? new Date(event.event_date).toLocaleString()
                      : "N/A"}
                  </p>

                  <p>
                    <strong>Tickets:</strong>{" "}
                    {booking.ticket_quantity}
                  </p>

                  <p>
                    <strong>Total Price:</strong>{" "}
                    ₹{booking.total_price}
                  </p>

                  <p>
                    <strong>Status:</strong>{" "}
                    <span
                      className={`booking-status booking-status-${(
                        booking.booking_status || "unknown"
                      ).toLowerCase()}`}
                    >
                      {booking.booking_status || "UNKNOWN"}
                    </span>
                  </p>

                  <p>
                    <strong>Booked On:</strong>{" "}
                    {booking.created_at
                      ? new Date(booking.created_at).toLocaleString()
                      : "N/A"}
                  </p>

                  {booking.booking_status !== "CANCELLED" && (
                    <button
                      type="button"
                      className="booking-cancel-button"
                      onClick={() => cancelBooking(booking.id)}
                    >
                      Cancel Booking
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default BookingHistory;

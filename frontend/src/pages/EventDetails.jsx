
import { useEffect, useState } from "react";
import api from "../api";
import { useParams, useNavigate } from "react-router-dom";

function EventDetails() {
  const { event_id } = useParams();

  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [bookingLoading, setBookingLoading] = useState(false);

  const navigate = useNavigate();

  // GET EVENT DETAILS
  useEffect(() => {
    let cancelled = false;

    const fetchEvent = async () => {
      setLoading(true);

      try {
        const response = await api.get(`/events/${event_id}`);

        if (!cancelled) {
          setEvent(response.data);
        }
      } catch (error) {
        console.error("Error fetching event:", error);

        if (!cancelled) {
          setEvent(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchEvent();

    return () => {
      cancelled = true;
    };
  }, [event_id]);

  // BOOK TICKETS
  const handleBooking = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Please login to book tickets.");
      navigate("/login");
      return;
    }

    try {
      setBookingLoading(true);

      const response = await api.post("/bookings", {
        event_id: Number(event_id),
        ticket_quantity: quantity,
      });

      alert("Booking successful!");

      navigate("/booking-confirmation", {
        state: {
          booking: response.data,
          event: event,
          ticket: response.data.ticket,
        },
      });
    } catch (error) {
      alert(
        error.response?.data?.detail || "Booking failed"
      );
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return <h2>Loading event...</h2>;
  }

  if (!event) {
    return <h2>Event not found</h2>;
  }

  const status = event.event_status || "UPCOMING";
  const statusClass = status.toLowerCase();

  const canBook =
    status !== "CANCELLED" &&
    status !== "ONGOING" &&
    status !== "COMPLETED";

  return (
    <div className="event-details">
      <button
        className="back-button"
        onClick={() => navigate("/home")}
      >
        ← Back to Events
      </button>

      {event.banner_image && (
        <img
          src={event.banner_image}
          alt={event.title}
          className="details-image"
        />
      )}

      <h1>{event.title}</h1>

      {/* EVENT STATUS */}
      <span className={`event-status ${statusClass}`}>
        {status}
      </span>

      {/* CANCELLATION NOTICE */}
      {status === "CANCELLED" && (
        <div className="cancellation-notice">
          <h3>Event Cancelled</h3>
          <p>
            This event has been cancelled. Ticket booking is
            unavailable for this event.
          </p>
        </div>
      )}

      {status === "COMPLETED" && (
        <p className="event-info-notice">
          This event has already been completed.
        </p>
      )}

      {status === "ONGOING" && (
        <p className="event-info-notice">
          This event is currently ongoing. Ticket booking is
          unavailable.
        </p>
      )}

      <p>{event.description}</p>

      <p>
        <strong>Category:</strong> {event.category}
      </p>

      <p>
        <strong>Location:</strong> {event.location}
      </p>

      <p>
        <strong>Date:</strong>{" "}
        {new Date(event.event_date).toLocaleString()}
      </p>

      <p className="details-price">
        ₹{event.ticket_price}
      </p>

      {/* BOOKING SECTION */}
      {canBook ? (
        <div className="booking-box">
          <h3>Book Tickets</h3>

          <label htmlFor="ticket-quantity">
            Number of Tickets:
          </label>

          <select
            id="ticket-quantity"
            value={quantity}
            onChange={(e) =>
              setQuantity(Number(e.target.value))
            }
          >
            {Array.from({ length: 10 }, (_, index) => (
              <option key={index + 1} value={index + 1}>
                {index + 1}{" "}
                {index === 0 ? "Ticket" : "Tickets"}
              </option>
            ))}
          </select>

          <p>
            <strong>Total Price:</strong>{" "}
            ₹{event.ticket_price * quantity}
          </p>

          <button
            className="book-button"
            onClick={handleBooking}
            disabled={bookingLoading}
          >
            {bookingLoading ? "Booking..." : "Book Tickets"}
          </button>
        </div>
      ) : (
        <p className="event-info-notice">
          Booking is currently unavailable.
        </p>
      )}
    </div>
  );
}

export default EventDetails;
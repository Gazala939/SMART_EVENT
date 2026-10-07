import { useLocation, useNavigate } from "react-router-dom";

function BookingConfirmation() {
  const location = useLocation();
  const navigate = useNavigate();

  const booking = location.state?.booking;
  const event = location.state?.event;
  const ticket = location.state?.ticket;

  if (!booking || !event) {
    return (
      <div className="confirmation-container">
        <h2>Booking details not found</h2>

        <button onClick={() => navigate("/home")}>
          Back to Events
        </button>
      </div>
    );
  }

  return (
    <div className="confirmation-container">

      <h1>🎉 Booking Confirmed!</h1>

      <p>Your tickets have been successfully booked.</p>

      <div className="confirmation-card">

        <h2>{event.title}</h2>

        <p>
          <strong>Booking ID:</strong>{" "}
          {booking.id}
        </p>

        <p>
          <strong>Location:</strong>{" "}
          {event.location}
        </p>

        <p>
          <strong>Date:</strong>{" "}
          {new Date(event.event_date).toLocaleString()}
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
          {booking.booking_status}
        </p>

        {ticket && (
          <div className="ticket-section">

            <h3>Your QR Ticket</h3>

            <p>
              <strong>Ticket Code:</strong>{" "}
              {ticket.ticket_code}
            </p>

            <img
              src={`http://127.0.0.1:8000${ticket.qr_code_url}`}
              alt="Ticket QR Code"
              className="qr-image"
            />

            <br />

            <a
              href={`http://127.0.0.1:8000${ticket.qr_code_url}`}
              download
              className="download-ticket-button"
            >
              ⬇ Download Ticket
            </a>

          </div>
        )}

      </div>

      <div className="confirmation-buttons">

        <button onClick={() => navigate("/home")}>
          Browse More Events
        </button>

        <button
          onClick={() => navigate("/booking-history")}
        >
          View My Bookings
        </button>

      </div>

    </div>
  );
}

export default BookingConfirmation;
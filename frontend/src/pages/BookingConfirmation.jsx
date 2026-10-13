import { useLocation, useNavigate } from "react-router-dom";

function BookingConfirmation() {
  const location = useLocation();
  const navigate = useNavigate();

  const booking = location.state?.booking;
  const event = location.state?.event;
  const ticket = location.state?.ticket;

  const formatDate = (date) => {
    if (!date) return "Date not available";

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "Date not available";
    }

    return parsedDate.toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  };

  const getQrUrl = (url) => {
    if (!url) return "";

    // Support both full URLs and backend-relative URLs.
    if (url.startsWith("http://") || url.startsWith("https://")) {
      return url;
    }

    return `http://127.0.0.1:8000${url.startsWith("/") ? "" : "/"}${url}`;
  };

  if (!booking || !event) {
    return (
      <main className="confirmation-page">
        <section className="confirmation-empty">
          <div className="confirmation-empty-icon">🎟️</div>

          <h1>Booking Details Not Found</h1>

          <p>
            We couldn't find your booking details on this page.
            You can check your previous bookings or browse upcoming events.
          </p>

          <div className="confirmation-buttons">
            <button
              type="button"
              className="confirmation-primary-button"
              onClick={() => navigate("/booking-history")}
            >
              View My Bookings
            </button>

            <button
              type="button"
              className="confirmation-secondary-button"
              onClick={() => navigate("/home")}
            >
              Browse Events
            </button>
          </div>
        </section>
      </main>
    );
  }

  const qrUrl = getQrUrl(ticket?.qr_code_url);

  return (
    <main className="confirmation-page">
      <section className="confirmation-success">
        <div className="confirmation-success-icon" aria-hidden="true">
          ✓
        </div>

        <p className="confirmation-eyebrow">SMART EVENT</p>

        <h1>Booking Confirmed!</h1>

        <p className="confirmation-subtitle">
          You're all set! Your booking details are ready below.
        </p>

        <span className="confirmation-status-badge">
          {booking.booking_status || "CONFIRMED"}
        </span>
      </section>

      <section className="confirmation-card">
        <div className="confirmation-card-heading">
          <div>
            <p className="confirmation-section-label">YOUR EVENT</p>
            <h2>{event.title || "Event"}</h2>
          </div>

          <div className="confirmation-ticket-icon" aria-hidden="true">
            🎫
          </div>
        </div>

        <div className="confirmation-details-grid">
          <div className="confirmation-detail">
            <span className="confirmation-detail-icon" aria-hidden="true">
              📍
            </span>

            <div>
              <p>Location</p>
              <strong>{event.location || "Not available"}</strong>
            </div>
          </div>

          <div className="confirmation-detail">
            <span className="confirmation-detail-icon" aria-hidden="true">
              📅
            </span>

            <div>
              <p>Date and Time</p>
              <strong>{formatDate(event.event_date)}</strong>
            </div>
          </div>

          <div className="confirmation-detail">
            <span className="confirmation-detail-icon" aria-hidden="true">
              🎟️
            </span>

            <div>
              <p>Number of Tickets</p>
              <strong>{booking.ticket_quantity ?? 0}</strong>
            </div>
          </div>

          <div className="confirmation-detail">
            <span className="confirmation-detail-icon" aria-hidden="true">
              #️⃣
            </span>

            <div>
              <p>Booking ID</p>
              <strong>{booking.id ?? "Not available"}</strong>
            </div>
          </div>
        </div>

        <div className="confirmation-price-row">
          <div>
            <p>Total Amount</p>
            <span>Including your booked tickets</span>
          </div>

          <strong>
            ₹{Number(booking.total_price ?? 0).toLocaleString("en-IN")}
          </strong>
        </div>

        {ticket && (
          <div className="confirmation-qr-section">
            <div className="confirmation-qr-heading">
              <h3>Your Digital Ticket</h3>
              <p>Keep your QR code ready for event entry.</p>
            </div>

            {ticket.ticket_code && (
              <p className="confirmation-ticket-code">
                <span>Ticket Code</span>
                <strong>{ticket.ticket_code}</strong>
              </p>
            )}

            {qrUrl ? (
              <>
                <div className="confirmation-qr-frame">
                  <img
                    src={qrUrl}
                    alt="QR code for your event ticket"
                    className="confirmation-qr-image"
                  />
                </div>

                <a
                  href={qrUrl}
                  download
                  target="_blank"
                  rel="noreferrer"
                  className="confirmation-download-button"
                >
                  ↓ Download QR Ticket
                </a>
              </>
            ) : (
              <p className="confirmation-qr-unavailable">
                Your QR code is not available here. Please check your tickets
                page.
              </p>
            )}
          </div>
        )}
      </section>

      <section className="confirmation-next-steps">
        <h3>What's next?</h3>
        <p>
          Keep your booking details and QR ticket safe. You can return to your
          bookings whenever you need them.
        </p>
      </section>

      <div className="confirmation-buttons">
        <button
          type="button"
          className="confirmation-primary-button"
          onClick={() => navigate("/booking-history")}
        >
          View My Bookings
        </button>

        <button
          type="button"
          className="confirmation-secondary-button"
          onClick={() => navigate("/home")}
        >
          Browse More Events
        </button>
      </div>
    </main>
  );
}

export default BookingConfirmation;
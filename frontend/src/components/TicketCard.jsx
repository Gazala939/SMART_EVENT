function TicketCard({ ticket }) {
  return (
    <div className="ticket-card">

      <h2>🎟️ Ticket</h2>

      <div className="ticket-event-details">

        <h3>{ticket.event.title}</h3>

        <p>
          <strong>Location:</strong>{" "}
          {ticket.event.location}
        </p>

        <p>
          <strong>Event Date:</strong>{" "}
          {new Date(
            ticket.event.event_date
          ).toLocaleString()}
        </p>

      </div>

      <p>
        <strong>Ticket Code:</strong>{" "}
        {ticket.ticket_code}
      </p>

      <p>
        <strong>Booking ID:</strong>{" "}
        {ticket.booking_id}
      </p>

      {ticket.qr_code_url && (
        <>
          <img
            src={`http://127.0.0.1:8000${ticket.qr_code_url}`}
            alt="Ticket QR Code"
            className="ticket-qr"
          />

          <br />

          <a
            href={`http://127.0.0.1:8000${ticket.qr_code_url}`}
            download
            className="ticket-download-button"
          >
            ⬇ Download QR
          </a>
        </>
      )}

      <p className="ticket-date">
        Created:{" "}
        {new Date(
          ticket.created_at
        ).toLocaleString()}
      </p>

    </div>
  );
}

export default TicketCard;
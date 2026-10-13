
import { useNavigate } from "react-router-dom";

function EventCard({ event }) {
  const navigate = useNavigate();

  const status = event.event_status || "UPCOMING";
  const statusClass = status.toLowerCase();

  const formattedDate = event.event_date
    ? new Date(event.event_date).toLocaleString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
      })
    : "Date to be announced";

  const formattedPrice = Number(event.ticket_price || 0).toLocaleString(
    "en-IN"
  );

  return (
    <article className="event-card">
      <div className="event-card-image-wrapper">
        {event.banner_image ? (
          <img
            src={event.banner_image}
            alt={event.title || "Event"}
            className="event-image"
            loading="lazy"
          />
        ) : (
          <div className="event-image-placeholder">
            <span>🎟️</span>
            <p>SmartEvent</p>
          </div>
        )}

        <span className={`event-status ${statusClass}`}>
          {status}
        </span>

        {event.category && (
          <span className="event-category-badge">
            {event.category}
          </span>
        )}
      </div>

      <div className="event-card-content">
        <h2 className="event-card-title">
          {event.title || "Untitled Event"}
        </h2>

        {status === "CANCELLED" && (
          <p className="cancellation-notice">
            This event has been cancelled.
          </p>
        )}

        <p className="event-card-description">
          {event.description || "Discover more about this event."}
        </p>

        <div className="event-card-info">
          <p>
            <span aria-hidden="true">📍</span>
            <span>{event.location || "Location to be announced"}</span>
          </p>

          <p>
            <span aria-hidden="true">📅</span>
            <span>{formattedDate}</span>
          </p>
        </div>

        <div className="event-card-footer">
          <div className="event-price">
            <span>Ticket price</span>
            <strong>₹{formattedPrice}</strong>
          </div>

          <button
            type="button"
            className="event-details-button"
            onClick={() => navigate(`/events/${event.id}`)}
            aria-label={`View details for ${event.title}`}
          >
            View Details <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </article>
  );
}

export default EventCard;

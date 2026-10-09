
import { useNavigate } from "react-router-dom";

function EventCard({ event }) {
  const navigate = useNavigate();

  // Get the event status from the backend
  const status = event.event_status || "UPCOMING";

  // Set a CSS class based on the event status
  const statusClass = status.toLowerCase();

  return (
    <div className="event-card">
      {event.banner_image && (
        <img
          src={event.banner_image}
          alt={event.title}
          className="event-image"
        />
      )}

      <div className="event-card-content">
        <h2>{event.title}</h2>

        {/* Event Status Badge */}
        <span className={`event-status ${statusClass}`}>
          {status}
        </span>

        {/* Cancellation Notice */}
        {status === "CANCELLED" && (
          <p className="cancellation-notice">
            This event has been cancelled.
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

        <p>
          <strong>Price:</strong> ₹{event.ticket_price}
        </p>

        <button
          onClick={() => navigate(`/events/${event.id}`)}
        >
          View Details
        </button>
      </div>
    </div>
  );
}

export default EventCard;


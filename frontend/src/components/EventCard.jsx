import { useNavigate } from "react-router-dom";

function EventCard({ event }) {
  const navigate = useNavigate();

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
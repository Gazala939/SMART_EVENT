
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

function EventCard({ event }) {
  const navigate = useNavigate();

  const [isWishlisted, setIsWishlisted] = useState(false);
  const [wishlistLoading, setWishlistLoading] = useState(false);

  const status = event.event_status || "UPCOMING";
  const statusClass = status.toLowerCase();

  // Check whether this event is already in the user's wishlist
  useEffect(() => {
    let cancelled = false;

    const checkWishlist = async () => {
      const token = localStorage.getItem("token");

      // Wishlist is available only to logged-in users
      if (!token || !event?.id) {
        setIsWishlisted(false);
        return;
      }

      try {
        const response = await api.get("/wishlist");

        const wishlistItems = Array.isArray(response.data)
          ? response.data
          : [];

        const exists = wishlistItems.some(
          (item) => Number(item.event_id) === Number(event.id)
        );

        if (!cancelled) {
          setIsWishlisted(exists);
        }
      } catch (error) {
        console.error("Unable to check wishlist:", error);
      }
    };

    checkWishlist();

    return () => {
      cancelled = true;
    };
  }, [event?.id]);

  // Add or remove this event from the wishlist
  const handleWishlist = async () => {
    if (!localStorage.getItem("token")) {
      navigate("/login");
      return;
    }

    if (wishlistLoading || !event?.id) return;

    setWishlistLoading(true);

    try {
      if (isWishlisted) {
        await api.delete(`/wishlist/${event.id}`);
        setIsWishlisted(false);
      } else {
        await api.post("/wishlist", {
          event_id: Number(event.id),
        });
        setIsWishlisted(true);
      }
    } catch (error) {
      console.error("Unable to update wishlist:", error);

      const message =
        error.response?.data?.detail ||
        "Could not update your wishlist. Please try again.";

      alert(
        typeof message === "string"
          ? message
          : "Could not update your wishlist. Please try again."
      );
    } finally {
      setWishlistLoading(false);
    }
  };

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

        <button
          type="button"
          className={`wishlist-button ${
            isWishlisted ? "wishlisted" : ""
          }`}
          onClick={handleWishlist}
          disabled={wishlistLoading}
          aria-label={
            isWishlisted
              ? "Remove event from wishlist"
              : "Add event to wishlist"
          }
          aria-pressed={isWishlisted}
          title={
            isWishlisted
              ? "Remove from wishlist"
              : "Add to wishlist"
          }
        >
          {wishlistLoading ? "…" : isWishlisted ? "♥" : "♡"}
        </button>
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
            aria-label={`View details for ${event.title || "event"}`}
          >
            View Details <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </article>
  );
}

export default EventCard;

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import EventCard from "../components/EventCard";
import "./Wishlist.css";

function Wishlist() {
  const navigate = useNavigate();

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchWishlist = useCallback(async () => {
    if (!localStorage.getItem("token")) {
      setError("Please log in to view your wishlist.");
      setEvents([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await api.get("/wishlist/events");

      setEvents(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error("Error fetching wishlist:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to load your wishlist. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWishlist();
  }, [fetchWishlist]);

  const handleRemove = async (eventId) => {
    try {
      await api.delete(`/wishlist/${eventId}`);

      setEvents((currentEvents) =>
        currentEvents.filter(
          (event) => Number(event.id) !== Number(eventId)
        )
      );
    } catch (err) {
      console.error("Error removing wishlist event:", err);

      alert(
        err.response?.data?.detail ||
          "Unable to remove this event from your wishlist."
      );
    }
  };

  const handleBookNow = (eventId) => {
    navigate(`/events/${eventId}`);
  };

  if (loading) {
    return (
      <main className="wishlist-page">
        <h1>My Wishlist</h1>
        <p>Loading your saved events...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="wishlist-page">
        <h1>My Wishlist</h1>
        <p className="wishlist-error">{error}</p>

        {!localStorage.getItem("token") ? (
          <button onClick={() => navigate("/login")}>
            Log In
          </button>
        ) : (
          <button onClick={fetchWishlist}>Try Again</button>
        )}
      </main>
    );
  }

  return (
    <main className="wishlist-page">
      <div className="wishlist-heading">
        <div>
          <h1>My Wishlist {"\u2665"}</h1>
          <p>Keep track of events you want to attend.</p>
        </div>

        <button
          className="wishlist-browse-button"
          onClick={() => navigate("/")}
        >
          Browse Events
        </button>
      </div>

      {events.length === 0 ? (
        <section className="wishlist-empty">
          <div className="wishlist-empty-icon">{"\u2661"}</div>
          <h2>Your wishlist is empty</h2>
          <p>
            Save events using the heart button to find them here later.
          </p>
          <button onClick={() => navigate("/")}>
            Explore Events
          </button>
        </section>
      ) : (
        <>
          <p className="wishlist-count">
            {events.length} saved{" "}
            {events.length === 1 ? "event" : "events"}
          </p>

          <div className="wishlist-grid">
            {events.map((event) => (
              <div className="wishlist-item" key={event.id}>
                <EventCard event={event} />

                <div className="wishlist-item-actions">
                  <button
                    className="wishlist-book-button"
                    onClick={() => handleBookNow(event.id)}
                  >
                    Book Now
                  </button>

                  <button
                    className="wishlist-remove-button"
                    onClick={() => handleRemove(event.id)}
                  >
                    Remove from Wishlist
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </main>
  );
}

export default Wishlist;

import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

function ManageEvents() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  // GET ORGANIZER EVENTS
  const getMyEvents = useCallback(async () => {
    try {
      const response = await api.get("/organizer/events");
      setEvents(response.data || []);
    } catch (error) {
      console.error("Error fetching events:", error);

      alert(
        error.response?.data?.detail ||
          "Failed to fetch organizer events"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  // CANCEL EVENT
  const cancelEvent = async (eventId) => {
    const confirmCancel = window.confirm(
      "Are you sure you want to cancel this event?"
    );

    if (!confirmCancel) return;

    try {
      await api.put(`/organizer/events/${eventId}/cancel`, {});

      alert("Event cancelled successfully");
      await getMyEvents();
    } catch (error) {
      console.error("Error cancelling event:", error);

      alert(
        error.response?.data?.detail ||
          "Failed to cancel event"
      );
    }
  };

  // MARK EVENT AS COMPLETED
  const completeEvent = async (eventId) => {
    const confirmComplete = window.confirm(
      "Are you sure you want to mark this event as completed?"
    );

    if (!confirmComplete) return;

    try {
      await api.put(`/organizer/events/${eventId}/complete`, {});

      alert("Event marked as completed successfully");
      await getMyEvents();
    } catch (error) {
      console.error("Error completing event:", error);

      alert(
        error.response?.data?.detail ||
          "Failed to mark event as completed"
      );
    }
  };

  // LOAD EVENTS
  useEffect(() => {
    getMyEvents();
  }, [getMyEvents]);

  // LOADING
  if (loading) {
    return (
      <div className="manage-events-page">
        <h2>Manage Events</h2>
        <p>Loading events...</p>
      </div>
    );
  }

  return (
    <div className="manage-events-page">
      <h2>Manage My Events</h2>

      <button onClick={() => navigate("/create-event")}>
        ➕ Create Event
      </button>

      {events.length === 0 ? (
        <div className="no-events">
          <p>You have not created any events yet.</p>
        </div>
      ) : (
        <div className="events-container">
          {events.map((event) => {
            const eventStatus = String(
              event.event_status || "UPCOMING"
            ).toUpperCase();

            // Allow event management for active and upcoming events.
            const canManage = [
              "ACTIVE",
              "UPCOMING",
              "ONGOING",
            ].includes(eventStatus);

            return (
              <div className="event-card" key={event.id}>
                {/* EVENT IMAGE */}
                {event.banner_image && (
                  <img
                    src={event.banner_image}
                    alt={event.title}
                    className="event-image"
                  />
                )}

                <div className="event-details">
                  <h3>{event.title}</h3>

                  <p>
                    <strong>Description:</strong>{" "}
                    {event.description}
                  </p>

                  <p>
                    <strong>Category:</strong>{" "}
                    {event.category}
                  </p>

                  <p>
                    <strong>Location:</strong>{" "}
                    {event.location}
                  </p>

                  <p>
                    <strong>Date:</strong>{" "}
                    {new Date(
                      event.event_date
                    ).toLocaleString()}
                  </p>

                  <p>
                    <strong>Ticket Price:</strong>{" "}
                    ₹{event.ticket_price}
                  </p>

                  <p>
                    <strong>Status:</strong>{" "}
                    <span
                      className={`event-status ${eventStatus.toLowerCase()}`}
                    >
                      {eventStatus}
                    </span>
                  </p>

                  {/* EVENT ACTIONS */}
                  <div className="event-actions">
                    {canManage && (
                      <>
                        <button
                          className="edit-btn"
                          onClick={() =>
                            navigate(
                              `/organizer/events/edit/${event.id}`
                            )
                          }
                        >
                          Edit
                        </button>

                        <button
                          className="cancel-btn"
                          onClick={() => cancelEvent(event.id)}
                        >
                          Cancel
                        </button>

                        <button
                          className="complete-btn"
                          onClick={() => completeEvent(event.id)}
                        >
                          Complete
                        </button>
                      </>
                    )}

                    {/* SHOW BOOKINGS FOR ALL EVENT STATUSES */}
                    <button
                      className="bookings-btn"
                      onClick={() =>
                        navigate(`/event-bookings/${event.id}`)
                      }
                    >
                      View Bookings
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ManageEvents;
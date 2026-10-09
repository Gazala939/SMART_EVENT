
import { useEffect, useState } from "react";
import axios from "axios";

function EventsOverview() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("token");

      const response = await axios.get(
        "http://127.0.0.1:8000/events",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setEvents(
        Array.isArray(response.data)
          ? response.data
          : response.data.events || []
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load events."
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <h2>Loading Events...</h2>;
  }

  return (
    <div className="admin-dashboard">
      <h1>Events Overview</h1>
      <p>Total events: {events.length}</p>

      {error && (
        <div>
          <p>{error}</p>
          <button onClick={fetchEvents}>Retry</button>
        </div>
      )}

      {!error && events.length === 0 && (
        <p>No events found.</p>
      )}

      {!error && events.length > 0 && (
        <div className="admin-table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Category</th>
                <th>Location</th>
                <th>Date</th>
                <th>Price</th>
                <th>Organizer ID</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td>{event.id}</td>
                  <td>{event.title}</td>
                  <td>{event.category}</td>
                  <td>{event.location}</td>
                  <td>
                    {event.event_date
                      ? new Date(event.event_date).toLocaleString()
                      : "—"}
                  </td>
                  <td>₹{event.ticket_price}</td>
                  <td>{event.organizer_id ?? "—"}</td>
                  <td>
                    <span
                      className={`event-status ${
                        (event.event_status || "UPCOMING").toLowerCase()
                      }`}
                    >
                      {event.event_status || "UPCOMING"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default EventsOverview;


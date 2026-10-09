
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api";
import "./EventBookings.css";

function EventBookings() {
  const { event_id } = useParams();
  const navigate = useNavigate();

  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isActive = true;

    async function fetchBookings() {
      setLoading(true);
      setError("");

      try {
        const response = await api.get(
          `/organizer/events/${event_id}/bookings`
        );

        if (isActive) {
          setBookings(response.data || []);
        }
      } catch (err) {
        if (isActive) {
          setError(
            err.response?.data?.detail ||
              "Unable to load event bookings."
          );
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    fetchBookings();

    return () => {
      isActive = false;
    };
  }, [event_id]);

  if (loading) {
    return <h2>Loading bookings...</h2>;
  }

  if (error) {
    return (
      <div className="event-bookings-page">
        <button onClick={() => navigate("/manage-events")}>
          ← Back to Manage Events
        </button>
        <h1>Event Bookings</h1>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="event-bookings-page">
      <button onClick={() => navigate("/manage-events")}>
        ← Back to Manage Events
      </button>

      <h1>Event Bookings</h1>
      <p>Event ID: {event_id}</p>
      <h3>Total bookings: {bookings.length}</h3>

      {bookings.length === 0 ? (
        <p>No bookings found for this event.</p>
      ) : (
        <div className="bookings-table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Booking ID</th>
                <th>User ID</th>
                <th>Tickets</th>
                <th>Total Price</th>
                <th>Status</th>
                <th>Booking Date</th>
              </tr>
            </thead>

            <tbody>
              {bookings.map((booking) => (
                <tr key={booking.id}>
                  <td>{booking.id}</td>
                  <td>{booking.user_id}</td>
                  <td>{booking.ticket_quantity}</td>
                  <td>₹{booking.total_price}</td>
                  <td>{booking.booking_status}</td>
                  <td>
                    {booking.created_at
                      ? new Date(
                          booking.created_at
                        ).toLocaleString()
                      : "—"}
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

export default EventBookings;
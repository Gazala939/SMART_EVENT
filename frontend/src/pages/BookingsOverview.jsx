
import { useEffect, useState } from "react";
import axios from "axios";

function BookingsOverview() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("token");

      const response = await axios.get(
        "http://127.0.0.1:8000/admin/bookings",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setBookings(
        Array.isArray(response.data)
          ? response.data
          : response.data.bookings || []
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load bookings. Check the admin API."
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <h2>Loading Bookings...</h2>;
  }

  return (
    <div className="admin-dashboard">
      <h1>Booking Overview</h1>
      <p>Total bookings: {bookings.length}</p>

      {error && (
        <div>
          <p>{error}</p>
          <button onClick={fetchBookings}>Retry</button>
        </div>
      )}

      {!error && bookings.length === 0 && (
        <p>No bookings found.</p>
      )}

      {!error && bookings.length > 0 && (
        <div className="admin-table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Booking ID</th>
                <th>User ID</th>
                <th>Event ID</th>
                <th>Ticket Quantity</th>
                <th>Total Price</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {bookings.map((booking) => (
                <tr key={booking.id}>
                  <td>{booking.id}</td>
                  <td>{booking.user_id}</td>
                  <td>{booking.event_id}</td>
                  <td>{booking.ticket_quantity}</td>
                  <td>
                    ₹
                    {Number(booking.total_price || 0).toLocaleString(
                      "en-IN"
                    )}
                  </td>
                  <td>{booking.booking_status || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default BookingsOverview;


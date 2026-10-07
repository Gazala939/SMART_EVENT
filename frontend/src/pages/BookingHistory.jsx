import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function BookingHistory() {
  const [bookings, setBookings] = useState([]);
  const [events, setEvents] = useState({});
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  const getBookings = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Please login first.");
      navigate("/login");
      return;
    }

    try {
      const bookingResponse = await axios.get(
        "http://127.0.0.1:8000/bookings/my-bookings",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setBookings(bookingResponse.data);

      const eventData = {};

      for (const booking of bookingResponse.data) {
        try {
          const eventResponse = await axios.get(
            `http://127.0.0.1:8000/events/${booking.event_id}`
          );

          eventData[booking.event_id] = eventResponse.data;
        } catch (error) {
          console.log(error);
        }
      }

      setEvents(eventData);

    } catch (error) {
      console.log(error);

      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/login");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getBookings();
  }, []);

  const cancelBooking = async (bookingId) => {
    const token = localStorage.getItem("token");

    try {
      await axios.put(
        `http://127.0.0.1:8000/bookings/${bookingId}/cancel`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      alert("Booking cancelled successfully!");

      getBookings();

    } catch (error) {
      alert(
        error.response?.data?.detail ||
          "Unable to cancel booking"
      );
    }
  };

  if (loading) {
    return <h2>Loading bookings...</h2>;
  }

  return (
    <div className="booking-history-container">

      <h1>SmartEvent</h1>

      <h2>My Booking History</h2>

      <button
        className="back-button"
        onClick={() => navigate("/home")}
      >
        ← Back to Events
      </button>

      {bookings.length === 0 ? (
        <div className="no-bookings">
          <h3>No bookings found</h3>

          <button onClick={() => navigate("/home")}>
            Browse Events
          </button>
        </div>
      ) : (
        <div className="booking-list">

          {bookings.map((booking) => {

            const event = events[booking.event_id];

            return (
              <div
                className="booking-card"
                key={booking.id}
              >

                {event?.banner_image && (
                  <img
                    src={event.banner_image}
                    alt={event.title}
                    className="booking-image"
                  />
                )}

                <div className="booking-content">

                  <h3>
                    {event?.title || "Event"}
                  </h3>

                  <p>
                    <strong>Booking ID:</strong>{" "}
                    {booking.id}
                  </p>

                  <p>
                    <strong>Location:</strong>{" "}
                    {event?.location || "N/A"}
                  </p>

                  <p>
                    <strong>Event Date:</strong>{" "}
                    {event
                      ? new Date(
                          event.event_date
                        ).toLocaleString()
                      : "N/A"}
                  </p>

                  <p>
                    <strong>Tickets:</strong>{" "}
                    {booking.ticket_quantity}
                  </p>

                  <p>
                    <strong>Total Price:</strong>{" "}
                    ₹{booking.total_price}
                  </p>

                  <p>
                    <strong>Status:</strong>{" "}
                    {booking.booking_status}
                  </p>

                  <p>
                    <strong>Booked On:</strong>{" "}
                    {new Date(
                      booking.created_at
                    ).toLocaleString()}
                  </p>

                  {booking.booking_status !== "CANCELLED" && (
                    <button
                      className="cancel-button"
                      onClick={() =>
                        cancelBooking(booking.id)
                      }
                    >
                      Cancel Booking
                    </button>
                  )}

                </div>

              </div>
            );
          })}

        </div>
      )}

    </div>
  );
}

export default BookingHistory;
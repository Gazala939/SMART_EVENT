import { useEffect, useState } from "react";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";

function EventDetails() {
  const { event_id } = useParams();

  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [bookingLoading, setBookingLoading] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    axios
      .get(`http://127.0.0.1:8000/events/${event_id}`)
      .then((response) => {
        setEvent(response.data);
        setLoading(false);
      })
      .catch((error) => {
        console.log(error);
        setLoading(false);
      });
  }, [event_id]);

  const handleBooking = async () => {
    const token = localStorage.getItem("token");

    console.log("Token:", token);

    if (!token) {
      alert("Please login to book tickets.");
      navigate("/login");
      return;
    }

    try {
      setBookingLoading(true);

      const response = await axios.post(
        "http://127.0.0.1:8000/bookings",
        {
          event_id: Number(event_id),
          ticket_quantity: quantity,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      alert("Booking successful!");

      navigate("/booking-confirmation", {
        state: {
          booking: response.data,
          event: event,
          ticket:response.data.ticket,
        },
      });
    } catch (error) {
      alert(
        error.response?.data?.detail ||
          "Booking failed"
      );
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return <h2>Loading event...</h2>;
  }

  if (!event) {
    return <h2>Event not found</h2>;
  }

  return (
    <div className="event-details">

      <button
        className="back-button"
        onClick={() => navigate("/home")}
      >
        ← Back to Events
      </button>

      {event.banner_image && (
        <img
          src={event.banner_image}
          alt={event.title}
          className="details-image"
        />
      )}

      <h1>{event.title}</h1>

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

      <p className="details-price">
        ₹{event.ticket_price}
      </p>

      <div className="booking-box">

        <h3>Book Tickets</h3>

        <label>
          Number of Tickets:
        </label>

        <select
          value={quantity}
          onChange={(e) =>
            setQuantity(Number(e.target.value))
          }
        >
          <option value={1}>1 Ticket</option>
          <option value={2}>2 Tickets</option>
          <option value={3}>3 Tickets</option>
          <option value={4}>4 Tickets</option>
          <option value={5}>5 Tickets</option>
          <option value={6}>6 Tickets</option>
          <option value={7}>7 Tickets</option>
          <option value={8}>8 Tickets</option>
          <option value={9}>9 Tickets</option>
          <option value={10}>10 Tickets</option>
        </select>

        <p>
          <strong>Total Price:</strong>{" "}
          ₹{event.ticket_price * quantity}
        </p>

        <button
          className="book-button"
          onClick={handleBooking}
          disabled={bookingLoading}
        >
          {bookingLoading
            ? "Booking..."
            : "Book Tickets"}
        </button>

      </div>

    </div>
  );
}

export default EventDetails;
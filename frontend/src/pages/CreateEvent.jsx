import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function CreateEvent() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    category: "Tech",
    location: "",
    event_date: "",
    ticket_price: "",
    total_tickets: "",
    banner_image: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Handle input changes
  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  // Submit event
  const handleSubmit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setError("");

    const token = localStorage.getItem("token");

    try {
      await axios.post(
        "http://127.0.0.1:8000/events",
        {
          title: formData.title,
          description: formData.description,
          category: formData.category,
          location: formData.location,
          event_date: formData.event_date,
          ticket_price: Number(formData.ticket_price),
          total_tickets: Number(formData.total_tickets),
          banner_image: formData.banner_image || null,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      alert("Event created successfully!");

      navigate("/manage-events");

    } catch (error) {
      console.log(error);

      setError(
        error.response?.data?.detail ||
        "Failed to create event"
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="organizer-page">

      <h1>Create Event</h1>

      {error && (
        <p className="error-message">
          {error}
        </p>
      )}

      <form
        onSubmit={handleSubmit}
        className="event-form"
      >

        {/* Event Title */}
        <label>Event Title</label>

        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          placeholder="Enter event title"
          required
        />

        {/* Description */}
        <label>Description</label>

        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Enter event description"
          rows="4"
          required
        />

        {/* Category */}
        <label>Category</label>

        <select
          name="category"
          value={formData.category}
          onChange={handleChange}
        >
          <option value="Music">Music</option>
          <option value="Tech">Tech</option>
          <option value="Sports">Sports</option>
          <option value="Business">Business</option>
        </select>

        {/* Location */}
        <label>Location</label>

        <input
          type="text"
          name="location"
          value={formData.location}
          onChange={handleChange}
          placeholder="Enter event location"
          required
        />

        {/* Event Date */}
        <label>Event Date and Time</label>

        <input
          type="datetime-local"
          name="event_date"
          value={formData.event_date}
          onChange={handleChange}
          required
        />

        {/* Ticket Price */}
        <label>Ticket Price</label>

        <input
          type="number"
          name="ticket_price"
          value={formData.ticket_price}
          onChange={handleChange}
          placeholder="Enter ticket price"
          min="0"
          required
        />

        {/* Total Tickets */}
        <label>Total Tickets</label>

        <input
          type="number"
          name="total_tickets"
          value={formData.total_tickets}
          onChange={handleChange}
          placeholder="Enter total tickets"
          min="1"
          required
        />

        {/* Banner Image */}
        <label>Banner Image URL</label>

        <input
          type="text"
          name="banner_image"
          value={formData.banner_image}
          onChange={handleChange}
          placeholder="Paste live image URL"
        />

        {/* Submit */}
        <button
          type="submit"
          className="primary-btn"
          disabled={loading}
        >
          {loading ? "Creating..." : "Create Event"}
        </button>

      </form>

    </div>
  );
}

export default CreateEvent;
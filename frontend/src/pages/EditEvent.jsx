
import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate, useParams } from "react-router-dom";

function EditEvent() {

  // IMPORTANT:
  // App.jsx uses :eventId
  const { eventId } = useParams();

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

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // ============================================================
  // GET EVENT DETAILS
  // ============================================================

  useEffect(() => {
    getEvent();
  }, [eventId]);

  const getEvent = async () => {

    const token = localStorage.getItem("token");

    if (!eventId) {
      setError("Event ID is missing");
      setLoading(false);
      return;
    }

    try {

      const response = await axios.get(
        `http://127.0.0.1:8000/events/${eventId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const event = response.data;

      setFormData({
        title: event.title || "",
        description: event.description || "",
        category: event.category || "Tech",
        location: event.location || "",
        event_date: event.event_date
          ? event.event_date.slice(0, 16)
          : "",
        ticket_price: event.ticket_price || "",
        total_tickets: event.total_tickets || "",
        banner_image: event.banner_image || "",
      });

    } catch (error) {

      console.error("Error loading event:", error);

      setError(
        error.response?.data?.detail ||
        "Failed to load event"
      );

    } finally {

      setLoading(false);
    }
  };

  // ============================================================
  // HANDLE INPUT CHANGE
  // ============================================================

  const handleChange = (e) => {

    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  // ============================================================
  // UPDATE EVENT
  // ============================================================

  const handleSubmit = async (e) => {

    e.preventDefault();

    setSaving(true);
    setError("");

    const token = localStorage.getItem("token");

    try {

      await axios.put(
        `http://127.0.0.1:8000/events/${eventId}`,
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

      alert("Event updated successfully!");

      navigate("/manage-events");

    } catch (error) {

      console.error("Error updating event:", error);

      setError(
        error.response?.data?.detail ||
        "Failed to update event"
      );

    } finally {

      setSaving(false);
    }
  };

  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {
    return (
      <div style={styles.loading}>
        <h2>Loading event...</h2>
      </div>
    );
  }

  // ============================================================
  // PAGE
  // ============================================================

  return (
    <div style={styles.container}>

      <h1 style={styles.heading}>
        Edit Event
      </h1>

      {error && (
        <p style={styles.error}>
          {error}
        </p>
      )}

      <form
        onSubmit={handleSubmit}
        style={styles.form}
      >

        {/* EVENT TITLE */}

        <label>
          Event Title
        </label>

        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          required
          style={styles.input}
        />


        {/* DESCRIPTION */}

        <label>
          Description
        </label>

        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows="4"
          required
          style={styles.input}
        />


        {/* CATEGORY */}

        <label>
          Category
        </label>

        <select
          name="category"
          value={formData.category}
          onChange={handleChange}
          style={styles.input}
        >
          <option value="Music">
            Music
          </option>

          <option value="Tech">
            Tech
          </option>

          <option value="Sports">
            Sports
          </option>

          <option value="Business">
            Business
          </option>
        </select>


        {/* LOCATION */}

        <label>
          Location
        </label>

        <input
          type="text"
          name="location"
          value={formData.location}
          onChange={handleChange}
          required
          style={styles.input}
        />


        {/* EVENT DATE */}

        <label>
          Event Date and Time
        </label>

        <input
          type="datetime-local"
          name="event_date"
          value={formData.event_date}
          onChange={handleChange}
          required
          style={styles.input}
        />


        {/* TICKET PRICE */}

        <label>
          Ticket Price
        </label>

        <input
          type="number"
          name="ticket_price"
          value={formData.ticket_price}
          onChange={handleChange}
          min="0"
          required
          style={styles.input}
        />


        {/* TOTAL TICKETS */}

        <label>
          Total Tickets
        </label>

        <input
          type="number"
          name="total_tickets"
          value={formData.total_tickets}
          onChange={handleChange}
          min="1"
          required
          style={styles.input}
        />


        {/* BANNER IMAGE */}

        <label>
          Banner Image URL
        </label>

        <input
          type="text"
          name="banner_image"
          value={formData.banner_image}
          onChange={handleChange}
          style={styles.input}
        />


        {/* UPDATE BUTTON */}

        <button
          type="submit"
          disabled={saving}
          style={styles.button}
        >
          {saving
            ? "Saving..."
            : "Update Event"}
        </button>


        {/* BACK BUTTON */}

        <button
          type="button"
          onClick={() => navigate("/manage-events")}
          style={styles.backButton}
        >
          Back to Manage Events
        </button>

      </form>

    </div>
  );
}


// ============================================================
// STYLES
// ============================================================

const styles = {

  container: {
    maxWidth: "700px",
    margin: "40px auto",
    padding: "30px",
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    boxShadow: "0 4px 15px rgba(0, 0, 0, 0.08)",
  },

  heading: {
    textAlign: "center",
    marginBottom: "25px",
    color: "#1f2937",
  },

  loading: {
    textAlign: "center",
    marginTop: "60px",
  },

  form: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },

  input: {
    padding: "11px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    fontSize: "15px",
    marginBottom: "8px",
  },

  button: {
    marginTop: "15px",
    padding: "12px",
    backgroundColor: "#2563eb",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "16px",
    fontWeight: "600",
  },

  backButton: {
    padding: "11px",
    backgroundColor: "#6b7280",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "15px",
  },

  error: {
    color: "#dc2626",
    backgroundColor: "#fee2e2",
    padding: "10px",
    borderRadius: "6px",
    marginBottom: "15px",
  },
};

export default EditEvent;

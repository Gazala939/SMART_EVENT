
import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function AdminDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const token = localStorage.getItem("token");

        const response = await axios.get(
          "http://127.0.0.1:8000/admin/analytics",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        setAnalytics(response.data);
      } catch (err) {
        console.error(err);
        setError(
          err.response?.data?.detail ||
            "Unable to load admin analytics."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return <h2>Loading Admin Dashboard...</h2>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  // Read common analytics field names safely
  const totalUsers =
    analytics.total_users ?? analytics.registered_users ?? 0;

  const totalEvents =
    analytics.total_events ?? analytics.total_events_created ?? 0;

  const totalBookings =
    analytics.total_bookings ?? 0;

  const totalTickets =
    analytics.total_tickets_sold ?? analytics.tickets_sold ?? 0;

  const revenue =
    analytics.platform_revenue ??
    analytics.total_revenue ??
    analytics.total_sales ??
    0;

  const cards = [
    { title: "Registered Users", value: totalUsers },
    { title: "Total Events", value: totalEvents },
    { title: "Tickets Sold", value: totalTickets },
    { title: "Total Bookings", value: totalBookings },
    {
      title: "Platform Revenue",
      value: `₹${Number(revenue).toLocaleString("en-IN")}`,
    },
  ];

  return (
    <div className="admin-dashboard">
      <h1>Admin Dashboard</h1>
      <p>SmartEvent platform overview</p>

      <div className="admin-kpi-grid">
        {cards.map((card) => (
          <div className="admin-kpi-card" key={card.title}>
            <h3>{card.title}</h3>
            <p>{card.value}</p>
          </div>
        ))}
      </div>

      <h2>Platform Management</h2>

      <div className="admin-actions">
        <button onClick={() => navigate("/admin/analytics")}>
          Platform Analytics
        </button>

        <button onClick={() => navigate("/admin/users")}>
          View Users
        </button>

        <button onClick={() => navigate("/admin/events")}>
          View Events
        </button>

        <button onClick={() => navigate("/admin/bookings")}>
          View Bookings
        </button>
      </div>
    </div>
  );
}

export default AdminDashboard;


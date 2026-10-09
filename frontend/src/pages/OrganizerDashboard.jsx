
import { useEffect, useState } from "react";
import axios from "axios";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const API_URL = "http://127.0.0.1:8000";

function OrganizerDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("token");

      if (!token) {
        setError("Please log in as an organizer to view analytics.");
        return;
      }

      const response = await axios.get(
        `${API_URL}/organizer/analytics`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setAnalytics(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load analytics. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(amount || 0);

  if (loading) {
    return (
      <div className="organizer-dashboard">
        <div className="dashboard-message">
          Loading organizer analytics...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="organizer-dashboard">
        <div className="dashboard-error">
          <h2>Unable to Load Dashboard</h2>
          <p>{error}</p>
          <button onClick={fetchAnalytics}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const events = analytics?.events || [];

  const salesData = events.map((event) => ({
    name:
      event.event_title.length > 18
        ? `${event.event_title.slice(0, 18)}...`
        : event.event_title,
    tickets: event.tickets_sold,
  }));

  const revenueData = events.map((event) => ({
    name:
      event.event_title.length > 18
        ? `${event.event_title.slice(0, 18)}...`
        : event.event_title,
    revenue: event.total_revenue,
  }));

  const COLORS = [
    "#6366f1",
    "#06b6d4",
    "#10b981",
    "#f59e0b",
    "#ec4899",
    "#8b5cf6",
  ];

  return (
    <main className="organizer-dashboard">
      <header className="dashboard-header">
        <div>
          <p className="dashboard-eyebrow">
            SMARTEVENT / ANALYTICS
          </p>
          <h1>Organizer Dashboard</h1>
          <p className="dashboard-subtitle">
            Track your event performance, ticket sales, and revenue.
          </p>
        </div>

        <button
          className="dashboard-refresh"
          onClick={fetchAnalytics}
        >
          ↻ Refresh
        </button>
      </header>

      {/* SUMMARY CARDS */}
      <section className="analytics-cards">
        <article className="analytics-card">
          <div className="analytics-icon purple">▦</div>
          <p>Total Events</p>
          <h2>{analytics.total_events}</h2>
        </article>

        <article className="analytics-card">
          <div className="analytics-icon blue">🎟</div>
          <p>Tickets Sold</p>
          <h2>{analytics.total_tickets_sold}</h2>
        </article>

        <article className="analytics-card">
          <div className="analytics-icon green">✓</div>
          <p>Tickets Remaining</p>
          <h2>{analytics.total_remaining_tickets}</h2>
        </article>

        <article className="analytics-card">
          <div className="analytics-icon orange">₹</div>
          <p>Total Revenue</p>
          <h2>{formatCurrency(analytics.total_revenue)}</h2>
        </article>

        <article className="analytics-card">
          <div className="analytics-icon pink">▤</div>
          <p>Confirmed Bookings</p>
          <h2>{analytics.total_booking_count}</h2>
        </article>
      </section>

      {/* CHARTS */}
      <section className="analytics-charts">
        <article className="analytics-panel">
          <div className="panel-heading">
            <div>
              <h2>Ticket Sales</h2>
              <p>Confirmed tickets sold per event</p>
            </div>
          </div>

          {salesData.length === 0 ? (
            <p className="empty-chart">
              No event data available yet.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={salesData}
                margin={{
                  top: 15,
                  right: 10,
                  left: 0,
                  bottom: 55,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={-25}
                  textAnchor="end"
                  interval={0}
                  height={70}
                  fontSize={11}
                />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="tickets"
                  name="Tickets Sold"
                  fill="#6366f1"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </article>

        <article className="analytics-panel">
          <div className="panel-heading">
            <div>
              <h2>Revenue by Event</h2>
              <p>Revenue from confirmed bookings</p>
            </div>
          </div>

          {revenueData.length === 0 ? (
            <p className="empty-chart">
              No revenue data available yet.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={revenueData}
                  dataKey="revenue"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={95}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {revenueData.map((entry, index) => (
                    <Cell
                      key={`${entry.name}-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => formatCurrency(value)}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </article>
      </section>

      {/* EVENT PERFORMANCE TABLE */}
      <section className="analytics-panel event-performance">
        <div className="panel-heading">
          <div>
            <h2>Event Performance</h2>
            <p>Sales and revenue for your events</p>
          </div>
          <span className="event-count">
            {events.length} events
          </span>
        </div>

        {events.length === 0 ? (
          <p className="empty-chart">
            You have not created any events yet.
          </p>
        ) : (
          <div className="analytics-table-wrapper">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Status</th>
                  <th>Total Tickets</th>
                  <th>Sold</th>
                  <th>Remaining</th>
                  <th>Bookings</th>
                  <th>Revenue</th>
                </tr>
              </thead>

              <tbody>
                {events.map((event) => (
                  <tr key={event.event_id}>
                    <td className="event-name-cell">
                      {event.event_title}
                    </td>

                    <td>
                      <span
                        className={`event-status status-${(
                          event.event_status || ""
                        ).toLowerCase()}`}
                      >
                        {event.event_status}
                      </span>
                    </td>

                    <td>{event.total_tickets}</td>
                    <td>{event.tickets_sold}</td>
                    <td>{event.remaining_tickets}</td>
                    <td>{event.booking_count}</td>
                    <td className="revenue-cell">
                      {formatCurrency(event.total_revenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}

export default OrganizerDashboard;


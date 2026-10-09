import { useCallback, useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000/admin/analytics";

function getArray(data, possibleKeys) {
  for (const key of possibleKeys) {
    if (Array.isArray(data?.[key])) {
      return data[key];
    }
  }

  return [];
}

function convertToChartRows(items, labelKeys, valueKeys) {
  if (!Array.isArray(items)) return [];

  return items.map((item, index) => {
    if (typeof item === "number") {
      return {
        label: `Item ${index + 1}`,
        value: item,
      };
    }

    const label =
      labelKeys.map((key) => item?.[key]).find(
        (value) => value !== undefined && value !== null && value !== ""
      ) ?? `Item ${index + 1}`;

    const rawValue = valueKeys
      .map((key) => item?.[key])
      .find((value) => value !== undefined && value !== null && value !== "");

    const value = Number(rawValue ?? 0);

    return {
      label: String(label),
      value: Number.isFinite(value) ? value : 0,
    };
  });
}

function BarChart({ title, rows, currency = false }) {
  const maxValue = Math.max(0, ...rows.map((row) => row.value));

  const formatValue = (value) =>
    currency
      ? `₹${value.toLocaleString("en-IN")}`
      : value.toLocaleString("en-IN");

  return (
    <section className="analytics-chart-card">
      <h2>{title}</h2>

      {rows.length === 0 ? (
        <p className="chart-empty">
          No data available for this period.
        </p>
      ) : (
        <div className="chart-bars">
          {rows.map((row, index) => {
            const width =
              maxValue > 0 && row.value > 0
                ? Math.max(3, (row.value / maxValue) * 100)
                : 0;

            return (
              <div className="chart-row" key={`${row.label}-${index}`}>
                <div className="chart-row-heading">
                  <span className="chart-label" title={row.label}>
                    {row.label}
                  </span>

                  <strong className="chart-value">
                    {formatValue(row.value)}
                  </strong>
                </div>

                <div
                  className="chart-track"
                  role="progressbar"
                  aria-label={row.label}
                  aria-valuemin={0}
                  aria-valuemax={maxValue || 1}
                  aria-valuenow={row.value}
                >
                  <div
                    className="chart-fill"
                    style={{ width: `${width}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function PlatformAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAnalytics = useCallback(async (start = "", end = "") => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("token");

      const params = {};
      if (start) params.start_date = start;
      if (end) params.end_date = end;

      const response = await axios.get(API_URL, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        params,
      });

      const payload =
        response.data?.analytics ??
        response.data?.data ??
        response.data;

      setAnalytics(payload ?? {});
    } catch (err) {
      console.error("Platform analytics error:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to load platform analytics. Please check your backend API."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const handleFilter = (event) => {
    event.preventDefault();

    if (startDate && endDate && startDate > endDate) {
      setError("Start date cannot be later than end date.");
      return;
    }

    fetchAnalytics(startDate, endDate);
  };

  if (loading && !analytics) {
    return (
      <div className="platform-analytics">
        <h1>Platform Analytics</h1>
        <p>Loading analytics...</p>
      </div>
    );
  }

  const data = analytics ?? {};

  const dailyData = getArray(data, [
    "daily_ticket_sales",
    "daily_sales",
    "daily_ticket_sales_data",
    "daily_sales_data",
  ]);

  const monthlyData = getArray(data, [
    "monthly_booking_trends",
    "monthly_bookings",
    "monthly_booking_data",
  ]);

  const popularData = getArray(data, [
    "most_popular_events",
    "popular_events",
  ]);

  const revenueData = getArray(data, [
    "top_revenue_events",
    "top_revenue_generating_events",
    "top_revenue_events_data",
  ]);

  const dailyRows = convertToChartRows(
    dailyData,
    ["date", "day", "label"],
    ["tickets_sold", "total_tickets_sold", "ticket_count", "tickets", "count", "sales", "value", "total"]
  );

  const monthlyRows = convertToChartRows(
    monthlyData,
    ["month", "label", "period"],
    ["total_bookings", "booking_count", "bookings", "count", "value", "total"]
  );

  const popularRows = convertToChartRows(
    popularData,
    ["event_title", "event_name", "title", "name", "label"],
    ["booking_count", "bookings", "tickets_sold", "ticket_count", "tickets", "count", "popularity", "value"]
  );

  const revenueRows = convertToChartRows(
    revenueData,
    ["event_title", "event_name", "title", "name", "label"],
    ["revenue", "total_revenue", "total_price", "amount", "sales", "value", "total"]
  );

  const summary = [
    {
      title: "Registered Users",
      value: data.total_users ?? data.registered_users ?? 0,
    },
    {
      title: "Total Events",
      value: data.total_events ?? data.total_events_created ?? 0,
    },
    {
      title: "Tickets Sold",
      value: data.total_tickets_sold ?? data.tickets_sold ?? 0,
    },
    {
      title: "Total Bookings",
      value: data.total_bookings ?? 0,
    },
    {
      title: "Platform Revenue",
      value: `₹${Number(
        data.platform_revenue ??
          data.total_revenue ??
          data.total_sales ??
          0
      ).toLocaleString("en-IN")}`,
    },
  ];

  return (
    <div className="platform-analytics">
      <h1>Platform Analytics</h1>
      <p className="analytics-subtitle">
        Monitor SmartEvent activity, ticket sales, bookings, and revenue.
      </p>

      <form className="analytics-filters" onSubmit={handleFilter}>
        <label>
          Start Date
          <input
            type="date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
          />
        </label>

        <label>
          End Date
          <input
            type="date"
            value={endDate}
            onChange={(event) => setEndDate(event.target.value)}
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Loading..." : "Apply Filter"}
        </button>

        <button
          type="button"
          className="analytics-reset-btn"
          onClick={() => {
            setStartDate("");
            setEndDate("");
            fetchAnalytics();
          }}
        >
          Reset
        </button>
      </form>

      {error && (
        <div className="analytics-error">
          <p>{error}</p>
          <button
            type="button"
            onClick={() => fetchAnalytics(startDate, endDate)}
          >
            Retry
          </button>
        </div>
      )}

      {loading && analytics && (
        <p className="analytics-loading">Updating analytics...</p>
      )}

      <div className="analytics-summary-grid">
        {summary.map((item) => (
          <div className="analytics-summary-card" key={item.title}>
            <span>{item.title}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>

      <div className="analytics-charts-grid">
        <BarChart
          title="Daily Ticket Sales"
          rows={dailyRows}
        />

        <BarChart
          title="Monthly Booking Trends"
          rows={monthlyRows}
        />

        <BarChart
          title="Most Popular Events"
          rows={popularRows}
        />

        <BarChart
          title="Top Revenue-Generating Events"
          rows={revenueRows}
          currency
        />
      </div>
    </div>
  );
}

export default PlatformAnalytics;
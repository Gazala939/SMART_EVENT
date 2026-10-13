
import { useEffect, useState } from "react";
import axios from "axios";
import EventCard from "../components/EventCard";
import EventCardSkeleton from "../components/EventCardSkeleton";
import "../components/EventCardSkeleton.css";
import "./Home.css";

function Home() {
  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [location, setLocation] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [sortBy, setSortBy] = useState("date");
  const [sortOrder, setSortOrder] = useState("asc");

  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  // Fetch events using search and filter values
  const fetchEvents = async (overrides = {}) => {
    setLoading(true);
    setErrorMessage("");

    try {
      const params = {
        title: search.trim(),
        category,
        location: location.trim(),
        start_date: startDate,
        end_date: endDate,
        sort_by: sortBy,
        sort_order: sortOrder,
        ...overrides,
      };

      Object.keys(params).forEach((key) => {
        if (params[key] === "") {
          delete params[key];
        }
      });

      const response = await axios.get(
        "http://127.0.0.1:8000/events/search",
        { params }
      );

      setEvents(
        Array.isArray(response.data) ? response.data : []
      );
    } catch (error) {
      console.error("Error fetching events:", error);
      setEvents([]);
      setErrorMessage(
        error.response?.data?.detail ||
          "Unable to load events. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  // Load events when Home opens
  useEffect(() => {
    const loadInitialEvents = async () => {
      setLoading(true);
      setErrorMessage("");

      try {
        const response = await axios.get(
          "http://127.0.0.1:8000/events"
        );

        setEvents(
          Array.isArray(response.data) ? response.data : []
        );
      } catch (error) {
        console.error("Error loading events:", error);
        setEvents([]);
        setErrorMessage(
          "Unable to load events. Please check whether the backend is running."
        );
      } finally {
        setLoading(false);
      }
    };

    loadInitialEvents();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchEvents();
  };

  const handleCategory = (newCategory) => {
    setCategory(newCategory);
    fetchEvents({ category: newCategory });
  };

  const handleClearFilters = async () => {
    setSearch("");
    setCategory("");
    setLocation("");
    setStartDate("");
    setEndDate("");
    setSortBy("date");
    setSortOrder("asc");

    setLoading(true);
    setErrorMessage("");

    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/events"
      );

      setEvents(
        Array.isArray(response.data) ? response.data : []
      );
    } catch (error) {
      console.error("Error loading events:", error);
      setEvents([]);
      setErrorMessage("Unable to load events. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const featuredEvents = events
    .filter((event) => {
      const status = (
        event.event_status || "UPCOMING"
      ).toUpperCase();

      return status !== "CANCELLED" && status !== "COMPLETED";
    })
    .slice(0, 3);

  const categories = [
    "All",
    "Music",
    "Tech",
    "Sports",
    "Business",
  ];

  return (
    <div className="home-container">
      {/* 1. Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <span className="hero-eyebrow">
            YOUR NEXT EXPERIENCE STARTS HERE
          </span>

          <h1>Discover Events That Inspire You</h1>

          <p>
            Find exciting events, explore new interests, and book
            your next unforgettable experience with SmartEvent.
          </p>

          <button
            type="button"
            className="hero-button"
            onClick={() =>
              document
                .getElementById("event-list")
                ?.scrollIntoView({ behavior: "smooth" })
            }
          >
            Explore Events <span aria-hidden="true">→</span>
          </button>
        </div>

        <div className="hero-decoration" aria-hidden="true">
          <span>🎟️</span>
          <span>🎉</span>
          <span>✨</span>
        </div>
      </section>

      {/* 2. Search Bar */}
      <form
        className="search-container"
        onSubmit={handleSearch}
      >
        <input
          id="event-search"
          type="text"
          placeholder="Search by event name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoComplete="off"
        />

        <button type="submit">Search</button>
      </form>

      {/* 3. Category Buttons */}
      <div className="category-container">
        {categories.map((item) => {
          const value = item === "All" ? "" : item;

          return (
            <button
              key={item}
              type="button"
              className={
                category === value
                  ? "category-button active"
                  : "category-button"
              }
              onClick={() => handleCategory(value)}
            >
              {item}
            </button>
          );
        })}
      </div>

      {/* 4. Featured Events */}
      {!loading &&
        !errorMessage &&
        featuredEvents.length > 0 && (
          <section className="featured-section">
            <div className="featured-heading">
              <div>
                <span className="featured-eyebrow">
                  HANDPICKED FOR YOU
                </span>

                <h2>Featured Events</h2>

                <p>
                  Discover experiences worth looking forward to.
                </p>
              </div>
            </div>

            <div className="featured-grid">
              {featuredEvents.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          </section>
        )}

      {/* 5. Filters */}
      <aside className="event-filters">
        <h2>Filter Events</h2>

        <label htmlFor="filter-location">Location</label>
        <input
          id="filter-location"
          type="text"
          placeholder="Enter location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />

        <label htmlFor="filter-start-date">Start Date</label>
        <input
          id="filter-start-date"
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
        />

        <label htmlFor="filter-end-date">End Date</label>
        <input
          id="filter-end-date"
          type="date"
          min={startDate || undefined}
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
        />

        <label htmlFor="filter-sort">Sort By</label>
        <select
          id="filter-sort"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
        >
          <option value="date">Event Date</option>
          <option value="price">Ticket Price</option>
          <option value="popularity">Popularity</option>
        </select>

        <label htmlFor="filter-order">Sort Order</label>
        <select
          id="filter-order"
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value)}
        >
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>

        <button type="button" onClick={() => fetchEvents()}>
          Apply Filters
        </button>

        <button type="button" onClick={handleClearFilters}>
          Clear Filters
        </button>
      </aside>

      {/* 6. All Events */}
      <section className="event-grid" id="event-list">
        <div className="event-list-heading">
          <h2>Explore All Events</h2>

          {!loading && !errorMessage && (
            <p>
              {events.length}{" "}
              {events.length === 1 ? "event" : "events"} found
            </p>
          )}
        </div>

        {loading ? (
          <div className="event-list-grid">
            {Array.from({ length: 4 }).map((_, index) => (
              <EventCardSkeleton key={index} />
            ))}
          </div>
        ) : errorMessage ? (
          <p className="error-message">{errorMessage}</p>
        ) : events.length === 0 ? (
          <p className="empty-state">
            No events found. Try changing your search or filters.
          </p>
        ) : (
          <div className="event-list-grid">
            {events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default Home;

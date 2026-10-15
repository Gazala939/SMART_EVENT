
import { useEffect, useState, useCallback } from "react";
import { Link, useLocation } from "react-router-dom";
import api from "../api";
import EventCard from "../components/EventCard";
import EventCardSkeleton from "../components/EventCardSkeleton";
import "../components/EventCardSkeleton.css";
import "./Home.css";

function Home() {
  const currentRoute = useLocation();

  const [events, setEvents] = useState([]);
  const [trendingEvents, setTrendingEvents] = useState([]);
  const [recommendedEvents, setRecommendedEvents] = useState([]);

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [location, setLocation] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [sortBy, setSortBy] = useState("date");
  const [sortOrder, setSortOrder] = useState("asc");

 

  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [recommendationsLoading, setRecommendationsLoading] =
    useState(true);

  // Fetch events using all selected filters.
  const fetchEvents = useCallback(async (overrides = {}) => {
    setLoading(true);
    setErrorMessage("");

    try {
      const params = {
        title: search.trim(),
        category,
        location: location.trim(),
        start_date: startDate,
        end_date: endDate,
        min_price: minPrice,
        max_price: maxPrice,
        sort_by: sortBy,
        sort_order: sortOrder,
        ...overrides,
      };

      Object.keys(params).forEach((key) => {
        if (params[key] === "" || params[key] == null) {
          delete params[key];
        }
      });

      const response = await api.get("/events/search", { params });

      setEvents(Array.isArray(response.data) ? response.data : []);
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
  }, [
    search,
    category,
    location,
    startDate,
    endDate,
    minPrice,
    maxPrice,
    sortBy,
    sortOrder,
  ]);

  
  // Load trending events and personalized recommendations.
  const fetchDiscoverSections = useCallback(async () => {
    setRecommendationsLoading(true);

    try {
      // Trending events can be loaded without logging in.
      try {
        const trendingResponse = await api.get("/recommendations/trending");
        setTrendingEvents(
          Array.isArray(trendingResponse.data)
            ? trendingResponse.data
            : []
        );
      } catch (error) {
        console.error("Unable to load trending events:", error);
        setTrendingEvents([]);
      }

      // Personalized recommendations require a logged-in user.
      const token = localStorage.getItem("token");

      if (!token) {
        setRecommendedEvents([]);
        return;
      }

      try {
        const recommendedResponse = await api.get(
          "/recommendations/for-me"
        );

        setRecommendedEvents(
          Array.isArray(recommendedResponse.data)
            ? recommendedResponse.data
            : []
        );
      } catch (error) {
        console.error(
          "Unable to load personalized recommendations:",
          error
        );
        setRecommendedEvents([]);
      }
    } finally {
      setRecommendationsLoading(false);
    }
  }, []);


  // Initial page loading.
  useEffect(() => {
    fetchEvents();
    fetchDiscoverSections();
  }, [location.pathname, fetchEvents, fetchDiscoverSections]);

  const handleSearch = (event) => {
    event.preventDefault();
    fetchEvents();
  };

  const handleApplyFilters = () => {
    if (
      minPrice !== "" &&
      maxPrice !== "" &&
      Number(minPrice) > Number(maxPrice)
    ) {
      setErrorMessage(
        "Minimum price cannot be greater than maximum price."
      );
      return;
    }

    if (startDate && endDate && startDate > endDate) {
      setErrorMessage(
        "End date cannot be earlier than start date."
      );
      return;
    }

    fetchEvents();
  };

  
  const handleCategory = (newCategory) => {
    setCategory(newCategory);
  };


  const handleClearFilters = () => {
    setSearch("");
    setCategory("");
    setLocation("");
    setStartDate("");
    setEndDate("");
    setMinPrice("");
    setMaxPrice("");
    setSortBy("date");
    setSortOrder("asc");

    fetchEvents({
      title: "",
      category: "",
      location: "",
      start_date: "",
      end_date: "",
      min_price: "",
      max_price: "",
      sort_by: "date",
      sort_order: "asc",
    });
  };

  const categories = [
    "All",
    "Music",
    "Tech",
    "Sports",
    "Business",
  ];

  const renderEventCards = (items, emptyMessage) => {
    if (items.length === 0) {
      return <p className="empty-state">{emptyMessage}</p>;
    }

    return (
      <div className="event-list-grid">
        {items.map((event) => (
          <EventCard key={event.id} event={event} />
        ))}
      </div>
    );
  };

  return (
    <div className="home-container">
      {/* HERO SECTION */}
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

      {/* SEARCH */}
      <form className="search-container" onSubmit={handleSearch}>
        <input
          id="event-search"
          type="text"
          placeholder="Search by event name..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          autoComplete="off"
        />

        <button type="submit">Search</button>
      </form>

      {/* CATEGORY FILTERS */}
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

      {/* MODULE 19: TRENDING EVENTS */}
      <section className="featured-section">
        <div className="featured-heading">
          <div>
            <span className="featured-eyebrow">POPULAR RIGHT NOW</span>
            <h2>Trending Events 🔥</h2>
            <p>Explore events attracting attention from attendees.</p>
          </div>
        </div>

        {recommendationsLoading ? (
          <div className="event-list-grid">
            {Array.from({ length: 3 }).map((_, index) => (
              <EventCardSkeleton key={index} />
            ))}
          </div>
        ) : (
          renderEventCards(
            trendingEvents,
            "No trending events are available right now."
          )
        )}
      </section>

      {/* MODULE 19: PERSONALIZED RECOMMENDATIONS */}
      <section className="featured-section">
        <div className="featured-heading">
          <div>
            <span className="featured-eyebrow">PICKED FOR YOUR INTERESTS</span>
            <h2>Recommended for You ✨</h2>
            <p>
              Suggestions based on your event interests and booking activity.
            </p>
          </div>
        </div>

        {recommendationsLoading ? (
          <div className="event-list-grid">
            {Array.from({ length: 3 }).map((_, index) => (
              <EventCardSkeleton key={index} />
            ))}
          </div>
        ) : recommendedEvents.length > 0 ? (
          renderEventCards(recommendedEvents, "")
        ) : (
          <div className="empty-state">
            <p>
              {localStorage.getItem("token")
                ? "We don't have personalized suggestions for you yet. Explore events and book one to help us learn your interests."
                : "Log in to discover event recommendations tailored to your interests."}
            </p>  
            {localStorage.getItem("token") ? (
              <Link to="/booking-history">View My Bookings</Link>
            ) : (
              <Link to="/login">Log In</Link>
            )}

          </div>
        )}
      </section>

      {/* MODULE 23: ADVANCED FILTERS */}
      <aside className="event-filters">
        <h2>Filter Events</h2>

        <label htmlFor="filter-location">Location</label>
        <input
          id="filter-location"
          type="text"
          placeholder="Enter location"
          value={location}
          onChange={(event) => setLocation(event.target.value)}
        />

        <label htmlFor="filter-start-date">Start Date</label>
        <input
          id="filter-start-date"
          type="date"
          value={startDate}
          onChange={(event) => setStartDate(event.target.value)}
        />

        <label htmlFor="filter-end-date">End Date</label>
        <input
          id="filter-end-date"
          type="date"
          min={startDate || undefined}
          value={endDate}
          onChange={(event) => setEndDate(event.target.value)}
        />

        <label htmlFor="filter-min-price">Minimum Ticket Price (₹)</label>
        <input
          id="filter-min-price"
          type="number"
          min="0"
          placeholder="Minimum price"
          value={minPrice}
          onChange={(event) => setMinPrice(event.target.value)}
        />

        <label htmlFor="filter-max-price">Maximum Ticket Price (₹)</label>
        <input
          id="filter-max-price"
          type="number"
          min="0"
          placeholder="Maximum price"
          value={maxPrice}
          onChange={(event) => setMaxPrice(event.target.value)}
        />

        <label htmlFor="filter-sort">Sort By</label>
        <select
          id="filter-sort"
          value={sortBy}
          onChange={(event) => setSortBy(event.target.value)}
        >
          <option value="date">Event Date</option>
          <option value="price">Ticket Price</option>
          <option value="popularity">Popularity</option>
        </select>

        <label htmlFor="filter-order">Sort Order</label>
        <select
          id="filter-order"
          value={sortOrder}
          onChange={(event) => setSortOrder(event.target.value)}
        >
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>

        <button type="button" onClick={handleApplyFilters}>
          Apply Filters
        </button>

        <button type="button" onClick={handleClearFilters}>
          Clear Filters
        </button>
      </aside>

      {/* ALL EVENTS */}
      <section className="event-grid" id="event-list">
        <div className="event-list-heading">
          <h2>Explore All Events</h2>

          {!loading && !errorMessage && (
            <p>
              {events.length} {events.length === 1 ? "event" : "events"} found
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
        ) : (
          renderEventCards(
            events,
            "No events found. Try changing your search or filters."
          )
        )}
      </section>
    </div>
  );
}

export default Home;

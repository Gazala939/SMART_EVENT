import { useEffect, useState } from "react";
import axios from "axios";
import EventCard from "../components/EventCard";

function Home() {
  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const getEvents = async () => {
    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/events"
      );

      setEvents(response.data);
      setLoading(false);
    } catch (error) {
      console.log(error);
      setLoading(false);
    }
  };

  useEffect(() => {
    getEvents();
  }, []);

  const handleSearch = async () => {
    try {
      if (search.trim() === "") {
        getEvents();
        return;
      }

      const response = await axios.get(
        `http://127.0.0.1:8000/events/search?title=${search}`
      );

      setEvents(response.data);
    } catch (error) {
      console.log(error);
    }
  };

  const handleCategory = async (selectedCategory) => {
    try {
      if (selectedCategory === "All") {
        getEvents();
        return;
      }

      const response = await axios.get(
        `http://127.0.0.1:8000/events/category/${selectedCategory}`
      );

      setEvents(response.data);
    } catch (error) {
      console.log(error);
    }
  };

  if (loading) {
    return <h2>Loading events...</h2>;
  }

  return (
    <div className="home-container">

      <h1>SmartEvent</h1>

      <h2>Discover Events</h2>

      <div className="search-container">

        <input
          type="text"
          placeholder="Search events..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <button onClick={handleSearch}>
          Search
        </button>

      </div>

      <div className="category-container">

        <button onClick={() => handleCategory("All")}>
          All
        </button>

        <button onClick={() => handleCategory("Music")}>
          Music
        </button>

        <button onClick={() => handleCategory("Tech")}>
          Tech
        </button>

        <button onClick={() => handleCategory("Sports")}>
          Sports
        </button>

        <button onClick={() => handleCategory("Business")}>
          Business
        </button>

      </div>

      <div className="event-grid">

        {events.length === 0 ? (

          <h3>No events found</h3>

        ) : (

          events.map((event) => (
            <EventCard
              key={event.id}
              event={event}
            />
          ))

        )}

      </div>

    </div>
  );
}

export default Home;
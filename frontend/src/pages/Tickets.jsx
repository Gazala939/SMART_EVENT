import { useEffect, useState } from "react";
import axios from "axios";
import TicketCard from "../components/TicketCard";

function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  const getTickets = async () => {
    const token = localStorage.getItem("token");

    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/tickets/my-tickets",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setTickets(response.data);
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getTickets();
  }, []);

  if (loading) {
    return (
      <div className="tickets-container">
        <h2>Loading tickets...</h2>
      </div>
    );
  }

  return (
    <div className="tickets-container">

      <h1>My Tickets</h1>

      {tickets.length === 0 ? (
        <p>No tickets found.</p>
      ) : (
        <div className="tickets-list">

          {tickets.map((ticket) => (
            <TicketCard
              key={ticket.id}
              ticket={ticket}
            />
          ))}

        </div>
      )}

    </div>
  );
}

export default Tickets;
import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import NotificationDropdown from "./NotificationDropdown";

function Navbar() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);

  const navigate = useNavigate();

  const getNotifications = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      return;
    }

    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/notifications",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setNotifications(response.data);

      const unread = response.data.filter(
        (notification) => !notification.is_read
      );

      setUnreadCount(unread.length);
    } catch (error) {
      console.log(error);
    }
  };

  useEffect(() => {
    getNotifications();
  }, []);

  const markAsRead = async (notificationId) => {
    const token = localStorage.getItem("token");

    try {
      await axios.put(
        `http://127.0.0.1:8000/notifications/${notificationId}/read`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      getNotifications();
    } catch (error) {
      console.log(error);
    }
  };

  const handleViewAll = () => {
    setShowDropdown(false);
    navigate("/notifications");
  };

  return (
    <nav className="navbar">

      <div
        className="navbar-logo"
        onClick={() => navigate("/home")}
      >
        SmartEvent
      </div>

      <div className="navbar-actions">

        <button
            className="navbar-link"
            onClick={() => navigate("/tickets")}
          >
            🎟️ My Tickets
        </button>

        <button
          className="navbar-link"
          onClick={() => navigate("/booking-history")}
        >
          📋 Booking History
        </button>

        <div className="notification-wrapper">
          <button
            className="notification-button"
            onClick={() => setShowDropdown(!showDropdown)}
          >
            🔔

            {unreadCount > 0 && (
              <span className="notification-count">
                {unreadCount}
              </span>
            )}
          </button>

          {showDropdown && (
            <NotificationDropdown
              notifications={notifications}
              onMarkAsRead={markAsRead}
              onViewAll={handleViewAll}
            />
          )}

        </div>

      </div>

    </nav>
  );
}

export default Navbar;
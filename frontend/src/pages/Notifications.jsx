import { useEffect, useState } from "react";
import axios from "axios";

function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const getNotifications = async () => {
    const token = localStorage.getItem("token");

    setLoading(true);
    setError("");

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
    } catch (error) {
      console.log(error);
      setError("Unable to load notifications.");
    } finally {
      setLoading(false);
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
      setError("Unable to mark notification as read.");
    }
  };

  if (loading) {
    return (
      <div className="notifications-container">
        <h2>Loading notifications...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <div className="notifications-container">
        <h2>{error}</h2>

        <button
          className="notification-retry-button"
          onClick={getNotifications}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="notifications-container">
      <h1>Notifications</h1>

      {notifications.length === 0 ? (
        <p>No notifications found.</p>
      ) : (
        notifications.map((notification) => (
          <div
            key={notification.id}
            className={`notification-card ${
              notification.is_read ? "read" : "unread"
            }`}
          >
            <h3>{notification.title}</h3>

            <p>{notification.message}</p>

            <p>
              <strong>Type:</strong> {notification.type}
            </p>

            <p>
              <strong>Date:</strong>{" "}
              {new Date(
                notification.created_at
              ).toLocaleString()}
            </p>

            {!notification.is_read && (
              <button
                onClick={() =>
                  markAsRead(notification.id)
                }
              >
                Mark as Read
              </button>
            )}

            {notification.is_read && (
              <span className="read-text">
                ✓ Read
              </span>
            )}
          </div>
        ))
      )}
    </div>
  );
}

export default Notifications;
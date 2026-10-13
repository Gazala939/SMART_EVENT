
import { useEffect, useState } from "react";
import api from "../api";

function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const getNotifications = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/notifications");
      setNotifications(response.data || []);
    } catch (error) {
      console.error("Error fetching notifications:", error);
      setError("Unable to load notifications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getNotifications();
  }, []);

  const markAsRead = async (notificationId) => {
    try {
      await api.put(
        `/notifications/${notificationId}/read`,
        {}
      );

      await getNotifications();
    } catch (error) {
      console.error("Error marking notification as read:", error);
      setError("Unable to mark notification as read.");
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.put("/notifications/read-all", {});
      await getNotifications();
    } catch (error) {
      console.error("Error marking all notifications as read:", error);
      setError("Unable to mark all notifications as read.");
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

  const unreadCount = notifications.filter(
    (notification) => !notification.is_read
  ).length;

  return (
    <div className="notifications-container">
      <h1>Notifications</h1>

      {unreadCount > 0 && (
        <button onClick={markAllAsRead}>
          Mark All as Read ({unreadCount})
        </button>
      )}

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
              <strong>Type:</strong>{" "}
              {notification.notification_type || notification.type}
            </p>

            <p>
              <strong>Date:</strong>{" "}
              {new Date(notification.created_at).toLocaleString()}
            </p>

            {!notification.is_read ? (
              <button
                onClick={() => markAsRead(notification.id)}
              >
                Mark as Read
              </button>
            ) : (
              <span className="read-text">✓ Read</span>
            )}
          </div>
        ))
      )}
    </div>
  );
}

export default Notifications;

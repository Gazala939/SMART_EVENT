
import { useCallback, useEffect, useState } from "react";
import api from "../api";
import { useLocation, useNavigate } from "react-router-dom";
import NotificationDropdown from "./NotificationDropdown";

function Navbar() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [role, setRole] = useState("");

  const navigate = useNavigate();
  const location = useLocation();

  // GET CURRENT USER PROFILE
  const getProfile = useCallback(async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      setRole("");
      return;
    }

    try {
      const response = await api.get("/auth/profile");

      // Normalize the role to uppercase
      const userRole = String(
        response.data.role || ""
      ).toUpperCase();

      setRole(userRole);
    } catch (error) {
      console.error("Error fetching profile:", error);
      setRole("");
    }
  }, []);

  // GET NOTIFICATIONS
  const getNotifications = useCallback(async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    try {
      const response = await api.get("/notifications");
      const notificationList = response.data || [];

      setNotifications(notificationList);

      const unread = notificationList.filter(
        (notification) => !notification.is_read
      );

      setUnreadCount(unread.length);
    } catch (error) {
      console.error("Error fetching notifications:", error);
    }
  }, []);

  // REFRESH NAVBAR DATA WHEN THE ROUTE CHANGES
  useEffect(() => {
    getProfile();
    getNotifications();
  }, [location.pathname, getProfile, getNotifications]);

  // MARK NOTIFICATION AS READ
  const markAsRead = async (notificationId) => {
    try {
      await api.put(`/notifications/${notificationId}/read`, {});
      await getNotifications();
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  };

  // VIEW ALL NOTIFICATIONS
  const handleViewAll = () => {
    setShowDropdown(false);
    navigate("/notifications");
  };

  return (
    <nav className="navbar">
      {/* LOGO */}
      <div
        className="navbar-logo"
        onClick={() => navigate("/home")}
      >
        SmartEvent
      </div>

      {/* NAVBAR ACTIONS */}
      <div className="navbar-actions">
        {/* MY TICKETS */}
        <button
          className="navbar-link"
          onClick={() => navigate("/tickets")}
        >
          🎟️ My Tickets
        </button>

        {/* BOOKING HISTORY */}
        <button
          className="navbar-link"
          onClick={() => navigate("/booking-history")}
        >
          📋 Booking History
        </button>

        {/* ORGANIZER LINKS */}
        {role === "ORGANIZER" && (
          <>
            <button
              className="navbar-link"
              onClick={() => navigate("/organizer/dashboard")}
            >
              📊 Organizer Dashboard
            </button>

            <button
              className="navbar-link"
              onClick={() => navigate("/create-event")}
            >
              ➕ Create Event
            </button>

            <button
              className="navbar-link"
              onClick={() => navigate("/manage-events")}
            >
              🗂️ Manage Events
            </button>
          </>
        )}

        {/* ADMIN LINK */}
        {role === "ADMIN" && (
          <button
            className="navbar-link"
            onClick={() => navigate("/admin/dashboard")}
          >
            🛡️ Admin Dashboard
          </button>
        )}

        {/* NOTIFICATIONS */}
        <div className="notification-wrapper">
          <button
            className="notification-button"
            onClick={() => setShowDropdown((previous) => !previous)}
            aria-label={`Notifications, ${unreadCount} unread`}
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
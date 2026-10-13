
import { useCallback, useEffect, useState } from "react";
import api from "../api";
import { useLocation, useNavigate } from "react-router-dom";
import NotificationDropdown from "./NotificationDropdown";

function Navbar() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [role, setRole] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  // Hide navigation items on Login and Register pages
  const isAuthPage =
    location.pathname === "/login" ||
    location.pathname === "/register";

  const getProfile = useCallback(async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      setRole("");
      return;
    }

    try {
      const response = await api.get("/auth/profile");
      setRole(String(response.data.role || "").toUpperCase());
    } catch (error) {
      console.error("Error fetching profile:", error);
      setRole("");
    }
  }, []);

  const getNotifications = useCallback(async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    try {
      const [notificationsResponse, countResponse] =
        await Promise.all([
          api.get("/notifications"),
          api.get("/notifications/unread-count"),
        ]);

      setNotifications(
        Array.isArray(notificationsResponse.data)
          ? notificationsResponse.data
          : []
      );

      setUnreadCount(countResponse.data.unread_count || 0);
    } catch (error) {
      console.error("Error fetching notifications:", error);
    }
  }, []);

  useEffect(() => {
    getProfile();
    getNotifications();
    setShowDropdown(false);
    setMenuOpen(false);
  }, [location.pathname, getProfile, getNotifications]);

  const handleNavigate = (path) => {
    setMenuOpen(false);
    setShowDropdown(false);
    navigate(path);
  };

  const isActive = (path) => {
    if (path === "/home") {
      return (
        location.pathname === "/" ||
        location.pathname === "/home"
      );
    }

    return location.pathname.startsWith(path);
  };

  const markAsRead = async (notificationId) => {
    try {
      await api.put(`/notifications/${notificationId}/read`, {});
      await getNotifications();
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  };

  const handleViewAll = () => {
    setShowDropdown(false);
    navigate("/notifications");
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("user_id");

    setNotifications([]);
    setUnreadCount(0);
    setRole("");
    setShowDropdown(false);
    setMenuOpen(false);

    navigate("/login", { replace: true });
  };

  return (
    <nav className={`navbar ${isAuthPage ? "navbar-auth-page" : ""}`}>
      {/* SmartEvent logo */}
      

      {!isAuthPage && (
        <button
          type="button"
          className="navbar-logo"
          onClick={() => handleNavigate("/home")}
          aria-label="SmartEvent home"
        >
          

          <span>
            Smart<span className="navbar-logo-highlight">Event</span>
          </span>
        </button>
      )}


      {/* Hide the mobile menu on Login and Register pages */}
      {!isAuthPage && (
        <button
          type="button"
          className="navbar-menu-toggle"
          onClick={() => setMenuOpen((previous) => !previous)}
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
        >
          {menuOpen ? "✕" : "☰"}
        </button>
      )}

      {!isAuthPage && (
        <div
          className={`navbar-actions ${
            menuOpen ? "navbar-actions-open" : ""
          }`}
        >
          <button
            type="button"
            className={`navbar-link ${
              isActive("/tickets") ? "navbar-link-active" : ""
            }`}
            onClick={() => handleNavigate("/tickets")}
          >
            <span aria-hidden="true">🎟️</span>
            My Tickets
          </button>

          <button
            type="button"
            className={`navbar-link ${
              isActive("/booking-history") ? "navbar-link-active" : ""
            }`}
            onClick={() => handleNavigate("/booking-history")}
          >
            <span aria-hidden="true">📋</span>
            Booking History
          </button>

          {role === "ORGANIZER" && (
            <>
              <button
                type="button"
                className={`navbar-link ${
                  isActive("/organizer/dashboard")
                    ? "navbar-link-active"
                    : ""
                }`}
                onClick={() => handleNavigate("/organizer/dashboard")}
              >
                📊 Organizer Dashboard
              </button>

              <button
                type="button"
                className={`navbar-link ${
                  isActive("/create-event") ? "navbar-link-active" : ""
                }`}
                onClick={() => handleNavigate("/create-event")}
              >
                ➕ Create Event
              </button>

              <button
                type="button"
                className={`navbar-link ${
                  isActive("/manage-events") ? "navbar-link-active" : ""
                }`}
                onClick={() => handleNavigate("/manage-events")}
              >
                🗂️ Manage Events
              </button>
            </>
          )}

          {role === "ADMIN" && (
            <button
              type="button"
              className={`navbar-link ${
                isActive("/admin/dashboard") ? "navbar-link-active" : ""
              }`}
              onClick={() => handleNavigate("/admin/dashboard")}
            >
              🛡️ Admin Dashboard
            </button>
          )}

          <div className="notification-wrapper">
            <button
              type="button"
              className="notification-button"
              onClick={() =>
                setShowDropdown((previous) => !previous)
              }
              aria-label={`Notifications, ${unreadCount} unread`}
              aria-expanded={showDropdown}
            >
              <span aria-hidden="true">🔔</span>

              {unreadCount > 0 && (
                <span className="notification-count">
                  {unreadCount > 99 ? "99+" : unreadCount}
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

          <button
            type="button"
            className="navbar-link navbar-logout"
            onClick={handleLogout}
          >
            <span aria-hidden="true">↪️</span>
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}

export default Navbar;

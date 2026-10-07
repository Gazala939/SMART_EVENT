function NotificationDropdown({
  notifications,
  onMarkAsRead,
  onViewAll,
}) {
  return (
    <div className="notification-dropdown">

      <h3>Notifications</h3>

      {notifications.length === 0 ? (
        <p className="no-notifications">
          No notifications
        </p>
      ) : (
        notifications.slice(0, 5).map((notification) => (
          <div
            key={notification.id}
            className={`dropdown-notification ${
              notification.is_read ? "read" : "unread"
            }`}
          >
            <strong>{notification.title}</strong>

            <p>{notification.message}</p>

            {!notification.is_read && (
              <button
                onClick={() =>
                  onMarkAsRead(notification.id)
                }
              >
                Mark as Read
              </button>
            )}
          </div>
        ))
      )}

      <button
        className="view-all-button"
        onClick={onViewAll}
      >
        View All Notifications
      </button>

    </div>
  );
}

export default NotificationDropdown;
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";


function Profile() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [summary, setSummary] = useState(null);

  const [formData, setFormData] = useState({
    username: "",
    email: "",
    location: "",
  });

  const [selectedPicture, setSelectedPicture] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const fetchProfile = useCallback(async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      navigate("/login");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const [profileResponse, summaryResponse] = await Promise.all([
        api.get("/auth/profile"),
        api.get("/auth/profile/summary"),
      ]);

      const profile = profileResponse.data;

      setUser(profile);
      setFormData({
        username: profile.username || "",
        email: profile.email || "",
        location: profile.location || "",
      });

      setSummary(summaryResponse.data);
    } catch (err) {
      console.error("Unable to load profile:", err);

      if (err.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/login");
        return;
      }

      setError(
        err.response?.data?.detail ||
          "Unable to load your profile. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleSaveProfile = async (event) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");
      setMessage("");

      const response = await api.put("/auth/profile", {
        username: formData.username.trim(),
        email: formData.email.trim(),
        location: formData.location.trim(),
      });

      setUser(response.data);
      setFormData({
        username: response.data.username || "",
        email: response.data.email || "",
        location: response.data.location || "",
      });

      setMessage("Profile updated successfully.");
    } catch (err) {
      console.error("Unable to update profile:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to update your profile. Please try again."
      );
    } finally {
      setSaving(false);
    }
  };

  const handlePictureChange = (event) => {
    const file = event.target.files?.[0];

    setSelectedPicture(null);
    setError("");
    setMessage("");

    if (!file) return;

    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

    if (!allowedTypes.includes(file.type)) {
      setError("Choose a JPG, PNG, or WEBP image.");
      event.target.value = "";
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("The profile picture must be 5 MB or smaller.");
      event.target.value = "";
      return;
    }

    setSelectedPicture(file);
  };

  const handleUploadPicture = async () => {
    if (!selectedPicture) {
      setError("Please choose a picture first.");
      return;
    }

    try {
      setUploading(true);
      setError("");
      setMessage("");

      const form = new FormData();
      form.append("picture", selectedPicture);

      const response = await api.post(
        "/auth/profile/picture",
        form
      );

      setUser(response.data);
      setSelectedPicture(null);
      setMessage("Profile picture updated successfully.");
    } catch (err) {
      console.error("Unable to upload profile picture:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to upload your picture. Please try again."
      );
    } finally {
      setUploading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  if (loading) {
    return (
      <main className="profile-container">
        <p>Loading your profile...</p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="profile-container">
        <h2>Unable to load profile</h2>
        {error && <p className="profile-error">{error}</p>}

        <button type="button" onClick={fetchProfile}>
          Try Again
        </button>
      </main>
    );
  }

  const pictureUrl = user.profile_picture
    ? user.profile_picture.startsWith("http")
      ? user.profile_picture
      : `http://127.0.0.1:8000${user.profile_picture}`
    : "";

  return (
    <main className="profile-container">
      <header className="profile-header">
        <div>
          <h1>SMART_EVENT</h1>
          <p>Manage your account and event activity.</p>
        </div>

        <button
          type="button"
          className="logout-button"
          onClick={logout}
        >
          Logout
        </button>
      </header>

      <section className="profile-card">
        <h2>My Profile</h2>

        {error && <p className="profile-error">{error}</p>}
        {message && <p className="profile-success">{message}</p>}

        <div className="profile-picture-section">
          {pictureUrl ? (
            <img
              className="profile-picture"
              src={pictureUrl}
              alt="Profile"
            />
          ) : (
            <div className="profile-picture-placeholder">
              {user.username?.charAt(0).toUpperCase() || "U"}
            </div>
          )}

          <div className="profile-picture-controls">
            <label htmlFor="profile-picture-input">
              Change profile picture
            </label>

            <input
              id="profile-picture-input"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handlePictureChange}
            />

            {selectedPicture && (
              <>
                <p>{selectedPicture.name}</p>
                <button
                  type="button"
                  onClick={handleUploadPicture}
                  disabled={uploading}
                >
                  {uploading ? "Uploading..." : "Upload Picture"}
                </button>
              </>
            )}

            <small>JPG, PNG, or WEBP · Maximum 5 MB</small>
          </div>
        </div>

        <div className="profile-account-info">
          <p><strong>User ID:</strong> {user.id}</p>
          <p><strong>Role:</strong> {user.role}</p>
        </div>

        <form onSubmit={handleSaveProfile} className="profile-form">
          <label htmlFor="profile-username">Username</label>
          <input
            id="profile-username"
            name="username"
            type="text"
            minLength={3}
            maxLength={50}
            value={formData.username}
            onChange={handleChange}
            required
          />

          <label htmlFor="profile-email">Email</label>
          <input
            id="profile-email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            required
          />

          <label htmlFor="profile-location">
            Preferred Location
          </label>
          <input
            id="profile-location"
            name="location"
            type="text"
            maxLength={200}
            placeholder="e.g. Pune"
            value={formData.location}
            onChange={handleChange}
          />

          <small>
            Your preferred location helps personalize event recommendations.
          </small>

          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save Profile"}
          </button>
        </form>
      </section>

      <section className="profile-summary">
        <h2>My Booking Activity</h2>

        {summary ? (
          <div className="profile-summary-grid">
            <article className="profile-stat">
              <span>Total Bookings</span>
              <strong>{summary.total_bookings}</strong>
            </article>

            <article className="profile-stat">
              <span>Confirmed Bookings</span>
              <strong>{summary.confirmed_bookings}</strong>
            </article>

            <article className="profile-stat">
              <span>Cancelled Bookings</span>
              <strong>{summary.cancelled_bookings}</strong>
            </article>

            <article className="profile-stat">
              <span>Tickets Booked</span>
              <strong>{summary.total_tickets}</strong>
            </article>

            <article className="profile-stat">
              <span>Total Spent</span>
              <strong>
                ₹{Number(summary.total_spent || 0).toLocaleString("en-IN")}
              </strong>
            </article>
          </div>
        ) : (
          <p>Booking summary is unavailable.</p>
        )}

        <button
          type="button"
          className="profile-history-button"
          onClick={() => navigate("/booking-history")}
        >
          View Booking History
        </button>
      </section>
    </main>
  );
}

export default Profile;
import { useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";


function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);

      // Step 1: Login and get JWT token
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      const token = response.data.access_token;

      // Save token
      localStorage.setItem("token", token);

      // Step 2: Get user profile
      const profileResponse = await api.get("/auth/profile");
      const user = profileResponse.data;

      const role = String(user.role || "").toUpperCase();

      if (!["USER", "ORGANIZER", "ADMIN"].includes(role)) {
        localStorage.removeItem("token");
        localStorage.removeItem("role");
        localStorage.removeItem("user_id");

        alert("Your account role could not be verified.");
        return;
      }

      // Step 3: Save user ID and role
      if (user.id == null) {
        localStorage.removeItem("token");
        localStorage.removeItem("role");
        localStorage.removeItem("user_id");

        alert("User ID was not found in your profile response.");
        return;
      }

      localStorage.setItem("user_id", String(user.id));
      localStorage.setItem("role", role);

      alert("Login successful!");

      // Step 4: Redirect according to role
      if (role === "ADMIN") {
        navigate("/admin/dashboard");
      } else if (role === "ORGANIZER") {
        navigate("/organizer/dashboard");
      } else {
        navigate("/home");
      }
    } catch (error) {
      localStorage.removeItem("token");
      localStorage.removeItem("role");
      localStorage.removeItem("user_id");

      alert(
        error.response?.data?.detail ||
          "Login failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-brand-icon">🎟️</div>

        <h1 className="login-brand">SMART_EVENT</h1>
        <p className="login-tagline">
          Discover events. Create memories.
        </p>

        <div className="login-heading">
          <h2>Welcome Back!</h2>
          <p>Sign in to continue to your account.</p>
        </div>

        <form className="login-form" onSubmit={handleLogin}>
          <label htmlFor="login-email">Email Address</label>
          <input
            id="login-email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />

          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />

          <button
            className="login-submit-button"
            type="submit"
            disabled={loading}
          >
            {loading ? "Logging in..." : "Login to Your Account"}
          </button>
        </form>

        <p className="login-register-text">
          Don't have an account?{" "}
          <button
            className="login-register-button"
            type="button"
            onClick={() => navigate("/register")}
          >
            Register
          </button>
        </p>
      </section>
    </main>
  );
}

export default Login;
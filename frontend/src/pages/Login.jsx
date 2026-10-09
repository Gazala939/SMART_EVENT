
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

      // Step 1: Login and get the JWT token
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      const token = response.data.access_token;

      // Save token so api.js can attach it to protected requests
      localStorage.setItem("token", token);

      // Step 2: Get the logged-in user's profile
      const profileResponse = await api.get("/auth/profile");

      const role = String(
        profileResponse.data.role || ""
      ).toUpperCase();

      if (!["USER", "ORGANIZER", "ADMIN"].includes(role)) {
        localStorage.removeItem("token");
        localStorage.removeItem("role");

        alert("Your account role could not be verified.");
        return;
      }

      // Step 3: Save the user's role
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

      alert(
        error.response?.data?.detail ||
          "Login failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>SMART_EVENT</h1>

      <h2>Login</h2>

      <form onSubmit={handleLogin}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <br />
        <br />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <br />
        <br />

        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>

      <p>
        Don't have an account?{" "}
        <button
          type="button"
          onClick={() => navigate("/register")}
        >
          Register
        </button>
      </p>
    </div>
  );
}

export default Login;
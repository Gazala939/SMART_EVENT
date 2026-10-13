
import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";


function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);

      await axios.post("http://127.0.0.1:8000/auth/register", {
        username: username,
        email: email,
        password: password,
      });

      alert("Registration successful!");
      navigate("/login");
    } catch (error) {
      alert(
        error.response?.data?.detail || "Registration failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="register-page">
      <section className="register-card">
        <div className="register-brand-icon">🎟️</div>

        <h1 className="register-brand">SMART_EVENT</h1>

        <p className="register-tagline">
          Discover events. Create memories.
        </p>

        <div className="register-heading">
          <h2>Create Your Account</h2>
          <p>Join SmartEvent and start exploring events.</p>
        </div>

        <form className="register-form" onSubmit={handleRegister}>
          <label htmlFor="register-username">Username</label>
          <input
            id="register-username"
            type="text"
            placeholder="Choose a username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
            minLength={3}
          />

          <label htmlFor="register-email">Email Address</label>
          <input
            id="register-email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />

          <label htmlFor="register-password">Password</label>
          <input
            id="register-password"
            type="password"
            placeholder="Create a password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            minLength={6}
            required
          />

          <button
            className="register-submit-button"
            type="submit"
            disabled={loading}
          >
            {loading ? "Creating Account..." : "Create Account"}
          </button>
        </form>

        <p className="register-login-text">
          Already have an account?{" "}
          <button
            className="register-login-button"
            type="button"
            onClick={() => navigate("/login")}
          >
            Login
          </button>
        </p>
      </section>
    </main>
  );
}

export default Register;

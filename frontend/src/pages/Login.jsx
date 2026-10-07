import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/auth/login",
        {
          email: email,
          password: password,
        }
      );

      localStorage.setItem(
        "token",
        response.data.access_token
      );

      alert("Login successful!");

      navigate("/home");
    } catch (error) {
      alert(
        error.response?.data?.detail || "Login failed"
      );
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
        />

        <br />
        <br />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <br />
        <br />

        <button type="submit">
          Login
        </button>
      </form>

      <p>
        Don't have an account?{" "}
        <button onClick={() => navigate("/register")}>
          Register
        </button>
      </p>
    </div>
  );
}

export default Login;
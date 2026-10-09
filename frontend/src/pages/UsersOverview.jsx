
import { useEffect, useState } from "react";
import axios from "axios";

function UsersOverview() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("token");

      const response = await axios.get(
        "http://127.0.0.1:8000/admin/users",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setUsers(
        Array.isArray(response.data)
          ? response.data
          : response.data.users || []
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load users. Check the admin API endpoint."
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <h2>Loading Users...</h2>;
  }

  return (
    <div className="admin-dashboard">
      <h1>Users Overview</h1>
      <p>Total users: {users.length}</p>

      {error && (
        <div>
          <p>{error}</p>
          <button onClick={fetchUsers}>Retry</button>
        </div>
      )}

      {!error && users.length === 0 && (
        <p>No users found.</p>
      )}

      {!error && users.length > 0 && (
        <div className="admin-table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Registered At</th>
              </tr>
            </thead>

            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>{user.username}</td>
                  <td>{user.email}</td>
                  <td>{user.role || "USER"}</td>
                  <td>
                    {user.created_at
                      ? new Date(user.created_at).toLocaleDateString()
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default UsersOverview;


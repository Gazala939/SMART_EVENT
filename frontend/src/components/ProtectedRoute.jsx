
import { Navigate } from "react-router-dom";

function ProtectedRoute({ children, allowedRoles }) {
  const token = localStorage.getItem("token");

  // Check whether the user is logged in
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Read the logged-in user's role
  const userRole = (
    localStorage.getItem("role") || ""
  ).toUpperCase();

  // Check whether the user's role is allowed
  if (
    allowedRoles &&
    !allowedRoles.map((role) => role.toUpperCase()).includes(userRole)
  ) {
    return <Navigate to="/home" replace />;
  }

  return children;
}

export default ProtectedRoute;


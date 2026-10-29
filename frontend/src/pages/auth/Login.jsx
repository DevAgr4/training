import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  loginWithMicrosoft,
  getCurrentUser,
} from "../../services/authService";

function Login() {
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        await getCurrentUser();
        setAuthenticated(true);
      } catch (error) {
        setAuthenticated(false);
      } finally {
        setCheckingAuth(false);
      }
    };

    checkAuthentication();
  }, []);

  if (checkingAuth) {
    return (
      <div className="login-page">
        <div className="login-card">
          <p>Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (authenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="login-page">
      <div className="login-card">

        <div className="login-logo">
          TR
        </div>

        <h1>Training Reminder System</h1>

        <p className="login-subtitle">
          Manage training schedules and automate
          reminders from one place.
        </p>

        <button
          className="microsoft-button"
          onClick={loginWithMicrosoft}
        >
          <span className="microsoft-logo">
            ⊞
          </span>

          Continue with Microsoft
        </button>

        <p className="login-footer">
          Authorized HR personnel only
        </p>

      </div>
    </div>
  );
}

export default Login;
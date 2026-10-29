import { useState } from "react";

function Topbar({ onLogout }) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <header className="topbar">
      <div>
        <h1>Training Reminder System</h1>
        <p>Training management and automated reminders</p>
      </div>

      <div className="topbar-user-wrapper">
        <button
          type="button"
          className="topbar-user"
          onClick={() => setShowMenu((prev) => !prev)}
        >
          <div className="user-avatar">
            N
          </div>

          <div className="user-info">
            <strong>Nisha</strong>
            <span>HR Administrator</span>
          </div>

          <span className="dropdown-arrow">
            {showMenu ? "⌃" : "⌄"}
          </span>
        </button>

        {showMenu && (
          <div className="user-dropdown">
            <button
              type="button"
              className="logout-button"
              onClick={onLogout}
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Topbar;
import { NavLink } from "react-router-dom";

function Sidebar() {
  const menuItems = [
    {
      name: "Dashboard",
      path: "/dashboard",
      icon: "▦",
    },
    {
      name: "Training Calendar",
      path: "/calendar",
      icon: "▣",
    },
    {
      name: "Trainings",
      path: "/trainings",
      icon: "◫",
    },
    {
      name: "Reminders",
      path: "/reminders",
      icon: "◷",
    },
    {
      name: "WhatsApp Templates",
      path: "/reminders/templates",
      icon: "◉",
    },
    {
      name: "Post Training",
      path: "/post-training",
      icon: "✓",
    },
    {
      name: "Reports",
      path: "/reports",
      icon: "▥",
    },
    {
      name: "Excel Import",
      path: "/excel-import",
      icon: "⇧",
    },
  ];

  return (
    <aside className="sidebar">

      {/* =========================================
          BRAND
      ========================================= */}

      <div className="sidebar-brand">
        <div className="brand-icon">
          TR
        </div>

        <div>
          <h2>Training</h2>
          <span>Reminder System</span>
        </div>
      </div>

      {/* =========================================
          MAIN NAVIGATION
      ========================================= */}

      <nav className="sidebar-nav">

        <p className="nav-section-title">
          MAIN MENU
        </p>

        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${
                isActive ? "active" : ""
              }`
            }
          >
            <span className="nav-icon">
              {item.icon}
            </span>

            <span>
              {item.name}
            </span>
          </NavLink>
        ))}

      </nav>

      {/* =========================================
          SETTINGS
      ========================================= */}

      <div className="sidebar-bottom">

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `nav-item ${
              isActive ? "active" : ""
            }`
          }
        >
          <span className="nav-icon">
            ⚙
          </span>

          <span>
            Settings
          </span>
        </NavLink>

      </div>

    </aside>
  );
}

export default Sidebar;
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTrainings } from "../../services/trainingService";

function Dashboard() {
  const [trainings, setTrainings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      // getTrainings() already returns the training array
      const data = await getTrainings();

      console.log("Dashboard training data:", data);

      if (Array.isArray(data)) {
        setTrainings(data);
      } else {
        console.warn(
          "Unexpected trainings response:",
          data
        );
        setTrainings([]);
      }
    } catch (error) {
      console.error(
        "Failed to load trainings:",
        error
      );

      setError(
        "Unable to load training data."
      );

      setTrainings([]);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // STATUS COUNTS
  // ============================================================

  const total = trainings.length;

  const completed = trainings.filter(
    (training) =>
      String(training.status || "").toUpperCase() ===
      "COMPLETED"
  ).length;

  const pending = trainings.filter(
    (training) =>
      String(training.status || "").toUpperCase() ===
      "PENDING"
  ).length;

  const rescheduled = trainings.filter(
    (training) =>
      String(training.status || "").toUpperCase() ===
      "RESCHEDULED"
  ).length;

  const notConducted = trainings.filter(
    (training) =>
      String(training.status || "").toUpperCase() ===
      "NOT_CONDUCTED"
  ).length;

  return (
    <div className="dashboard">

      {/* ==========================================
          PAGE HEADER
      ========================================== */}

      <div className="page-header">
        <div>
          <h2>Dashboard</h2>

          <p>
            Welcome back. Here's your training overview.
          </p>
        </div>

        <Link
          to="/trainings/create"
          className="primary-button"
        >
          + Add Training
        </Link>
      </div>


      {/* ==========================================
          ERROR
      ========================================== */}

      {error && (
        <div className="empty-state">
          {error}
        </div>
      )}


      {/* ==========================================
          STATISTICS
      ========================================== */}

      <div className="stats-grid">

        {/* TOTAL */}

        <div className="stat-card">
          <span className="stat-label">
            Total Trainings
          </span>

          <strong className="stat-value">
            {loading ? "..." : total}
          </strong>
        </div>


        {/* COMPLETED */}

        <div className="stat-card">
          <span className="stat-label">
            Completed
          </span>

          <strong className="stat-value">
            {loading ? "..." : completed}
          </strong>
        </div>


        {/* PENDING */}

        <div className="stat-card">
          <span className="stat-label">
            Pending Actions
          </span>

          <strong className="stat-value">
            {loading ? "..." : pending}
          </strong>
        </div>


        {/* RESCHEDULED */}

        <div className="stat-card">
          <span className="stat-label">
            Rescheduled
          </span>

          <strong className="stat-value">
            {loading ? "..." : rescheduled}
          </strong>
        </div>

      </div>


      {/* ==========================================
          ADDITIONAL STATUS SUMMARY
      ========================================== */}

      {!loading && trainings.length > 0 && (
        <div className="dashboard-section">

          <div className="section-header">
            <div>
              <h3>Training Status</h3>

              <p>
                Current training status summary
              </p>
            </div>
          </div>


          <div className="stats-grid">

            {/* COMPLETED */}

            <div className="stat-card">
              <span className="stat-label">
                Completed
              </span>

              <strong className="stat-value">
                {completed}
              </strong>
            </div>


            {/* PENDING */}

            <div className="stat-card">
              <span className="stat-label">
                Pending
              </span>

              <strong className="stat-value">
                {pending}
              </strong>
            </div>


            {/* NOT CONDUCTED */}

            <div className="stat-card">
              <span className="stat-label">
                Not Conducted
              </span>

              <strong className="stat-value">
                {notConducted}
              </strong>
            </div>


            {/* RESCHEDULED */}

            <div className="stat-card">
              <span className="stat-label">
                Rescheduled
              </span>

              <strong className="stat-value">
                {rescheduled}
              </strong>
            </div>

          </div>

        </div>
      )}


      {/* ==========================================
          RECENT TRAININGS
      ========================================== */}

      <div className="dashboard-section">

        <div className="section-header">

          <div>
            <h3>Recent Trainings</h3>

            <p>
              Latest training schedules
            </p>
          </div>

          <Link
            to="/trainings"
            className="view-link"
          >
            View All
          </Link>

        </div>


        {/* LOADING */}

        {loading ? (
          <div className="empty-state">
            Loading trainings...
          </div>

        ) : trainings.length === 0 ? (

          /* EMPTY */

          <div className="empty-state">
            No trainings available.
          </div>

        ) : (

          /* TABLE */

          <div className="training-table">

            {/* TABLE HEADER */}

            <div className="table-header">
              <span>Training</span>
              <span>Department</span>
              <span>Date</span>
              <span>Status</span>
            </div>


            {/* TABLE ROWS */}

            {trainings
              .slice(0, 8)
              .map((training) => (
                <div
                  className="table-row"
                  key={training.id}
                >

                  {/* TRAINING */}

                  <span>
                    {training.training_name || "-"}
                  </span>


                  {/* DEPARTMENT */}

                  <span>
                    {training.department_name ||
                      `Department ${
                        training.department_id || "-"
                      }`}
                  </span>


                  {/* DATE */}

                  <span>
                    {formatDate(
                      training.scheduled_date
                    )}
                  </span>


                  {/* STATUS */}

                  <span>
                    <StatusBadge
                      status={training.status}
                    />
                  </span>

                </div>
              ))}

          </div>
        )}

      </div>

    </div>
  );
}


/* ==========================================
   STATUS BADGE
========================================== */

function StatusBadge({ status }) {
  const normalized =
    String(status || "unknown").toLowerCase();

  return (
    <span
      className={`status-badge ${normalized}`}
    >
      {status || "Unknown"}
    </span>
  );
}


/* ==========================================
   DATE FORMAT
========================================== */

function formatDate(date) {
  if (!date) {
    return "-";
  }

  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) {
    return date;
  }

  return parsedDate.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}


export default Dashboard;
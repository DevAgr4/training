import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTrainings } from "../../services/trainingService";

function Trainings() {
  const [trainings, setTrainings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadTrainings();
  }, []);

  const loadTrainings = async () => {
    try {
      setLoading(true);
      setError("");

      // getTrainings() already returns the training array
      const data = await getTrainings();

      console.log("Trainings data:", data);

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

      setError("Unable to load trainings.");
      setTrainings([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>

      {/* ==========================================
          PAGE HEADER
      ========================================== */}

      <div className="page-header">

        <div>
          <h2>Trainings</h2>

          <p>
            Manage training schedules.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: "10px",
            alignItems: "center",
          }}
        >

          <button
            type="button"
            className="secondary-button"
            onClick={loadTrainings}
            disabled={loading}
          >
            {loading
              ? "Refreshing..."
              : "Refresh"}
          </button>

          <Link
            to="/trainings/create"
            className="primary-button"
          >
            + Add Training
          </Link>

        </div>

      </div>


      {/* ==========================================
          SUMMARY
      ========================================== */}

      {!loading && !error && (
        <div
          style={{
            marginBottom: "16px",
            fontSize: "14px",
            color: "#6b7280",
          }}
        >
          {trainings.length}{" "}
          {trainings.length === 1
            ? "training"
            : "trainings"}{" "}
          found
        </div>
      )}


      {/* ==========================================
          ERROR
      ========================================== */}

      {error && (
        <div className="empty-state">

          <p>{error}</p>

          <button
            type="button"
            className="primary-button"
            onClick={loadTrainings}
          >
            Try Again
          </button>

        </div>
      )}


      {/* ==========================================
          TRAINING TABLE
      ========================================== */}

      {!error && (
        <div className="training-table">

          {/* TABLE HEADER */}

          <div className="table-header">

            <span>ID</span>

            <span>Training</span>

            <span>Type</span>

            <span>Date</span>

            <span>Status</span>

            <span>Action</span>

          </div>


          {/* LOADING */}

          {loading ? (

            <div className="empty-state">
              Loading trainings...
            </div>

          ) : trainings.length === 0 ? (

            /* EMPTY */

            <div className="empty-state">
              No trainings found.
            </div>

          ) : (

            /* TRAININGS */

            trainings.map((training) => (

              <div
                className="table-row"
                key={training.id}
              >

                {/* ID */}

                <span>
                  <strong>
                    #{training.id}
                  </strong>
                </span>


                {/* TRAINING NAME */}

                <span>
                  <strong>
                    {training.training_name || "-"}
                  </strong>
                </span>


                {/* TYPE */}

                <span>
                  {training.training_type || "-"}
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


                {/* ACTION */}

                <span>
                  <Link
                    to={`/trainings/${training.id}`}
                    className="view-link"
                  >
                    View
                  </Link>
                </span>

              </div>

            ))

          )}

        </div>
      )}

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

  return parsedDate.toLocaleDateString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  );
}


export default Trainings;
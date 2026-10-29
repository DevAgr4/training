import { useEffect, useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  getTraining,
  rescheduleTraining,
} from "../../services/trainingService";

import "./TrainingDetails.css";

function TrainingDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [training, setTraining] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Rescheduling state
  const [showRescheduleForm, setShowRescheduleForm] =
    useState(false);
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");
  const [rescheduleReason, setRescheduleReason] =
    useState("");
  const [rescheduling, setRescheduling] = useState(false);
  const [rescheduleError, setRescheduleError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    loadTraining();
  }, [id]);

  const loadTraining = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getTraining(id);

      console.log("Training details:", data);

      if (data) {
        setTraining(data);
      } else {
        setTraining(null);
        setError("Training not found.");
      }
    } catch (err) {
      console.error("Failed to load training:", err);

      setError("Unable to load training details.");
      setTraining(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReschedule = async (event) => {
    event.preventDefault();

    setRescheduleError("");
    setSuccessMessage("");

    if (!newDate) {
      setRescheduleError("Please select a new training date.");
      return;
    }

    if (!rescheduleReason.trim()) {
      setRescheduleError(
        "Please enter a reason for rescheduling."
      );
      return;
    }

    // Do not allow a date earlier than today.
    const today = getLocalDateString();

    if (newDate < today) {
      setRescheduleError(
        "The new training date cannot be in the past."
      );
      return;
    }

    try {
      setRescheduling(true);

      const payload = {
        new_date: newDate,
        new_time: newTime || null,
        reason: rescheduleReason.trim(),
      };

      await rescheduleTraining(id, payload);

      setSuccessMessage(
        "Training rescheduled successfully."
      );

      setShowRescheduleForm(false);
      setNewDate("");
      setNewTime("");
      setRescheduleReason("");

      await loadTraining();
    } catch (err) {
      console.error("Failed to reschedule training:", err);

      const detail = err.response?.data?.detail;

      setRescheduleError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : "Unable to reschedule training. Please try again."
      );
    } finally {
      setRescheduling(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="training-details-page">
        <div className="page-header">
          <div>
            <h2>Training Details</h2>
            <p>Loading training information...</p>
          </div>
        </div>

        <div className="empty-state">Loading...</div>
      </div>
    );
  }

  // Error / not found
  if (error || !training) {
    return (
      <div className="training-details-page">
        <div className="page-header">
          <div>
            <h2>Training Details</h2>
            <p>Training ID: #{id}</p>
          </div>
        </div>

        <div className="empty-state">
          <p>{error || "Training not found."}</p>

          <button
            type="button"
            className="primary-button"
            onClick={() => navigate("/trainings")}
          >
            Back to Trainings
          </button>
        </div>
      </div>
    );
  }

  const isNotConducted =
    String(training.status || "").toUpperCase() ===
    "NOT_CONDUCTED";

  return (
    <div className="training-details-page">
      {/* HEADER */}
      <div className="page-header">
        <div>
          <h2>
            {training.training_name || "Training Details"}
          </h2>

          <p>Training ID: #{training.id}</p>
        </div>

        <Link
          to="/trainings"
          className="secondary-button"
        >
          ← Back to Trainings
        </Link>
      </div>

      {successMessage && (
        <div
          className="reschedule-success"
          role="status"
        >
          {successMessage}
        </div>
      )}

      {/* STATUS */}
      <div className="dashboard-section">
        <div className="section-header">
          <div>
            <h3>Training Status</h3>
            <p>Current status of this training</p>
          </div>

          <StatusBadge status={training.status} />
        </div>
      </div>

      {/* TRAINING INFORMATION */}
      <div className="dashboard-section">
        <div className="section-header">
          <div>
            <h3>Training Information</h3>
            <p>Schedule and training details</p>
          </div>
        </div>

        <div className="details-grid">
          <DetailItem
            label="Training ID"
            value={`#${training.id}`}
          />

          <DetailItem
            label="Training Name"
            value={training.training_name}
          />

          <DetailItem
            label="Training Type"
            value={training.training_type}
          />

          <DetailItem
            label="Department"
            value={
              training.department_name ||
              training.department_id
            }
          />

          <DetailItem
            label="Target Audience"
            value={
              training.audience_name ||
              training.audience_id
            }
          />

          <DetailItem
            label="Training From"
            value={formatDate(training.scheduled_date)}
          />

          <DetailItem
            label="Training To"
            value={formatDate(training.training_to_date)}
          />

          <DetailItem
            label="Training Time"
            value={formatTime(training.scheduled_time)}
          />

          <DetailItem
            label="Duration"
            value={
              training.duration_hours !== null &&
              training.duration_hours !== undefined
                ? `${training.duration_hours} hour(s)`
                : "-"
            }
          />

          <DetailItem
            label="Venue"
            value={training.venue}
          />

          <DetailItem
            label="Trainer"
            value={training.trainer_name}
          />
        </div>
      </div>

      {/* REQUIREMENTS */}
      <div className="dashboard-section">
        <div className="section-header">
          <div>
            <h3>Requirements</h3>
            <p>Training configuration</p>
          </div>
        </div>

        <div className="details-grid">
          <DetailItem
            label="Department Wise"
            value={formatBoolean(
              training.is_department_wise
            )}
          />

          <DetailItem
            label="Attendance Required"
            value={formatBoolean(
              training.attendance_required
            )}
          />

          <DetailItem
            label="OJT Required"
            value={formatBoolean(training.ojt_required)}
          />
        </div>
      </div>

      {/* RESCHEDULE INFORMATION */}
      {(String(training.status || "").toUpperCase() ===
        "RESCHEDULED" ||
        training.rescheduled_date) && (
        <div className="dashboard-section">
          <div className="section-header">
            <div>
              <h3>Reschedule Information</h3>
              <p>Previous and current schedule</p>
            </div>
          </div>

          <div className="details-grid">
            <DetailItem
              label="Original Date"
              value={formatDate(training.original_date)}
            />

            <DetailItem
              label="Rescheduled Date"
              value={formatDate(training.rescheduled_date)}
            />

            <DetailItem
              label="Reschedule Reason"
              value={training.reschedule_reason}
            />
          </div>
        </div>
      )}

      {/* NOT CONDUCTED INFORMATION */}
      {isNotConducted && (
        <div className="dashboard-section">
          <div className="section-header">
            <div>
              <h3>Not Conducted</h3>
              <p>Reason provided by HR</p>
            </div>
          </div>

          <div className="reason-box">
            {training.not_conducted_reason ||
              "No reason provided."}
          </div>
        </div>
      )}

      {/* RESCHEDULE ACTION - ONLY FOR NOT CONDUCTED */}
      {isNotConducted && (
        <div className="dashboard-section">
          <div className="section-header">
            <div>
              <h3>Reschedule Training</h3>
              <p>
                Choose a new date and provide a reason to
                schedule this training again.
              </p>
            </div>

            {!showRescheduleForm && (
              <button
                type="button"
                className="primary-button"
                onClick={() => {
                  setRescheduleError("");
                  setSuccessMessage("");
                  setShowRescheduleForm(true);
                }}
              >
                Reschedule Training
              </button>
            )}
          </div>

          {showRescheduleForm && (
            <form
              className="reschedule-form"
              onSubmit={handleReschedule}
            >
              {rescheduleError && (
                <div
                  className="reschedule-error"
                  role="alert"
                >
                  {rescheduleError}
                </div>
              )}

              <div className="reschedule-form-grid">
                <div className="reschedule-field">
                  <label htmlFor="reschedule-date">
                    New Training Date *
                  </label>

                  <input
                    id="reschedule-date"
                    type="date"
                    value={newDate}
                    min={getLocalDateString()}
                    onChange={(event) =>
                      setNewDate(event.target.value)
                    }
                    required
                    disabled={rescheduling}
                  />
                </div>

                <div className="reschedule-field">
                  <label htmlFor="reschedule-time">
                    New Training Time (optional)
                  </label>

                  <input
                    id="reschedule-time"
                    type="time"
                    value={newTime}
                    onChange={(event) =>
                      setNewTime(event.target.value)
                    }
                    disabled={rescheduling}
                  />
                </div>

                <div className="reschedule-field reschedule-reason-field">
                  <label htmlFor="reschedule-reason">
                    Reason for Rescheduling *
                  </label>

                  <textarea
                    id="reschedule-reason"
                    value={rescheduleReason}
                    onChange={(event) =>
                      setRescheduleReason(event.target.value)
                    }
                    placeholder="Explain why the training needs to be rescheduled..."
                    rows={4}
                    maxLength={1000}
                    required
                    disabled={rescheduling}
                  />
                </div>
              </div>

              <div className="reschedule-form-actions">
                <button
                  type="submit"
                  className="primary-button"
                  disabled={rescheduling}
                >
                  {rescheduling
                    ? "Rescheduling..."
                    : "Confirm Reschedule"}
                </button>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setShowRescheduleForm(false);
                    setRescheduleError("");
                    setNewDate("");
                    setNewTime("");
                    setRescheduleReason("");
                  }}
                  disabled={rescheduling}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* ACTIONS */}
      <div className="details-actions">
        <Link
          to="/trainings"
          className="secondary-button"
        >
          Back
        </Link>

        {!isNotConducted && (
          <Link
            to={`/post-training?trainingId=${training.id}`}
            className="primary-button"
          >
            Post Training
          </Link>
        )}
      </div>
    </div>
  );
}

// DETAIL ITEM
function DetailItem({ label, value }) {
  return (
    <div className="detail-item">
      <span className="detail-label">{label}</span>

      <strong className="detail-value">
        {value !== null &&
        value !== undefined &&
        value !== ""
          ? value
          : "-"}
      </strong>
    </div>
  );
}

// STATUS BADGE
function StatusBadge({ status }) {
  const normalized = String(status || "UNKNOWN")
    .toLowerCase()
    .replace(/\s+/g, "_");

  const label = String(status || "Unknown").replaceAll(
    "_",
    " "
  );

  return (
    <span className={`status-badge ${normalized}`}>
      {label}
    </span>
  );
}

// DATE
function formatDate(date) {
  if (!date) {
    return "-";
  }

  // Avoid timezone shifts for YYYY-MM-DD values.
  const dateString = String(date);

  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    const [year, month, day] = dateString
      .split("-")
      .map(Number);

    return new Date(year, month - 1, day).toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "long",
        year: "numeric",
      }
    );
  }

  const parsedDate = new Date(dateString);

  if (Number.isNaN(parsedDate.getTime())) {
    return dateString;
  }

  return parsedDate.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

// TIME
function formatTime(time) {
  if (!time) {
    return "-";
  }

  const parts = String(time).split(":");

  if (parts.length < 2) {
    return time;
  }

  const hours = Number(parts[0]);
  const minutes = Number(parts[1]);

  if (
    Number.isNaN(hours) ||
    Number.isNaN(minutes)
  ) {
    return time;
  }

  const date = new Date();
  date.setHours(hours, minutes, 0, 0);

  return date.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// BOOLEAN
function formatBoolean(value) {
  if (value === true) {
    return "Yes";
  }

  if (value === false) {
    return "No";
  }

  return "-";
}

// LOCAL DATE STRING FOR DATE INPUTS
function getLocalDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(
    2,
    "0"
  );
  const day = String(now.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

export default TrainingDetails;
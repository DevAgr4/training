
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createTraining } from "../../services/trainingService";
import { getDepartments } from "../../services/departmentService";
import api from "../../services/api";

import "./CreateTraining.css";

function CreateTraining() {
  const navigate = useNavigate();

  const [departments, setDepartments] = useState([]);
  const [audiences, setAudiences] = useState([]);

  const [loadingDepartments, setLoadingDepartments] = useState(true);
  const [loadingAudiences, setLoadingAudiences] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    training_name: "",
    training_type: "",
    department_id: "",
    audience_id: "",
    scheduled_date: "",
    training_to_date: "",
    scheduled_time: "",
    duration_hours: "",
    venue: "",
    trainer_name: "",
    is_department_wise: false,
    attendance_required: true,
    ojt_required: false,
  });

  useEffect(() => {
    loadDepartments();
    loadAudiences();
  }, []);

  // ==========================================================
  // NORMALIZE API RESPONSES
  // Supports Axios response, response body, array, and { value }
  // ==========================================================

  const normalizeList = (response) => {
    const body = response?.data ?? response;

    if (Array.isArray(body)) {
      return body;
    }

    if (Array.isArray(body?.value)) {
      return body.value;
    }

    return [];
  };

  // ==========================================================
  // DEPARTMENTS
  // ==========================================================

  const loadDepartments = async () => {
    try {
      setLoadingDepartments(true);

      const response = await getDepartments();
      const list = normalizeList(response);

      const validDepartments = list
        .filter(
          (department) =>
            department?.id !== null &&
            department?.id !== undefined &&
            typeof department.name === "string" &&
            department.name.trim() !== ""
        )
        .sort((a, b) =>
          a.name.localeCompare(b.name)
        );

      setDepartments(validDepartments);

      if (validDepartments.length === 0) {
        console.warn(
          "No departments returned by GET /api/departments:",
          response
        );
      }

      setForm((previous) => {
        const selectedExists = validDepartments.some(
          (department) =>
            String(department.id) === String(previous.department_id)
        );

        return {
          ...previous,
          department_id: selectedExists
            ? previous.department_id
            : "",
        };
      });
    } catch (err) {
      console.error("Failed to load departments:", err);
      setDepartments([]);
      setError(
        "Unable to load departments. Check the backend and try again."
      );
    } finally {
      setLoadingDepartments(false);
    }
  };

  // ==========================================================
  // TARGET AUDIENCES
  // ==========================================================

  const loadAudiences = async () => {
    try {
      setLoadingAudiences(true);

      const response = await api.get("/recipients/audiences");
      const list = normalizeList(response);

      setAudiences(
        list.filter(
          (audience) =>
            audience?.id !== null &&
            audience?.id !== undefined
        )
      );
    } catch (err) {
      console.error("Failed to load target audiences:", err);
      setAudiences([]);
      setError(
        "Unable to load target audiences. Check the backend and try again."
      );
    } finally {
      setLoadingAudiences(false);
    }
  };

  // ==========================================================
  // FORM CHANGES
  // ==========================================================

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));

    setError("");
    setSuccess("");
  };

  // ==========================================================
  // ERROR FORMATTER
  // ==========================================================

  const getErrorMessage = (err) => {
    const detail = err?.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => item.msg || "Validation error")
        .join(", ");
    }

    return "An unexpected error occurred. Please try again.";
  };

  // ==========================================================
  // SUBMIT
  // ==========================================================

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!form.training_name.trim()) {
      setError("Training name is required.");
      return;
    }

    if (!form.training_type) {
      setError("Please select a training type.");
      return;
    }

    if (!form.department_id) {
      setError("Please select a department.");
      return;
    }

    if (!form.audience_id) {
      setError("Please select a target audience.");
      return;
    }

    if (!form.scheduled_date) {
      setError("Training start date is required.");
      return;
    }

    if (
      form.training_to_date &&
      form.training_to_date < form.scheduled_date
    ) {
      setError(
        "Training end date cannot be before the start date."
      );
      return;
    }

    if (!form.scheduled_time) {
      setError("Training time is required.");
      return;
    }

    try {
      setSubmitting(true);

      const payload = {
        training_name: form.training_name.trim(),
        training_type: form.training_type,
        department_id: Number(form.department_id),
        audience_id: Number(form.audience_id),
        scheduled_date: form.scheduled_date,
        training_to_date: form.training_to_date || null,
        scheduled_time: form.scheduled_time,
        duration_hours: form.duration_hours
          ? Number(form.duration_hours)
          : null,
        venue: form.venue.trim() || null,
        trainer_name: form.trainer_name.trim() || null,
        is_department_wise: form.is_department_wise,
        attendance_required: form.attendance_required,
        ojt_required: form.ojt_required,
      };

      const response = await createTraining(payload);

      // The service may return an Axios response or its body.
      const data = response?.data ?? response;

      setSuccess("Training created successfully.");

      const trainingId =
        data?.id ??
        data?.training?.id ??
        data?.training_id;

      if (trainingId !== undefined && trainingId !== null) {
        navigate(`/trainings/${trainingId}`);
      } else {
        navigate("/trainings");
      }
    } catch (err) {
      console.error("Training creation failed:", err);
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="create-training-page">
      <div className="page-header">
        <div>
          <h2>Add Training</h2>
          <p>Create a new training schedule.</p>
        </div>
      </div>

      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="form-success" role="status">
          {success}
        </div>
      )}

      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          {/* TRAINING NAME */}
          <div className="form-group">
            <label htmlFor="training_name">Training Name</label>
            <input
              id="training_name"
              name="training_name"
              type="text"
              value={form.training_name}
              onChange={handleChange}
              placeholder="e.g. Workplace Safety"
              required
            />
          </div>

          {/* TRAINING TYPE */}
          <div className="form-group">
            <label htmlFor="training_type">Training Type</label>
            <select
              id="training_type"
              name="training_type"
              value={form.training_type}
              onChange={handleChange}
              required
            >
              <option value="">Select training type</option>
              <option value="Safety">Safety</option>
              <option value="Leadership">Leadership</option>
              <option value="Technical">Technical</option>
              <option value="Compliance">Compliance</option>
              <option value="Soft Skills">Soft Skills</option>
              <option value="Other">Other</option>
            </select>
          </div>

          {/* DEPARTMENT */}
          <div className="form-group">
            <label htmlFor="department_id">Department</label>

            <select
              id="department_id"
              name="department_id"
              value={form.department_id}
              onChange={handleChange}
              required
              disabled={
                loadingDepartments || departments.length === 0
              }
            >
              <option value="">
                {loadingDepartments
                  ? "Loading departments..."
                  : departments.length === 0
                    ? "No departments available"
                    : "Select department"}
              </option>

              {departments.map((department) => (
                <option
                  key={department.id}
                  value={department.id}
                >
                  {department.name}
                </option>
              ))}
            </select>

            {!loadingDepartments && departments.length === 0 && (
              <button
                type="button"
                className="secondary-button"
                onClick={loadDepartments}
                style={{ marginTop: "8px" }}
              >
                Retry loading departments
              </button>
            )}
          </div>

          {/* TARGET AUDIENCE */}
          <div className="form-group">
            <label htmlFor="audience_id">Target Audience</label>

            <select
              id="audience_id"
              name="audience_id"
              value={form.audience_id}
              onChange={handleChange}
              required
              disabled={loadingAudiences || audiences.length === 0}
            >
              <option value="">
                {loadingAudiences
                  ? "Loading target audiences..."
                  : audiences.length === 0
                    ? "No target audiences available"
                    : "Select target audience"}
              </option>

              {audiences.map((audience) => (
                <option key={audience.id} value={audience.id}>
                  {audience.name || audience.recipient_type || `Audience ${audience.id}`}
                </option>
              ))}
            </select>

            {!loadingAudiences && audiences.length === 0 && (
              <button
                type="button"
                className="secondary-button"
                onClick={loadAudiences}
                style={{ marginTop: "8px" }}
              >
                Retry loading audiences
              </button>
            )}
          </div>

          {/* START DATE */}
          <div className="form-group">
            <label htmlFor="scheduled_date">Training From Date</label>
            <input
              id="scheduled_date"
              type="date"
              name="scheduled_date"
              value={form.scheduled_date}
              onChange={handleChange}
              required
            />
          </div>

          {/* END DATE */}
          <div className="form-group">
            <label htmlFor="training_to_date">Training To Date</label>
            <input
              id="training_to_date"
              type="date"
              name="training_to_date"
              value={form.training_to_date}
              onChange={handleChange}
              min={form.scheduled_date || undefined}
            />
          </div>

          {/* TIME */}
          <div className="form-group">
            <label htmlFor="scheduled_time">Scheduled Time</label>
            <input
              id="scheduled_time"
              type="time"
              name="scheduled_time"
              value={form.scheduled_time}
              onChange={handleChange}
              required
            />
          </div>

          {/* DURATION */}
          <div className="form-group">
            <label htmlFor="duration_hours">Duration (Hours)</label>
            <input
              id="duration_hours"
              type="number"
              name="duration_hours"
              value={form.duration_hours}
              onChange={handleChange}
              placeholder="e.g. 2"
              min="0"
              step="0.5"
            />
          </div>

          {/* VENUE */}
          <div className="form-group">
            <label htmlFor="venue">Venue</label>
            <input
              id="venue"
              type="text"
              name="venue"
              value={form.venue}
              onChange={handleChange}
              placeholder="e.g. Conference Room"
            />
          </div>

          {/* TRAINER */}
          <div className="form-group">
            <label htmlFor="trainer_name">Trainer</label>
            <input
              id="trainer_name"
              type="text"
              name="trainer_name"
              value={form.trainer_name}
              onChange={handleChange}
              placeholder="e.g. Mrs Sita"
            />
          </div>
        </div>

        {/* REQUIREMENTS */}
        <div className="checkbox-section">
          <label>
            <input
              type="checkbox"
              name="is_department_wise"
              checked={form.is_department_wise}
              onChange={handleChange}
            />
            Department-wise training
          </label>

          <label>
            <input
              type="checkbox"
              name="attendance_required"
              checked={form.attendance_required}
              onChange={handleChange}
            />
            Attendance required
          </label>

          <label>
            <input
              type="checkbox"
              name="ojt_required"
              checked={form.ojt_required}
              onChange={handleChange}
            />
            OJT report required
          </label>
        </div>

        {/* ACTIONS */}
        <div className="form-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => navigate("/trainings")}
            disabled={submitting}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-button"
            disabled={
              submitting ||
              loadingDepartments ||
              loadingAudiences ||
              departments.length === 0 ||
              audiences.length === 0
            }
          >
            {submitting ? "Creating..." : "Create Training"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default CreateTraining;

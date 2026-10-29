import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  getPostTrainingStatus,
  markTrainingConducted,
  updateDocumentStatus,
} from "../../services/postTrainingService";

import "./PostTraining.css";


function PostTraining() {
  const [searchParams] = useSearchParams();

  const [trainingId, setTrainingId] = useState(
    searchParams.get("trainingId") || ""
  );

  const [data, setData] = useState(null);

  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] =
    useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [notConductedReason, setNotConductedReason] =
    useState("");


  // ==================================================
  // LOAD TRAINING STATUS
  // ==================================================

  const loadStatus = async (
    selectedTrainingId = trainingId
  ) => {
    if (!selectedTrainingId) {
      setError("Please enter a training ID.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSuccess("");

      const response =
        await getPostTrainingStatus(
          Number(selectedTrainingId)
        );

      setData(response.data);

    } catch (error) {
      console.error(
        "Failed to load post-training status:",
        error
      );

      setData(null);

      setError(
        error.response?.data?.detail ||
          "Failed to load training."
      );

    } finally {
      setLoading(false);
    }
  };


  // ==================================================
  // AUTO LOAD TRAINING FROM URL
  // ==================================================

  useEffect(() => {
    const queryTrainingId =
      searchParams.get("trainingId");

    if (queryTrainingId) {
      setTrainingId(queryTrainingId);
      loadStatus(queryTrainingId);
    }
  }, []);


  // ==================================================
  // MARK CONDUCTED
  // ==================================================

  const handleConducted = async () => {
    if (!trainingId) {
      setError("Please enter a training ID.");
      return;
    }

    try {
      setActionLoading(true);
      setError("");
      setSuccess("");

      await markTrainingConducted(
        Number(trainingId),
        {
          conducted: true,
        }
      );

      setSuccess(
        "Training marked as conducted successfully."
      );

      await loadStatus();

    } catch (error) {
      console.error(error);

      setError(
        error.response?.data?.detail ||
          "Failed to update training."
      );

    } finally {
      setActionLoading(false);
    }
  };


  // ==================================================
  // MARK NOT CONDUCTED
  // ==================================================

  const handleNotConducted = async () => {
    if (!trainingId) {
      setError("Please enter a training ID.");
      return;
    }

    if (!notConductedReason.trim()) {
      setError(
        "Please provide a reason for not conducting the training."
      );
      return;
    }

    try {
      setActionLoading(true);
      setError("");
      setSuccess("");

      await markTrainingConducted(
        Number(trainingId),
        {
          conducted: false,
          reason: notConductedReason,
        }
      );

      setSuccess(
        "Training marked as not conducted."
      );

      setNotConductedReason("");

      await loadStatus();

    } catch (error) {
      console.error(error);

      setError(
        error.response?.data?.detail ||
          "Failed to update training."
      );

    } finally {
      setActionLoading(false);
    }
  };


  // ==================================================
  // UPDATE DOCUMENT
  // ==================================================

  const updateDocument = async (
    documentType,
    status
  ) => {
    if (!trainingId) {
      setError("Please enter a training ID.");
      return;
    }

    try {
      setActionLoading(true);
      setError("");
      setSuccess("");

      await updateDocumentStatus(
        Number(trainingId),
        documentType,
        {
          status,
          received_via: "MANUAL",
        }
      );

      setSuccess(
        `${documentType
          .replace("_", " ")} status updated successfully.`
      );

      await loadStatus();

    } catch (error) {
      console.error(error);

      setError(
        error.response?.data?.detail ||
          "Failed to update document."
      );

    } finally {
      setActionLoading(false);
    }
  };


  // ==================================================
  // STATUS HELPERS
  // ==================================================

  const getStatusClass = (status) => {
    if (!status) return "";

    return status
      .toLowerCase()
      .replaceAll("_", "-");
  };


  const formatStatus = (status) => {
    if (!status) return "-";

    return status
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      );
  };


  // ==================================================
  // UI
  // ==================================================

  return (
    <div className="post-training-page">

      {/* ==========================================
          HEADER
      ========================================== */}

      <div className="page-header">

        <div>
          <h2>Post-Training</h2>

          <p>
            Track training completion, attendance
            and OJT reports.
          </p>
        </div>

      </div>


      {/* ==========================================
          TRAINING SEARCH
      ========================================== */}

      <div className="post-training-search">

        <div className="search-content">

          <div>

            <label>
              Training ID
            </label>

            <input
              type="number"
              min="1"
              placeholder="Enter training ID"
              value={trainingId}
              onChange={(e) => {
                setTrainingId(e.target.value);

                // Clear previously loaded training
                if (
                  e.target.value !==
                  String(trainingId)
                ) {
                  setData(null);
                }
              }}
            />

          </div>


          <button
            type="button"
            className="primary-button"
            onClick={() => loadStatus()}
            disabled={loading}
          >
            {loading
              ? "Loading..."
              : "Load Training"}
          </button>

        </div>

      </div>


      {/* ==========================================
          ERROR
      ========================================== */}

      {error && (
        <div className="post-training-alert error">
          {error}
        </div>
      )}


      {/* ==========================================
          SUCCESS
      ========================================== */}

      {success && (
        <div className="post-training-alert success">
          {success}
        </div>
      )}


      {/* ==========================================
          TRAINING DETAILS
      ========================================== */}

      {data && (
        <>

          {/* TRAINING OVERVIEW */}

          <div className="training-overview">

            <div>
              <span>Training</span>

              <strong>
                {data.training_name || "-"}
              </strong>
            </div>


            <div>
              <span>Training ID</span>

              <strong>
                #{trainingId}
              </strong>
            </div>


            <div>
              <span>Date</span>

              <strong>
                {data.scheduled_date || "-"}
              </strong>
            </div>


            <div>
              <span>Status</span>

              <span
                className={`training-status ${getStatusClass(
                  data.status
                )}`}
              >
                {formatStatus(data.status)}
              </span>
            </div>

          </div>


          {/* ========================================
              TRAINING COMPLETION
          ======================================== */}

          <div className="post-training-card">

            <div className="card-header">

              <div>

                <h3>
                  Training Completion
                </h3>

                <p>
                  Confirm whether the scheduled
                  training was conducted.
                </p>

              </div>

            </div>


            <div className="completion-actions">

              <button
                type="button"
                className="success-button"
                onClick={handleConducted}
                disabled={actionLoading}
              >
                ✓ Training Conducted
              </button>


              <button
                type="button"
                className="danger-button"
                onClick={handleNotConducted}
                disabled={actionLoading}
              >
                ✕ Not Conducted
              </button>

            </div>


            <div className="not-conducted-box">

              <label>
                Reason if training was not conducted
              </label>

              <textarea
                rows="3"
                placeholder="Enter reason..."
                value={notConductedReason}
                onChange={(e) =>
                  setNotConductedReason(
                    e.target.value
                  )
                }
              />

            </div>

          </div>


          {/* ========================================
              DOCUMENTS
          ======================================== */}

          <div className="document-grid">

            {/* ======================================
                ATTENDANCE
            ====================================== */}

            <div className="post-training-card">

              <div className="card-header">

                <div>

                  <h3>
                    Attendance
                  </h3>

                  <p>
                    Attendance submission status.
                  </p>

                </div>


                <span
                  className={`document-status ${getStatusClass(
                    data.attendance_status
                  )}`}
                >
                  {formatStatus(
                    data.attendance_status
                  )}
                </span>

              </div>


              {data.attendance_required ? (

                <div className="document-actions">

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      updateDocument(
                        "ATTENDANCE",
                        "RECEIVED"
                      )
                    }
                    disabled={actionLoading}
                  >
                    Mark Received
                  </button>


                  <button
                    type="button"
                    className="success-button"
                    onClick={() =>
                      updateDocument(
                        "ATTENDANCE",
                        "DONE"
                      )
                    }
                    disabled={actionLoading}
                  >
                    Mark Done
                  </button>

                </div>

              ) : (

                <div className="not-required">
                  Attendance not required.
                </div>

              )}

            </div>


            {/* ======================================
                OJT
            ====================================== */}

            <div className="post-training-card">

              <div className="card-header">

                <div>

                  <h3>
                    OJT Report
                  </h3>

                  <p>
                    OJT report submission status.
                  </p>

                </div>


                <span
                  className={`document-status ${getStatusClass(
                    data.ojt_status
                  )}`}
                >
                  {formatStatus(
                    data.ojt_status
                  )}
                </span>

              </div>


              {data.ojt_required ? (

                <div className="document-actions">

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      updateDocument(
                        "OJT_REPORT",
                        "RECEIVED"
                      )
                    }
                    disabled={actionLoading}
                  >
                    Mark Received
                  </button>


                  <button
                    type="button"
                    className="success-button"
                    onClick={() =>
                      updateDocument(
                        "OJT_REPORT",
                        "DONE"
                      )
                    }
                    disabled={actionLoading}
                  >
                    Mark Done
                  </button>

                </div>

              ) : (

                <div className="not-required">
                  OJT report not required.
                </div>

              )}

            </div>

          </div>

        </>
      )}

    </div>
  );
}

export default PostTraining;
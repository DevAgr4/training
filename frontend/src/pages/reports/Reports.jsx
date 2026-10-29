import { useEffect, useMemo, useState } from "react";
import api from "../../services/api";
import "./Reports.css";

function Reports() {
  const [departments, setDepartments] = useState([]);
  const [backendSummary, setBackendSummary] =
    useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ============================================================
  // LOAD REPORT
  // ============================================================

  const loadReport = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get(
        "/reports/department-wise"
      );

      const data = response.data;

      // --------------------------------------------------------
      // DEPARTMENT DATA
      // --------------------------------------------------------

      if (Array.isArray(data)) {
        setDepartments(data);
        setBackendSummary(null);
      } else if (Array.isArray(data?.value)) {
        setDepartments(data.value);

        // Backend may return consolidated summary
        if (data?.summary) {
          setBackendSummary(data.summary);
        } else {
          setBackendSummary(null);
        }
      } else {
        setDepartments([]);
        setBackendSummary(null);
      }
    } catch (err) {
      console.error(
        "Failed to load department report:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to load training reports."
      );

      setDepartments([]);
      setBackendSummary(null);
    } finally {
      setLoading(false);
    }
  };


  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {
    loadReport();
  }, []);


  // ============================================================
  // OVERALL SUMMARY
  // ============================================================

  const summary = useMemo(() => {
    // ----------------------------------------------------------
    // Prefer backend consolidated summary
    // ----------------------------------------------------------

    if (backendSummary) {
      return {
        total:
          Number(
            backendSummary.total_trainings
          ) || 0,

        completed:
          Number(
            backendSummary.completed_trainings
          ) || 0,

        pending:
          Number(
            backendSummary.pending_trainings
          ) || 0,

        notConducted:
          Number(
            backendSummary.not_conducted_trainings
          ) || 0,

        rescheduled:
          Number(
            backendSummary.rescheduled_trainings
          ) || 0,

        completion:
          Number(
            backendSummary.completion_percentage
          ) || 0,
      };
    }


    // ----------------------------------------------------------
    // Fallback calculation
    // ----------------------------------------------------------

    return departments.reduce(
      (accumulator, department) => {
        accumulator.total +=
          Number(
            department.total_trainings
          ) || 0;

        accumulator.completed +=
          Number(
            department.completed_trainings
          ) || 0;

        accumulator.pending +=
          Number(
            department.pending_trainings
          ) || 0;

        accumulator.notConducted +=
          Number(
            department.not_conducted_trainings
          ) || 0;

        accumulator.rescheduled +=
          Number(
            department.rescheduled_trainings
          ) || 0;

        return accumulator;
      },
      {
        total: 0,
        completed: 0,
        pending: 0,
        notConducted: 0,
        rescheduled: 0,
        completion: 0,
      }
    );
  }, [departments, backendSummary]);


  // ============================================================
  // OVERALL COMPLETION
  // ============================================================

  const overallCompletion =
    backendSummary
      ? Number(
          backendSummary.completion_percentage
        ) || 0
      : summary.total > 0
      ? (
          (summary.completed /
            summary.total) *
          100
        )
      : 0;


  // ============================================================
  // HELPERS
  // ============================================================

  const formatPercentage = (value) => {
    const percentage =
      Number(value) || 0;

    return `${percentage.toFixed(2)}%`;
  };


  const formatCount = (value) => {
    return Number(value) || 0;
  };


  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {
    return (
      <div className="reports-page">
        <div className="reports-empty">
          Loading reports...
        </div>
      </div>
    );
  }


  // ============================================================
  // PAGE
  // ============================================================

  return (
    <div className="reports-page">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <div className="reports-header">

        <div>
          <h2>
            Training Reports
          </h2>

          <p>
            Monitor training completion across
            departments.
          </p>
        </div>


        <button
          type="button"
          className="reports-refresh-button"
          onClick={loadReport}
          disabled={loading}
        >
          ↻ Refresh
        </button>

      </div>


      {/* ======================================================
          ERROR
      ====================================================== */}

      {error && (
        <div className="reports-alert">
          {error}
        </div>
      )}


      {/* ======================================================
          SUMMARY CARDS
      ====================================================== */}

      <div className="report-summary-grid">

        {/* TOTAL */}

        <div className="report-summary-card">

          <span>
            Total Trainings
          </span>

          <strong>
            {formatCount(
              summary.total
            )}
          </strong>

        </div>


        {/* COMPLETED */}

        <div className="report-summary-card completed">

          <span>
            Completed
          </span>

          <strong>
            {formatCount(
              summary.completed
            )}
          </strong>

        </div>


        {/* PENDING */}

        <div className="report-summary-card pending">

          <span>
            Pending
          </span>

          <strong>
            {formatCount(
              summary.pending
            )}
          </strong>

        </div>


        {/* NOT CONDUCTED */}

        <div className="report-summary-card not-conducted">

          <span>
            Not Conducted
          </span>

          <strong>
            {formatCount(
              summary.notConducted
            )}
          </strong>

        </div>


        {/* RESCHEDULED */}

        <div className="report-summary-card rescheduled">

          <span>
            Rescheduled
          </span>

          <strong>
            {formatCount(
              summary.rescheduled
            )}
          </strong>

        </div>


        {/* COMPLETION */}

        <div className="report-summary-card percentage">

          <span>
            Completion Rate
          </span>

          <strong>
            {formatPercentage(
              overallCompletion
            )}
          </strong>

        </div>

      </div>


      {/* ======================================================
          DEPARTMENT REPORT
      ====================================================== */}

      <div className="department-report-card">

        {/* SECTION HEADER */}

        <div className="report-section-header">

          <div>
            <h3>
              Department-wise Training Report
            </h3>

            <p>
              Training completion statistics
              for each department.
            </p>
          </div>


          <span className="department-count">
            {departments.length}{" "}
            {departments.length === 1
              ? "Department"
              : "Departments"}
          </span>

        </div>


        {/* ====================================================
            TABLE
        ==================================================== */}

        {departments.length === 0 ? (

          <div className="reports-empty">

            No department report data
            available.

          </div>

        ) : (

          <div className="department-table-wrapper">

            <table className="department-report-table">

              <thead>

                <tr>

                  <th>
                    ID
                  </th>

                  <th>
                    Department
                  </th>

                  <th>
                    Total
                  </th>

                  <th>
                    Completed
                  </th>

                  <th>
                    Pending
                  </th>

                  <th>
                    Not Conducted
                  </th>

                  <th>
                    Rescheduled
                  </th>

                  <th>
                    Completion
                  </th>

                </tr>

              </thead>


              <tbody>

                {departments.map(
                  (department) => {

                    const completion =
                      Math.min(
                        Math.max(
                          Number(
                            department.completion_percentage
                          ) || 0,
                          0
                        ),
                        100
                      );


                    return (
                      <tr
                        key={
                          department.department_id
                        }
                      >

                        {/* ID */}

                        <td>
                          #
                          {
                            department.department_id
                          }
                        </td>


                        {/* DEPARTMENT */}

                        <td>

                          <strong>
                            {
                              department.department_name ||
                              "Unknown Department"
                            }
                          </strong>

                        </td>


                        {/* TOTAL */}

                        <td>
                          {
                            formatCount(
                              department.total_trainings
                            )
                          }
                        </td>


                        {/* COMPLETED */}

                        <td>

                          <span className="count-badge completed">

                            {
                              formatCount(
                                department.completed_trainings
                              )
                            }

                          </span>

                        </td>


                        {/* PENDING */}

                        <td>

                          <span className="count-badge pending">

                            {
                              formatCount(
                                department.pending_trainings
                              )
                            }

                          </span>

                        </td>


                        {/* NOT CONDUCTED */}

                        <td>

                          <span className="count-badge not-conducted">

                            {
                              formatCount(
                                department.not_conducted_trainings
                              )
                            }

                          </span>

                        </td>


                        {/* RESCHEDULED */}

                        <td>

                          <span className="count-badge rescheduled">

                            {
                              formatCount(
                                department.rescheduled_trainings
                              )
                            }

                          </span>

                        </td>


                        {/* COMPLETION */}

                        <td>

                          <div className="completion-cell">

                            <div className="completion-bar">

                              <div
                                className="completion-fill"
                                style={{
                                  width: `${completion}%`,
                                }}
                              />

                            </div>


                            <span>
                              {
                                formatPercentage(
                                  department.completion_percentage
                                )
                              }
                            </span>

                          </div>

                        </td>

                      </tr>
                    );
                  }
                )}

              </tbody>

            </table>

          </div>

        )}

      </div>

    </div>
  );
}

export default Reports;
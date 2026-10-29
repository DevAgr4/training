import { useRef, useState } from "react";
import {
  uploadExcel,
  importExcel,
} from "../../services/excelService";
import "./ExcelImport.css";

function ExcelImport() {
  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState([]);
  const [errors, setErrors] = useState([]);
  const [summary, setSummary] = useState(null);

  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [dragging, setDragging] = useState(false);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;

    const validExtensions = [
      ".xlsx",
      ".xls",
    ];

    const extension =
      "." +
      selectedFile.name
        .split(".")
        .pop()
        .toLowerCase();

    if (!validExtensions.includes(extension)) {
      alert(
        "Please select an Excel file (.xlsx or .xls)."
      );
      return;
    }

    if (
      selectedFile.size >
      10 * 1024 * 1024
    ) {
      alert(
        "File size must be less than 10 MB."
      );
      return;
    }

    setFile(selectedFile);
    setPreview([]);
    setErrors([]);
    setSummary(null);
  };

  const handleFileChange = (event) => {
    handleFile(
      event.target.files?.[0]
    );
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);

    handleFile(
      event.dataTransfer.files?.[0]
    );
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleBrowse = () => {
    fileInputRef.current?.click();
  };

  const handleRemoveFile = () => {
    setFile(null);
    setPreview([]);
    setErrors([]);
    setSummary(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // ==========================================================
  // VALIDATION ERROR NORMALIZATION
  // ==========================================================

  const normalizeErrors = (
    data
  ) => {
    const result = [];

    if (
      Array.isArray(
        data?.missing_columns
      ) &&
      data.missing_columns.length > 0
    ) {
      result.push({
        field: "Missing Columns",
        message:
          "The following training-calendar columns are missing:",
        rows: [],
        missingColumns:
          data.missing_columns,
      });
    }

    if (
      Array.isArray(
        data?.errors
      ) &&
      data.errors.length > 0
    ) {
      result.push(
        ...data.errors
      );
    }

    if (result.length === 0) {
      result.push({
        field: "Error",
        message:
          data?.message ||
          "Excel validation failed.",
        rows: [],
      });
    }

    return result;
  };

  // ==========================================================
  // PREVIEW
  // ==========================================================

  const handlePreview = async () => {
    if (!file) {
      alert(
        "Please select an Excel file first."
      );
      return;
    }

    setLoading(true);
    setErrors([]);
    setPreview([]);
    setSummary(null);

    try {
      const response =
        await uploadExcel(file);

      const data =
        response.data;

      console.log(
        "Excel validation response:",
        data
      );

      if (!data.success) {
        setErrors(
          normalizeErrors(data)
        );
        return;
      }

      setPreview(
        data.preview || []
      );

    } catch (error) {
      console.error(
        "Excel validation failed:",
        error
      );

      console.error(
        "Backend response:",
        error.response?.data
      );

      const detail =
        error.response?.data?.detail;

      if (
        detail &&
        typeof detail === "object"
      ) {
        setErrors(
          normalizeErrors(
            detail
          )
        );
      } else {
        setErrors([
          {
            field: "Error",
            message:
              detail ||
              "Unable to validate Excel file.",
            rows: [],
          },
        ]);
      }

    } finally {
      setLoading(false);
    }
  };

  // ==========================================================
  // IMPORT
  // ==========================================================

  const handleImport = async () => {
    if (!file) {
      alert(
        "Please select an Excel file first."
      );
      return;
    }

    if (
      preview.length === 0
    ) {
      alert(
        "Please validate the Excel file before importing."
      );
      return;
    }

    const confirmed =
      window.confirm(
        "Are you sure you want to import this annual training calendar into the database?"
      );

    if (!confirmed) return;

    setImporting(true);
    setErrors([]);
    setSummary(null);

    try {
      const response =
        await importExcel(file);

      const data =
        response.data;

      if (data.success) {
        setSummary(data);
      } else {
        setErrors(
          normalizeErrors(data)
        );
      }

    } catch (error) {
      console.error(
        "Excel import failed:",
        error
      );

      const detail =
        error.response?.data?.detail;

      if (
        detail &&
        typeof detail === "object"
      ) {
        setErrors(
          normalizeErrors(
            detail
          )
        );
      } else {
        setErrors([
          {
            field: "Import Error",
            message:
              detail ||
              "Excel import failed.",
            rows: [],
          },
        ]);
      }

    } finally {
      setImporting(false);
    }
  };

  // ==========================================================
  // TEMPLATE
  // ==========================================================

  const downloadTemplate = () => {
    const link =
      document.createElement(
        "a"
      );

    link.href =
      "/templates/training_schedule_template.xlsx";

    link.download =
      "training_schedule_template.xlsx";

    document.body.appendChild(
      link
    );

    link.click();

    document.body.removeChild(
      link
    );
  };

  return (
    <div className="excel-import-page">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="excel-page-header">
        <div>
          <div className="excel-title-row">

            <div className="excel-title-icon">
              ↑
            </div>

            <div>
              <h2>
                Training Calendar Excel
              </h2>

              <p>
                Upload the annual training
                schedule.
              </p>
            </div>

          </div>
        </div>
      </div>

      {/* =====================================================
          STEPS
      ===================================================== */}

      <div className="import-steps">

        <div className="import-step active">
          <div className="step-number">
            1
          </div>

          <div>
            <strong>
              Select File
            </strong>

            <span>
              Choose your calendar
            </span>
          </div>
        </div>

        <div className="step-line" />

        <div
          className={`import-step ${
            preview.length > 0
              ? "active"
              : ""
          }`}
        >
          <div className="step-number">
            2
          </div>

          <div>
            <strong>
              Preview
            </strong>

            <span>
              Validate schedule
            </span>
          </div>
        </div>

        <div className="step-line" />

        <div
          className={`import-step ${
            summary
              ? "active"
              : ""
          }`}
        >
          <div className="step-number">
            3
          </div>

          <div>
            <strong>
              Import
            </strong>

            <span>
              Save to database
            </span>
          </div>
        </div>

      </div>

      {/* =====================================================
          MAIN GRID
      ===================================================== */}

      <div className="excel-content-grid">

        <div>

          {/* =================================================
              UPLOAD CARD
          ================================================= */}

          <div className="excel-upload-card">

            <div className="card-heading">
              <div>
                <h3>
                  Upload Training Calendar
                </h3>

                <p>
                  Upload the annual training
                  schedule containing the
                  required 11 columns.
                </p>
              </div>
            </div>

            {!file ? (

              <div
                className={`drop-zone ${
                  dragging
                    ? "dragging"
                    : ""
                }`}
                onDragOver={
                  handleDragOver
                }
                onDragLeave={
                  handleDragLeave
                }
                onDrop={
                  handleDrop
                }
                onClick={
                  handleBrowse
                }
              >

                <div className="upload-icon">
                  ↑
                </div>

                <h4>
                  Drop your Excel file here
                </h4>

                <p>
                  or click to browse
                  from your computer
                </p>

                <button
                  type="button"
                  className="browse-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleBrowse();
                  }}
                >
                  Choose Excel File
                </button>

                <span className="file-hint">
                  Supported formats:
                  .xlsx, .xls
                  <br />
                  Maximum size: 10 MB
                </span>

              </div>

            ) : (

              <div className="selected-file-card">

                <div className="file-icon">
                  XLS
                </div>

                <div className="file-details">

                  <strong>
                    {file.name}
                  </strong>

                  <span>
                    {(
                      file.size /
                      1024 /
                      1024
                    ).toFixed(2)}{" "}
                    MB
                  </span>

                </div>

                <button
                  type="button"
                  className="remove-file"
                  onClick={
                    handleRemoveFile
                  }
                >
                  ×
                </button>

              </div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={
                handleFileChange
              }
              hidden
            />

            {file && (

              <div className="excel-actions">

                <button
                  type="button"
                  className="secondary-button"
                  onClick={
                    handlePreview
                  }
                  disabled={loading}
                >
                  {loading
                    ? "Validating..."
                    : "Validate & Preview"}
                </button>

                <button
                  type="button"
                  className="primary-button"
                  onClick={
                    handleImport
                  }
                  disabled={
                    preview.length === 0 ||
                    importing
                  }
                >
                  {importing
                    ? "Importing..."
                    : "Import to Database"}
                </button>

              </div>
            )}

          </div>

          {/* =================================================
              ERRORS
          ================================================= */}

          {errors.length > 0 && (

            <div className="excel-error-card">

              <div className="message-icon">
                !
              </div>

              <div>

                <h3>
                  Validation / Import Errors
                </h3>

                {errors.map(
                  (
                    error,
                    index
                  ) => (

                    <div
                      className="error-item"
                      key={index}
                    >

                      <strong>
                        {error.field ||
                          "Error"}
                      </strong>

                      <p>
                        {error.message}
                      </p>

                      {error.missingColumns &&
                        error.missingColumns.length >
                          0 && (

                          <div className="error-list">

                            {error.missingColumns.map(
                              (
                                column
                              ) => (

                                <div
                                  key={
                                    column
                                  }
                                  className="error-column"
                                >
                                  • {column}
                                </div>

                              )
                            )}

                          </div>
                        )}

                      {error.rows &&
                        error.rows.length >
                          0 && (

                          <small>
                            Rows:{" "}
                            {error.rows.join(
                              ", "
                            )}
                          </small>
                        )}

                    </div>
                  )
                )}

              </div>

            </div>
          )}

          {/* =================================================
              PREVIEW
          ================================================= */}

          {preview.length > 0 && (

            <div className="excel-preview-card">

              <div className="preview-header">

                <div>

                  <h3>
                    Excel Preview
                  </h3>

                  <p>
                    Training calendar
                    validated successfully.
                  </p>

                </div>

                <span className="valid-badge">
                  ✓ Valid
                </span>

              </div>

              <div className="excel-table-wrapper">

                <table className="excel-table">

                  <thead>

                    <tr>

                      {Object.keys(
                        preview[0]
                      ).map(
                        (column) => (

                          <th key={column}>
                            {column}
                          </th>

                        )
                      )}

                    </tr>

                  </thead>

                  <tbody>

                    {preview.map(
                      (
                        row,
                        index
                      ) => (

                        <tr
                          key={index}
                        >

                          {Object.keys(
                            preview[0]
                          ).map(
                            (column) => (

                              <td
                                key={
                                  column
                                }
                              >
                                {String(
                                  row[
                                    column
                                  ] ?? ""
                                )}
                              </td>

                            )
                          )}

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            </div>
          )}

          {/* =================================================
              SUCCESS
          ================================================= */}

          {summary && (

            <div className="excel-success-card">

              <div className="success-icon">
                ✓
              </div>

              <div>

                <h3>
                  Import Successful
                </h3>

                <p>
                  The annual training
                  calendar has been
                  imported successfully.
                </p>

              </div>

              <div className="summary-grid">

                <div>
                  <span>
                    Rows Imported
                  </span>

                  <strong>
                    {
                      summary.imported_rows
                    }
                  </strong>
                </div>

                <div>
                  <span>
                    Departments
                  </span>

                  <strong>
                    {
                      summary.created_departments
                    }
                  </strong>
                </div>

                <div>
                  <span>
                    Trainings Created
                  </span>

                  <strong>
                    {
                      summary.created_trainings
                    }
                  </strong>
                </div>

                <div>
                  <span>
                    Trainings Updated
                  </span>

                  <strong>
                    {
                      summary.updated_trainings
                    }
                  </strong>
                </div>

                <div>
                  <span>
                    Reminders
                  </span>

                  <strong>
                    {
                      summary.reminders_created
                    }
                  </strong>
                </div>

              </div>

              {summary.reminder_errors?.length >
                0 && (

                <div className="error-item">

                  <strong>
                    Reminder generation
                    warnings
                  </strong>

                  <p>
                    Some reminders could
                    not be generated.
                  </p>

                </div>
              )}

            </div>
          )}

        </div>

        {/* =====================================================
            RIGHT SIDE
        ===================================================== */}

        <div>

          <div className="excel-info-card">

            <div className="info-card-header">

              <div className="info-icon">
                i
              </div>

              <div>

                <h3>
                  Training Calendar Format
                </h3>

                <p>
                  The annual calendar must
                  contain these columns.
                </p>

              </div>

            </div>

            <div className="requirements">

              <div>
                <span>✓</span>
                <p>
                  S.No
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Training From Date
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Training To Date
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Day
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Training Topic
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Training Type
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Target Audience
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Trainer's Name
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Timing
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Duration
                </p>
              </div>

              <div>
                <span>✓</span>
                <p>
                  Venue
                </p>
              </div>

            </div>

            <button
              type="button"
              className="template-button"
              onClick={
                downloadTemplate
              }
            >
              ↓ Download Excel Template
            </button>

          </div>

          {/* =================================================
              RECIPIENT INFORMATION
          ================================================= */}

          <div className="excel-info-card">

            <h3>
              HOD & Line Manager
            </h3>

            <p>
              HOD and Line Manager details
              are not entered in the training
              calendar.
            </p>

            <div className="workflow">

              <div className="workflow-item">

                <div>1</div>

                <p>
                  Maintain HOD and Line
                  Manager details in
                  Settings.
                </p>

              </div>

              <div className="workflow-item">

                <div>2</div>

                <p>
                  Associate recipients
                  with their Department ID.
                </p>

              </div>

              <div className="workflow-item">

                <div>3</div>

                <p>
                  Import the training
                  calendar.
                </p>

              </div>

              <div className="workflow-item">

                <div>4</div>

                <p>
                  Reminder engine resolves
                  the recipients.
                </p>

              </div>

            </div>

          </div>

        </div>

      </div>

    </div>
  );
}

export default ExcelImport;
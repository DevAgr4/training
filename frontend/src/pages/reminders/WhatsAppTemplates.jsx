import { useEffect, useMemo, useState } from "react";
import {
  getWhatsAppTemplates,
  updateWhatsAppTemplate,
} from "../../services/whatsappTemplateService";
import "./WhatsAppTemplates.css";

const TEMPLATE_TYPES = [
  {
    value: "TRAINING_REMINDER",
    label: "Training Reminder",
  },
  {
    value: "ATTENDANCE_REMINDER",
    label: "Attendance Reminder",
  },
  {
    value: "OJT_REPORT_REMINDER",
    label: "OJT Report Reminder",
  },
  {
    value: "TRAINING_REPORT_REMINDER",
    label: "Training Report Reminder",
  },
  {
    value: "TRAINING_PERCENTAGE_REPORT",
    label: "Training Percentage Report",
  },
];

const VARIABLES = [
  "{{name}}",
  "{{training_name}}",
  "{{date}}",
  "{{time}}",
  "{{trainer}}",
  "{{department}}",
  "{{deadline}}",
  "{{completion_percentage}}",
  "{{pending_count}}",
];

function WhatsAppTemplates() {
  const [templates, setTemplates] = useState([]);

  const [selectedType, setSelectedType] = useState(
    "TRAINING_REMINDER"
  );

  const [message, setMessage] = useState("");
  const [name, setName] = useState("");
  const [metaTemplateName, setMetaTemplateName] =
    useState("");
  const [languageCode, setLanguageCode] =
    useState("en_US");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const selectedTemplate = useMemo(() => {
    return templates.find(
      (template) =>
        template.template_type === selectedType
    );
  }, [templates, selectedType]);

  // ============================================
  // LOAD TEMPLATES
  // ============================================

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await getWhatsAppTemplates();

      const data = response.data;

      if (Array.isArray(data)) {
        setTemplates(data);
      } else if (Array.isArray(data?.value)) {
        setTemplates(data.value);
      } else {
        setTemplates([]);
      }
    } catch (err) {
      console.error(
        "Failed to load WhatsApp templates:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to load WhatsApp templates."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // INITIAL LOAD
  // ============================================

  useEffect(() => {
    loadTemplates();
  }, []);

  // ============================================
  // LOAD SELECTED TEMPLATE INTO FORM
  // ============================================

  useEffect(() => {
    if (!selectedTemplate) {
      setName("");
      setMessage("");
      setMetaTemplateName("");
      setLanguageCode("en_US");
      return;
    }

    setName(selectedTemplate.name || "");

    setMessage(
      selectedTemplate.message || ""
    );

    setMetaTemplateName(
      selectedTemplate.meta_template_name || ""
    );

    setLanguageCode(
      selectedTemplate.language_code || "en_US"
    );
  }, [selectedTemplate]);

  // ============================================
  // SAVE
  // ============================================

  const handleSave = async () => {
    if (!selectedTemplate) {
      setError(
        "Template not found in the database."
      );
      return;
    }

    if (!name.trim()) {
      setError("Template name is required.");
      return;
    }

    if (!message.trim()) {
      setError("Message is required.");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const response =
        await updateWhatsAppTemplate(
          selectedTemplate.id,
          {
            name: name.trim(),
            message: message.trim(),
            meta_template_name:
              metaTemplateName.trim(),
            language_code: languageCode,

            // Preserve existing values.
            is_default:
              selectedTemplate.is_default,
            is_active:
              selectedTemplate.is_active,
          }
        );

      const updatedTemplate =
        response.data?.value ||
        response.data;

      setTemplates((current) =>
        current.map((template) =>
          template.id === selectedTemplate.id
            ? {
                ...template,
                ...updatedTemplate,
              }
            : template
        )
      );

      setSuccess(
        "WhatsApp template saved successfully."
      );
    } catch (err) {
      console.error(
        "Failed to save template:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to save template."
      );
    } finally {
      setSaving(false);
    }
  };

  // ============================================
  // PREVIEW
  // ============================================

  const getPreview = () => {
    let preview = message;

    const values = {
      "{{name}}": "Anita Rao",
      "{{training_name}}": "Workplace Safety",
      "{{date}}": "22 September 2026",
      "{{time}}": "10:00 AM",
      "{{trainer}}": "Mrs Sita",
      "{{department}}": "Human Resources",
      "{{deadline}}": "23 September 2026",
      "{{completion_percentage}}": "75%",
      "{{pending_count}}": "2",
    };

    Object.entries(values).forEach(
      ([variable, value]) => {
        preview = preview.replaceAll(
          variable,
          value
        );
      }
    );

    return preview;
  };

  // ============================================
  // INSERT VARIABLE
  // ============================================

  const insertVariable = (variable) => {
    setMessage((current) =>
      current
        ? `${current} ${variable}`
        : variable
    );
  };

  // ============================================
  // STATUS
  // ============================================

  const getStatus = (template) => {
    if (
      template.template_type ===
      "TRAINING_REMINDER"
    ) {
      return {
        label: "Under Review",
        className: "review-badge",
      };
    }

    if (template.is_active) {
      return {
        label: "Active",
        className: "active-badge",
      };
    }

    return {
      label: "Inactive",
      className: "inactive-badge",
    };
  };

  // ============================================
  // LOADING
  // ============================================

  if (loading) {
    return (
      <div className="page-container">
        <div className="empty-state">
          Loading WhatsApp templates...
        </div>
      </div>
    );
  }

  // ============================================
  // PAGE
  // ============================================

  return (
    <div className="page-container whatsapp-templates-page">

      {/* HEADER */}

      <div className="page-header">

        <div>
          <h2>WhatsApp Templates</h2>

          <p>
            Manage automated WhatsApp reminder
            messages.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadTemplates}
          disabled={loading}
        >
          ↻ Refresh
        </button>

      </div>

      {/* ERROR */}

      {error && (
        <div className="alert error-alert">
          {error}
        </div>
      )}

      {/* SUCCESS */}

      {success && (
        <div className="alert success-alert">
          {success}
        </div>
      )}

      {/* META INFO */}

      <div className="template-info-box">

        <strong>
          WhatsApp / Meta status
        </strong>

        <p>
          The Training Reminder template is
          currently under Meta review. It will
          become available for WhatsApp delivery
          after Meta approves the template.
        </p>

      </div>

      <div className="template-layout">

        {/* ======================================
            LEFT
        ====================================== */}

        <div className="template-list-card">

          <h3>Template Types</h3>

          <div className="template-type-list">

            {TEMPLATE_TYPES.map((type) => {

              const template =
                templates.find(
                  (item) =>
                    item.template_type ===
                    type.value
                );

              const status = template
                ? getStatus(template)
                : null;

              return (
                <button
                  type="button"
                  key={type.value}
                  className={
                    selectedType ===
                    type.value
                      ? "template-type active"
                      : "template-type"
                  }
                  onClick={() => {
                    setSelectedType(
                      type.value
                    );
                    setError("");
                    setSuccess("");
                  }}
                >

                  <span>
                    {type.label}
                  </span>

                  <div className="template-list-badges">

                    {template?.is_default && (
                      <span className="default-badge">
                        Default
                      </span>
                    )}

                    {status && (
                      <span
                        className={
                          `mini-status ${status.className}`
                        }
                      >
                        {status.label}
                      </span>
                    )}

                  </div>

                </button>
              );
            })}

          </div>

        </div>

        {/* ======================================
            RIGHT
        ====================================== */}

        <div className="template-editor-card">

          {!selectedTemplate ? (

            <div className="empty-state">

              <h3>
                Template Not Found
              </h3>

              <p>
                This template type does not
                currently exist in the database.
              </p>

            </div>

          ) : (

            <>
              {/* EDITOR HEADER */}

              <div className="editor-header">

                <div>

                  <h3>
                    {
                      TEMPLATE_TYPES.find(
                        (item) =>
                          item.value ===
                          selectedType
                      )?.label
                    }
                  </h3>

                  <p>
                    Configure the default message
                    used by the reminder engine.
                  </p>

                </div>

                <span
                  className={
                    `template-status-badge ${
                      getStatus(
                        selectedTemplate
                      ).className
                    }`
                  }
                >
                  {
                    getStatus(
                      selectedTemplate
                    ).label
                  }
                </span>

              </div>

              {/* TEMPLATE NAME */}

              <div className="form-group">

                <label>
                  Template Name
                </label>

                <input
                  value={name}
                  onChange={(event) =>
                    setName(
                      event.target.value
                    )
                  }
                  placeholder="Training Reminder"
                />

              </div>

              {/* META + LANGUAGE */}

              <div className="form-row">

                <div className="form-group">

                  <label>
                    Meta Template Name
                  </label>

                  <input
                    value={metaTemplateName}
                    onChange={(event) =>
                      setMetaTemplateName(
                        event.target.value
                      )
                    }
                    placeholder="training_reminder"
                  />

                </div>

                <div className="form-group">

                  <label>
                    Language
                  </label>

                  <select
                    value={languageCode}
                    onChange={(event) =>
                      setLanguageCode(
                        event.target.value
                      )
                    }
                  >

                    <option value="en_US">
                      English (US)
                    </option>

                    <option value="en_GB">
                      English (UK)
                    </option>

                  </select>

                </div>

              </div>

              {/* MESSAGE */}

              <div className="form-group">

                <label>
                  Message
                </label>

                <textarea
                  rows="10"
                  value={message}
                  onChange={(event) =>
                    setMessage(
                      event.target.value
                    )
                  }
                  placeholder="Write your WhatsApp message..."
                />

              </div>

              {/* VARIABLES */}

              <div className="variables-section">

                <label>
                  Available Variables
                </label>

                <div className="variable-list">

                  {VARIABLES.map(
                    (variable) => (
                      <button
                        type="button"
                        key={variable}
                        className="variable-chip"
                        onClick={() =>
                          insertVariable(
                            variable
                          )
                        }
                      >
                        {variable}
                      </button>
                    )
                  )}

                </div>

              </div>

              {/* PREVIEW */}

              <div className="preview-section">

                <h4>
                  Message Preview
                </h4>

                <div className="whatsapp-preview">

                  <div className="preview-header">
                    HR Team
                  </div>

                  <div className="preview-message">
                    {getPreview() ||
                      "No message configured."}
                  </div>

                </div>

              </div>

              {/* ACTION */}

              <div className="editor-actions">

                <button
                  type="button"
                  className="primary-button"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : "Save Template"}
                </button>

              </div>
            </>
          )}

        </div>

      </div>
    </div>
  );
}

export default WhatsAppTemplates;
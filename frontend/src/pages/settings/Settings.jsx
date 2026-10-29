import { useEffect, useState } from "react";

import {
  getReminderConfigs,
  createReminderConfig,
  updateReminderConfig,
  deleteReminderConfig,
  getReminderRecipients,
  addReminderRecipient,
  deleteReminderRecipient,
  getHODs,
  getLineManagers,
  getMasterRecipients,
  updateHOD,
  updateLineManager,
  deleteHOD,
  deleteLineManager,
  uploadMasterRecipients,
} from "../../services/reminderConfigService";

import "./Settings.css";
import api from "../../services/api";

// =========================================================
// CONSTANTS
// =========================================================

const reminderTypes = [
  "BEFORE_TRAINING",
  "POST_TRAINING",
  "DOCUMENT_SUBMISSION",
  "MONTHLY",
  "WEEKLY",
];

const recipientTypes = [
  "HOD",
  "LINE_MANAGER",
];

const channels = [
  "EMAIL",
  "WHATSAPP",
];

// =========================================================
// ERROR HELPER
// =========================================================

const getErrorMessage = (
  err,
  fallback = "Something went wrong."
) => {
  const detail = err?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (detail && typeof detail === "object") {
    if (
      Array.isArray(detail.missing_columns) &&
      detail.missing_columns.length > 0
    ) {
      return `${detail.message || "Required columns are missing"}: ${detail.missing_columns.join(
        ", "
      )}`;
    }

    if (Array.isArray(detail.errors) && detail.errors.length > 0) {
      return detail.errors
        .map((item) => {
          if (typeof item === "string") {
            return item;
          }

          if (item?.row && item?.error) {
            return `Row ${item.row}: ${item.error}`;
          }

          return item?.message || JSON.stringify(item);
        })
        .join("\n");
    }

    if (detail.message) {
      return detail.message;
    }

    try {
      return JSON.stringify(detail);
    } catch {
      return fallback;
    }
  }

  if (typeof err?.response?.data?.message === "string") {
    return err.response.data.message;
  }

  if (typeof err?.message === "string") {
    return err.message;
  }

  return fallback;
};

// =========================================================
// COMPONENT
// =========================================================

function Settings() {
  // =======================================================
  // REMINDER CONFIGURATION STATE
  // =======================================================

  const [configs, setConfigs] = useState([]);
  const [selectedConfig, setSelectedConfig] = useState(null);

  const [form, setForm] = useState({
    name: "",
    reminder_type: "BEFORE_TRAINING",
    days_before: 2,
    send_time: "09:00",
    enabled: true,
  });

  const [editing, setEditing] = useState(false);

  // =======================================================
  // RECIPIENT STATE
  // =======================================================

  const [recipients, setRecipients] = useState([]);
  const [hods, setHods] = useState([]);
  const [lineManagers, setLineManagers] = useState([]);

  const [recipientForm, setRecipientForm] = useState({
    recipient_type: "HOD",
    recipient_id: "",
    channel: "EMAIL",
  });

  const [showRecipientForm, setShowRecipientForm] =
    useState(false);

  const [recipientLoading, setRecipientLoading] =
    useState(false);

  // =======================================================
  // MASTER DATA STATE
  // =======================================================

  const [masterRecipients, setMasterRecipients] =
    useState([]);

  const [targetAudiences, setTargetAudiences] =
    useState([]);

  const [masterLoading, setMasterLoading] =
    useState(false);

  const [masterFile, setMasterFile] =
    useState(null);

  const [uploadingMaster, setUploadingMaster] =
    useState(false);

  const [editingRecipient, setEditingRecipient] =
    useState(null);

  const [editForm, setEditForm] = useState({
    name: "",
    email: "",
    whatsapp_number: "",
    target_audience: "",
  });

  const [masterMessage, setMasterMessage] =
    useState("");

  const [masterError, setMasterError] =
    useState("");

  // =======================================================
  // GENERAL STATE
  // =======================================================

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // =======================================================
  // LOAD CONFIGURATIONS
  // =======================================================

  const loadConfigs = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await getReminderConfigs();

      const data = Array.isArray(response.data)
        ? response.data
        : response.data?.value || [];

      setConfigs(data);

      if (data.length > 0) {
        const firstConfig = data[0];

        setSelectedConfig(firstConfig);
        setFormFromConfig(firstConfig);

        await loadRecipients(firstConfig.id);
      } else {
        setSelectedConfig(null);
        setRecipients([]);
      }
    } catch (err) {
      console.error(
        "Failed to load reminder configurations:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Failed to load reminder configurations."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  // =======================================================
  // LOAD TARGET AUDIENCES
  // =======================================================

  const loadTargetAudiences = async () => {
    try {
      const response = await api.get(
        "/recipients/audiences"
      );

      const data = Array.isArray(response.data)
        ? response.data
        : response.data?.value || [];

      setTargetAudiences(data);
    } catch (err) {
      console.error(
        "Failed to load target audiences:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Failed to load target audiences."
        )
      );
    }
  };

  // =======================================================
  // LOAD HOD / LINE MANAGER OPTIONS
  // =======================================================

  const loadRecipientOptions = async () => {
    try {
      const [
        hodResponse,
        managerResponse,
      ] = await Promise.all([
        getHODs(),
        getLineManagers(),
      ]);

      const hodData = Array.isArray(hodResponse.data)
        ? hodResponse.data
        : hodResponse.data?.value || [];

      const managerData = Array.isArray(
        managerResponse.data
      )
        ? managerResponse.data
        : managerResponse.data?.value || [];

      setHods(hodData);
      setLineManagers(managerData);
    } catch (err) {
      console.error(
        "Failed to load recipient options:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Failed to load HOD and Line Manager options."
        )
      );
    }
  };

  // =======================================================
  // LOAD MASTER RECIPIENTS
  // =======================================================

  const loadMasterRecipients = async () => {
    try {
      setMasterLoading(true);
      setMasterError("");

      const response =
        await getMasterRecipients();

      const data = Array.isArray(response.data)
        ? response.data
        : response.data?.value || [];

      setMasterRecipients(data);
    } catch (err) {
      console.error(
        "Failed to load master recipients:",
        err
      );

      setMasterError(
        getErrorMessage(
          err,
          "Failed to load master recipient data."
        )
      );
    } finally {
      setMasterLoading(false);
    }
  };

  // =======================================================
  // INITIAL LOAD
  // =======================================================

  useEffect(() => {
    const initializeSettings = async () => {
      await Promise.all([
        loadRecipientOptions(),
        loadTargetAudiences(),
        loadConfigs(),
        loadMasterRecipients(),
      ]);
    };

    initializeSettings();
  }, []);

  // =======================================================
  // SET FORM FROM CONFIG
  // =======================================================

  const setFormFromConfig = (config) => {
    setForm({
      name: config.name || "",

      reminder_type:
        config.reminder_type ||
        "BEFORE_TRAINING",

      days_before:
        config.days_before !== null &&
        config.days_before !== undefined
          ? config.days_before
          : 2,

      send_time: config.send_time
        ? String(config.send_time).slice(0, 5)
        : "09:00",

      enabled: config.enabled ?? true,
    });
  };

  // =======================================================
  // SELECT CONFIGURATION
  // =======================================================

  const handleSelectConfig = async (config) => {
    setSelectedConfig(config);
    setFormFromConfig(config);

    setEditing(false);
    setShowRecipientForm(false);

    setMessage("");
    setError("");

    setRecipientForm({
      recipient_type: "HOD",
      recipient_id: "",
      channel: "EMAIL",
    });

    await loadRecipients(config.id);
  };

  // =======================================================
  // LOAD RECIPIENTS
  // =======================================================

  const loadRecipients = async (configId) => {
    try {
      setRecipientLoading(true);

      const response =
        await getReminderRecipients(configId);

      const data = Array.isArray(response.data)
        ? response.data
        : response.data?.value || [];

      setRecipients(data);
    } catch (err) {
      console.error(
        "Failed to load recipients:",
        err
      );

      setRecipients([]);
    } finally {
      setRecipientLoading(false);
    }
  };

  // =======================================================
  // CONFIG FORM CHANGE
  // =======================================================

  const handleChange = (event) => {
    const {
      name,
      value,
      type,
      checked,
    } = event.target;

    setForm((previous) => ({
      ...previous,

      [name]:
        type === "checkbox"
          ? checked
          : value,
    }));
  };

  // =======================================================
  // RECIPIENT FORM CHANGE
  // =======================================================

  const handleRecipientChange = (event) => {
    const {
      name,
      value,
    } = event.target;

    if (name === "recipient_type") {
      setRecipientForm((previous) => ({
        ...previous,
        recipient_type: value,
        recipient_id: "",
      }));

      return;
    }

    setRecipientForm((previous) => ({
      ...previous,

      [name]:
        name === "recipient_id"
          ? value === ""
            ? ""
            : Number(value)
          : value,
    }));
  };

  // =======================================================
  // CREATE CONFIGURATION
  // =======================================================

  const handleCreate = async () => {
    if (!form.name.trim()) {
      setError(
        "Configuration name is required."
      );
      return;
    }

    try {
      setError("");
      setMessage("");

      const payload = {
        name: form.name.trim(),

        reminder_type:
          form.reminder_type,

        days_before:
          form.reminder_type ===
          "BEFORE_TRAINING"
            ? Number(form.days_before)
            : null,

        send_time:
          `${form.send_time}:00`,

        enabled: form.enabled,
      };

      await createReminderConfig(
        payload
      );

      setMessage(
        "Reminder configuration created successfully."
      );

      await loadConfigs();

      setEditing(false);
    } catch (err) {
      console.error(
        "Failed to create configuration:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Failed to create reminder configuration."
        )
      );
    }
  };

  // =======================================================
  // UPDATE CONFIGURATION
  // =======================================================

  const handleUpdate = async () => {
    if (!selectedConfig) {
      return;
    }

    if (!form.name.trim()) {
      setError(
        "Configuration name is required."
      );
      return;
    }

    try {
      setError("");
      setMessage("");

      const payload = {
        name: form.name.trim(),

        reminder_type:
          form.reminder_type,

        days_before:
          form.reminder_type ===
          "BEFORE_TRAINING"
            ? Number(form.days_before)
            : null,

        send_time:
          `${form.send_time}:00`,

        enabled: form.enabled,
      };

      await updateReminderConfig(
        selectedConfig.id,
        payload
      );

      setMessage(
        "Reminder configuration updated successfully."
      );

      await loadConfigs();

      setEditing(false);
    } catch (err) {
      console.error(
        "Failed to update configuration:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Failed to update reminder configuration."
        )
      );
    }
  };

  // =======================================================
  // DELETE CONFIGURATION
  // =======================================================

  const handleDelete = async () => {
    if (!selectedConfig) {
      return;
    }

    const confirmed = window.confirm(
      `Delete "${selectedConfig.name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setMessage("");

      await deleteReminderConfig(
        selectedConfig.id
      );

      setMessage(
        "Reminder configuration deleted successfully."
      );

      setSelectedConfig(null);
      setRecipients([]);

      await loadConfigs();

      setEditing(false);
    } catch (err) {
      console.error(
        "Failed to delete configuration:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Failed to delete reminder configuration."
        )
      );
    }
  };

  // =======================================================
  // ADD RECIPIENT
  // =======================================================

  const handleAddRecipient = async () => {
    if (!selectedConfig) {
      return;
    }

    if (
      recipientForm.recipient_id === "" ||
      recipientForm.recipient_id === null ||
      recipientForm.recipient_id === undefined
    ) {
      setError(
        "Please select a recipient."
      );

      return;
    }

    try {
      setError("");
      setMessage("");

      const payload = {
        recipient_type:
          recipientForm.recipient_type,

        recipient_id:
          Number(
            recipientForm.recipient_id
          ),

        channel:
          recipientForm.channel,
      };

      await addReminderRecipient(
        selectedConfig.id,
        payload
      );

      setMessage(
        "Recipient added successfully."
      );

      setRecipientForm({
        recipient_type: "HOD",
        recipient_id: "",
        channel: "EMAIL",
      });

      setShowRecipientForm(false);

      await loadRecipients(
        selectedConfig.id
      );
    } catch (err) {
      console.error(
        "Failed to add recipient:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Failed to add recipient."
        )
      );
    }
  };

  // =======================================================
  // DELETE CONFIG RECIPIENT
  // =======================================================

  const handleDeleteRecipient = async (
    recipientId
  ) => {
    if (!selectedConfig) {
      return;
    }

    const confirmed = window.confirm(
      "Remove this recipient from the reminder configuration?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setMessage("");

      await deleteReminderRecipient(
        selectedConfig.id,
        recipientId
      );

      setMessage(
        "Recipient removed successfully."
      );

      await loadRecipients(
        selectedConfig.id
      );
    } catch (err) {
      console.error(
        "Failed to remove recipient:",
        err
      );

      setError(
        getErrorMessage(
          err,
          "Failed to remove recipient."
        )
      );
    }
  };

  // =======================================================
  // NEW CONFIGURATION
  // =======================================================

  const handleNewConfiguration = () => {
    setSelectedConfig(null);
    setRecipients([]);

    setForm({
      name: "",
      reminder_type:
        "BEFORE_TRAINING",
      days_before: 2,
      send_time: "09:00",
      enabled: true,
    });

    setRecipientForm({
      recipient_type: "HOD",
      recipient_id: "",
      channel: "EMAIL",
    });

    setEditing(true);
    setShowRecipientForm(false);

    setMessage("");
    setError("");
  };

  // =======================================================
  // AVAILABLE RECIPIENTS
  // =======================================================

  const getAvailableRecipients = () => {
    if (
      recipientForm.recipient_type ===
      "HOD"
    ) {
      return hods;
    }

    return lineManagers;
  };

  // =======================================================
  // FIND RECIPIENT DETAILS
  // =======================================================

  const getRecipientDetails = (
    recipient
  ) => {
    const list =
      recipient.recipient_type ===
      "HOD"
        ? hods
        : lineManagers;

    return (
      list.find(
        (person) =>
          Number(person.id) ===
          Number(
            recipient.recipient_id
          )
      ) || null
    );
  };

  // =======================================================
  // MASTER EXCEL FILE CHANGE
  // =======================================================

  const handleMasterFileChange = (
    event
  ) => {
    const file =
      event.target.files?.[0];

    if (!file) {
      setMasterFile(null);
      return;
    }

    const validExtension =
      file.name
        .toLowerCase()
        .endsWith(".xlsx") ||
      file.name
        .toLowerCase()
        .endsWith(".xlsm");

    if (!validExtension) {
      setMasterError(
        "Please select an .xlsx or .xlsm file."
      );

      setMasterFile(null);

      // Reset file input
      event.target.value = "";

      return;
    }

    setMasterError("");
    setMasterMessage("");
    setMasterFile(file);
  };

  // =======================================================
  // MASTER EXCEL UPLOAD
  // =======================================================

  const handleMasterUpload = async () => {
    if (!masterFile) {
      setMasterError(
        "Please select an Excel file first."
      );

      return;
    }

    try {
      setUploadingMaster(true);
      setMasterError("");
      setMasterMessage("");

      const response =
        await uploadMasterRecipients(
          masterFile
        );

      const result =
        response?.data || {};

      // ---------------------------------------------------
      // BACKEND RETURNED FAILURE
      // ---------------------------------------------------

      if (result.success === false) {
        let errorText =
          result.message ||
          "Import failed.";

        if (
          Array.isArray(result.errors) &&
          result.errors.length > 0
        ) {
          errorText =
            result.errors
              .map((item) => {
                if (
                  typeof item ===
                  "string"
                ) {
                  return item;
                }

                if (
                  item?.row &&
                  item?.error
                ) {
                  return `Row ${item.row}: ${item.error}`;
                }

                return (
                  item?.message ||
                  JSON.stringify(item)
                );
              })
              .join("\n");
        }

        setMasterError(errorText);

        return;
      }

      // ---------------------------------------------------
      // SUCCESS
      // ---------------------------------------------------

      const created =
        result.summary?.created || 0;

      const updated =
        result.summary?.updated || 0;

      setMasterMessage(
        `Import successful. ${created} record(s) created and ${updated} record(s) updated.`
      );

      setMasterFile(null);

      await loadMasterRecipients();
      await loadRecipientOptions();
      await loadTargetAudiences();
    } catch (err) {
      console.error(
        "Master data upload failed:",
        err
      );

      // ---------------------------------------------------
      // IMPORTANT:
      // Backend can return detail as either a string
      // or an object. Never put an object directly into
      // React state and render it.
      // ---------------------------------------------------

      const detail =
        err?.response?.data?.detail;

      if (
        typeof detail ===
        "string"
      ) {
        setMasterError(detail);
      } else if (
        detail &&
        typeof detail ===
          "object"
      ) {
        const missingColumns =
          detail.missing_columns ||
          [];

        if (
          Array.isArray(
            missingColumns
          ) &&
          missingColumns.length > 0
        ) {
          setMasterError(
            `${
              detail.message ||
              "Required columns are missing"
            }: ${missingColumns.join(
              ", "
            )}`
          );
        } else if (
          Array.isArray(
            detail.errors
          ) &&
          detail.errors.length > 0
        ) {
          setMasterError(
            detail.errors
              .map((item) => {
                if (
                  typeof item ===
                  "string"
                ) {
                  return item;
                }

                if (
                  item?.row &&
                  item?.error
                ) {
                  return `Row ${item.row}: ${item.error}`;
                }

                return (
                  item?.message ||
                  JSON.stringify(item)
                );
              })
              .join("\n")
          );
        } else {
          setMasterError(
            detail.message ||
              "Master data upload failed."
          );
        }
      } else {
        setMasterError(
          err?.message ||
            "Master data upload failed."
        );
      }
    } finally {
      setUploadingMaster(false);
    }
  };

  // =======================================================
  // EDIT MASTER RECIPIENT
  // =======================================================

  const handleEditRecipient = (
    recipient
  ) => {
    setEditingRecipient(
      recipient
    );

    setEditForm({
      name: recipient.name || "",

      email:
        recipient.email || "",

      whatsapp_number:
        recipient.whatsapp_number ||
        "",

      target_audience:
        recipient.target_audience ||
        "",
    });

    setMasterError("");
    setMasterMessage("");
  };

  // =======================================================
  // EDIT FORM CHANGE
  // =======================================================

  const handleEditChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setEditForm(
      (previous) => ({
        ...previous,
        [name]: value,
      })
    );
  };

  // =======================================================
  // SAVE MASTER RECIPIENT
  // =======================================================

  const handleSaveRecipient =
    async () => {
      if (!editingRecipient) {
        return;
      }

      if (!editForm.name.trim()) {
        setMasterError(
          "Name is required."
        );
        return;
      }

      if (!editForm.email.trim()) {
        setMasterError(
          "Email is required."
        );
        return;
      }

      if (
        !editForm.target_audience
      ) {
        setMasterError(
          "Target Audience is required."
        );
        return;
      }

      try {
        setMasterError("");
        setMasterMessage("");

        const payload = {
          name:
            editForm.name.trim(),

          email:
            editForm.email.trim(),

          whatsapp_number:
            editForm.whatsapp_number.trim() ||
            null,

          target_audience:
            editForm.target_audience.trim(),
        };

        if (
          editingRecipient.type ===
          "HOD"
        ) {
          await updateHOD(
            editingRecipient.id,
            payload
          );
        } else {
          await updateLineManager(
            editingRecipient.id,
            payload
          );
        }

        setMasterMessage(
          `${
            editingRecipient.type ===
            "HOD"
              ? "HOD"
              : "Line Manager"
          } updated successfully.`
        );

        setEditingRecipient(
          null
        );

        await loadMasterRecipients();
        await loadRecipientOptions();
        await loadTargetAudiences();
      } catch (err) {
        console.error(
          "Failed to update recipient:",
          err
        );

        setMasterError(
          getErrorMessage(
            err,
            "Failed to update recipient."
          )
        );
      }
    };

  // =======================================================
  // CANCEL MASTER EDIT
  // =======================================================

  const handleCancelEdit = () => {
    setEditingRecipient(null);

    setEditForm({
      name: "",
      email: "",
      whatsapp_number: "",
      target_audience: "",
    });

    setMasterError("");
  };

  // =======================================================
  // DELETE MASTER RECIPIENT
  // =======================================================

  const handleDeleteMasterRecipient =
    async (recipient) => {
      const confirmed =
        window.confirm(
          `Are you sure you want to delete ${recipient.name}?`
        );

      if (!confirmed) {
        return;
      }

      try {
        setMasterError("");
        setMasterMessage("");

        if (
          recipient.type ===
          "HOD"
        ) {
          await deleteHOD(
            recipient.id
          );
        } else {
          await deleteLineManager(
            recipient.id
          );
        }

        setMasterMessage(
          `${recipient.name} deleted successfully.`
        );

        await loadMasterRecipients();
        await loadRecipientOptions();
        await loadTargetAudiences();
      } catch (err) {
        console.error(
          "Failed to delete recipient:",
          err
        );

        setMasterError(
          getErrorMessage(
            err,
            "Failed to delete recipient."
          )
        );
      }
    };

  // =======================================================
  // LOADING
  // =======================================================

  if (loading) {
    return (
      <div className="settings-page">
        <div className="settings-loading">
          Loading reminder settings...
        </div>
      </div>
    );
  }

  // =======================================================
  // RENDER
  // =======================================================

  return (
    <div className="settings-page">

      {/* =================================================
          HEADER
      ================================================= */}

      <div className="settings-header">

        <div>
          <h1>Settings</h1>

          <p>
            Configure reminder schedules
            and notification recipients.
          </p>
        </div>

        <button
          className="primary-btn"
          onClick={
            handleNewConfiguration
          }
        >
          + New Configuration
        </button>

      </div>

      {/* =================================================
          GLOBAL MESSAGES
      ================================================= */}

      {message && (
        <div className="settings-message success">
          ✓ {message}
        </div>
      )}

      {error && (
        <div className="settings-message error">
          ⚠ {error}
        </div>
      )}

      {/* =================================================
          MAIN LAYOUT
      ================================================= */}

      <div className="settings-layout">

        {/* ===============================================
            CONFIGURATION LIST
        =============================================== */}

        <div className="config-list-card">

          <div className="card-header">

            <div>
              <h2>
                Reminder Configurations
              </h2>

              <span>
                {configs.length}{" "}
                configuration
                {configs.length !== 1
                  ? "s"
                  : ""}
              </span>
            </div>

          </div>

          <div className="config-list">

            {configs.length === 0 ? (

              <div className="empty-state">

                <p>
                  No reminder
                  configurations found.
                </p>

                <button
                  className="secondary-btn"
                  onClick={
                    handleNewConfiguration
                  }
                >
                  Create Configuration
                </button>

              </div>

            ) : (

              configs.map(
                (config) => (
                  <button
                    key={config.id}
                    className={`config-item ${
                      selectedConfig?.id ===
                      config.id
                        ? "selected"
                        : ""
                    }`}
                    onClick={() =>
                      handleSelectConfig(
                        config
                      )
                    }
                  >

                    <div className="config-item-top">

                      <strong>
                        {config.name}
                      </strong>

                      <span
                        className={
                          config.enabled
                            ? "status-badge active"
                            : "status-badge inactive"
                        }
                      >
                        {config.enabled
                          ? "Active"
                          : "Inactive"}
                      </span>

                    </div>

                    <div className="config-item-details">

                      <span>
                        {
                          config.reminder_type
                        }
                      </span>

                      {config.days_before !==
                        null &&
                        config.days_before !==
                          undefined && (
                          <span>
                            {
                              config.days_before
                            }{" "}
                            day
                            {config.days_before !==
                            1
                              ? "s"
                              : ""}{" "}
                            before
                          </span>
                        )}

                      <span>
                        {String(
                          config.send_time ||
                            ""
                        ).slice(0, 5)}
                      </span>

                    </div>

                  </button>
                )
              )

            )}

          </div>

        </div>

        {/* ===============================================
            MAIN CONTENT
        =============================================== */}

        <div className="settings-main">

          {/* =============================================
              CONFIGURATION EDITOR
          ============================================= */}

          <div className="settings-card">

            <div className="card-header">

              <div>

                <h2>
                  {selectedConfig
                    ? "Reminder Configuration"
                    : "New Reminder Configuration"}
                </h2>

                <span>
                  {selectedConfig
                    ? `Configuration #${selectedConfig.id}`
                    : "Create a new reminder schedule"}
                </span>

              </div>

              {selectedConfig &&
                !editing && (
                  <button
                    className="secondary-btn"
                    onClick={() =>
                      setEditing(true)
                    }
                  >
                    Edit
                  </button>
                )}

            </div>

            <div className="form-grid">

              <div className="form-group full-width">

                <label>
                  Configuration Name
                </label>

                <input
                  type="text"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  disabled={!editing}
                  placeholder="e.g. 2-Day Training Reminder"
                />

              </div>

              <div className="form-group">

                <label>
                  Reminder Type
                </label>

                <select
                  name="reminder_type"
                  value={
                    form.reminder_type
                  }
                  onChange={
                    handleChange
                  }
                  disabled={!editing}
                >

                  {reminderTypes.map(
                    (type) => (
                      <option
                        key={type}
                        value={type}
                      >
                        {type}
                      </option>
                    )
                  )}

                </select>

              </div>

              {form.reminder_type ===
                "BEFORE_TRAINING" && (
                <div className="form-group">

                  <label>
                    Days Before Training
                  </label>

                  <input
                    type="number"
                    name="days_before"
                    min="0"
                    value={
                      form.days_before
                    }
                    onChange={
                      handleChange
                    }
                    disabled={!editing}
                  />

                </div>
              )}

              <div className="form-group">

                <label>
                  Send Time
                </label>

                <input
                  type="time"
                  name="send_time"
                  value={
                    form.send_time
                  }
                  onChange={
                    handleChange
                  }
                  disabled={!editing}
                />

              </div>

              <div className="form-group enabled-group">

                <label>
                  Configuration Status
                </label>

                <label className="toggle-container">

                  <input
                    type="checkbox"
                    name="enabled"
                    checked={
                      form.enabled
                    }
                    onChange={
                      handleChange
                    }
                    disabled={!editing}
                  />

                  <span className="toggle-slider"></span>

                  <span>
                    {form.enabled
                      ? "Enabled"
                      : "Disabled"}
                  </span>

                </label>

              </div>

            </div>

            {editing && (

              <div className="form-actions">

                <button
                  className="primary-btn"
                  onClick={
                    selectedConfig
                      ? handleUpdate
                      : handleCreate
                  }
                  disabled={
                    !form.name.trim()
                  }
                >
                  {selectedConfig
                    ? "Save Changes"
                    : "Create Configuration"}
                </button>

                {selectedConfig && (
                  <button
                    className="secondary-btn"
                    onClick={() => {
                      setFormFromConfig(
                        selectedConfig
                      );

                      setEditing(
                        false
                      );
                    }}
                  >
                    Cancel
                  </button>
                )}

                {selectedConfig && (
                  <button
                    className="danger-btn"
                    onClick={
                      handleDelete
                    }
                  >
                    Delete
                  </button>
                )}

              </div>

            )}

          </div>

          {/* =============================================
              REMINDER RECIPIENTS
          ============================================= */}

          {selectedConfig && (

            <div className="settings-card recipients-card">

              <div className="card-header">

                <div>

                  <h2>
                    Recipients
                  </h2>

                  <span>
                    Notification recipients
                    for this configuration
                  </span>

                </div>

                <button
                  className="primary-btn"
                  onClick={() =>
                    setShowRecipientForm(
                      !showRecipientForm
                    )
                  }
                >
                  {showRecipientForm
                    ? "Cancel"
                    : "+ Add Recipient"}
                </button>

              </div>

              {showRecipientForm && (

                <div className="recipient-form">

                  <div className="form-group">

                    <label>
                      Recipient Type
                    </label>

                    <select
                      name="recipient_type"
                      value={
                        recipientForm.recipient_type
                      }
                      onChange={
                        handleRecipientChange
                      }
                    >

                      {recipientTypes.map(
                        (type) => (
                          <option
                            key={type}
                            value={type}
                          >
                            {type ===
                            "LINE_MANAGER"
                              ? "Line Manager"
                              : "HOD"}
                          </option>
                        )
                      )}

                    </select>

                  </div>

                  <div className="form-group">

                    <label>
                      Recipient
                    </label>

                    <select
                      name="recipient_id"
                      value={
                        recipientForm.recipient_id
                      }
                      onChange={
                        handleRecipientChange
                      }
                    >

                      <option value="">
                        Select recipient
                      </option>

                      {getAvailableRecipients().map(
                        (person) => (
                          <option
                            key={person.id}
                            value={person.id}
                          >
                            {person.name}
                            {" — "}
                            {person.email}
                          </option>
                        )
                      )}

                    </select>

                    {getAvailableRecipients()
                      .length === 0 && (
                      <small>
                        No{" "}
                        {recipientForm.recipient_type ===
                        "HOD"
                          ? "HODs"
                          : "Line Managers"}{" "}
                        available.
                      </small>
                    )}

                  </div>

                  <div className="form-group">

                    <label>
                      Channel
                    </label>

                    <select
                      name="channel"
                      value={
                        recipientForm.channel
                      }
                      onChange={
                        handleRecipientChange
                      }
                    >

                      {channels.map(
                        (channel) => (
                          <option
                            key={channel}
                            value={channel}
                          >
                            {channel}
                          </option>
                        )
                      )}

                    </select>

                  </div>

                  <div className="recipient-form-actions">

                    <button
                      className="primary-btn"
                      onClick={
                        handleAddRecipient
                      }
                      disabled={
                        recipientForm.recipient_id ===
                        ""
                      }
                    >
                      Add Recipient
                    </button>

                    <button
                      className="secondary-btn"
                      onClick={() =>
                        setShowRecipientForm(
                          false
                        )
                      }
                    >
                      Cancel
                    </button>

                  </div>

                </div>

              )}

              <div className="recipient-list">

                {recipientLoading ? (

                  <div className="empty-state">
                    Loading recipients...
                  </div>

                ) : recipients.length ===
                  0 ? (

                  <div className="empty-state">

                    <p>
                      No recipients
                      configured for this
                      reminder.
                    </p>

                    <span>
                      Add an HOD or Line
                      Manager and choose
                      Email or WhatsApp.
                    </span>

                  </div>

                ) : (

                  recipients.map(
                    (recipient) => {

                      const person =
                        getRecipientDetails(
                          recipient
                        );

                      return (
                        <div
                          className="recipient-row"
                          key={recipient.id}
                        >

                          <div className="recipient-info">

                            <div className="recipient-icon">

                              {recipient.recipient_type ===
                              "HOD"
                                ? "H"
                                : "LM"}

                            </div>

                            <div>

                              <strong>
                                {recipient.recipient_type ===
                                "LINE_MANAGER"
                                  ? "Line Manager"
                                  : "HOD"}
                              </strong>

                              <span>
                                {person?.name ||
                                  `Recipient #${recipient.recipient_id}`}
                              </span>

                              {person?.email && (
                                <small>
                                  {
                                    person.email
                                  }
                                </small>
                              )}

                            </div>

                          </div>

                          <div className="recipient-actions">

                            <span
                              className={`channel-badge ${
                                recipient.channel ===
                                "WHATSAPP"
                                  ? "whatsapp"
                                  : "email"
                              }`}
                            >
                              {
                                recipient.channel
                              }
                            </span>

                            <button
                              className="remove-btn"
                              onClick={() =>
                                handleDeleteRecipient(
                                  recipient.id
                                )
                              }
                            >
                              Remove
                            </button>

                          </div>

                        </div>
                      );
                    }
                  )

                )}

              </div>

            </div>

          )}

          {/* =============================================
              MASTER DATA
          ============================================= */}

          <div className="settings-card master-data-card">

            <div className="card-header">

              <div>

                <h2>
                  HOD & Line Manager Master Data
                </h2>

                <span>
                  Manage HOD and Line Manager
                  contact information and their
                  Target Audience assignments.
                </span>

              </div>

              <button
                className="secondary-btn"
                onClick={
                  loadMasterRecipients
                }
                disabled={
                  masterLoading
                }
              >
                {masterLoading
                  ? "Refreshing..."
                  : "Refresh"}
              </button>

            </div>

            {/* MASTER DATA UPLOAD */}

            <div className="master-upload">

              <div className="upload-info">

                <h3>
                  Import Master Data
                </h3>

                <p>
                  Upload an Excel file to
                  create or update HOD and
                  Line Manager records.
                  Each recipient is linked to a
                  Target Audience.
                </p>

                <small>
                  Required columns:
                  Type, Name, Email,
                  WhatsApp Number,
                  Target Audience
                </small>

              </div>

              <div className="upload-controls">

                <input
                  type="file"
                  accept=".xlsx,.xlsm"
                  onChange={
                    handleMasterFileChange
                  }
                />

                <button
                  className="primary-btn"
                  onClick={
                    handleMasterUpload
                  }
                  disabled={
                    !masterFile ||
                    uploadingMaster
                  }
                >
                  {uploadingMaster
                    ? "Uploading..."
                    : "Upload Excel"}
                </button>

              </div>

              {masterFile && (
                <div className="selected-file">

                  Selected file:

                  <strong>
                    {masterFile.name}
                  </strong>

                </div>
              )}

            </div>

            {/* MASTER DATA MESSAGES */}

            {masterMessage && (
              <div className="settings-message success">
                ✓ {masterMessage}
              </div>
            )}

            {masterError && (
              <div className="settings-message error">
                <div
                  style={{
                    whiteSpace:
                      "pre-line",
                  }}
                >
                  ⚠ {masterError}
                </div>
              </div>
            )}

            {/* MASTER DATA TABLE */}

            {masterLoading ? (

              <div className="settings-loading">
                Loading master data...
              </div>

            ) : masterRecipients.length ===
              0 ? (

              <div className="empty-state">

                <p>
                  No HOD or Line Manager
                  records found.
                </p>

              </div>

            ) : (

              <div className="master-table-wrapper">

                <table className="master-data-table">

                  <thead>

                    <tr>

                      <th>ID</th>

                      <th>Type</th>

                      <th>Name</th>

                      <th>Email</th>

                      <th>WhatsApp</th>

                      <th>Department</th>

                      <th>Status</th>

                      <th>Actions</th>

                    </tr>

                  </thead>

                  <tbody>

                    {masterRecipients.map(
                      (recipient) => (

                        <tr
                          key={`${recipient.type}-${recipient.id}`}
                        >

                          <td>
                            #{recipient.id}
                          </td>

                          <td>

                            <span
                              className={`recipient-type-badge ${
                                recipient.type ===
                                "HOD"
                                  ? "hod"
                                  : "manager"
                              }`}
                            >
                              {recipient.type ===
                              "LINE_MANAGER"
                                ? "LINE MANAGER"
                                : "HOD"}
                            </span>

                          </td>

                          <td>

                            <strong>
                              {
                                recipient.name
                              }
                            </strong>

                          </td>

                          <td>
                            {
                              recipient.email
                            }
                          </td>

                          <td>
                            {
                              recipient.whatsapp_number ||
                              "Not available"
                            }
                          </td>

                          <td>
                            {recipient.target_audience ||
                              "Not assigned"}
                          </td>

                          <td>

                            <span className="status-badge active">
                              Active
                            </span>

                          </td>

                          <td>

                            <div className="master-actions">

                              <button
                                className="edit-btn"
                                onClick={() =>
                                  handleEditRecipient(
                                    recipient
                                  )
                                }
                              >
                                Edit
                              </button>

                              <button
                                className="remove-btn"
                                onClick={() =>
                                  handleDeleteMasterRecipient(
                                    recipient
                                  )
                                }
                              >
                                Delete
                              </button>

                            </div>

                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            )}

          </div>

        </div>

      </div>

      {/* =================================================
          MASTER DATA EDIT MODAL
      ================================================= */}

      {editingRecipient && (

        <div className="modal-overlay">

          <div className="edit-recipient-modal">

            <div className="modal-header">

              <div>

                <h2>
                  Edit{" "}
                  {editingRecipient.type ===
                  "HOD"
                    ? "HOD"
                    : "Line Manager"}
                </h2>

                <p>
                  Update recipient information.
                </p>

              </div>

              <button
                className="modal-close"
                onClick={
                  handleCancelEdit
                }
              >
                ×
              </button>

            </div>

            {masterError && (
              <div className="settings-message error">

                <div
                  style={{
                    whiteSpace:
                      "pre-line",
                  }}
                >
                  ⚠ {masterError}
                </div>

              </div>
            )}

            <div className="form-grid">

              <div className="form-group">

                <label>
                  Name
                </label>

                <input
                  type="text"
                  name="name"
                  value={
                    editForm.name
                  }
                  onChange={
                    handleEditChange
                  }
                />

              </div>

              <div className="form-group">

                <label>
                  Email
                </label>

                <input
                  type="email"
                  name="email"
                  value={
                    editForm.email
                  }
                  onChange={
                    handleEditChange
                  }
                />

              </div>

              <div className="form-group">

                <label>
                  WhatsApp Number
                </label>

                <input
                  type="text"
                  name="whatsapp_number"
                  value={
                    editForm.whatsapp_number
                  }
                  onChange={
                    handleEditChange
                  }
                  placeholder="919876543210"
                />

              </div>

              <div className="form-group">

                <label>
                  Target Audience
                </label>

                <select
                  name="target_audience"
                  value={
                    editForm.target_audience
                  }
                  onChange={
                    handleEditChange
                  }
                >

                  <option value="">
                    Select Target Audience
                  </option>

                  {targetAudiences.map(
                    (audience) => (
                      <option
                        key={audience.id}
                        value={
                          audience.name
                        }
                      >
                        {
                          audience.name
                        }
                      </option>
                    )
                  )}

                </select>

                {targetAudiences.length ===
                  0 && (
                  <small>
                    No target audiences found.
                    Upload master data with a
                    Target Audience first.
                  </small>
                )}

              </div>

            </div>

            <div className="form-actions">

              <button
                className="secondary-btn"
                onClick={
                  handleCancelEdit
                }
              >
                Cancel
              </button>

              <button
                className="primary-btn"
                onClick={
                  handleSaveRecipient
                }
              >
                Save Changes
              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}

export default Settings;
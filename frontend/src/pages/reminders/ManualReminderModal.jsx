
import { useEffect, useMemo, useState } from "react";
import api from "../../services/api";
import "./ManualReminderModal.css";

function getList(response) {
  const data = response?.data;

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.value)) return data.value;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.data)) return data.data;

  return [];
}

function localDateString(date = new Date()) {
  const offsetDate = new Date(
    date.getTime() - date.getTimezoneOffset() * 60000
  );
  return offsetDate.toISOString().slice(0, 10);
}

function getPersonName(person) {
  return (
    person.name ||
    person.full_name ||
    person.hod_name ||
    person.line_manager_name ||
    person.employee_name ||
    `Contact #${person.id}`
  );
}

function getWhatsApp(person) {
  return (
    person.whatsapp_number ||
    person.whatsapp ||
    person.phone_number ||
    person.mobile_number ||
    person.phone ||
    ""
  );
}

export default function ManualReminderModal({ onClose, onCreated }) {
  const [trainings, setTrainings] = useState([]);
  const [hods, setHods] = useState([]);
  const [lineManagers, setLineManagers] = useState([]);

  const [trainingId, setTrainingId] = useState("");
  const [title, setTitle] = useState("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [scheduledTime, setScheduledTime] = useState("09:00");
  const [recipientType, setRecipientType] = useState("BOTH");
  const [selectedRecipients, setSelectedRecipients] = useState([]);
  const [message, setMessage] = useState("");

  const [loadingOptions, setLoadingOptions] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadOptions() {
      setLoadingOptions(true);
      setError("");

      try {
        const [trainingResponse, hodResponse, managerResponse] =
          await Promise.all([
            api.get("/trainings/"),
            api.get("/recipients/hods"),
            api.get("/recipients/line-managers"),
          ]);

        if (!mounted) return;

        setTrainings(getList(trainingResponse));
        setHods(getList(hodResponse));
        setLineManagers(getList(managerResponse));
      } catch (err) {
        if (mounted) {
          setError(
            err?.response?.data?.detail ||
              "Unable to load trainings and recipient master data. " +
                "Check the API routes and try again."
          );
        }
      } finally {
        if (mounted) setLoadingOptions(false);
      }
    }

    loadOptions();

    return () => {
      mounted = false;
    };
  }, []);

  const availableRecipients = useMemo(() => {
    const normalize = (list, type) =>
      list
        .filter((person) => person?.id != null)
        .map((person) => ({
          id: Number(person.id),
          recipient_type: type,
          name: getPersonName(person),
          email: String(person.email || person.email_address || "").trim(),
          whatsapp_number: String(getWhatsApp(person)).trim(),
        }));

    const all = [
      ...(recipientType === "LINE_MANAGER"
        ? []
        : normalize(hods, "HOD")),
      ...(recipientType === "HOD"
        ? []
        : normalize(lineManagers, "LINE_MANAGER")),
    ];

    return all.sort((a, b) => a.name.localeCompare(b.name));
  }, [hods, lineManagers, recipientType]);

  const selectedKeys = useMemo(
    () =>
      new Set(
        selectedRecipients.map(
          (person) => `${person.recipient_type}:${person.recipient_id}`
        )
      ),
    [selectedRecipients]
  );

  function toggleRecipient(person) {
    const key = `${person.recipient_type}:${person.id}`;

    setSelectedRecipients((current) => {
      const exists = current.some(
        (item) =>
          `${item.recipient_type}:${item.recipient_id}` === key
      );

      if (exists) {
        return current.filter(
          (item) =>
            `${item.recipient_type}:${item.recipient_id}` !== key
        );
      }

      return [
        ...current,
        {
          recipient_type: person.recipient_type,
          recipient_id: person.id,
        },
      ];
    });
  }

  function handleRecipientTypeChange(value) {
    setRecipientType(value);
    setSelectedRecipients([]);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!trainingId) {
      setError("Select a training.");
      return;
    }

    if (!title.trim()) {
      setError("Reminder title is required.");
      return;
    }

    if (!scheduledDate || !scheduledTime) {
      setError("Scheduled date and time are required.");
      return;
    }

    const scheduledAt = new Date(
      `${scheduledDate}T${scheduledTime}:00`
    );

    if (
      Number.isNaN(scheduledAt.getTime()) ||
      scheduledAt.getTime() <= Date.now()
    ) {
      setError("Select a future date and time.");
      return;
    }

    if (selectedRecipients.length === 0) {
      setError("Select at least one recipient.");
      return;
    }

    const selectedPeople = selectedRecipients.map((selected) =>
      availableRecipients.find(
        (person) =>
          person.id === selected.recipient_id &&
          person.recipient_type === selected.recipient_type
      )
    );

    if (selectedPeople.some((person) => !person)) {
      setError(
        "One or more selected recipients are no longer available. " +
          "Please select them again."
      );
      return;
    }

    const missingEmail = selectedPeople.find(
      (person) =>
        !person.email ||
        !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(person.email)
    );

    if (missingEmail) {
      setError(
        `${missingEmail.name} does not have a valid email address. ` +
          "Choose a recipient with a valid email."
      );
      return;
    }

    setSaving(true);

    try {
      await api.post("/reminder-engine/manual", {
        category: "TRAINING",
        training_id: Number(trainingId),
        title: title.trim(),
        scheduled_date: scheduledDate,
        scheduled_time: scheduledTime,
        recipient_type: recipientType,
        recipients: selectedRecipients,
        channel: "EMAIL",
        custom_message: message.trim(),
      });

      await onCreated?.();
      onClose();
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Could not create the reminder. Please try again."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="manual-reminder-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !saving) {
          onClose();
        }
      }}
    >
      <section
        className="manual-reminder-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="manual-reminder-title"
      >
        <header className="manual-reminder-dialog-header">
          <div>
            <h2 id="manual-reminder-title">Create Manual Reminder</h2>
            <p>Create a scheduled training reminder for selected contacts.</p>
          </div>

          <button
            type="button"
            className="manual-reminder-close"
            onClick={onClose}
            disabled={saving}
            aria-label="Close dialog"
          >
            ×
          </button>
        </header>

        {error && (
          <div className="manual-reminder-error" role="alert">
            {error}
          </div>
        )}

        {loadingOptions ? (
          <div className="manual-reminder-loading">
            Loading trainings and master-data recipients...
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <label className="manual-reminder-field">
              <span>Reminder category</span>
              <input value="TRAINING" readOnly />
            </label>

            <label className="manual-reminder-field">
              <span>Training *</span>
              <select
                value={trainingId}
                onChange={(event) => setTrainingId(event.target.value)}
                required
              >
                <option value="">Select an existing training</option>
                {trainings.map((training) => (
                  <option key={training.id} value={training.id}>
                    {training.training_name ||
                      training.title ||
                      `Training #${training.id}`}
                    {training.scheduled_date
                      ? ` — ${String(training.scheduled_date).slice(0, 10)}`
                      : ""}
                  </option>
                ))}
              </select>
            </label>

            <label className="manual-reminder-field">
              <span>Title *</span>
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                maxLength={255}
                placeholder="e.g. Upcoming Training Reminder"
                required
              />
            </label>

            <div className="manual-reminder-two-columns">
              <label className="manual-reminder-field">
                <span>Scheduled date *</span>
                <input
                  type="date"
                  min={localDateString()}
                  value={scheduledDate}
                  onChange={(event) =>
                    setScheduledDate(event.target.value)
                  }
                  required
                />
              </label>

              <label className="manual-reminder-field">
                <span>Scheduled time *</span>
                <input
                  type="time"
                  value={scheduledTime}
                  onChange={(event) =>
                    setScheduledTime(event.target.value)
                  }
                  required
                />
              </label>
            </div>

            <label className="manual-reminder-field">
              <span>Recipient type *</span>
              <select
                value={recipientType}
                onChange={(event) =>
                  handleRecipientTypeChange(event.target.value)
                }
              >
                <option value="BOTH">Both HOD and Line Manager</option>
                <option value="HOD">HOD only</option>
                <option value="LINE_MANAGER">Line Manager only</option>
              </select>
            </label>

            <div className="manual-reminder-recipient-heading">
              <div>
                <h3>Recipients *</h3>
                <p>
                  Choose individual recipients from the existing master data.
                </p>
              </div>
              <span>{selectedRecipients.length} selected</span>
            </div>

            <div className="manual-reminder-recipient-list">
              {availableRecipients.map((person) => {
                const key = `${person.recipient_type}:${person.id}`;

                return (
                  <label
                    key={key}
                    className="manual-reminder-recipient"
                  >
                    <input
                      type="checkbox"
                      checked={selectedKeys.has(key)}
                      onChange={() => toggleRecipient(person)}
                    />

                    <span className="manual-reminder-recipient-info">
                      <strong>{person.name}</strong>
                      <small>
                        {person.recipient_type === "HOD"
                          ? "Head of Department"
                          : "Line Manager"}
                      </small>
                      <small>Email: {person.email || "Not provided"}</small>
                      <small>
                        WhatsApp: {person.whatsapp_number || "Not provided"}
                      </small>
                    </span>
                  </label>
                );
              })}

              {availableRecipients.length === 0 && (
                <p className="manual-reminder-empty">
                  No contacts were returned by the master-data APIs.
                </p>
              )}
            </div>

            <label className="manual-reminder-field">
              <span>Message</span>
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                rows={5}
                maxLength={5000}
                placeholder="Enter the email message..."
              />
            </label>

            <div className="manual-reminder-summary">
              <span>
                Delivery channel: <strong>Email</strong>
              </span>
              <span>
                Default time: <strong>09:00</strong>
              </span>
            </div>

            <footer className="manual-reminder-footer">
              <button
                type="button"
                className="secondary-button"
                onClick={onClose}
                disabled={saving}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="primary-button"
                disabled={
                  saving ||
                  loadingOptions ||
                  trainings.length === 0 ||
                  availableRecipients.length === 0
                }
              >
                {saving ? "Scheduling..." : "Schedule Reminder"}
              </button>
            </footer>
          </form>
        )}
      </section>
    </div>
  );
}


import { useCallback, useEffect, useMemo, useState } from "react";
import { getReminders } from "../../services/reminderService";
import ManualReminderModal from "./ManualReminderModal";
import "./Reminders.css";

function Reminders() {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showManualReminder, setShowManualReminder] = useState(false);

  // Filters
  const [search, setSearch] = useState("");
  const [channelFilter, setChannelFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [recipientFilter, setRecipientFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState("scheduled_desc");

  const loadReminders = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await getReminders();
      const data = response?.data;

      if (Array.isArray(data)) {
        setReminders(data);
      } else if (Array.isArray(data?.value)) {
        setReminders(data.value);
      } else if (Array.isArray(data?.items)) {
        setReminders(data.items);
      } else {
        setReminders([]);
      }
    } catch (err) {
      console.error("Failed to load reminders:", err);
      setError(
        err?.response?.data?.detail ||
          "Unable to load reminders."
      );
      setReminders([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReminders();
  }, [loadReminders]);

  // Dashboard statistics
  const total = reminders.length;
  const sent = reminders.filter(
    (r) => String(r.status).toUpperCase() === "SENT"
  ).length;
  const pending = reminders.filter(
    (r) => String(r.status).toUpperCase() === "PENDING"
  ).length;
  const failed = reminders.filter(
    (r) => String(r.status).toUpperCase() === "FAILED"
  ).length;
  const processing = reminders.filter(
    (r) => String(r.status).toUpperCase() === "PROCESSING"
  ).length;
  const email = reminders.filter(
    (r) => String(r.channel).toUpperCase() === "EMAIL"
  ).length;
  const whatsapp = reminders.filter(
    (r) => String(r.channel).toUpperCase() === "WHATSAPP"
  ).length;
  const hod = reminders.filter(
    (r) => String(r.recipient_type).toUpperCase() === "HOD"
  ).length;
  const lineManager = reminders.filter(
    (r) => String(r.recipient_type).toUpperCase() === "LINE_MANAGER"
  ).length;

  const filteredReminders = useMemo(() => {
    const query = search.trim().toLowerCase();

    const filtered = reminders.filter((reminder) => {
      const searchableFields = [
        reminder.title,
        reminder.custom_message,
        reminder.training_name,
        reminder.recipient_name,
        reminder.recipient_email,
        String(reminder.recipient_type || "").replaceAll("_", " "),
        reminder.trainer_name,
        String(reminder.reminder_type || "").replaceAll("_", " "),
        reminder.channel,
        reminder.status,
        reminder.training_id,
        reminder.id,
      ];

      const matchesSearch =
        !query ||
        searchableFields.some((value) =>
          String(value ?? "").toLowerCase().includes(query)
        );

      const matchesChannel =
        channelFilter === "ALL" ||
        String(reminder.channel || "").toUpperCase() === channelFilter;

      const matchesStatus =
        statusFilter === "ALL" ||
        String(reminder.status || "").toUpperCase() === statusFilter;

      const matchesRecipient =
        recipientFilter === "ALL" ||
        String(reminder.recipient_type || "").toUpperCase() ===
          recipientFilter;

      const matchesType =
        typeFilter === "ALL" ||
        String(reminder.reminder_type || "").toUpperCase() === typeFilter;

      return (
        matchesSearch &&
        matchesChannel &&
        matchesStatus &&
        matchesRecipient &&
        matchesType
      );
    });

    const timestamp = (value) => {
      if (!value) return 0;
      const parsed = new Date(value).getTime();
      return Number.isNaN(parsed) ? 0 : parsed;
    };

    const compareText = (a, b) =>
      String(a ?? "").localeCompare(String(b ?? ""), undefined, {
        sensitivity: "base",
        numeric: true,
      });

    const statusRank = (status) => {
      const ranks = {
        FAILED: 0,
        PENDING: 1,
        PROCESSING: 2,
        SENT: 3,
      };
      return ranks[String(status || "").toUpperCase()] ?? 4;
    };

    return [...filtered].sort((a, b) => {
      switch (sortBy) {
        case "scheduled_asc":
          return timestamp(a.scheduled_at) - timestamp(b.scheduled_at);
        case "scheduled_desc":
          return timestamp(b.scheduled_at) - timestamp(a.scheduled_at);
        case "failed_first":
          return (
            statusRank(a.status) - statusRank(b.status) ||
            timestamp(b.scheduled_at) - timestamp(a.scheduled_at)
          );
        case "sent_desc":
          return timestamp(b.sent_at) - timestamp(a.sent_at);
        case "sent_asc":
          return timestamp(a.sent_at) - timestamp(b.sent_at);
        case "training_asc":
          return compareText(a.training_name, b.training_name);
        case "training_desc":
          return compareText(b.training_name, a.training_name);
        case "recipient_asc":
          return compareText(a.recipient_name, b.recipient_name);
        case "recipient_desc":
          return compareText(b.recipient_name, a.recipient_name);
        case "status_asc":
          return compareText(a.status, b.status);
        case "status_desc":
          return compareText(b.status, a.status);
        case "channel_asc":
          return compareText(a.channel, b.channel);
        case "channel_desc":
          return compareText(b.channel, a.channel);
        case "type_asc":
          return compareText(a.reminder_type, b.reminder_type);
        case "type_desc":
          return compareText(b.reminder_type, a.reminder_type);
        case "id_asc":
          return Number(a.id || 0) - Number(b.id || 0);
        case "id_desc":
          return Number(b.id || 0) - Number(a.id || 0);
        default:
          return timestamp(b.scheduled_at) - timestamp(a.scheduled_at);
      }
    });
  }, [
    reminders,
    search,
    channelFilter,
    statusFilter,
    recipientFilter,
    typeFilter,
    sortBy,
  ]);

  const formatDateTime = (value) => {
    if (!value) return "-";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);

    return date.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatReminderType = (type) => {
    if (!type) return "-";

    return String(type)
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  };

  const formatRecipientType = (type) => {
    if (!type) return "-";

    return String(type)
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  };

  const clearFilters = () => {
    setSearch("");
    setChannelFilter("ALL");
    setStatusFilter("ALL");
    setRecipientFilter("ALL");
    setTypeFilter("ALL");
    setSortBy("scheduled_desc");
  };

  const handleReminderCreated = async () => {
    await loadReminders();
  };

  return (
    <div className="reminders-page">
      <div className="page-header">
        <div>
          <h2>Reminder Dashboard</h2>
          <p>
            Monitor training reminders sent to HODs and Line Managers.
          </p>
        </div>

        <div className="reminder-header-actions">
          <button
            type="button"
            className="primary-button"
            onClick={() => setShowManualReminder(true)}
          >
            + Create Reminder
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={loadReminders}
            disabled={loading}
          >
            {loading ? "Loading..." : "↻ Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <div className="reminder-alert error" role="alert">
          {error}
        </div>
      )}

      <div className="reminder-stats">
        <div className="stat-card">
          <span>Total Reminders</span>
          <strong>{total}</strong>
        </div>
        <div className="stat-card">
          <span>Sent</span>
          <strong className="stat-success">{sent}</strong>
        </div>
        <div className="stat-card">
          <span>Pending</span>
          <strong className="stat-warning">{pending}</strong>
        </div>
        <div className="stat-card">
          <span>Failed</span>
          <strong className="stat-danger">{failed}</strong>
        </div>
        <div className="stat-card">
          <span>Processing</span>
          <strong>{processing}</strong>
        </div>
        <div className="stat-card">
          <span>Email</span>
          <strong>{email}</strong>
        </div>
        <div className="stat-card">
          <span>WhatsApp</span>
          <strong>{whatsapp}</strong>
        </div>
        <div className="stat-card">
          <span>HOD</span>
          <strong>{hod}</strong>
        </div>
        <div className="stat-card">
          <span>Line Manager</span>
          <strong>{lineManager}</strong>
        </div>
      </div>

      <div className="reminder-history-card">
        <div className="section-header">
          <div>
            <h3>Reminder History</h3>
            <p>Complete history of training notifications.</p>
          </div>
        </div>

        <div className="reminder-filters">
          <div className="search-box">
            <input
              type="text"
              placeholder="Search by title, message, training, recipient, email, status, or ID..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search reminders"
            />
          </div>

          <select
            aria-label="Sort reminders"
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value)}
          >
            <option value="scheduled_desc">Scheduled: Newest first</option>
            <option value="scheduled_asc">Scheduled: Oldest first</option>
            <option value="failed_first">Failed reminders first</option>
            <option value="sent_desc">Sent date: Newest first</option>
            <option value="sent_asc">Sent date: Oldest first</option>
            <option value="training_asc">Training: A–Z</option>
            <option value="training_desc">Training: Z–A</option>
            <option value="recipient_asc">Recipient: A–Z</option>
            <option value="recipient_desc">Recipient: Z–A</option>
            <option value="status_asc">Status: A–Z</option>
            <option value="status_desc">Status: Z–A</option>
            <option value="channel_asc">Channel: A–Z</option>
            <option value="channel_desc">Channel: Z–A</option>
            <option value="type_asc">Reminder type: A–Z</option>
            <option value="type_desc">Reminder type: Z–A</option>
            <option value="id_desc">Reminder ID: Highest first</option>
            <option value="id_asc">Reminder ID: Lowest first</option>
          </select>

          <select
            aria-label="Filter by channel"
            value={channelFilter}
            onChange={(event) => setChannelFilter(event.target.value)}
          >
            <option value="ALL">All Channels</option>
            <option value="EMAIL">Email</option>
            <option value="WHATSAPP">WhatsApp</option>
          </select>

          <select
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="ALL">All Status</option>
            <option value="SENT">Sent</option>
            <option value="PENDING">Pending</option>
            <option value="FAILED">Failed</option>
            <option value="PROCESSING">Processing</option>
            <option value="CANCELLED">Cancelled</option>
          </select>

          <select
            aria-label="Filter by recipient"
            value={recipientFilter}
            onChange={(event) => setRecipientFilter(event.target.value)}
          >
            <option value="ALL">All Recipients</option>
            <option value="HOD">HOD</option>
            <option value="LINE_MANAGER">Line Manager</option>
          </select>

          <select
            aria-label="Filter by reminder type"
            value={typeFilter}
            onChange={(event) => setTypeFilter(event.target.value)}
          >
            <option value="ALL">All Reminder Types</option>
            <option value="MANUAL_TRAINING">Manual Training</option>
            <option value="BEFORE_TRAINING_7_DAYS">7 Days Before</option>
            <option value="BEFORE_TRAINING_2_DAYS">2 Days Before</option>
            <option value="BEFORE_TRAINING_1_DAY">1 Day Before</option>
            <option value="MONTHLY">Monthly</option>
            <option value="WEEKLY">Weekly</option>
            <option value="BEFORE_TRAINING">Before Training</option>
            <option value="POST_TRAINING">Post Training</option>
            <option value="DOCUMENT_SUBMISSION">Document Submission</option>
            <option value="TRAINING_PERCENTAGE">Training Percentage</option>
          </select>

          <button
            type="button"
            className="secondary-button"
            onClick={clearFilters}
          >
            Clear
          </button>
        </div>

        <div className="filter-result">
          Showing <strong>{filteredReminders.length}</strong> of{" "}
          <strong>{reminders.length}</strong> reminders
        </div>

        {loading ? (
          <div className="empty-state">Loading reminders...</div>
        ) : error ? (
          <div className="empty-state">
            <p>Unable to load reminders.</p>
            <button
              type="button"
              className="primary-button"
              onClick={loadReminders}
            >
              Try Again
            </button>
          </div>
        ) : filteredReminders.length === 0 ? (
          <div className="empty-state">
            <h3>No reminders found</h3>
            <p>No reminders match the selected filters.</p>
          </div>
        ) : (
          <div className="reminder-table-wrapper">
            <table className="reminder-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title / Training</th>
                  <th>Recipient</th>
                  <th>Type</th>
                  <th>Channel</th>
                  <th>Scheduled</th>
                  <th>Status</th>
                  <th>Message ID</th>
                </tr>
              </thead>

              <tbody>
                {filteredReminders.map((reminder) => (
                  <tr key={reminder.id}>
                    <td>#{reminder.id}</td>

                    <td>
                      <div className="reminder-training">
                        <strong>
                          {reminder.title ||
                            reminder.training_name ||
                            `Training #${reminder.training_id || "-"}`}
                        </strong>

                        {reminder.title && reminder.training_name && (
                          <small>{reminder.training_name}</small>
                        )}

                        {reminder.trainer_name && (
                          <small>Trainer: {reminder.trainer_name}</small>
                        )}

                        {reminder.training_date && (
                          <small>
                            {reminder.training_date}
                            {reminder.training_time
                              ? ` • ${reminder.training_time}`
                              : ""}
                          </small>
                        )}

                        {reminder.custom_message && (
                          <small
                            className="reminder-custom-message"
                            title={reminder.custom_message}
                          >
                            {reminder.custom_message}
                          </small>
                        )}
                      </div>
                    </td>

                    <td>
                      <div className="reminder-recipient">
                        <strong>{reminder.recipient_name || "Unknown"}</strong>
                        <small>
                          {formatRecipientType(reminder.recipient_type)}
                        </small>
                        {reminder.recipient_email && (
                          <small>{reminder.recipient_email}</small>
                        )}
                      </div>
                    </td>

                    <td>
                      <span className="reminder-type">
                        {formatReminderType(reminder.reminder_type)}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`channel-badge ${String(
                          reminder.channel || ""
                        ).toLowerCase()}`}
                      >
                        {reminder.channel || "-"}
                      </span>
                    </td>

                    <td>{formatDateTime(reminder.scheduled_at)}</td>

                    <td>
                      <span
                        className={`status-badge ${String(
                          reminder.status || ""
                        ).toLowerCase()}`}
                      >
                        {reminder.status || "Unknown"}
                      </span>
                      {reminder.failure_reason && (
                        <small
                          className="reminder-failure-reason"
                          title={reminder.failure_reason}
                        >
                          {reminder.failure_reason}
                        </small>
                      )}
                    </td>

                    <td>
                      {reminder.whatsapp_message_id ? (
                        <span
                          className="message-id"
                          title={reminder.whatsapp_message_id}
                        >
                          {String(reminder.whatsapp_message_id).slice(0, 18)}...
                        </span>
                      ) : (
                        <span className="no-message-id">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showManualReminder && (
        <ManualReminderModal
          onClose={() => setShowManualReminder(false)}
          onCreated={handleReminderCreated}
        />
      )}
    </div>
  );
}

export default Reminders;

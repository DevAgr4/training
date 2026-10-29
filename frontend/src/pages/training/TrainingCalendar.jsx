import { useEffect, useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  CalendarDays,
} from "lucide-react";

import { getTrainingCalendar } from "../../services/trainingService";
import "./TrainingCalendar.css";

const STATUS_CONFIG = {
  SCHEDULED: {
    label: "Scheduled",
    className: "status-scheduled",
  },
  COMPLETED: {
    label: "Completed",
    className: "status-completed",
  },
  PENDING: {
    label: "Pending",
    className: "status-pending",
  },
  NOT_CONDUCTED: {
    label: "Not Conducted",
    className: "status-not-conducted",
  },
  RESCHEDULED: {
    label: "Rescheduled",
    className: "status-rescheduled",
  },
};

function TrainingCalendar() {
  const today = new Date();

  const [currentDate, setCurrentDate] = useState(
    new Date(today.getFullYear(), today.getMonth(), 1)
  );

  const [trainings, setTrainings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth() + 1;

  const monthName = currentDate.toLocaleString("default", {
    month: "long",
  });

  // ============================================================
  // LOAD CALENDAR DATA
  // ============================================================

  useEffect(() => {
    loadCalendar();
  }, [year, month]);

  const loadCalendar = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getTrainingCalendar(year, month);

      console.log("Calendar training data:", data);

      // getTrainingCalendar() already returns the array.
      if (Array.isArray(data)) {
        setTrainings(data);
      } else {
        console.warn(
          "Unexpected calendar response:",
          data
        );
        setTrainings([]);
      }
    } catch (err) {
      console.error("Calendar API error:", err);

      setError(
        "Unable to load training calendar."
      );

      setTrainings([]);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // BUILD CALENDAR DAYS
  // ============================================================

  const calendarDays = useMemo(() => {
    const firstDay = new Date(
      year,
      month - 1,
      1
    );

    const lastDay = new Date(
      year,
      month,
      0
    );

    // Sunday = 0
    const startingDay = firstDay.getDay();

    const totalDays = lastDay.getDate();

    const days = [];

    // Empty cells before month starts
    for (
      let i = 0;
      i < startingDay;
      i++
    ) {
      days.push(null);
    }

    // Actual days
    for (
      let day = 1;
      day <= totalDays;
      day++
    ) {
      days.push(day);
    }

    return days;
  }, [year, month]);

  // ============================================================
  // GET DATE STRING
  // ============================================================

  const getDateString = (day) => {
    return `${year}-${String(month).padStart(
      2,
      "0"
    )}-${String(day).padStart(2, "0")}`;
  };

  // ============================================================
  // GET TRAININGS FOR SPECIFIC DAY
  // ============================================================

  const getTrainingsForDay = (day) => {
    if (!day) {
      return [];
    }

    const dateString = getDateString(day);

    return trainings.filter((training) => {
      const trainingDate =
        training.scheduled_date ||
        training.scheduledDate ||
        training.date;

      if (!trainingDate) {
        return false;
      }

      return (
        String(trainingDate).slice(0, 10) ===
        dateString
      );
    });
  };

  // ============================================================
  // CHECK TODAY
  // ============================================================

  const isToday = (day) => {
    if (!day) {
      return false;
    }

    return (
      day === today.getDate() &&
      month === today.getMonth() + 1 &&
      year === today.getFullYear()
    );
  };

  // ============================================================
  // PREVIOUS MONTH
  // ============================================================

  const previousMonth = () => {
    setCurrentDate(
      new Date(
        year,
        currentDate.getMonth() - 1,
        1
      )
    );
  };

  // ============================================================
  // NEXT MONTH
  // ============================================================

  const nextMonth = () => {
    setCurrentDate(
      new Date(
        year,
        currentDate.getMonth() + 1,
        1
      )
    );
  };

  // ============================================================
  // GO TO TODAY
  // ============================================================

  const goToToday = () => {
    setCurrentDate(
      new Date(
        today.getFullYear(),
        today.getMonth(),
        1
      )
    );
  };

  // ============================================================
  // STATUS CONFIG
  // ============================================================

  const getStatusConfig = (status) => {
    return (
      STATUS_CONFIG[
        String(status || "").toUpperCase()
      ] || {
        label: status || "Unknown",
        className: "status-default",
      }
    );
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="training-calendar-page">

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <div className="calendar-header">

        <div className="calendar-title">

          <div className="calendar-title-icon">
            <CalendarDays size={24} />
          </div>

          <div>
            <h1>Training Calendar</h1>

            <p>
              View and manage scheduled training
              programs
            </p>
          </div>

        </div>

        <button
          className="today-button"
          onClick={goToToday}
        >
          Today
        </button>

      </div>


      {/* ================================================== */}
      {/* CALENDAR CARD */}
      {/* ================================================== */}

      <div className="calendar-card">

        {/* ================================================== */}
        {/* MONTH NAVIGATION */}
        {/* ================================================== */}

        <div className="calendar-toolbar">

          <button
            className="calendar-nav-button"
            onClick={previousMonth}
            aria-label="Previous month"
          >
            <ChevronLeft size={20} />
          </button>

          <h2>
            {monthName} {year}
          </h2>

          <button
            className="calendar-nav-button"
            onClick={nextMonth}
            aria-label="Next month"
          >
            <ChevronRight size={20} />
          </button>

        </div>


        {/* ================================================== */}
        {/* LOADING */}
        {/* ================================================== */}

        {loading && (
          <div className="calendar-message">
            Loading training calendar...
          </div>
        )}


        {/* ================================================== */}
        {/* ERROR */}
        {/* ================================================== */}

        {error && (
          <div className="calendar-error">
            {error}
          </div>
        )}


        {/* ================================================== */}
        {/* CALENDAR */}
        {/* ================================================== */}

        {!loading && !error && (
          <>

            {/* ================================================== */}
            {/* WEEKDAY HEADER */}
            {/* ================================================== */}

            <div className="calendar-weekdays">

              <div>Sun</div>
              <div>Mon</div>
              <div>Tue</div>
              <div>Wed</div>
              <div>Thu</div>
              <div>Fri</div>
              <div>Sat</div>

            </div>


            {/* ================================================== */}
            {/* CALENDAR GRID */}
            {/* ================================================== */}

            <div className="calendar-grid">

              {calendarDays.map(
                (day, index) => {

                  const dayTrainings =
                    getTrainingsForDay(day);

                  return (
                    <div
                      key={index}
                      className={`calendar-day ${
                        day
                          ? ""
                          : "empty-day"
                      } ${
                        isToday(day)
                          ? "today-cell"
                          : ""
                      }`}
                    >

                      {day && (
                        <>

                          {/* DAY NUMBER */}

                          <div
                            className={`day-number ${
                              isToday(day)
                                ? "today-number"
                                : ""
                            }`}
                          >
                            {day}
                          </div>


                          {/* TRAININGS */}

                          <div className="day-trainings">

                            {dayTrainings.length >
                              0 &&
                              dayTrainings.map(
                                (training) => {

                                  const status =
                                    getStatusConfig(
                                      training.status
                                    );

                                  const trainingName =
                                    training.training_name ||
                                    training.name ||
                                    "Training";

                                  return (
                                    <div
                                      key={
                                        training.id
                                      }
                                      className={`training-event ${status.className}`}
                                      title={`${trainingName} - ${status.label}`}
                                    >

                                      <span className="event-color-dot"></span>

                                      <div className="event-content">

                                        <span className="event-name">
                                          {trainingName}
                                        </span>

                                        {training.scheduled_time && (
                                          <span className="event-time">
                                            {String(
                                              training.scheduled_time
                                            ).slice(
                                              0,
                                              5
                                            )}
                                          </span>
                                        )}

                                      </div>

                                    </div>
                                  );
                                }
                              )}

                          </div>

                        </>
                      )}

                    </div>
                  );
                }
              )}

            </div>

          </>
        )}


        {/* ================================================== */}
        {/* LEGEND */}
        {/* ================================================== */}

        <div className="calendar-legend">

          <span className="legend-title">
            Training Status
          </span>

          {Object.entries(
            STATUS_CONFIG
          ).map(
            ([status, config]) => (

              <div
                key={status}
                className="legend-item"
              >

                <span
                  className={`legend-color ${config.className}`}
                ></span>

                <span>
                  {config.label}
                </span>

              </div>

            )
          )}

        </div>

      </div>

    </div>
  );
}

export default TrainingCalendar;
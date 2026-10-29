import api from "./api";

// ============================================================
// GET ALL TRAININGS
// ============================================================

export const getTrainings = async (params = {}) => {
  try {
    const response = await api.get("/trainings/", {
      params,
    });

    if (Array.isArray(response.data)) {
      return response.data;
    }

    if (Array.isArray(response.data?.value)) {
      return response.data.value;
    }

    return [];
  } catch (error) {
    console.error("Failed to fetch trainings:", error);
    throw error;
  }
};


// ============================================================
// GET ONE TRAINING
// ============================================================

export const getTraining = async (id) => {
  try {
    const response = await api.get(`/trainings/${id}`);

    return response.data?.value ?? response.data;
  } catch (error) {
    console.error(`Failed to fetch training ${id}:`, error);
    throw error;
  }
};


// ============================================================
// CREATE TRAINING
// ============================================================

export const createTraining = async (data) => {
  try {
    const response = await api.post("/trainings/", data);

    return response.data;
  } catch (error) {
    console.error("Failed to create training:", error);
    throw error;
  }
};


// ============================================================
// UPDATE TRAINING
// ============================================================

export const updateTraining = async (id, data) => {
  try {
    const response = await api.put(`/trainings/${id}`, data);

    return response.data;
  } catch (error) {
    console.error(`Failed to update training ${id}:`, error);
    throw error;
  }
};


// ============================================================
// RESCHEDULE TRAINING
// ============================================================

export const rescheduleTraining = async (id, data) => {
  try {
    const response = await api.patch(
      `/trainings/${id}/reschedule`,
      data
    );

    return response.data;
  } catch (error) {
    console.error(`Failed to reschedule training ${id}:`, error);
    throw error;
  }
};


// ============================================================
// UPDATE TRAINING STATUS
// ============================================================

export const updateTrainingStatus = async (id, data) => {
  try {
    const response = await api.patch(
      `/trainings/${id}/status`,
      data
    );

    return response.data;
  } catch (error) {
    console.error(`Failed to update status for training ${id}:`, error);
    throw error;
  }
};


// ============================================================
// GET TRAINING CALENDAR
// ============================================================

export const getTrainingCalendar = async (year, month) => {
  try {
    const response = await api.get("/trainings/calendar", {
      params: {
        year,
        month,
      },
    });

    // Backend returns:
    // {
    //   value: [...],
    //   Count: 5
    // }

    if (Array.isArray(response.data)) {
      return response.data;
    }

    if (Array.isArray(response.data?.value)) {
      return response.data.value;
    }

    return [];
  } catch (error) {
    console.error(
      `Failed to fetch training calendar for ${year}-${month}:`,
      error
    );
    throw error;
  }
};
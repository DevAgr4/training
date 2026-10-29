import api from "./api";

// Get all reminders
export const getReminders = (params = {}) => {
  return api.get("/reminder-engine", {
    params,
  });
};

// Get reminders for one training
export const getTrainingReminders = (trainingId) => {
  return api.get(
    `/reminder-engine/training/${trainingId}`
  );
};

// Generate reminders for one training
export const generateTrainingReminders = (
  trainingId
) => {
  return api.post(
    `/reminder-engine/training/${trainingId}/generate`
  );
};

export default {
  getReminders,
  getTrainingReminders,
  generateTrainingReminders,
};
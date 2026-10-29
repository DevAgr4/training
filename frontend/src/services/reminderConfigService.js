import api from "./api";

// =================================
// Reminder Configurations
// =================================

export const getReminderConfigs = () => {
  return api.get("/reminders/config");
};

export const getReminderConfig = (configId) => {
  return api.get(`/reminders/config/${configId}`);
};

export const createReminderConfig = (data) => {
  return api.post("/reminders/config", data);
};

export const updateReminderConfig = (configId, data) => {
  return api.put(
    `/reminders/config/${configId}`,
    data
  );
};

export const deleteReminderConfig = (configId) => {
  return api.delete(
    `/reminders/config/${configId}`
  );
};


// =================================
// Reminder Recipients
// =================================

export const getReminderRecipients = (configId) => {
  return api.get(
    `/reminders/config/${configId}/recipients`
  );
};

export const addReminderRecipient = (
  configId,
  data
) => {
  return api.post(
    `/reminders/config/${configId}/recipients`,
    data
  );
};

export const deleteReminderRecipient = (
  configId,
  recipientId
) => {
  return api.delete(
    `/reminders/config/${configId}/recipients/${recipientId}`
  );
};


// =================================
// HODs
// =================================

export const getHODs = () => {
  return api.get("/recipients/hods");
};


// =================================
// Line Managers
// =================================

export const getLineManagers = () => {
  return api.get("/recipients/line-managers");
};


// =================================
// Master Recipient Data
// =================================

export const getMasterRecipients = () => {
  return api.get("/recipients/master");
};


// =================================
// Update HOD
// =================================

export const updateHOD = (hodId, data) => {
  return api.put(
    `/recipients/hods/${hodId}`,
    data
  );
};


// =================================
// Update Line Manager
// =================================

export const updateLineManager = (
  managerId,
  data
) => {
  return api.put(
    `/recipients/line-managers/${managerId}`,
    data
  );
};


// =================================
// Delete HOD
// =================================

export const deleteHOD = (hodId) => {
  return api.delete(
    `/recipients/hods/${hodId}`
  );
};


// =================================
// Delete Line Manager
// =================================

export const deleteLineManager = (managerId) => {
  return api.delete(
    `/recipients/line-managers/${managerId}`
  );
};


// =================================
// Upload Master Recipient Excel
// =================================

export const uploadMasterRecipients = (file) => {
  const formData = new FormData();

  formData.append("file", file);

  return api.post(
    "/recipients/master/upload",
    formData
  );
};


// =================================
// Default Export
// =================================

export default {
  // Reminder Configurations
  getReminderConfigs,
  getReminderConfig,
  createReminderConfig,
  updateReminderConfig,
  deleteReminderConfig,

  // Reminder Recipients
  getReminderRecipients,
  addReminderRecipient,
  deleteReminderRecipient,

  // HODs
  getHODs,

  // Line Managers
  getLineManagers,

  // Master Data
  getMasterRecipients,
  updateHOD,
  updateLineManager,
  deleteHOD,
  deleteLineManager,
  uploadMasterRecipients,
};
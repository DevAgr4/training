import api from "./api";

// Get complete post-training status
export const getPostTrainingStatus = (trainingId) => {
  return api.get(`/post-training/${trainingId}`);
};

// Mark training as conducted / not conducted
export const markTrainingConducted = (trainingId, data) => {
  return api.post(
    `/post-training/${trainingId}/conducted`,
    data
  );
};

// Update attendance or OJT document status
export const updateDocumentStatus = (
  trainingId,
  documentType,
  data
) => {
  return api.patch(
    `/post-training/${trainingId}/documents/${documentType}`,
    data
  );
};

// Get attendance / OJT documents
export const getTrainingDocuments = (trainingId) => {
  return api.get(
    `/post-training/${trainingId}/documents`
  );
};

export default {
  getPostTrainingStatus,
  markTrainingConducted,
  updateDocumentStatus,
  getTrainingDocuments,
};
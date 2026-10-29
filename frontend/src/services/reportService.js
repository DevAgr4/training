import api from "./api";

export const getTrainingPercentageReport = (params = {}) => {
  return api.get("/reports/training-percentage", {
    params,
  });
};
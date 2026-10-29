import api from "./api";

export const getDepartments = () => {
  return api.get("/departments");
};

export default {
  getDepartments,
};
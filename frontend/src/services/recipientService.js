import api from "./api";

export const getHODs = () => {
  return api.get("/recipients/hods");
};

export const getLineManagers = () => {
  return api.get("/recipients/line-managers");
};
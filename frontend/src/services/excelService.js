import api from "./api";

export const uploadExcel = (file) => {
  const formData = new FormData();

  formData.append(
    "file",
    file
  );

  return api.post(
    "/excel/upload",
    formData,
    {
      headers: {
        "Content-Type":
          "multipart/form-data",
      },
    }
  );
};

export const importExcel = (file) => {
  const formData = new FormData();

  formData.append(
    "file",
    file
  );

  return api.post(
    "/excel/import",
    formData,
    {
      headers: {
        "Content-Type":
          "multipart/form-data",
      },
    }
  );
};

export default {
  uploadExcel,
  importExcel,
};
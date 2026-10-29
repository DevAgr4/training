import api from "./api";

export const getWhatsAppTemplates = () => {
  return api.get("/whatsapp-templates");
};

export const getDefaultWhatsAppTemplate = (templateType) => {
  return api.get(
    `/whatsapp-templates/default/${templateType}`
  );
};

export const createWhatsAppTemplate = (data) => {
  return api.post("/whatsapp-templates", data);
};

export const updateWhatsAppTemplate = (templateId, data) => {
  return api.put(
    `/whatsapp-templates/${templateId}`,
    data
  );
};

export default {
  getWhatsAppTemplates,
  getDefaultWhatsAppTemplate,
  createWhatsAppTemplate,
  updateWhatsAppTemplate,
};
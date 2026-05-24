import api from "./client";

export const fetchKnowledgePoints = (params: {
  subject_id?: number;
  parent_id?: number;
}) => api.get("/api/knowledge-points", { params }).then((r) => r.data);

export const fetchKnowledgePoint = (id: number) =>
  api.get(`/api/knowledge-points/${id}`).then((r) => r.data);

export const summarizeKnowledgePoint = (id: number) =>
  api.post(`/api/knowledge-points/${id}/summarize`).then((r) => r.data);

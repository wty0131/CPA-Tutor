import api from "./client";

export const fetchWrongAnswers = (params: {
  subject_id?: number;
  due_only?: boolean;
  page?: number;
  page_size?: number;
}) => api.get("/api/wrongbook", { params }).then((r) => r.data);

export const reviewWrongAnswer = (id: number, quality: number) =>
  api.post(`/api/wrongbook/${id}/review`, { quality }).then((r) => r.data);

export const deleteWrongAnswer = (id: number) =>
  api.delete(`/api/wrongbook/${id}`).then((r) => r.data);

export const fetchWrongStats = () =>
  api.get("/api/wrongbook/stats").then((r) => r.data);

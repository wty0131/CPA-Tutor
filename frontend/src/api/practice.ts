import api from "./client";

export const submitAnswer = (question_id: number, answer: string) =>
  api.post("/api/practice/submit", { question_id, answer }).then((r) => r.data);

export const fetchHistory = (page = 1, page_size = 20) =>
  api.get("/api/practice/history", { params: { page, page_size } }).then((r) => r.data);

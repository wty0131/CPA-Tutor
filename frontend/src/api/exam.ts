import api from "./client";

export const generateExam = (subject_id?: number) =>
  api.post("/api/exam/generate", null, { params: { subject_id } }).then((r) => r.data);

export const submitExam = (answers: Record<string, string>) =>
  api.post("/api/exam/submit", { answers }).then((r) => r.data);

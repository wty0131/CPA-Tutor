import api from "./client";

export interface Question {
  id: number;
  subject_id: number;
  subject_name: string;
  type: string;
  stem: string;
  options: { label: string; text: string }[];
  answer: string;
  explanation: string;
  difficulty: number;
  knowledge_points: { id: number; name: string }[];
}

export const fetchQuestions = (params: {
  subject_id?: number;
  kp_id?: number;
  difficulty?: number;
  type?: string;
  page?: number;
  page_size?: number;
}) => api.get("/api/questions", { params }).then((r) => r.data);

export const fetchQuestion = (id: number) =>
  api.get<Question>(`/api/questions/${id}`).then((r) => r.data);

export const fetchExplanation = (id: number) =>
  api.get(`/api/questions/${id}/explanation`).then((r) => r.data);

import api from "./client";

export interface Subject {
  id: number;
  code: string;
  name: string;
  description: string;
  question_count: number;
  wrong_count: number;
}

export const fetchSubjects = () => api.get<Subject[]>("/api/subjects").then((r) => r.data);
export const fetchSubject = (id: number) => api.get(`/api/subjects/${id}`).then((r) => r.data);

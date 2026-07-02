import { apiFetch } from "@/lib/api";

export interface SaveJobStatus {
  job_id: string;
  status: "pending" | "processing" | "done" | "error";
  video_id: number | null;
  error_message: string | null;
  completed_at: number | null;
}

export interface SaveMomentResponse {
  job_id: string;
  status: "pending";
  message: string;
}

export const momentsService = {
  save: (title?: string) =>
    apiFetch<SaveMomentResponse>("/moments/save", {
      method: "POST",
      body: JSON.stringify({ title: title ?? null }),
    }),

  getJobStatus: (jobId: string) =>
    apiFetch<SaveJobStatus>(`/moments/jobs/${jobId}`),
};

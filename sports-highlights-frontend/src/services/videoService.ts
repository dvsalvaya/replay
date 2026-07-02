import { apiFetch, getAuthToken } from "@/lib/api";

export interface Video {
  id: number;
  filename: string;
  title: string | null;
  duration_seconds: number;
  file_size_bytes: number;
  created_at: string;
  expires_at: string;
  days_until_expiry: number;
  is_expiring_soon: boolean;
}

export interface VideoListResponse {
  items: Video[];
  total: number;
  page: number;
  page_size: number;
}

export const videoService = {
  list: (page = 1, pageSize = 20) =>
    apiFetch<VideoListResponse>(`/videos?page=${page}&page_size=${pageSize}`),

  delete: (id: number) =>
    apiFetch<{ message: string }>(`/videos/${id}`, { method: "DELETE" }),

  getStreamUrl: (id: number): string => {
    const token = getAuthToken();
    return `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/videos/${id}/stream?token=${token}`;
  },
};

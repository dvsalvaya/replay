import { apiFetch } from "@/lib/api";

export interface CameraStatus {
  is_running: boolean;
  device_index: number;
  fps: number;
  resolution: [number, number];
  error: string | null;
  is_healthy: boolean;
}

export const cameraService = {
  getStatus: () => apiFetch<CameraStatus>("/camera/status"),
  start: () =>
    apiFetch<{ message: string }>("/camera/start", { method: "POST" }),
  stop: () =>
    apiFetch<{ message: string }>("/camera/stop", { method: "POST" }),
  getStreamUrl: () => `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/camera/stream`,
};

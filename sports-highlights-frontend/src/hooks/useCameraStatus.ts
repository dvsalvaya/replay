import { useState, useEffect, useCallback } from "react";
import { cameraService, type CameraStatus } from "@/services/cameraService";

export function useCameraStatus(pollIntervalMs = 3000) {
  const [status, setStatus] = useState<CameraStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await cameraService.getStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao buscar status");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchStatus, pollIntervalMs]);

  return { status, isLoading, error, refetch: fetchStatus };
}

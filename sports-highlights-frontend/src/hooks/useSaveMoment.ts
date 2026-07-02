import { useState, useRef, useCallback } from "react";
import { momentsService } from "@/services/momentsService";
import type { SaveJobStatus } from "@/services/momentsService";

export type SaveState =
  | { phase: "idle" }
  | { phase: "saving"; jobId: string; message: string }
  | { phase: "done"; videoId: number }
  | { phase: "error"; message: string };

export function useSaveMoment() {
  const [state, setState] = useState<SaveState>({ phase: "idle" });
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollJobStatus = useCallback(
    (jobId: string) => {
      pollRef.current = setInterval(async () => {
        try {
          const job: SaveJobStatus = await momentsService.getJobStatus(jobId);

          if (job.status === "done" && job.video_id) {
            stopPolling();
            setState({ phase: "done", videoId: job.video_id });
            setTimeout(() => setState({ phase: "idle" }), 3000);
          } else if (job.status === "error") {
            stopPolling();
            setState({
              phase: "error",
              message: job.error_message ?? "Erro desconhecido",
            });
            setTimeout(() => setState({ phase: "idle" }), 5000);
          }
        } catch {
          stopPolling();
          setState({
            phase: "error",
            message: "Erro ao verificar status do salvamento",
          });
          setTimeout(() => setState({ phase: "idle" }), 5000);
        }
      }, 1500);
    },
    [stopPolling]
  );

  const saveMoment = useCallback(
    async (title?: string) => {
      if (state.phase !== "idle") return;

      try {
        const response = await momentsService.save(title);
        setState({
          phase: "saving",
          jobId: response.job_id,
          message: response.message,
        });
        pollJobStatus(response.job_id);
      } catch (err) {
        setState({
          phase: "error",
          message:
            err instanceof Error ? err.message : "Erro ao iniciar salvamento",
        });
        setTimeout(() => setState({ phase: "idle" }), 5000);
      }
    },
    [state.phase, pollJobStatus]
  );

  return { state, saveMoment };
}

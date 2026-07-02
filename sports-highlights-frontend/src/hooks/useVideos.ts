import { useState, useEffect, useCallback } from "react";
import { videoService } from "@/services/videoService";
import type { Video, VideoListResponse } from "@/services/videoService";

interface UseVideosReturn {
  videos: Video[];
  total: number;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  deleteVideo: (id: number) => Promise<void>;
  isDeleting: boolean;
}

export function useVideos(): UseVideosReturn {
  const [data, setData] = useState<VideoListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVideos = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await videoService.list();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar vídeos");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  const deleteVideo = useCallback(async (id: number) => {
    try {
      setIsDeleting(true);
      await videoService.delete(id);
      setData((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.filter((v) => v.id !== id),
              total: prev.total - 1,
            }
          : null
      );
    } catch (err) {
      throw err;
    } finally {
      setIsDeleting(false);
    }
  }, []);

  return {
    videos: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    error,
    refetch: fetchVideos,
    deleteVideo,
    isDeleting,
  };
}

import { useEffect, useRef } from "react";
import type { Video } from "@/services/videoService";
import { videoService } from "@/services/videoService";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface VideoModalProps {
  video: Video | null;
  onClose: () => void;
}

export function VideoModal({ video, onClose }: VideoModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (!video && videoRef.current) {
      videoRef.current.pause();
      videoRef.current.src = "";
    }
  }, [video]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onClose]);

  if (!video) return null;

  const streamUrl = videoService.getStreamUrl(video.id);
  const title = video.title ?? video.filename;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm transition-all duration-300"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl mx-4 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800 bg-slate-900 text-slate-100">
          <h2 className="text-sm font-semibold truncate text-slate-200">{title}</h2>
          <Button
            size="sm"
            variant="ghost"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 flex items-center gap-1"
          >
            <X className="h-4 w-4" /> Fechar
          </Button>
        </div>

        {/* Player */}
        <div className="bg-black aspect-video w-full">
          <video
            ref={videoRef}
            src={streamUrl}
            controls
            autoPlay
            className="w-full h-full object-contain"
          >
            Seu browser não suporta reprodução de vídeo.
          </video>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-950 text-xs text-slate-400 flex gap-5">
          <span>
            {new Date(video.created_at).toLocaleString("pt-BR")}
          </span>
          <span className="text-slate-800">|</span>
          <span>
            Duração: {Math.floor(video.duration_seconds / 60)}:
            {String(Math.floor(video.duration_seconds % 60)).padStart(2, "0")}
          </span>
          <span className="text-slate-800">|</span>
          <span>
            Tamanho: {(video.file_size_bytes / (1024 * 1024)).toFixed(1)} MB
          </span>
        </div>
      </div>
    </div>
  );
}

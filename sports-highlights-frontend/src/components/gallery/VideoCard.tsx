import type { Video } from "@/services/videoService";
import { Button } from "@/components/ui/button";
import { Play, Trash2 } from "lucide-react";

interface VideoCardProps {
  video: Video;
  onPlay: (video: Video) => void;
  onDelete: (id: number) => void;
  isDeleting: boolean;
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatFileSize(bytes: number): string {
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function VideoCard({
  video,
  onPlay,
  onDelete,
  isDeleting,
}: VideoCardProps) {
  const title = video.title ?? video.filename;

  return (
    <div className="flex items-center justify-between py-4 px-5 border-b border-slate-800 bg-slate-900/50 hover:bg-slate-900 text-slate-50 transition-colors last:border-0">
      {/* Info */}
      <div className="flex-1 min-w-0 pr-4">
        <p className="text-sm font-semibold truncate text-slate-200">{title}</p>
        <p className="text-xs text-slate-400 mt-1 flex flex-wrap gap-x-2 gap-y-1">
          <span>{formatDate(video.created_at)}</span>
          <span className="text-slate-600">•</span>
          <span>{formatDuration(video.duration_seconds)}</span>
          <span className="text-slate-600">•</span>
          <span>{formatFileSize(video.file_size_bytes)}</span>
        </p>
        {/* Expire status */}
        <div className="mt-2">
          {video.is_expiring_soon ? (
            <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/20">
              Expira em {video.days_until_expiry}d
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-400 border border-slate-800/50">
              Expira em {video.days_until_expiry}d
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onPlay(video)}
          className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1"
        >
          <Play className="h-3 w-3 fill-current" /> Assistir
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={() => onDelete(video.id)}
          disabled={isDeleting}
          className="bg-rose-600 hover:bg-rose-700 text-white flex items-center gap-1"
        >
          <Trash2 className="h-3 w-3" /> Deletar
        </Button>
      </div>
    </div>
  );
}

import type { Video } from "@/services/videoService";
import { VideoCard } from "./VideoCard";
import { Film } from "lucide-react";

interface VideoListProps {
  videos: Video[];
  onPlay: (video: Video) => void;
  onDelete: (id: number) => void;
  isDeleting: boolean;
}

export function VideoList({
  videos,
  onPlay,
  onDelete,
  isDeleting,
}: VideoListProps) {
  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-500 space-y-3">
        <Film className="h-12 w-12 text-slate-700" />
        <p className="text-lg font-medium text-slate-400">Nenhum momento salvo ainda.</p>
        <p className="text-sm text-slate-500">
          Inicie a câmera no Dashboard e clique em "Salvar Momento" para começar.
        </p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-slate-800 rounded-xl border border-slate-800 bg-slate-900 overflow-hidden shadow-lg">
      {videos.map((video) => (
        <VideoCard
          key={video.id}
          video={video}
          onPlay={onPlay}
          onDelete={onDelete}
          isDeleting={isDeleting}
        />
      ))}
    </div>
  );
}

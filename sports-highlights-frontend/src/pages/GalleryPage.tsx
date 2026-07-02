import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useVideos } from "@/hooks/useVideos";
import { VideoList } from "@/components/gallery/VideoList";
import { VideoModal } from "@/components/gallery/VideoModal";
import type { Video } from "@/services/videoService";
import { Button } from "@/components/ui/button";

export function GalleryPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const { videos, total, isLoading, error, deleteVideo, isDeleting } = useVideos();
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handlePlay = useCallback((video: Video) => {
    setSelectedVideo(video);
  }, []);

  const handleCloseModal = useCallback(() => {
    setSelectedVideo(null);
  }, []);

  const handleDelete = useCallback(async (id: number) => {
    if (selectedVideo?.id === id) {
      setSelectedVideo(null);
    }
    try {
      setDeleteError(null);
      await deleteVideo(id);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Erro ao deletar vídeo");
    }
  }, [deleteVideo, selectedVideo]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 px-6 py-4 flex items-center justify-between sticky top-0 backdrop-blur-md z-40">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-slate-100 to-slate-400 bg-clip-text text-transparent">
            Sports Highlights
          </h1>
          <nav className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/dashboard")}
              className="text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            >
              Câmera
            </Button>
            <Button
              variant="secondary"
              size="sm"
              className="bg-slate-800 text-slate-100 hover:bg-slate-700"
            >
              Galeria
            </Button>
          </nav>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          className="text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
        >
          Sair
        </Button>
      </header>

      {/* Conteúdo */}
      <main className="max-w-3xl mx-auto px-6 py-8">
        {/* Título + contador */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-slate-100">Momentos Salvos</h2>
            <p className="text-sm text-slate-400 mt-1">
              Todos os momentos capturados e registrados localmente.
            </p>
          </div>
          {!isLoading && (
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              {total} {total === 1 ? "vídeo" : "vídeos"}
            </span>
          )}
        </div>

        {/* Estados */}
        {isLoading && (
          <div className="flex justify-center py-20 text-slate-400">
            <p>Carregando galeria...</p>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-400 mb-6">
            {error}
          </div>
        )}

        {deleteError && (
          <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-400 mb-6">
            {deleteError}
          </div>
        )}

        {!isLoading && !error && (
          <VideoList
            videos={videos}
            onPlay={handlePlay}
            onDelete={handleDelete}
            isDeleting={isDeleting}
          />
        )}
      </main>

      {/* Modal */}
      <VideoModal video={selectedVideo} onClose={handleCloseModal} />
    </div>
  );
}

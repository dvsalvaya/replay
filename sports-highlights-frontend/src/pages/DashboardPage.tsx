import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { useCameraStatus } from "@/hooks/useCameraStatus";
import { useSaveMoment } from "@/hooks/useSaveMoment";
import { cameraService } from "@/services/cameraService";
import { getAuthToken } from "@/lib/api";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Radio,
  Wifi,
  WifiOff,
  Video,
  Play,
  Square,
  AlertCircle,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";

interface HealthResponse {
  status: string;
  version: string;
}

export function DashboardPage() {
  const { data: health, loading: healthLoading, error: healthError } = useApi<HealthResponse>("/health", {
    immediate: true,
  });

  const {
    status: cameraStatus,
    isLoading: cameraLoading,
    error: cameraError,
    refetch: refetchCamera,
  } = useCameraStatus(3000);

  const { state: saveState, saveMoment } = useSaveMoment();
  const [momentTitle, setMomentTitle] = useState("");

  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const isConnected = !healthLoading && !healthError && health?.status === "ok";
  const isCameraRunning = !!cameraStatus?.is_running;

  const handleStartCamera = async () => {
    setActionLoading(true);
    setActionError(null);
    try {
      await cameraService.start();
      await refetchCamera();
    } catch (err: any) {
      setActionError(err.message || "Falha ao iniciar a câmera.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopCamera = async () => {
    setActionLoading(true);
    setActionError(null);
    try {
      await cameraService.stop();
      await refetchCamera();
    } catch (err: any) {
      setActionError(err.message || "Falha ao parar a câmera.");
    } finally {
      setActionLoading(false);
    }
  };

  const token = getAuthToken() || "";
  const streamUrl = `${cameraService.getStreamUrl()}?token=${token}`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-100 to-slate-400 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p className="text-sm text-slate-400">
          Gerenciamento e monitoramento da quadra local.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Server Status Card */}
        <Card className="border-slate-800 bg-slate-900 text-slate-50">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">
              Status do Servidor
            </CardTitle>
            {healthLoading ? (
              <div className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
            ) : isConnected ? (
              <Wifi className="h-4 w-4 text-emerald-500" />
            ) : (
              <WifiOff className="h-4 w-4 text-rose-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {healthLoading
                ? "Verificando..."
                : isConnected
                ? "Backend conectado"
                : "Desconectado"}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {isConnected
                ? `Versão da API: ${health?.version}`
                : "Não foi possível conectar ao servidor local."}
            </p>
          </CardContent>
        </Card>

        {/* Camera Status Card */}
        <Card className="border-slate-800 bg-slate-900 text-slate-50">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">
              Status da Câmera
            </CardTitle>
            {cameraLoading ? (
              <div className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
            ) : isCameraRunning ? (
              <Radio className="h-4 w-4 text-emerald-500 animate-pulse" />
            ) : (
              <Video className="h-4 w-4 text-slate-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="text-2xl font-bold">
                {cameraLoading
                  ? "Verificando..."
                  : isCameraRunning
                  ? "Capturando"
                  : "Parada"}
              </div>
              {!cameraLoading && (
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold leading-5 ${
                    isCameraRunning
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {isCameraRunning ? "Ativa" : "Inativa"}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {isCameraRunning && cameraStatus?.resolution
                ? `Resolução: ${cameraStatus.resolution[0]}x${cameraStatus.resolution[1]} @ ${cameraStatus.fps} FPS`
                : "A câmera não está transmitindo."}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Save Moment Controls Card */}
      <Card className="border-slate-800 bg-slate-900 text-slate-50">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">
            Salvar Jogada / Destaque
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-slate-400">
            Grave instantaneamente os últimos 120 segundos capturados pela câmera
            como um arquivo MP4 local.
          </p>

          <div className="space-y-2 max-w-md">
            <Label htmlFor="moment-title" className="text-xs text-slate-400">
              Título do Destaque (Opcional)
            </Label>
            <Input
              id="moment-title"
              type="text"
              placeholder="Ex: Gol de placa, Defesa incrível..."
              value={momentTitle}
              onChange={(e) => setMomentTitle(e.target.value)}
              disabled={!isCameraRunning || saveState.phase !== "idle"}
              className="border-slate-800 bg-slate-950 text-slate-50 focus-visible:ring-purple-500"
            />
          </div>

          <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center pt-2">
            {saveState.phase === "idle" && (
              <Button
                onClick={() => {
                  saveMoment(momentTitle || undefined);
                  setMomentTitle("");
                }}
                disabled={!isCameraRunning || actionLoading}
                className="bg-purple-600 hover:bg-purple-700 text-white font-semibold flex items-center justify-center gap-2"
              >
                <Video className="h-4 w-4" />
                Salvar Momento
              </Button>
            )}

            {saveState.phase === "saving" && (
              <Button
                disabled
                className="bg-purple-600/50 text-purple-300 font-semibold flex items-center justify-center gap-2 cursor-wait"
              >
                <Loader2 className="h-4 w-4 animate-spin" />
                Salvando... ({saveState.message})
              </Button>
            )}

            {saveState.phase === "done" && (
              <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-lg text-sm font-medium">
                <CheckCircle2 className="h-4 w-4 animate-bounce" />
                Momento salvo com sucesso! (Vídeo #{saveState.videoId})
              </div>
            )}

            {saveState.phase === "error" && (
              <div className="flex items-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/20 px-4 py-2 rounded-lg text-sm font-medium">
                <XCircle className="h-4 w-4" />
                Erro: {saveState.message}
              </div>
            )}

            {!isCameraRunning && saveState.phase === "idle" && (
              <span className="text-xs text-slate-500">
                (Inicie a câmera primeiro para habilitar o salvamento)
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Camera Live Stream Card */}
      <Card className="border-slate-800 bg-slate-900 text-slate-50 overflow-hidden">
        <CardHeader className="border-b border-slate-800">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold">
              Preview da Câmera ao Vivo
            </CardTitle>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300"
                disabled={isCameraRunning || actionLoading}
                onClick={handleStartCamera}
              >
                <Play className="h-4 w-4 mr-2" /> Iniciar
              </Button>
              <Button
                variant="destructive"
                size="sm"
                className="bg-rose-600 hover:bg-rose-700 text-white"
                disabled={!isCameraRunning || actionLoading}
                onClick={handleStopCamera}
              >
                <Square className="h-4 w-4 mr-2" /> Parar
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="relative aspect-video w-full bg-slate-950 flex items-center justify-center">
            {isCameraRunning ? (
              <img
                src={streamUrl}
                alt="Live Camera Feed"
                className="h-full w-full object-cover"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-500 space-y-2">
                <Video className="h-12 w-12 text-slate-700" />
                <span className="text-sm font-medium">Câmera parada</span>
                <span className="text-xs text-slate-600">
                  Clique em Iniciar para iniciar a captura de vídeo.
                </span>
              </div>
            )}
          </div>
          {(cameraError || actionError || (cameraStatus && cameraStatus.error)) && (
            <div className="p-4 border-t border-slate-800 bg-rose-500/10 text-rose-400 text-sm flex items-start gap-2">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold">Aviso do Sistema</p>
                <p className="text-xs">
                  {actionError || cameraError || (cameraStatus && cameraStatus.error)}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

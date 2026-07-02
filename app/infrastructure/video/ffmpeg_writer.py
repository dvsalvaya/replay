import os
import shutil
import subprocess
import tempfile
from app.config import settings
from app.core.logging_config import get_logger
from app.domain.camera.entities import Frame
from app.domain.camera.interfaces import IVideoWriter, VideoWriteError

logger = get_logger(__name__)


class FFmpegWriter(IVideoWriter):
    """
    Implementação de IVideoWriter usando FFmpeg via subprocess.

    Estratégia:
    1. Criar diretório temporário
    2. Salvar cada frame como arquivo JPEG numerado (frame_0001.jpg, ...)
    3. Chamar FFmpeg com input pattern para encodar MP4
    4. Limpar temporários independente de sucesso/falha
    """

    def write(
        self,
        frames: list[Frame],
        output_path: str,
        fps: float,
    ) -> tuple[str, float]:
        if not frames:
            raise VideoWriteError("Nenhum frame para processar")

        # Garantir que o diretório de saída existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Garantir que o diretório temp existe
        os.makedirs(settings.temp_dir, exist_ok=True)

        temp_dir = tempfile.mkdtemp(dir=settings.temp_dir)

        try:
            # 1. Salvar frames como JPEGs numerados
            self._write_frames_to_disk(frames, temp_dir)

            # 2. Montar e executar comando FFmpeg
            duration = self._run_ffmpeg(
                temp_dir=temp_dir,
                output_path=output_path,
                fps=fps,
                frame_count=len(frames),
            )

            return output_path, duration

        except subprocess.TimeoutExpired:
            raise VideoWriteError("FFmpeg excedeu o tempo limite de processamento")
        except subprocess.CalledProcessError as e:
            raise VideoWriteError(
                f"FFmpeg falhou com código {e.returncode}: {e.stderr}"
            )
        except OSError as e:
            raise VideoWriteError(f"Erro de disco ao salvar vídeo: {e}")
        finally:
            # Sempre limpar temporários, sucesso ou falha
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _write_frames_to_disk(self, frames: list[Frame], temp_dir: str) -> None:
        """Salva frames como JPEGs numerados no diretório temporário."""
        for i, frame in enumerate(frames):
            frame_path = os.path.join(temp_dir, f"frame_{i:06d}.jpg")
            with open(frame_path, "wb") as f:
                f.write(frame.data)

    def _run_ffmpeg(
        self,
        temp_dir: str,
        output_path: str,
        fps: float,
        frame_count: int,
    ) -> float:
        """
        Executa FFmpeg para encodar frames JPEG em MP4.
        Loga stderr mesmo em caso de sucesso (pode conter warnings úteis).
        Retorna a duração calculada em segundos.
        """
        input_pattern = os.path.join(temp_dir, "frame_%06d.jpg")

        cmd = [
            settings.ffmpeg_path,
            "-y",                          # sobrescrever sem perguntar
            "-framerate", str(fps),        # FPS de entrada
            "-i", input_pattern,           # padrão de entrada
            "-c:v", "libx264",             # codec H.264
            "-crf", str(settings.ffmpeg_crf),       # qualidade (23=default, menor=melhor)
            "-preset", settings.ffmpeg_preset,       # velocidade de encode (ultrafast no MVP)
            "-pix_fmt", "yuv420p",         # compatibilidade máxima (iOS, WhatsApp, etc)
            "-movflags", "+faststart",     # permite streaming progressivo
            output_path,
        ]

        logger.debug(f"FFmpeg comando: {' '.join(cmd)}")
        logger.info(f"FFmpeg iniciado: {frame_count} frames @ {fps:.1f}fps → {output_path}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutos de timeout máximo
        )

        # Logar stderr do FFmpeg independente do resultado
        # FFmpeg escreve tudo no stderr — mesmo em execuções bem-sucedidas
        if result.stderr:
            stderr_lines = result.stderr.strip().splitlines()
            relevant = [
                line
                for line in stderr_lines
                if any(
                    kw in line.lower()
                    for kw in ["error", "warning", "invalid", "failed", "unable"]
                )
            ]
            if relevant:
                logger.warning(f"FFmpeg avisos: {'; '.join(relevant[-3:])}")
            else:
                logger.debug(
                    f"FFmpeg stderr (últimas 3 linhas): {'; '.join(stderr_lines[-3:])}"
                )

        if result.returncode != 0:
            logger.error(
                f"FFmpeg falhou (código {result.returncode}):\n{result.stderr[-2000:]}"
            )
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

        # Verificar que o arquivo foi criado e tem tamanho > 0
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise VideoWriteError(
                f"FFmpeg completou mas arquivo não foi criado: {output_path}"
            )

        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        duration = frame_count / fps
        logger.info(
            f"FFmpeg concluído: {duration:.1f}s de vídeo, {file_size_mb:.1f} MB, "
            f"arquivo: {os.path.basename(output_path)}"
        )

        return duration

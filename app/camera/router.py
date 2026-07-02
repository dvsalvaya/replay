import asyncio
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from app.application.camera.use_cases import CameraUseCases
from app.camera.dependencies import get_camera_use_cases
from app.camera.schemas import CameraStatusResponse, MessageResponse
from app.config import settings
from app.core.security import get_current_user, verify_token
from app.domain.camera.interfaces import CameraAlreadyRunningError, CameraError

router = APIRouter(prefix="/camera", tags=["camera"])


@router.post("/start", response_model=MessageResponse)
def start_camera(
    use_cases: CameraUseCases = Depends(get_camera_use_cases),
    _: str = Depends(get_current_user),
):
    """Inicia a captura da câmera."""
    try:
        use_cases.start_capture()
        return MessageResponse(message="Câmera iniciada com sucesso")
    except CameraAlreadyRunningError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Câmera já está em execução",
        )
    except CameraError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@router.post("/stop", response_model=MessageResponse)
def stop_camera(
    use_cases: CameraUseCases = Depends(get_camera_use_cases),
    _: str = Depends(get_current_user),
):
    """Para a captura da câmera."""
    use_cases.stop_capture()
    return MessageResponse(message="Câmera parada")


@router.get("/status", response_model=CameraStatusResponse)
def get_camera_status(
    use_cases: CameraUseCases = Depends(get_camera_use_cases),
    _: str = Depends(get_current_user),
):
    """Retorna o status atual da câmera."""
    status_obj = use_cases.get_status()
    return CameraStatusResponse(
        is_running=status_obj.is_running,
        device_index=status_obj.device_index,
        fps=status_obj.fps,
        resolution=status_obj.resolution,
        error=status_obj.error,
        is_healthy=status_obj.is_healthy,
    )


@router.get("/stream")
async def stream_camera(
    token: str = Query(...),
    use_cases: CameraUseCases = Depends(get_camera_use_cases),
):
    """
    Stream MJPEG ao vivo da câmera.
    Compatível com <img src="/camera/stream?token=<jwt>"> no frontend.
    """
    # Valida o token recebido via query param (necessário para tag <img>)
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    username = payload.get("sub")
    if not username or not secrets.compare_digest(username, settings.ADMIN_USERNAME):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    if not use_cases.is_capturing():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Câmera não está em execução. Chame POST /camera/start primeiro.",
        )

    async def frame_generator():
        while True:
            frame = use_cases.get_current_frame()
            if frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(frame.data)).encode() + b"\r\n"
                    b"\r\n" + frame.data + b"\r\n"
                )
            await asyncio.sleep(1 / settings.camera_fps)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

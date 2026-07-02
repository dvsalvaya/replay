from functools import lru_cache
from app.application.camera.use_cases import CameraUseCases
from app.infrastructure.camera.opencv_adapter import OpenCVCameraAdapter


@lru_cache(maxsize=1)
def get_camera_use_cases() -> CameraUseCases:
    """
    Retorna instância singleton de CameraUseCases.
    lru_cache garante que apenas uma instância existe durante o ciclo de vida da app.
    """
    adapter = OpenCVCameraAdapter()
    return CameraUseCases(adapter=adapter)

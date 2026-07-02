from app.core.logging_config import setup_logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router
from app.core.exceptions import register_exception_handlers
from app.database import Base, engine
from app.videos.router import router as videos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # Inicializa o banco de dados na inicialização da aplicação
    Base.metadata.create_all(bind=engine)
    # Pré-aquecer a dependência singleton de câmera
    from app.camera.dependencies import get_camera_use_cases
    get_camera_use_cases()

    # Scheduler de limpeza TTL
    from app.infrastructure.scheduler.apscheduler import scheduler
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Sports Highlights API", version="0.1.0", lifespan=lifespan
)

# Configura CORS para o frontend local em Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra os handlers globais de exceção
register_exception_handlers(app)

# Registra as rotas
from app.camera.router import router as camera_router
from app.moments.router import router as moments_router
from app.admin.router import router as admin_router
app.include_router(auth_router)
app.include_router(videos_router)
app.include_router(camera_router)
app.include_router(moments_router)
app.include_router(admin_router)


@app.get("/health", tags=["Health"])
def health():
    """
    Endpoint público para verificação de integridade do sistema.
    """
    return {"status": "ok", "version": "0.1.0"}

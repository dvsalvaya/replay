from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registra todos os handlers globais de exceção na aplicação FastAPI.
    Chamar em main.py após criar a instância do app.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        Handler para HTTPExceptions explicitamente lançadas nas rotas (404, 401, etc).
        Loga como WARNING pois são erros esperados de uso da API.
        """
        logger.warning(
            f"HTTP {exc.status_code} | {request.method} {request.url.path} | {exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handler para erros de validação Pydantic (body inválido, params errados).
        Retorna os erros de forma estruturada sem stack trace.
        """
        errors = exc.errors()
        logger.warning(
            f"Validação falhou | {request.method} {request.url.path} | "
            f"{len(errors)} erro(s): {errors[0]['msg'] if errors else 'desconhecido'}"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Dados inválidos na requisição",
                "errors": [
                    {
                        "field": " → ".join(str(loc) for loc in err["loc"]),
                        "message": err["msg"],
                    }
                    for err in errors
                ],
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handler de último recurso para exceções não tratadas.
        Loga como CRITICAL com stack trace completo.
        NUNCA retorna detalhes internos ao cliente (segurança).
        """
        logger.critical(
            f"Exceção não tratada | {request.method} {request.url.path} | "
            f"{type(exc).__name__}: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Erro interno do servidor"},
        )

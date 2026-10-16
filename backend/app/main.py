import os

from fastapi import FastAPI

from app.api.errores import registrar_manejadores
from app.api.rutas import router
from app.application.servicio_ordenes import ServicioOrdenes
from app.core.logging import configurar_logging, registrar_middleware
from app.infrastructure.repositorio import RepositorioEnMemoria


def create_app() -> FastAPI:
    configurar_logging(os.getenv("LOG_LEVEL", "INFO"))
    app = FastAPI(
        title="API de órdenes de compra",
        version="1.0.0",
        description="Reto técnico QA: gestión de órdenes con reglas RN-01 a RN-06.",
    )
    app.state.servicio = ServicioOrdenes(RepositorioEnMemoria())
    registrar_manejadores(app)
    registrar_middleware(app)
    app.include_router(router)

    @app.get("/health", tags=["salud"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

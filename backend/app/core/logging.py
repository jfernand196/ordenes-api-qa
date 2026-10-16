import json
import logging
import sys
import time
from contextvars import ContextVar
from uuid import uuid4

from fastapi import FastAPI, Request

request_id_actual: ContextVar[str] = ContextVar("request_id", default="-")
CAMPOS_EXTRA = ("orden_id", "desde", "hacia", "total", "metodo", "ruta", "status", "duracion_ms")


class FormatoJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        datos = {
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
            "request_id": request_id_actual.get(),
        }
        for campo in CAMPOS_EXTRA:
            if hasattr(record, campo):
                datos[campo] = str(getattr(record, campo))
        return json.dumps(datos, ensure_ascii=False)


def configurar_logging(nivel: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(FormatoJson())
    raiz = logging.getLogger()
    raiz.handlers = [handler]
    raiz.setLevel(nivel)


def registrar_middleware(app: FastAPI) -> None:
    logger = logging.getLogger("http")

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid4())
        token = request_id_actual.set(rid)
        inicio = time.perf_counter()
        try:
            respuesta = await call_next(request)
            respuesta.headers["X-Request-ID"] = rid
            logger.info(
                "peticion",
                extra={
                    "metodo": request.method,
                    "ruta": request.url.path,
                    "status": respuesta.status_code,
                    "duracion_ms": round((time.perf_counter() - inicio) * 1000, 1),
                },
            )
            return respuesta
        finally:
            request_id_actual.reset(token)

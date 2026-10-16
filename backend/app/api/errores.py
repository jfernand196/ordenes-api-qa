from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.excepciones import (
    EstadoTerminalError,
    OrdenError,
    OrdenNoEncontradaError,
    PagoRequeridoError,
    TransicionInvalidaError,
    ValidacionOrdenError,
)

ESTADOS_HTTP: dict[type[OrdenError], tuple[int, str]] = {
    ValidacionOrdenError: (422, "Orden inválida"),
    PagoRequeridoError: (400, "La orden no ha sido pagada"),
    EstadoTerminalError: (409, "La orden está en un estado terminal"),
    TransicionInvalidaError: (409, "Transición de estado inválida"),
    OrdenNoEncontradaError: (404, "Orden no encontrada"),
}

# Pydantic devuelve mensajes en inglés; el contrato de la API es en español.
MENSAJES = {
    "missing": "Es obligatorio.",
    "greater_than": "Debe ser mayor que {gt}.",
    "too_short": "Debe tener al menos {min_length} elemento(s).",
    "string_too_short": "No puede estar vacío.",
    "extra_forbidden": "Campo no permitido.",
    "int_parsing": "Debe ser un número entero.",
    "int_type": "Debe ser un número entero.",
    "enum": "Valor no permitido. Opciones: {expected}.",
    "uuid_parsing": "No es un identificador válido.",
}
ORIGENES = {"body", "query", "path"}


def problema(
    request: Request, status: int, title: str, detail: str, codigo: str, **extra
) -> JSONResponse:
    """Respuesta de error en formato Problem Details (RFC 9457)."""
    contenido = {
        "type": f"https://errores.ordenes.local/{codigo.lower()}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "codigo": codigo,
        **extra,
    }
    return JSONResponse(
        status_code=status, content=contenido, media_type="application/problem+json"
    )


def traducir(error: dict) -> str:
    plantilla = MENSAJES.get(error["type"])
    if plantilla is None:
        return error["msg"]
    try:
        return plantilla.format(**error.get("ctx", {}))
    except (KeyError, IndexError):
        return error["msg"]


def nombre_campo(loc: tuple) -> str:
    """("body", "productos", 0, "cantidad") -> "productos.0.cantidad"."""
    partes = loc[1:] if loc and loc[0] in ORIGENES else loc
    return ".".join(str(p) for p in partes)


async def manejar_orden_error(request: Request, exc: OrdenError) -> JSONResponse:
    for clase in type(exc).__mro__:
        if clase in ESTADOS_HTTP:
            status, title = ESTADOS_HTTP[clase]
            return problema(request, status, title, exc.mensaje, exc.codigo)
    return problema(request, 500, "Error de dominio no mapeado", exc.mensaje, exc.codigo)


async def manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    errores = [{"campo": nombre_campo(e["loc"]), "mensaje": traducir(e)} for e in exc.errors()]
    return problema(
        request,
        422,
        "Solicitud inválida",
        "El cuerpo o los parámetros no son válidos.",
        "VALIDACION",
        errores=errores,
    )


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(OrdenError, manejar_orden_error)
    app.add_exception_handler(RequestValidationError, manejar_validacion)

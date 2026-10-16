# Plantillas del backend

Código base para `backend/`. Cada bloque indica su ruta. Cópialo y ajústalo, manteniendo las convenciones del SKILL.md.

Contenido:
1. Dependencias
2. Dominio (estado, excepciones, máquina de estados, orden)
3. Repositorio
4. Servicio
5. API (schemas, errores, rutas)
6. Logging
7. main.py

---

## 1. Dependencias

### requirements.txt
```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30
pydantic>=2.8,<3
```

### requirements-dev.txt
```text
-r requirements.txt
pytest>=8.2
pytest-cov>=5.0
httpx2>=2.4,<3
hypothesis>=6.100
mutmut>=3.2
ruff>=0.5
mypy>=1.10
```

---

## 2. Dominio

### app/domain/estado.py
```python
from enum import StrEnum


class Estado(StrEnum):
    CREADA = "CREADA"
    PAGADA = "PAGADA"
    ENVIADA = "ENVIADA"
    ENTREGADA = "ENTREGADA"
    CANCELADA = "CANCELADA"
```

### app/domain/excepciones.py
```python
class OrdenError(Exception):
    """Base de los errores de dominio. `codigo` enlaza el error con su regla."""

    codigo = "ORDEN"

    def __init__(self, mensaje: str, codigo: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        if codigo is not None:
            self.codigo = codigo


class ValidacionOrdenError(OrdenError):
    codigo = "VALIDACION"


class PagoRequeridoError(OrdenError):
    codigo = "RN-05"


class EstadoTerminalError(OrdenError):
    codigo = "RN-04"


class TransicionInvalidaError(OrdenError):
    codigo = "RN-06"


class OrdenNoEncontradaError(OrdenError):
    codigo = "NO_ENCONTRADA"
```

### app/domain/maquina_estados.py
```python
from app.domain.estado import Estado
from app.domain.excepciones import (
    EstadoTerminalError,
    PagoRequeridoError,
    TransicionInvalidaError,
)

TRANSICIONES: dict[Estado, frozenset[Estado]] = {
    Estado.CREADA: frozenset({Estado.PAGADA, Estado.CANCELADA}),
    Estado.PAGADA: frozenset({Estado.ENVIADA, Estado.CANCELADA}),
    # Supuesto documentado: RN-04 solo prohibe cancelar una orden ENTREGADA.
    Estado.ENVIADA: frozenset({Estado.ENTREGADA, Estado.CANCELADA}),
    Estado.ENTREGADA: frozenset(),
    Estado.CANCELADA: frozenset(),
}


def transiciones_permitidas(desde: Estado) -> list[Estado]:
    return sorted(TRANSICIONES[desde])


def validar_transicion(desde: Estado, hacia: Estado) -> None:
    """Lanza la excepcion de dominio que corresponde. El orden de las validaciones importa."""
    if not TRANSICIONES[desde]:
        raise EstadoTerminalError(
            f"La orden está en estado {desde} y no admite cambios (intento: {hacia})."
        )
    if hacia == Estado.ENVIADA and desde == Estado.CREADA:
        raise PagoRequeridoError("La orden no puede enviarse si no ha sido pagada.")
    if hacia not in TRANSICIONES[desde]:
        raise TransicionInvalidaError(f"Transición inválida de {desde} a {hacia}.")
```

### app/domain/orden.py
```python
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.domain.estado import Estado
from app.domain.excepciones import ValidacionOrdenError
from app.domain.maquina_estados import transiciones_permitidas, validar_transicion


@dataclass(frozen=True)
class LineaProducto:
    id: str
    cantidad: int
    valor_unitario: int

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidacionOrdenError("El id del producto es obligatorio.")
        if self.cantidad <= 0:
            raise ValidacionOrdenError(
                f"La cantidad del producto {self.id} debe ser mayor que cero.", "RN-02"
            )
        if self.valor_unitario <= 0:
            raise ValidacionOrdenError(
                f"El valor unitario del producto {self.id} debe ser mayor que cero."
            )

    @property
    def subtotal(self) -> int:
        return self.cantidad * self.valor_unitario


class Orden:
    """Raíz del agregado. Sus datos solo se leen; el estado solo cambia con cambiar_estado().

    Asi nadie puede saltarse la máquina de estados (orden.estado = ...) ni vaciar
    los productos después de creada la orden (RN-01).
    """

    def __init__(self, cliente: str, productos: Iterable[LineaProducto]) -> None:
        lineas = tuple(productos)  # copia inmutable: cambios a la lista original no la afectan
        if not cliente.strip():
            raise ValidacionOrdenError("El cliente es obligatorio.")
        if not lineas:
            raise ValidacionOrdenError("La orden debe contener al menos un producto.", "RN-01")
        self._id = uuid4()
        self._cliente = cliente
        self._productos = lineas
        self._estado = Estado.CREADA

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def cliente(self) -> str:
        return self._cliente

    @property
    def productos(self) -> tuple[LineaProducto, ...]:
        return self._productos

    @property
    def estado(self) -> Estado:
        return self._estado

    @property
    def total(self) -> int:  # RN-03
        return sum(p.subtotal for p in self._productos)

    @property
    def transiciones_permitidas(self) -> list[Estado]:
        return transiciones_permitidas(self._estado)

    def cambiar_estado(self, nuevo: Estado) -> Estado:
        """Aplica la transición y devuelve el estado anterior (útil para el log)."""
        validar_transicion(self._estado, nuevo)
        anterior = self._estado
        self._estado = nuevo
        return anterior

    def cancelar(self) -> Estado:
        return self.cambiar_estado(Estado.CANCELADA)
```

---

## 3. Repositorio

### app/application/puertos.py
```python
"""Puertos de la capa de aplicación: lo que la aplicación necesita del exterior.

La infraestructura los implementa; la aplicación nunca importa de la infraestructura
(inversión de dependencias, ADR-001).
"""

from typing import Protocol
from uuid import UUID

from app.domain.estado import Estado
from app.domain.orden import Orden


class RepositorioOrdenes(Protocol):
    def guardar(self, orden: Orden) -> None: ...
    def obtener(self, orden_id: UUID) -> Orden | None: ...
    def listar(self, estado: Estado | None, limit: int, offset: int) -> list[Orden]: ...
```

### app/infrastructure/repositorio.py
```python
from threading import Lock
from uuid import UUID

from app.domain.estado import Estado
from app.domain.orden import Orden


class RepositorioEnMemoria:
    """Implementación en memoria del puerto RepositorioOrdenes (ADR-002).

    Cumple el puerto por estructura (Protocol), sin importarlo: la infraestructura
    depende del dominio y la aplicación no depende de la infraestructura.
    Thread-safe para el servidor ASGI.
    """

    def __init__(self) -> None:
        self._ordenes: dict[UUID, Orden] = {}
        self._lock = Lock()

    def guardar(self, orden: Orden) -> None:
        with self._lock:
            self._ordenes[orden.id] = orden

    def obtener(self, orden_id: UUID) -> Orden | None:
        with self._lock:
            return self._ordenes.get(orden_id)

    def listar(self, estado: Estado | None, limit: int, offset: int) -> list[Orden]:
        with self._lock:
            # Más recientes primero: la última orden creada siempre aparece en la primera página.
            ordenes = list(reversed(self._ordenes.values()))
        if estado is not None:
            ordenes = [o for o in ordenes if o.estado == estado]
        return ordenes[offset : offset + limit]
```

---

## 4. Servicio

### app/application/servicio_ordenes.py
```python
import logging
from uuid import UUID

from app.application.puertos import RepositorioOrdenes
from app.domain.estado import Estado
from app.domain.excepciones import OrdenNoEncontradaError
from app.domain.orden import LineaProducto, Orden

logger = logging.getLogger("ordenes")

LIMITE_POR_DEFECTO = 50
LIMITE_MAXIMO = 100


class ServicioOrdenes:
    def __init__(self, repositorio: RepositorioOrdenes) -> None:
        self._repo = repositorio

    def crear(self, cliente: str, productos: list[LineaProducto]) -> Orden:
        orden = Orden(cliente=cliente, productos=productos)
        self._repo.guardar(orden)
        logger.info("orden_creada", extra={"orden_id": str(orden.id), "total": orden.total})
        return orden

    def obtener(self, orden_id: UUID) -> Orden:
        orden = self._repo.obtener(orden_id)
        if orden is None:
            raise OrdenNoEncontradaError(f"No existe una orden con id {orden_id}.")
        return orden

    def listar(
        self, estado: Estado | None = None, limit: int = LIMITE_POR_DEFECTO, offset: int = 0
    ) -> list[Orden]:
        return self._repo.listar(estado, limit, offset)

    def cambiar_estado(self, orden_id: UUID, nuevo: Estado) -> Orden:
        orden = self.obtener(orden_id)
        anterior = orden.cambiar_estado(nuevo)
        self._repo.guardar(orden)
        logger.info(
            "transicion_estado",
            extra={"orden_id": str(orden.id), "desde": anterior, "hacia": nuevo},
        )
        return orden

    def cancelar(self, orden_id: UUID) -> Orden:
        return self.cambiar_estado(orden_id, Estado.CANCELADA)
```

---

## 5. API

### app/api/schemas.py
```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.domain.estado import Estado
from app.domain.orden import LineaProducto, Orden


class Base(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Entrada(Base):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ProductoIn(Entrada):
    id: str = Field(min_length=1, examples=["P001"])
    cantidad: int = Field(gt=0, examples=[2])  # RN-02
    valor_unitario: int = Field(gt=0, examples=[100000])

    def a_dominio(self) -> LineaProducto:
        return LineaProducto(id=self.id, cantidad=self.cantidad, valor_unitario=self.valor_unitario)


class OrdenIn(Entrada):
    cliente: str = Field(min_length=1, examples=["Juan Pérez"])
    productos: list[ProductoIn] = Field(min_length=1)  # RN-01


class CambioEstadoIn(Entrada):
    estado: Estado


class ProductoOut(Base):
    id: str
    cantidad: int
    valor_unitario: int


class OrdenOut(Base):
    id: UUID
    cliente: str
    productos: list[ProductoOut]
    total: int
    estado: Estado
    transiciones_permitidas: list[Estado]

    @classmethod
    def desde_dominio(cls, orden: Orden) -> "OrdenOut":
        return cls(
            id=orden.id,
            cliente=orden.cliente,
            productos=[
                ProductoOut(id=p.id, cantidad=p.cantidad, valor_unitario=p.valor_unitario)
                for p in orden.productos
            ],
            total=orden.total,
            estado=orden.estado,
            transiciones_permitidas=orden.transiciones_permitidas,
        )
```

### app/api/errores.py
```python
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

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
    request: Request, status: int, title: str, detail: str, codigo: str, **extra: object
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


def traducir(error: dict[str, Any]) -> str:
    plantilla = MENSAJES.get(error["type"])
    if plantilla is None:
        return str(error["msg"])
    try:
        return plantilla.format(**error.get("ctx", {}))
    except (KeyError, IndexError):
        return str(error["msg"])


def nombre_campo(loc: tuple[int | str, ...]) -> str:
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
    # Starlette declara que los manejadores reciben cualquier Exception; en la práctica
    # cada uno recibe solo el tipo con el que se registra, así que la conversión es segura.
    app.add_exception_handler(OrdenError, cast(ExceptionHandler, manejar_orden_error))
    app.add_exception_handler(RequestValidationError, cast(ExceptionHandler, manejar_validacion))
```

### app/api/rutas.py
```python
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.schemas import CambioEstadoIn, OrdenIn, OrdenOut
from app.application.servicio_ordenes import (
    LIMITE_MAXIMO,
    LIMITE_POR_DEFECTO,
    ServicioOrdenes,
)
from app.domain.estado import Estado

router = APIRouter(prefix="/orders", tags=["órdenes"])

# Documentación de errores para OpenAPI: cada código con la regla que lo produce.
RESPUESTAS: dict[int, dict[str, Any]] = {
    400: {"description": "La orden no ha sido pagada (RN-05)"},
    404: {"description": "La orden no existe"},
    409: {"description": "Estado terminal (RN-04) o transición inválida (RN-06)"},
    422: {"description": "Datos inválidos (RN-01, RN-02, total enviado o formato)"},
}


def respuestas(*codigos: int) -> dict[int | str, dict[str, Any]]:
    return {codigo: RESPUESTAS[codigo] for codigo in codigos}


def obtener_servicio(request: Request) -> ServicioOrdenes:
    # app.state no tiene tipos: create_app() garantiza que aquí hay un ServicioOrdenes.
    return cast(ServicioOrdenes, request.app.state.servicio)


Servicio = Annotated[ServicioOrdenes, Depends(obtener_servicio)]


@router.post(
    "", response_model=OrdenOut, status_code=status.HTTP_201_CREATED, responses=respuestas(422)
)
def crear_orden(datos: OrdenIn, response: Response, servicio: Servicio) -> OrdenOut:
    """Crea una orden en estado CREADA. El total se calcula automáticamente (RN-03)."""
    orden = servicio.crear(datos.cliente, [p.a_dominio() for p in datos.productos])
    # REST: un 201 indica dónde quedó el recurso; ruta relativa para que funcione tras nginx.
    response.headers["Location"] = f"{router.prefix}/{orden.id}"
    return OrdenOut.desde_dominio(orden)


@router.get("", response_model=list[OrdenOut], responses=respuestas(422))
def listar_ordenes(
    servicio: Servicio,
    estado: Estado | None = None,
    limit: Annotated[int, Query(ge=1, le=LIMITE_MAXIMO)] = LIMITE_POR_DEFECTO,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[OrdenOut]:
    """Lista las órdenes, más recientes primero, con filtro opcional por estado."""
    return [OrdenOut.desde_dominio(o) for o in servicio.listar(estado, limit, offset)]


@router.get("/{orden_id}", response_model=OrdenOut, responses=respuestas(404, 422))
def consultar_orden(orden_id: UUID, servicio: Servicio) -> OrdenOut:
    """Consulta una orden por su id."""
    return OrdenOut.desde_dominio(servicio.obtener(orden_id))


@router.patch(
    "/{orden_id}/status", response_model=OrdenOut, responses=respuestas(400, 404, 409, 422)
)
def actualizar_estado(orden_id: UUID, datos: CambioEstadoIn, servicio: Servicio) -> OrdenOut:
    """Cambia el estado de la orden respetando la máquina de estados (RN-04, RN-05, RN-06)."""
    return OrdenOut.desde_dominio(servicio.cambiar_estado(orden_id, datos.estado))


@router.delete("/{orden_id}", response_model=OrdenOut, responses=respuestas(404, 409, 422))
def cancelar_orden(orden_id: UUID, servicio: Servicio) -> OrdenOut:
    """Cancelación lógica: la orden pasa a CANCELADA y se conserva (es un registro auditable)."""
    return OrdenOut.desde_dominio(servicio.cancelar(orden_id))
```

Un `orden_id` que no es UUID devuelve 422 por la validación de FastAPI; es coherente con la política.

---

## 6. Logging

### app/core/logging.py
```python
import json
import logging
import sys
import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from uuid import uuid4

from fastapi import FastAPI, Request, Response

request_id_actual: ContextVar[str] = ContextVar("request_id", default="-")
CAMPOS_EXTRA = ("orden_id", "desde", "hacia", "total", "metodo", "ruta", "status", "duracion_ms")


class FormatoJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        datos: dict[str, object] = {
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
            "request_id": request_id_actual.get(),
        }
        for campo in CAMPOS_EXTRA:
            if hasattr(record, campo):
                valor = getattr(record, campo)
                # Números como números para poder filtrarlos; el resto, como texto.
                datos[campo] = valor if isinstance(valor, int | float) else str(valor)
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
    async def request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
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
```

---

## 7. main.py

### app/main.py
```python
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
```

Ejecutar en local:
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8080
```
Swagger queda en http://localhost:8080/docs

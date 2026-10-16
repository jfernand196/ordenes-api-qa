from threading import Lock
from typing import Protocol
from uuid import UUID

from app.domain.estado import Estado
from app.domain.orden import Orden


class OrderRepository(Protocol):
    def guardar(self, orden: Orden) -> None: ...
    def obtener(self, orden_id: UUID) -> Orden | None: ...
    def listar(self, estado: Estado | None, limit: int, offset: int) -> list[Orden]: ...


class RepositorioEnMemoria:
    """Persistencia en memoria (ADR-002). Thread-safe para el servidor ASGI."""

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
            # Mas recientes primero: la ultima orden creada siempre aparece en la primera pagina.
            ordenes = list(reversed(self._ordenes.values()))
        if estado is not None:
            ordenes = [o for o in ordenes if o.estado == estado]
        return ordenes[offset : offset + limit]
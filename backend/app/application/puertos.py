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

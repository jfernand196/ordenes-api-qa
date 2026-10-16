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

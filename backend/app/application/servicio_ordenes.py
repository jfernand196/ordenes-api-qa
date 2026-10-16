import logging
from uuid import UUID

from app.domain.estado import Estado
from app.domain.excepciones import OrdenNoEncontradaError
from app.domain.orden import LineaProducto, Orden
from app.infrastructure.repositorio import OrderRepository

logger = logging.getLogger("ordenes")


class ServicioOrdenes:
    def __init__(self, repositorio: OrderRepository) -> None:
        self._repo = repositorio

    def crear(self, cliente: str, productos: list[tuple[str, int, int]]) -> Orden:
        lineas = [LineaProducto(id=i, cantidad=c, valor_unitario=v) for i, c, v in productos]
        orden = Orden(cliente=cliente, productos=lineas)
        self._repo.guardar(orden)
        logger.info("orden_creada", extra={"orden_id": str(orden.id), "total": orden.total})
        return orden

    def obtener(self, orden_id: UUID) -> Orden:
        orden = self._repo.obtener(orden_id)
        if orden is None:
            raise OrdenNoEncontradaError(f"No existe una orden con id {orden_id}.")
        return orden

    def listar(self, estado: Estado | None = None, limit: int = 50, offset: int = 0) -> list[Orden]:
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

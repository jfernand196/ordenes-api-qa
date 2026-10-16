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

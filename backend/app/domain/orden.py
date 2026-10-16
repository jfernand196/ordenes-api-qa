from dataclasses import dataclass, field
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


@dataclass
class Orden:
    cliente: str
    productos: list[LineaProducto]
    id: UUID = field(default_factory=uuid4)
    estado: Estado = Estado.CREADA

    def __post_init__(self) -> None:
        if not self.cliente.strip():
            raise ValidacionOrdenError("El cliente es obligatorio.")
        if not self.productos:
            raise ValidacionOrdenError("La orden debe contener al menos un producto.", "RN-01")

    @property
    def total(self) -> int:  # RN-03
        return sum(p.subtotal for p in self.productos)

    @property
    def transiciones_permitidas(self) -> list[Estado]:
        return transiciones_permitidas(self.estado)

    def cambiar_estado(self, nuevo: Estado) -> Estado:
        """Aplica la transicion y devuelve el estado anterior (util para el log)."""
        validar_transicion(self.estado, nuevo)
        anterior = self.estado
        self.estado = nuevo
        return anterior

    def cancelar(self) -> Estado:
        return self.cambiar_estado(Estado.CANCELADA)

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

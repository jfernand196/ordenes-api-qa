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

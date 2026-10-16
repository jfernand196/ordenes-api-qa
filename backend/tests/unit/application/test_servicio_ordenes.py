from uuid import uuid4

import pytest

from app.application.servicio_ordenes import ServicioOrdenes
from app.domain.estado import Estado
from app.domain.excepciones import OrdenNoEncontradaError, PagoRequeridoError
from app.domain.orden import LineaProducto
from app.infrastructure.repositorio import RepositorioEnMemoria


@pytest.fixture
def servicio() -> ServicioOrdenes:
    return ServicioOrdenes(RepositorioEnMemoria())


def test_crear_y_obtener(servicio):
    orden = servicio.crear("Ana", [LineaProducto("P1", 2, 500)])
    assert servicio.obtener(orden.id) is orden
    assert orden.total == 1000


def test_obtener_inexistente_lanza_error(servicio):
    with pytest.raises(OrdenNoEncontradaError) as exc:
        servicio.obtener(uuid4())
    assert exc.value.codigo == "NO_ENCONTRADA"


def test_listar_devuelve_las_mas_recientes_primero(servicio):
    primera = servicio.crear("A", [LineaProducto("P1", 1, 10)])
    segunda = servicio.crear("B", [LineaProducto("P1", 1, 10)])
    assert [o.id for o in servicio.listar()] == [segunda.id, primera.id]


def test_listar_filtra_por_estado_y_pagina(servicio):
    a = servicio.crear("A", [LineaProducto("P1", 1, 10)])
    servicio.crear("B", [LineaProducto("P1", 1, 10)])
    servicio.cambiar_estado(a.id, Estado.PAGADA)
    assert [o.id for o in servicio.listar(Estado.PAGADA)] == [a.id]
    assert len(servicio.listar()) == 2
    assert len(servicio.listar(limit=1)) == 1
    assert [o.id for o in servicio.listar(offset=1)] == [a.id]


def test_cancelar_pasa_a_cancelada(servicio):
    orden = servicio.crear("A", [LineaProducto("P1", 1, 10)])
    assert servicio.cancelar(orden.id).estado == Estado.CANCELADA


@pytest.mark.rn("RN-05")
def test_una_transicion_rechazada_no_cambia_la_orden_guardada(servicio):
    orden = servicio.crear("A", [LineaProducto("P1", 1, 10)])
    with pytest.raises(PagoRequeridoError):
        servicio.cambiar_estado(orden.id, Estado.ENVIADA)
    assert servicio.obtener(orden.id).estado == Estado.CREADA

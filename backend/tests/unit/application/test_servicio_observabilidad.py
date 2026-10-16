import logging
from uuid import uuid4

import pytest

from app.application.servicio_ordenes import ServicioOrdenes
from app.domain.estado import Estado
from app.domain.excepciones import OrdenNoEncontradaError
from app.infrastructure.repositorio import RepositorioEnMemoria


class RepositorioEspia(RepositorioEnMemoria):
    """Doble de prueba: registra cada guardado para verificar la interacción con el puerto."""

    def __init__(self) -> None:
        super().__init__()
        self.guardados: list[tuple] = []

    def guardar(self, orden) -> None:
        self.guardados.append((orden.id, orden.estado))
        super().guardar(orden)


@pytest.fixture
def repo() -> RepositorioEspia:
    return RepositorioEspia()


@pytest.fixture
def servicio(repo) -> ServicioOrdenes:
    return ServicioOrdenes(repo)


def registros_de_ordenes(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == "ordenes"]


def test_crear_registra_un_log_con_id_y_total(servicio, caplog):
    caplog.set_level(logging.INFO, logger="ordenes")
    orden = servicio.crear("Ana", [("P1", 2, 500)])
    [registro] = registros_de_ordenes(caplog)
    assert registro.getMessage() == "orden_creada"
    assert registro.orden_id == str(orden.id)
    assert registro.total == 1000


def test_cambiar_estado_registra_la_transicion(servicio, caplog):
    caplog.set_level(logging.INFO, logger="ordenes")
    orden = servicio.crear("Ana", [("P1", 1, 10)])
    caplog.clear()
    servicio.cambiar_estado(orden.id, Estado.PAGADA)
    [registro] = registros_de_ordenes(caplog)
    assert registro.getMessage() == "transicion_estado"
    assert registro.orden_id == str(orden.id)
    assert (registro.desde, registro.hacia) == (Estado.CREADA, Estado.PAGADA)


def test_cambiar_estado_guarda_la_orden_actualizada(servicio, repo):
    orden = servicio.crear("Ana", [("P1", 1, 10)])
    servicio.cambiar_estado(orden.id, Estado.PAGADA)
    assert repo.guardados == [(orden.id, Estado.CREADA), (orden.id, Estado.PAGADA)]


def test_obtener_inexistente_indica_el_id_buscado(servicio):
    orden_id = uuid4()
    with pytest.raises(OrdenNoEncontradaError) as exc:
        servicio.obtener(orden_id)
    assert exc.value.mensaje == f"No existe una orden con id {orden_id}."


def test_listar_devuelve_como_maximo_50_por_defecto(servicio):
    for i in range(51):
        servicio.crear(f"Cliente {i}", [("P1", 1, 1)])
    assert len(servicio.listar()) == 50

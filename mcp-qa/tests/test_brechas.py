from pathlib import Path

import pytest
from app.domain.estado import Estado as E

from qa.brechas import PRIORIDAD, clasificar, sin_aceptacion, transiciones_karate


@pytest.mark.parametrize(
    ("desde", "hacia", "riesgo"),
    [
        (E.CANCELADA, E.PAGADA, "critico"),
        (E.ENTREGADA, E.CREADA, "critico"),
        (E.PAGADA, E.ENTREGADA, "alto"),
        (E.PAGADA, E.CANCELADA, "alto"),
        (E.ENVIADA, E.PAGADA, "medio"),
        (E.PAGADA, E.PAGADA, "bajo"),
        (E.CANCELADA, E.CANCELADA, "bajo"),
    ],
)
def test_clasificacion_de_riesgo(desde, hacia, riesgo):
    assert clasificar(desde, hacia)[0] == riesgo


def test_karate_cubre_al_menos_los_flujos_del_enunciado():
    obligatorias = {
        (E.CREADA, E.ENVIADA),  # enviar sin pagar -> 400
        (E.ENTREGADA, E.CANCELADA),  # cancelar entregada -> 409
        (E.CREADA, E.PAGADA),
        (E.PAGADA, E.ENVIADA),
        (E.ENVIADA, E.ENTREGADA),
    }
    assert obligatorias <= transiciones_karate()


def test_cubiertas_y_brechas_suman_las_25_combinaciones():
    assert len(transiciones_karate()) + len(sin_aceptacion()) == len(E) ** 2


def test_las_brechas_van_de_mayor_a_menor_riesgo():
    prioridades = [PRIORIDAD[b["riesgo"]] for b in sin_aceptacion()]
    assert prioridades == sorted(prioridades)
    # Regresión: las transiciones desde estados terminales ya tienen escenario Karate.
    assert PRIORIDAD["critico"] not in prioridades


def test_ninguna_brecha_esta_cubierta_por_karate():
    cubiertas = transiciones_karate()
    assert all((b["desde"], b["hacia"]) not in cubiertas for b in sin_aceptacion())


def test_sigue_el_estado_a_traves_de_los_pasos_del_escenario(tmp_path: Path):
    (tmp_path / "flujo.feature").write_text(
        """Feature: prueba
  Background:
    * def creada = call read(crearOrden)

  Scenario: pagar y luego intentar entregar
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'PAGADA' }
    And request { estado: 'ENTREGADA' }
    When method patch

  Scenario: cancelar
    When method delete
""",
        encoding="utf-8",
    )
    assert transiciones_karate(tmp_path) == {
        (E.CREADA, E.PAGADA),
        (E.PAGADA, E.ENTREGADA),
        (E.CREADA, E.CANCELADA),
    }


def test_ignora_los_helpers_y_las_features_sin_orden(tmp_path: Path):
    (tmp_path / "helpers").mkdir()
    (tmp_path / "helpers" / "h.feature").write_text(
        "Feature: h\n  Background:\n    * call read(crearOrden)\n  Scenario: x\n"
        "    When method delete\n",
        encoding="utf-8",
    )
    (tmp_path / "crear.feature").write_text(
        "Feature: c\n  Scenario: y\n    When method delete\n", encoding="utf-8"
    )
    assert transiciones_karate(tmp_path) == set()


def test_expande_los_outlines_y_avanza_tras_una_respuesta_exitosa(tmp_path: Path):
    (tmp_path / "terminal.feature").write_text(
        """Feature: prueba
  Background:
    * def creada = call read(crearOrden)

  Scenario Outline: cancelar y luego intentar <destino>
    Given path 'orders', ordenId
    When method delete
    Then status 200
    And request { estado: '<destino>' }
    When method patch
    Then status 409

    Examples:
      | destino |
      | PAGADA  |
      | ENVIADA |

  Scenario: una cancelación rechazada no avanza el estado
    * call read(cambiarEstado) { id: '#(ordenId)', estado: 'PAGADA' }
    When method delete
    Then status 409
    And request { estado: 'ENVIADA' }
    When method patch
""",
        encoding="utf-8",
    )
    assert transiciones_karate(tmp_path) == {
        (E.CREADA, E.CANCELADA),
        (E.CANCELADA, E.PAGADA),
        (E.CANCELADA, E.ENVIADA),
        (E.CREADA, E.PAGADA),
        (E.PAGADA, E.CANCELADA),
        (E.PAGADA, E.ENVIADA),
    }

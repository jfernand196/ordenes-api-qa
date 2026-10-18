import generar_trazabilidad as escaner
import pytest

from qa.reglas import IMPLEMENTACION, listar
from qa.trazabilidad import matriz


def test_la_matriz_incluye_las_seis_reglas_con_pruebas_unitarias():
    filas = matriz()
    assert [f.regla for f in filas] == list(escaner.REGLAS)
    assert all(f.unitarias_e_integracion for f in filas)


def test_filtra_una_regla_sin_importar_mayusculas_ni_espacios():
    [fila] = matriz(" rn-04 ")
    assert fila.regla == "RN-04"
    assert fila.aceptacion_karate


def test_una_regla_desconocida_es_un_error_claro():
    with pytest.raises(ValueError, match="Regla desconocida: RN-99"):
        matriz("RN-99")


def test_la_implementacion_documenta_exactamente_las_reglas_del_escaner():
    assert set(IMPLEMENTACION) == set(escaner.REGLAS)


def test_los_conteos_coinciden_con_la_matriz():
    for regla, fila in zip(listar(), matriz(), strict=True):
        assert regla["regla"] == fila.regla
        assert regla["pruebas"] == {
            "unitarias_e_integracion": len(fila.unitarias_e_integracion),
            "aceptacion_karate": len(fila.aceptacion_karate),
            "e2e_playwright": len(fila.e2e_playwright),
        }

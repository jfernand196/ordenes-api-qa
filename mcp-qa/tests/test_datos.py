import pytest
from app.main import create_app
from fastapi.testclient import TestClient

from qa.datos import generar

CASOS = [(tipo, caso) for tipo in ("validos", "frontera", "invalidos") for caso in generar(tipo)]


@pytest.mark.parametrize(("tipo", "caso"), CASOS, ids=[c["descripcion"] for _, c in CASOS])
def test_cada_payload_produce_la_respuesta_que_anuncia(tipo, caso):
    """Los datos se validan contra la API real: si cambia una regla, esta prueba lo detecta."""
    respuesta = TestClient(create_app()).post("/orders", json=caso["payload"])
    assert respuesta.status_code == caso["status_esperado"], respuesta.text
    if "campo_con_error" in caso:
        campos = [e["campo"] for e in respuesta.json()["errores"]]
        assert caso["campo_con_error"] in campos


def test_los_limites_se_leen_del_schema():
    descripciones = [c["descripcion"] for c in generar("frontera")]
    assert "Cantidad en el límite (0)" in descripciones
    assert "Menos productos que el mínimo (0)" in descripciones

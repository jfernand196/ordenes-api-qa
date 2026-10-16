import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def payload_valido() -> dict:
    return {
        "cliente": "Juan Pérez",
        "productos": [{"id": "P001", "cantidad": 2, "valorUnitario": 100000}],
    }


@pytest.fixture
def crear_orden(cliente, payload_valido):
    def _crear(**cambios) -> dict:
        respuesta = cliente.post("/orders", json={**payload_valido, **cambios})
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _crear


@pytest.fixture
def llevar_a(cliente):
    def _llevar(orden_id: str, *estados: str) -> dict:
        datos = {}
        for estado in estados:
            r = cliente.patch(f"/orders/{orden_id}/status", json={"estado": estado})
            assert r.status_code == 200, r.text
            datos = r.json()
        return datos

    return _llevar

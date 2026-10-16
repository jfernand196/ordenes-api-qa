# Ejemplos de pruebas

Contenido:
1. pyproject.toml (pytest, coverage, mutmut, ruff)
2. conftest.py
3. Matriz de transiciones
4. Entidad Orden (RN-01, RN-02, RN-03 con Hypothesis)
5. Servicio
6. IntegraciÃ³n de la API

---

## 1. backend/pyproject.toml

```toml
[project]
name = "ordenes-api"
version = "1.0.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-ra --strict-markers"
markers = [
    "rn(id): regla de negocio que valida la prueba (RN-01 a RN-06)",
]

[tool.coverage.run]
branch = true
source = ["app"]

[tool.coverage.report]
fail_under = 80
show_missing = true
skip_covered = false

[tool.mutmut]
paths_to_mutate = ["app/"]
do_not_mutate = ["app/api/*", "app/core/*", "app/infrastructure/*", "app/main.py"]
tests_dir = ["tests/"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM"]
```

---

## 2. backend/tests/conftest.py

```python
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def payload_valido() -> dict:
    return {
        "cliente": "Juan PÃ©rez",
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
```

---

## 3. backend/tests/unit/domain/test_maquina_estados.py

La matriz se escribe a mano a propÃ³sito. Si se derivara de `TRANSICIONES`, cualquier mutante del diccionario pasarÃ­a.

```python
import pytest

from app.domain.estado import Estado as E
from app.domain.excepciones import (
    EstadoTerminalError,
    PagoRequeridoError,
    TransicionInvalidaError,
)
from app.domain.maquina_estados import transiciones_permitidas, validar_transicion

OK = None
PAGO = PagoRequeridoError
TERMINAL = EstadoTerminalError
INVALIDA = TransicionInvalidaError

MATRIZ = [
    (E.CREADA, E.CREADA, INVALIDA),
    (E.CREADA, E.PAGADA, OK),
    (E.CREADA, E.ENVIADA, PAGO),
    (E.CREADA, E.ENTREGADA, INVALIDA),
    (E.CREADA, E.CANCELADA, OK),
    (E.PAGADA, E.CREADA, INVALIDA),
    (E.PAGADA, E.PAGADA, INVALIDA),
    (E.PAGADA, E.ENVIADA, OK),
    (E.PAGADA, E.ENTREGADA, INVALIDA),
    (E.PAGADA, E.CANCELADA, OK),
    (E.ENVIADA, E.CREADA, INVALIDA),
    (E.ENVIADA, E.PAGADA, INVALIDA),
    (E.ENVIADA, E.ENVIADA, INVALIDA),
    (E.ENVIADA, E.ENTREGADA, OK),
    (E.ENVIADA, E.CANCELADA, OK),
    (E.ENTREGADA, E.CREADA, TERMINAL),
    (E.ENTREGADA, E.PAGADA, TERMINAL),
    (E.ENTREGADA, E.ENVIADA, TERMINAL),
    (E.ENTREGADA, E.ENTREGADA, TERMINAL),
    (E.ENTREGADA, E.CANCELADA, TERMINAL),
    (E.CANCELADA, E.CREADA, TERMINAL),
    (E.CANCELADA, E.PAGADA, TERMINAL),
    (E.CANCELADA, E.ENVIADA, TERMINAL),
    (E.CANCELADA, E.ENTREGADA, TERMINAL),
    (E.CANCELADA, E.CANCELADA, TERMINAL),
]


@pytest.mark.rn("RN-04")
@pytest.mark.rn("RN-05")
@pytest.mark.rn("RN-06")
@pytest.mark.parametrize(("desde", "hacia", "esperado"), MATRIZ, ids=lambda v: str(v) if v else "OK")
def test_matriz_de_transiciones(desde, hacia, esperado):
    if esperado is OK:
        validar_transicion(desde, hacia)
    else:
        with pytest.raises(esperado):
            validar_transicion(desde, hacia)


@pytest.mark.rn("RN-04")
def test_cancelar_una_orden_entregada_informa_regla_rn04():
    with pytest.raises(EstadoTerminalError) as exc:
        validar_transicion(E.ENTREGADA, E.CANCELADA)
    assert exc.value.codigo == "RN-04"


@pytest.mark.rn("RN-05")
def test_enviar_sin_pagar_informa_regla_rn05():
    with pytest.raises(PagoRequeridoError) as exc:
        validar_transicion(E.CREADA, E.ENVIADA)
    assert exc.value.codigo == "RN-05"


@pytest.mark.rn("RN-06")
@pytest.mark.parametrize(
    ("estado", "esperadas"),
    [
        (E.CREADA, [E.CANCELADA, E.PAGADA]),
        (E.PAGADA, [E.CANCELADA, E.ENVIADA]),
        (E.ENVIADA, [E.CANCELADA, E.ENTREGADA]),
        (E.ENTREGADA, []),
        (E.CANCELADA, []),
    ],
)
def test_transiciones_permitidas(estado, esperadas):
    assert transiciones_permitidas(estado) == esperadas
```

---

## 4. backend/tests/unit/domain/test_orden.py

```python
import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.estado import Estado
from app.domain.excepciones import EstadoTerminalError, ValidacionOrdenError
from app.domain.orden import LineaProducto, Orden


def linea(cantidad: int = 1, valor: int = 1000, id_: str = "P001") -> LineaProducto:
    return LineaProducto(id=id_, cantidad=cantidad, valor_unitario=valor)


@pytest.mark.rn("RN-01")
def test_una_orden_sin_productos_es_invalida():
    with pytest.raises(ValidacionOrdenError) as exc:
        Orden(cliente="Ana", productos=[])
    assert exc.value.codigo == "RN-01"


@pytest.mark.rn("RN-01")
def test_una_orden_con_un_producto_es_valida():
    assert Orden(cliente="Ana", productos=[linea()]).estado == Estado.CREADA


@pytest.mark.rn("RN-02")
@pytest.mark.parametrize("cantidad", [-1, 0])
def test_cantidad_no_positiva_es_invalida(cantidad):
    with pytest.raises(ValidacionOrdenError) as exc:
        linea(cantidad=cantidad)
    assert exc.value.codigo == "RN-02"


@pytest.mark.rn("RN-02")
def test_cantidad_uno_es_valida():
    assert linea(cantidad=1).cantidad == 1


@pytest.mark.parametrize("valor", [-1, 0])
def test_valor_unitario_no_positivo_es_invalido(valor):
    with pytest.raises(ValidacionOrdenError):
        linea(valor=valor)


@pytest.mark.parametrize("cliente", ["", "   "])
def test_cliente_vacio_es_invalido(cliente):
    with pytest.raises(ValidacionOrdenError):
        Orden(cliente=cliente, productos=[linea()])


def test_id_de_producto_vacio_es_invalido():
    with pytest.raises(ValidacionOrdenError):
        linea(id_=" ")


@pytest.mark.rn("RN-03")
def test_total_del_ejemplo_del_enunciado():
    orden = Orden(cliente="Juan PÃ©rez", productos=[linea(cantidad=2, valor=100000)])
    assert orden.total == 200000


@pytest.mark.rn("RN-03")
def test_total_con_varios_productos():
    orden = Orden(cliente="Ana", productos=[linea(2, 1500, "P1"), linea(3, 200, "P2")])
    assert orden.total == 3600


@pytest.mark.rn("RN-03")
@given(
    st.lists(
        st.tuples(st.integers(1, 1_000), st.integers(1, 10_000_000)), min_size=1, max_size=20
    )
)
def test_total_es_la_suma_de_cantidad_por_valor(items):
    productos = [linea(c, v, f"P{i}") for i, (c, v) in enumerate(items)]
    assert Orden(cliente="Ana", productos=productos).total == sum(c * v for c, v in items)


@pytest.mark.rn("RN-04")
def test_cancelar_desde_entregada_no_cambia_el_estado():
    orden = Orden(cliente="Ana", productos=[linea()])
    for estado in (Estado.PAGADA, Estado.ENVIADA, Estado.ENTREGADA):
        orden.cambiar_estado(estado)
    with pytest.raises(EstadoTerminalError):
        orden.cancelar()
    assert orden.estado == Estado.ENTREGADA


def test_cambiar_estado_devuelve_el_estado_anterior():
    orden = Orden(cliente="Ana", productos=[linea()])
    assert orden.cambiar_estado(Estado.PAGADA) == Estado.CREADA
    assert orden.estado == Estado.PAGADA
```

---

## 5. backend/tests/unit/application/test_servicio_ordenes.py

```python
from uuid import uuid4

import pytest

from app.application.servicio_ordenes import ServicioOrdenes
from app.domain.estado import Estado
from app.domain.excepciones import OrdenNoEncontradaError
from app.infrastructure.repositorio import RepositorioEnMemoria


@pytest.fixture
def servicio() -> ServicioOrdenes:
    return ServicioOrdenes(RepositorioEnMemoria())


def test_crear_y_obtener(servicio):
    orden = servicio.crear("Ana", [("P1", 2, 500)])
    assert servicio.obtener(orden.id) is orden
    assert orden.total == 1000


def test_obtener_inexistente_lanza_error(servicio):
    with pytest.raises(OrdenNoEncontradaError):
        servicio.obtener(uuid4())


def test_listar_filtra_por_estado_y_pagina(servicio):
    a = servicio.crear("A", [("P1", 1, 10)])
    servicio.crear("B", [("P1", 1, 10)])
    servicio.cambiar_estado(a.id, Estado.PAGADA)
    assert [o.id for o in servicio.listar(Estado.PAGADA)] == [a.id]
    assert len(servicio.listar()) == 2
    assert len(servicio.listar(limit=1)) == 1
    assert len(servicio.listar(offset=1)) == 1


def test_cancelar_pasa_a_cancelada(servicio):
    orden = servicio.crear("A", [("P1", 1, 10)])
    assert servicio.cancelar(orden.id).estado == Estado.CANCELADA
```

---

## 6. backend/tests/integration/api/test_ordenes_api.py

```python
import pytest

PROBLEM = "application/problem+json"


@pytest.mark.rn("RN-03")
def test_crear_orden_valida_responde_201(cliente, payload_valido):
    r = cliente.post("/orders", json=payload_valido)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["total"] == 200000
    assert cuerpo["estado"] == "CREADA"
    assert cuerpo["transicionesPermitidas"] == ["CANCELADA", "PAGADA"]
    assert r.headers["Location"] == f"/orders/{cuerpo['id']}"
    assert "X-Request-ID" in r.headers


@pytest.mark.rn("RN-03")
def test_no_se_acepta_un_total_enviado_por_el_cliente(cliente, payload_valido):
    r = cliente.post("/orders", json={**payload_valido, "total": 1})
    assert r.status_code == 422


@pytest.mark.rn("RN-01")
def test_crear_orden_sin_productos_responde_422(cliente):
    r = cliente.post("/orders", json={"cliente": "Ana", "productos": []})
    assert r.status_code == 422
    assert r.headers["content-type"].startswith(PROBLEM)
    assert r.json()["codigo"] == "VALIDACION"


@pytest.mark.rn("RN-02")
def test_crear_orden_con_cantidad_cero_responde_422(cliente):
    r = cliente.post(
        "/orders",
        json={"cliente": "Ana", "productos": [{"id": "P1", "cantidad": 0, "valorUnitario": 10}]},
    )
    assert r.status_code == 422
    assert r.json()["errores"] == [
        {"campo": "productos.0.cantidad", "mensaje": "Debe ser mayor que 0."}
    ]


def test_consultar_orden_existente_responde_200(cliente, crear_orden):
    orden = crear_orden()
    r = cliente.get(f"/orders/{orden['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == orden["id"]


def test_consultar_orden_inexistente_responde_404(cliente):
    r = cliente.get("/orders/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert r.json()["codigo"] == "NO_ENCONTRADA"


def test_listar_ordenes_con_filtro(cliente, crear_orden, llevar_a):
    pagada = crear_orden()
    crear_orden()
    llevar_a(pagada["id"], "PAGADA")
    r = cliente.get("/orders", params={"estado": "PAGADA"})
    assert r.status_code == 200
    assert [o["id"] for o in r.json()] == [pagada["id"]]


@pytest.mark.rn("RN-05")
def test_enviar_orden_no_pagada_responde_400(cliente, crear_orden):
    orden = crear_orden()
    r = cliente.patch(f"/orders/{orden['id']}/status", json={"estado": "ENVIADA"})
    assert r.status_code == 400
    assert r.headers["content-type"].startswith(PROBLEM)
    assert r.json()["codigo"] == "RN-05"


@pytest.mark.rn("RN-04")
def test_cancelar_orden_entregada_responde_409(cliente, crear_orden, llevar_a):
    orden = crear_orden()
    llevar_a(orden["id"], "PAGADA", "ENVIADA", "ENTREGADA")
    r = cliente.delete(f"/orders/{orden['id']}")
    assert r.status_code == 409
    assert r.json()["codigo"] == "RN-04"


@pytest.mark.rn("RN-06")
def test_transicion_invalida_responde_409(cliente, crear_orden):
    orden = crear_orden()
    r = cliente.patch(f"/orders/{orden['id']}/status", json={"estado": "ENTREGADA"})
    assert r.status_code == 409
    assert r.json()["codigo"] == "RN-06"


def test_cancelar_orden_creada_responde_200(cliente, crear_orden):
    orden = crear_orden()
    r = cliente.delete(f"/orders/{orden['id']}")
    assert r.status_code == 200
    assert r.json()["estado"] == "CANCELADA"


def test_estado_desconocido_responde_422(cliente, crear_orden):
    orden = crear_orden()
    r = cliente.patch(f"/orders/{orden['id']}/status", json={"estado": "PERDIDA"})
    assert r.status_code == 422


def test_health(cliente):
    assert cliente.get("/health").json() == {"status": "ok"}
```

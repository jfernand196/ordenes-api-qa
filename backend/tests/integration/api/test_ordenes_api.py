import pytest

PROBLEM = "application/problem+json"


@pytest.mark.rn("RN-03")
def test_crear_orden_valida_responde_201(cliente, payload_valido):
    r = cliente.post("/orders", json=payload_valido)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["total"] == 200000
    assert cuerpo["estado"] == "CREADA"
    assert cuerpo["productos"] == [{"id": "P001", "cantidad": 2, "valorUnitario": 100000}]
    assert cuerpo["transicionesPermitidas"] == ["CANCELADA", "PAGADA"]
    assert r.headers["Location"] == f"/orders/{cuerpo['id']}"


def test_toda_respuesta_trae_x_request_id(cliente):
    r = cliente.get("/health", headers={"X-Request-ID": "prueba-123"})
    assert r.headers["X-Request-ID"] == "prueba-123"
    assert cliente.get("/health").headers["X-Request-ID"]


@pytest.mark.rn("RN-03")
def test_no_se_acepta_un_total_enviado_por_el_cliente(cliente, payload_valido):
    r = cliente.post("/orders", json={**payload_valido, "total": 1})
    assert r.status_code == 422
    assert r.json()["errores"] == [{"campo": "total", "mensaje": "Campo no permitido."}]


@pytest.mark.rn("RN-01")
def test_crear_orden_sin_productos_responde_422(cliente):
    r = cliente.post("/orders", json={"cliente": "Ana", "productos": []})
    assert r.status_code == 422
    assert r.headers["content-type"].startswith(PROBLEM)
    cuerpo = r.json()
    assert cuerpo["codigo"] == "VALIDACION"
    assert cuerpo["errores"] == [
        {"campo": "productos", "mensaje": "Debe tener al menos 1 elemento(s)."}
    ]


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


def test_cliente_solo_con_espacios_lo_rechaza_el_dominio(cliente, payload_valido):
    r = cliente.post("/orders", json={**payload_valido, "cliente": "   "})
    assert r.status_code == 422
    assert r.json()["codigo"] == "VALIDACION"


def test_consultar_orden_existente_responde_200(cliente, crear_orden):
    orden = crear_orden()
    r = cliente.get(f"/orders/{orden['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == orden["id"]


def test_consultar_orden_inexistente_responde_404(cliente):
    r = cliente.get("/orders/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith(PROBLEM)
    assert r.json()["codigo"] == "NO_ENCONTRADA"


def test_id_que_no_es_uuid_responde_422(cliente):
    r = cliente.get("/orders/no-es-un-uuid")
    assert r.status_code == 422
    assert r.json()["errores"][0]["campo"] == "orden_id"


def test_listar_ordenes_con_filtro(cliente, crear_orden, llevar_a):
    pagada = crear_orden()
    crear_orden()
    llevar_a(pagada["id"], "PAGADA")
    r = cliente.get("/orders", params={"estado": "PAGADA"})
    assert r.status_code == 200
    assert [o["id"] for o in r.json()] == [pagada["id"]]


@pytest.mark.parametrize(
    ("parametros", "campo"),
    [({"limit": 0}, "limit"), ({"limit": 101}, "limit"), ({"offset": -1}, "offset")],
)
def test_paginacion_invalida_responde_422(cliente, parametros, campo):
    r = cliente.get("/orders", params=parametros)
    assert r.status_code == 422
    assert r.json()["errores"][0]["campo"] == campo


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


def test_ciclo_completo_hasta_entregada(cliente, crear_orden, llevar_a):
    orden = crear_orden()
    final = llevar_a(orden["id"], "PAGADA", "ENVIADA", "ENTREGADA")
    assert final["estado"] == "ENTREGADA"
    assert final["transicionesPermitidas"] == []


def test_cancelar_orden_creada_responde_200(cliente, crear_orden):
    orden = crear_orden()
    r = cliente.delete(f"/orders/{orden['id']}")
    assert r.status_code == 200
    assert r.json()["estado"] == "CANCELADA"


def test_estado_desconocido_responde_422(cliente, crear_orden):
    orden = crear_orden()
    r = cliente.patch(f"/orders/{orden['id']}/status", json={"estado": "PERDIDA"})
    assert r.status_code == 422
    assert r.json()["errores"][0]["campo"] == "estado"


def test_health(cliente):
    assert cliente.get("/health").json() == {"status": "ok"}

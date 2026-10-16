import asyncio
import json

from starlette.requests import Request

from app.api.errores import manejar_orden_error, nombre_campo, traducir
from app.domain.excepciones import OrdenError


def test_traducir_usa_el_mensaje_original_si_no_hay_traduccion():
    assert traducir({"type": "desconocido", "msg": "original"}) == "original"


def test_traducir_usa_el_mensaje_original_si_falta_contexto():
    assert traducir({"type": "greater_than", "msg": "original"}) == "original"


def test_nombre_campo_conserva_rutas_sin_origen():
    assert nombre_campo(("productos", 0, "id")) == "productos.0.id"


def test_un_error_de_dominio_sin_mapeo_responde_500():
    peticion = Request({"type": "http", "method": "GET", "path": "/x", "headers": []})
    respuesta = asyncio.run(manejar_orden_error(peticion, OrdenError("sin mapeo")))
    assert respuesta.status_code == 500
    assert json.loads(respuesta.body)["codigo"] == "ORDEN"

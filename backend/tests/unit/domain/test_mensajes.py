"""Los mensajes de error son parte del contrato: la API los devuelve en `detail`
y el frontend los muestra al usuario, así que se verifican de forma literal."""

import pytest

from app.domain.estado import Estado as E
from app.domain.excepciones import (
    EstadoTerminalError,
    OrdenError,
    PagoRequeridoError,
    TransicionInvalidaError,
    ValidacionOrdenError,
)
from app.domain.maquina_estados import validar_transicion
from app.domain.orden import LineaProducto, Orden


def error_de(accion, tipo=OrdenError) -> OrdenError:
    with pytest.raises(tipo) as exc:
        accion()
    return exc.value


def linea() -> LineaProducto:
    return LineaProducto(id="P1", cantidad=1, valor_unitario=1)


def test_la_excepcion_conserva_mensaje_y_codigo():
    exc = OrdenError("algo falló", "RN-99")
    assert str(exc) == "algo falló"
    assert exc.mensaje == "algo falló"
    assert exc.codigo == "RN-99"


def test_sin_codigo_explicito_se_usa_el_de_la_clase():
    assert ValidacionOrdenError("x").codigo == "VALIDACION"


def test_mensaje_id_de_producto_vacio():
    exc = error_de(lambda: LineaProducto(id=" ", cantidad=1, valor_unitario=1))
    assert (exc.mensaje, exc.codigo) == ("El id del producto es obligatorio.", "VALIDACION")


@pytest.mark.rn("RN-02")
def test_mensaje_cantidad_no_positiva():
    exc = error_de(lambda: LineaProducto(id="P7", cantidad=0, valor_unitario=1))
    assert exc.mensaje == "La cantidad del producto P7 debe ser mayor que cero."
    assert exc.codigo == "RN-02"


def test_mensaje_valor_unitario_no_positivo():
    exc = error_de(lambda: LineaProducto(id="P7", cantidad=1, valor_unitario=0))
    assert exc.mensaje == "El valor unitario del producto P7 debe ser mayor que cero."
    assert exc.codigo == "VALIDACION"


def test_mensaje_cliente_vacio():
    exc = error_de(lambda: Orden(cliente=" ", productos=[linea()]))
    assert (exc.mensaje, exc.codigo) == ("El cliente es obligatorio.", "VALIDACION")


@pytest.mark.rn("RN-01")
def test_mensaje_orden_sin_productos():
    exc = error_de(lambda: Orden(cliente="Ana", productos=[]))
    assert exc.mensaje == "La orden debe contener al menos un producto."
    assert exc.codigo == "RN-01"


@pytest.mark.rn("RN-04")
def test_mensaje_estado_terminal():
    exc = error_de(lambda: validar_transicion(E.ENTREGADA, E.CANCELADA), EstadoTerminalError)
    assert exc.mensaje == (
        "La orden está en estado ENTREGADA y no admite cambios (intento: CANCELADA)."
    )


@pytest.mark.rn("RN-05")
def test_mensaje_pago_requerido():
    exc = error_de(lambda: validar_transicion(E.CREADA, E.ENVIADA), PagoRequeridoError)
    assert exc.mensaje == "La orden no puede enviarse si no ha sido pagada."


@pytest.mark.rn("RN-06")
def test_mensaje_transicion_invalida():
    exc = error_de(lambda: validar_transicion(E.CREADA, E.ENTREGADA), TransicionInvalidaError)
    assert exc.mensaje == "Transición inválida de CREADA a ENTREGADA."
    assert exc.codigo == "RN-06"


def test_cancelar_una_orden_creada_desde_la_entidad():
    orden = Orden(cliente="Ana", productos=[linea()])
    assert orden.cancelar() == E.CREADA
    assert orden.estado == E.CANCELADA

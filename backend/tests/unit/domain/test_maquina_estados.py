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

# Tabla escrita a mano a proposito: si se derivara de TRANSICIONES,
# cualquier mutante del diccionario pasaria las pruebas.
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
@pytest.mark.parametrize(("desde", "hacia", "esperado"), MATRIZ)
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

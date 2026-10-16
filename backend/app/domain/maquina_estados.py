from app.domain.estado import Estado
from app.domain.excepciones import (
    EstadoTerminalError,
    PagoRequeridoError,
    TransicionInvalidaError,
)

TRANSICIONES: dict[Estado, frozenset[Estado]] = {
    Estado.CREADA: frozenset({Estado.PAGADA, Estado.CANCELADA}),
    Estado.PAGADA: frozenset({Estado.ENVIADA, Estado.CANCELADA}),
    # Supuesto documentado: RN-04 solo prohibe cancelar una orden ENTREGADA.
    Estado.ENVIADA: frozenset({Estado.ENTREGADA, Estado.CANCELADA}),
    Estado.ENTREGADA: frozenset(),
    Estado.CANCELADA: frozenset(),
}


def transiciones_permitidas(desde: Estado) -> list[Estado]:
    return sorted(TRANSICIONES[desde])


def validar_transicion(desde: Estado, hacia: Estado) -> None:
    """Lanza la excepcion de dominio que corresponde. El orden de las validaciones importa."""
    if not TRANSICIONES[desde]:
        raise EstadoTerminalError(
            f"La orden está en estado {desde} y no admite cambios (intento: {hacia})."
        )
    if hacia == Estado.ENVIADA and desde == Estado.CREADA:
        raise PagoRequeridoError("La orden no puede enviarse si no ha sido pagada.")
    if hacia not in TRANSICIONES[desde]:
        raise TransicionInvalidaError(f"Transición inválida de {desde} a {hacia}.")

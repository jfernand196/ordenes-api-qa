class OrdenError(Exception):
    """Base de los errores de dominio. `codigo` enlaza el error con su regla."""

    codigo = "ORDEN"

    def __init__(self, mensaje: str, codigo: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        if codigo is not None:
            self.codigo = codigo


class ValidacionOrdenError(OrdenError):
    codigo = "VALIDACION"


class PagoRequeridoError(OrdenError):
    codigo = "RN-05"


class EstadoTerminalError(OrdenError):
    codigo = "RN-04"


class TransicionInvalidaError(OrdenError):
    codigo = "RN-06"


class OrdenNoEncontradaError(OrdenError):
    codigo = "NO_ENCONTRADA"
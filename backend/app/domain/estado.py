from enum import StrEnum


class Estado(StrEnum):
    CREADA = "CREADA"
    PAGADA = "PAGADA"
    ENVIADA = "ENVIADA"
    ENTREGADA = "ENTREGADA"
    CANCELADA = "CANCELADA"
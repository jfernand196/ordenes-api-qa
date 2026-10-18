"""Transiciones de estado sin prueba de aceptación (Karate), ordenadas por riesgo."""

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from app.domain.estado import Estado
from app.domain.maquina_estados import TRANSICIONES

from qa import KARATE

# Orden del ciclo de vida normal; CANCELADA queda fuera porque se alcanza desde varios estados.
CICLO = [Estado.CREADA, Estado.PAGADA, Estado.ENVIADA, Estado.ENTREGADA]
PRIORIDAD = {"critico": 0, "alto": 1, "medio": 2, "bajo": 3}

_HELPER = re.compile(r"call read\(cambiarEstado\) \{.*estado: '(\w+)'")
_REQUEST = re.compile(r"request \{ estado: '(\w+)' \}")


@dataclass(frozen=True)
class Brecha:
    desde: Estado
    hacia: Estado
    permitida: bool
    riesgo: str
    motivo: str


def clasificar(desde: Estado, hacia: Estado) -> tuple[str, str]:
    """Riesgo de una transición, con un criterio determinista y documentado."""
    if desde == hacia:
        return "bajo", "Transición al mismo estado."
    if not TRANSICIONES[desde]:
        return "critico", f"{desde} es terminal: reactivaría o alteraría una orden cerrada."
    if hacia in TRANSICIONES[desde]:
        return "alto", "Flujo permitido sin verificar contra la API desplegada."
    if desde in CICLO and hacia in CICLO and CICLO.index(hacia) > CICLO.index(desde):
        return "alto", "Se salta estados del ciclo de vida."
    return "medio", "Retrocede en el ciclo de vida."


def transiciones_karate(raiz: Path = KARATE) -> set[tuple[Estado, Estado]]:
    """Transiciones que ejercitan los escenarios Karate.

    Sigue el estado de la orden creada en el Background de cada escenario: cada llamada al
    helper cambiarEstado lo avanza, y cada PATCH o DELETE prueba una transición.
    """
    cubiertas: set[tuple[Estado, Estado]] = set()
    for archivo in sorted(raiz.rglob("*.feature")):
        if "helpers" in archivo.parts:
            continue
        texto = archivo.read_text(encoding="utf-8")
        if "call read(crearOrden)" not in texto:
            continue
        for escenario in re.split(r"^\s*Scenario(?: Outline)?:", texto, flags=re.M)[1:]:
            actual = Estado.CREADA
            pendiente: Estado | None = None
            for linea in escenario.splitlines():
                if m := _HELPER.search(linea):
                    nuevo = Estado(m.group(1))
                    cubiertas.add((actual, nuevo))
                    actual = nuevo
                elif m := _REQUEST.search(linea):
                    pendiente = Estado(m.group(1))
                elif "method patch" in linea and pendiente is not None:
                    cubiertas.add((actual, pendiente))
                elif "method delete" in linea:
                    cubiertas.add((actual, Estado.CANCELADA))
    return cubiertas


def sin_aceptacion(raiz: Path = KARATE) -> list[dict[str, object]]:
    """Las transiciones que ningún escenario Karate ejercita, de mayor a menor riesgo."""
    cubiertas = transiciones_karate(raiz)
    estados = list(Estado)
    brechas = []
    for desde in estados:
        for hacia in estados:
            if (desde, hacia) in cubiertas:
                continue
            riesgo, motivo = clasificar(desde, hacia)
            brechas.append(Brecha(desde, hacia, hacia in TRANSICIONES[desde], riesgo, motivo))
    brechas.sort(
        key=lambda b: (PRIORIDAD[b.riesgo], estados.index(b.desde), estados.index(b.hacia))
    )
    return [asdict(b) for b in brechas]

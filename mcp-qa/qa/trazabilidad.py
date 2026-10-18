"""Matriz regla -> pruebas, reutilizando el escáner de scripts/generar_trazabilidad.py."""

from dataclasses import dataclass

import generar_trazabilidad as escaner

from qa import E2E, KARATE, PRUEBAS_PYTEST


@dataclass(frozen=True)
class FilaMatriz:
    regla: str
    descripcion: str
    unitarias_e_integracion: list[str]
    aceptacion_karate: list[str]
    e2e_playwright: list[str]
    estado: str


def matriz(regla: str | None = None) -> list[FilaMatriz]:
    """Pruebas por nivel para cada regla, o solo para la regla indicada (RN-01 a RN-06)."""
    buscada = regla.strip().upper() if regla else None
    if buscada is not None and buscada not in escaner.REGLAS:
        raise ValueError(f"Regla desconocida: {regla}. Use una de {', '.join(escaner.REGLAS)}.")
    unitarias = escaner.escanear_pytest(PRUEBAS_PYTEST)
    aceptacion = escaner.escanear_karate(KARATE)
    e2e = escaner.escanear_playwright(E2E)
    filas = []
    for rn, descripcion in escaner.REGLAS.items():
        if buscada is not None and rn != buscada:
            continue
        u, k, e = unitarias.get(rn, []), aceptacion.get(rn, []), e2e.get(rn, [])
        filas.append(
            FilaMatriz(
                regla=rn,
                descripcion=descripcion,
                unitarias_e_integracion=sorted(set(u)),
                aceptacion_karate=sorted(set(k)),
                e2e_playwright=sorted(set(e)),
                estado=escaner.estado(u, k, e),
            )
        )
    return filas

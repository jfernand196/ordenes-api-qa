"""Servidor MCP de QA del proyecto de órdenes (solo lectura, determinista).

Ejecutar: python mcp-qa/servidor.py  (transporte stdio; nunca escribir en stdout).
"""

from dataclasses import asdict
from typing import Any

from mcp.server import MCPServer

from qa import brechas, datos, reglas, trazabilidad
from qa.datos import Tipo

mcp = MCPServer(
    "qa-ordenes",
    instructions=(
        "Herramientas de solo lectura sobre la calidad de la API de órdenes de compra: "
        "reglas de negocio, trazabilidad regla -> pruebas, transiciones de estado sin "
        "prueba de aceptación y datos de prueba derivados del schema real."
    ),
    version="1.2.0",
)


@mcp.tool()
def reglas_de_negocio() -> list[dict[str, Any]]:
    """Reglas RN-01 a RN-06: descripción, dónde se implementan y cuántas pruebas las verifican
    en cada nivel (unitarias e integración, Karate y Playwright)."""
    return reglas.listar()


@mcp.tool()
def matriz_trazabilidad(regla: str | None = None) -> list[dict[str, Any]]:
    """Pruebas que verifican cada regla, por nivel. Opcional: una regla, por ejemplo "RN-04"."""
    return [asdict(fila) for fila in trazabilidad.matriz(regla)]


@mcp.tool()
def transiciones_sin_aceptacion() -> list[dict[str, Any]]:
    """Transiciones de estado que ningún escenario Karate ejercita, de mayor a menor riesgo
    (critico, alto, medio, bajo), con el motivo de cada clasificación."""
    return brechas.sin_aceptacion()


@mcp.tool()
def datos_de_prueba(tipo: Tipo = "frontera") -> list[dict[str, Any]]:
    """Payloads para POST /orders con el status esperado y, si aplica, el campo con error.
    tipo: "validos", "frontera" (límites leídos del schema) o "invalidos"."""
    return datos.generar(tipo)


if __name__ == "__main__":
    mcp.run(transport="stdio")

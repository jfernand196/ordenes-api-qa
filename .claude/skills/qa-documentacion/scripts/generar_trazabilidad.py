#!/usr/bin/env python3
"""Genera la matriz de trazabilidad reglas de negocio -> pruebas.

Lee, sin ejecutar nada:
  - pytest:     @pytest.mark.rn("RN-xx") en backend/tests (también pytestmark y clases)
  - Karate:     tags @RN-xx en acceptance-tests (a nivel de Feature o Scenario)
  - Playwright: tags @RN-xx en frontend/e2e (opción { tag: [...] } o en el título)

Uso (desde la raíz del repo):
    python scripts/generar_trazabilidad.py --salida docs/TRACEABILITY.md
    python scripts/generar_trazabilidad.py --estricto   # código 1 si una regla no tiene pruebas
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

REGLAS = {
    "RN-01": "Una orden debe contener al menos un producto",
    "RN-02": "La cantidad de cada producto debe ser mayor que cero",
    "RN-03": "El total se calcula automáticamente",
    "RN-04": "Una orden entregada no puede ser cancelada",
    "RN-05": "Una orden no puede ser enviada si no ha sido pagada",
    "RN-06": "No se permiten transiciones inválidas de estado",
}

RE_RN = re.compile(r"RN-\d{2}")
RE_MARKER = re.compile(r"""pytest\.mark\.rn\(\s*["'](RN-\d{2})["']\s*\)""")
RE_DEF_TEST = re.compile(r"^(\s*)(?:async\s+)?def\s+(test_\w+)")
RE_CLASS = re.compile(r"^(\s*)class\s+(\w+)")
RE_PW_TEST = re.compile(
    r"""\btest\(\s*(['"`])(?P<titulo>.+?)\1\s*,\s*(?P<resto>\{[^{}]*\})?""", re.S
)

Hallazgos = dict[str, list[str]]


def escanear_pytest(raiz: Path) -> Hallazgos:
    resultado: Hallazgos = defaultdict(list)
    for archivo in sorted(raiz.rglob("test_*.py")):
        lineas = archivo.read_text(encoding="utf-8").splitlines()
        reglas_modulo = {
            rn for linea in lineas if linea.startswith("pytestmark") for rn in RE_MARKER.findall(linea)
        }
        pendientes: set[str] = set()
        clases: list[tuple[int, set[str]]] = []  # (indentación, reglas de la clase)
        for linea in lineas:
            if not linea.strip():
                continue
            indent = len(linea) - len(linea.lstrip())
            clases = [(i, r) for i, r in clases if indent > i or linea.lstrip().startswith("@")]
            pendientes.update(RE_MARKER.findall(linea) if linea.lstrip().startswith("@") else [])
            if m := RE_CLASS.match(linea):
                clases.append((len(m.group(1)), pendientes))
                pendientes = set()
            elif m := RE_DEF_TEST.match(linea):
                reglas = pendientes | reglas_modulo
                for _, r in clases:
                    reglas |= r
                nombre = f"{archivo.stem}::{m.group(2)}"
                for rn in reglas:
                    resultado[rn].append(nombre)
                pendientes = set()
    return resultado


def escanear_karate(raiz: Path) -> Hallazgos:
    resultado: Hallazgos = defaultdict(list)
    for archivo in sorted(raiz.rglob("*.feature")):
        tags_feature: set[str] = set()
        pendientes: set[str] = set()
        ignorado = False
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            texto = linea.strip()
            if not texto or texto.startswith("#"):
                continue
            if texto.startswith("@"):
                pendientes |= set(texto.split())
                continue
            if texto.startswith("Feature:"):
                tags_feature = pendientes
                ignorado = "@ignore" in tags_feature
            elif texto.startswith(("Scenario:", "Scenario Outline:")) and not ignorado:
                nombre = texto.split(":", 1)[1].strip()
                for rn in RE_RN.findall(" ".join(pendientes | tags_feature)):
                    resultado[rn].append(f"{archivo.stem}: {nombre}")
            pendientes = set()
    return resultado


def escanear_playwright(raiz: Path) -> Hallazgos:
    resultado: Hallazgos = defaultdict(list)
    archivos = sorted({*raiz.rglob("*.spec.ts"), *raiz.rglob("*.test.ts")})
    for archivo in archivos:
        for m in RE_PW_TEST.finditer(archivo.read_text(encoding="utf-8")):
            titulo = m.group("titulo")
            reglas = set(RE_RN.findall(titulo)) | set(RE_RN.findall(m.group("resto") or ""))
            for rn in reglas:
                resultado[rn].append(f"{archivo.name}: {titulo}")
    return resultado


def celda(pruebas: list[str], maximo: int = 4) -> str:
    if not pruebas:
        return "—"
    unicos = sorted(set(pruebas))
    lista = "<br>".join(f"`{p}`" for p in unicos[:maximo])
    extra = f"<br>y {len(unicos) - maximo} más" if len(unicos) > maximo else ""
    return f"**{len(unicos)}**<br>{lista}{extra}"


def estado(unit: list[str], karate: list[str], e2e: list[str]) -> str:
    niveles = sum(bool(x) for x in (unit, karate, e2e))
    if niveles == 0:
        return "❌ Sin pruebas"
    if unit and karate:
        return "✅ Cubierta"
    return "⚠️ Un solo nivel" if niveles == 1 else "✅ Cubierta"


def generar(unit: Hallazgos, karate: Hallazgos, e2e: Hallazgos) -> tuple[str, bool]:
    filas = [
        "# Matriz de trazabilidad",
        "",
        "Generada automáticamente por `scripts/generar_trazabilidad.py` a partir de los markers",
        "de pytest y los tags de Karate y Playwright. No editar a mano.",
        "",
        "| Regla | Descripción | Unitarias e integración | Aceptación (Karate) | E2E (Playwright) | Estado |",
        "|---|---|---|---|---|---|",
    ]
    completa = True
    for rn, descripcion in REGLAS.items():
        st = estado(unit.get(rn, []), karate.get(rn, []), e2e.get(rn, []))
        completa &= not st.startswith("❌")
        filas.append(
            f"| {rn} | {descripcion} | {celda(unit.get(rn, []))} | "
            f"{celda(karate.get(rn, []))} | {celda(e2e.get(rn, []))} | {st} |"
        )
    desconocidas = sorted((set(unit) | set(karate) | set(e2e)) - set(REGLAS))
    if desconocidas:
        filas += ["", f"⚠️ Reglas referenciadas que no existen: {', '.join(desconocidas)}"]
    return "\n".join(filas) + "\n", completa


def main() -> int:
    parser = argparse.ArgumentParser(description="Matriz de trazabilidad RN -> pruebas")
    parser.add_argument("--pytest", default="backend/tests", type=Path)
    parser.add_argument("--karate", default="acceptance-tests", type=Path)
    parser.add_argument("--e2e", default="frontend/e2e", type=Path)
    parser.add_argument("--salida", type=Path, help="archivo Markdown de salida (si no, stdout)")
    parser.add_argument("--estricto", action="store_true", help="falla si una regla no tiene pruebas")
    args = parser.parse_args()

    def escanear(funcion, ruta: Path) -> Hallazgos:
        return funcion(ruta) if ruta.exists() else {}

    texto, completa = generar(
        escanear(escanear_pytest, args.pytest),
        escanear(escanear_karate, args.karate),
        escanear(escanear_playwright, args.e2e),
    )
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(texto, encoding="utf-8")
        print(f"Matriz escrita en {args.salida}")
    else:
        print(texto)
    if args.estricto and not completa:
        print("Hay reglas sin ninguna prueba.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

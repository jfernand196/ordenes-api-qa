"""Lógica de las herramientas de QA, en funciones puras y probables.

Al importar el paquete se agregan backend/ y scripts/ al path: las herramientas leen la
máquina de estados, los schemas y el escáner de trazabilidad del propio proyecto, en lugar
de copiarlos (una sola fuente de verdad).
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BACKEND = RAIZ / "backend"
SCRIPTS = RAIZ / "scripts"
PRUEBAS_PYTEST = BACKEND / "tests"
KARATE = RAIZ / "acceptance-tests"
E2E = RAIZ / "frontend" / "e2e"

for _ruta in (BACKEND, SCRIPTS):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

#!/usr/bin/env python3
"""Quality gate de mutation testing.

Lee las estadísticas que genera `mutmut export-cicd-stats`, calcula el mutation score,
lo publica en el resumen de GitHub Actions (si existe) y termina con código 1 cuando
queda por debajo del umbral.

Uso:
    python scripts/check_mutation_score.py --umbral 70
    python scripts/check_mutation_score.py --archivo mutants/mutmut-cicd-stats.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def calcular(stats: dict) -> tuple[float, int, int]:
    """Devuelve (score, detectados, evaluados).

    Detectados: mutantes que alguna prueba hizo fallar (killed), más los que colgaron o
    rompieron el proceso (timeout, segfault), porque la suite también los detecta.
    Evaluados: todos menos los omitidos. Los mutantes sin pruebas (no_tests) cuentan
    como no detectados: código sin cubrir no debe mejorar el score.
    """
    detectados = sum(int(stats.get(k, 0)) for k in ("killed", "timeout", "segfault"))
    evaluados = int(stats.get("total", 0)) - int(stats.get("skipped", 0))
    if evaluados <= 0:
        return 0.0, detectados, evaluados
    return detectados / evaluados * 100, detectados, evaluados


def publicar_resumen(texto: str) -> None:
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(texto + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--archivo", default="mutants/mutmut-cicd-stats.json")
    parser.add_argument("--umbral", type=float, default=70.0)
    args = parser.parse_args()

    archivo = Path(args.archivo)
    if not archivo.exists():
        print(f"No existe {archivo}. Ejecuta antes: mutmut run && mutmut export-cicd-stats")
        return 2

    stats = json.loads(archivo.read_text(encoding="utf-8"))
    score, detectados, evaluados = calcular(stats)
    aprobado = evaluados > 0 and score >= args.umbral

    tabla = "\n".join(
        [
            "### Mutation testing",
            "",
            "| Métrica | Valor |",
            "|---|---|",
            f"| Mutation score | **{score:.1f} %** (umbral {args.umbral:.0f} %) |",
            f"| Detectados | {detectados} de {evaluados} |",
            f"| Sobrevivientes | {stats.get('survived', 0)} |",
            f"| Sin pruebas | {stats.get('no_tests', 0)} |",
            f"| Resultado | {'✅ Aprobado' if aprobado else '❌ Rechazado'} |",
        ]
    )
    print(tabla)
    publicar_resumen(tabla)
    return 0 if aprobado else 1


if __name__ == "__main__":
    sys.exit(main())

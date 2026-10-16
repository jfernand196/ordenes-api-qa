---
name: pytest-calidad
description: Cómo escribir y organizar las pruebas unitarias y de integración del backend del reto técnico con pytest, Hypothesis, cobertura (pytest-cov) y mutation testing (mutmut), incluyendo el quality gate de mutation score de al menos 70 %. Usa este skill siempre que crees o modifiques archivos en backend/tests, configures pytest, coverage o mutmut, investigues mutantes sobrevivientes, o el usuario hable de cobertura, ramas, mutation score, "tests que faltan" o quality gates, aunque no nombre pytest.
---

# Pruebas del backend: pytest, cobertura y mutation

La meta no es solo pasar los mínimos (80 % de líneas y ramas, 70 % de mutation score) sino mostrar una estrategia: más pruebas donde más riesgo hay (máquina de estados y cálculo del total) y cada prueba enlazada a una regla de negocio.

## Organización

```
backend/tests/
├── conftest.py                  fixtures compartidas (cliente HTTP, payload válido)
├── unit/
│   ├── domain/                  test_maquina_estados.py, test_orden.py
│   └── application/             test_servicio_ordenes.py
└── integration/
    └── api/                     test_ordenes_api.py
```

Pirámide: la mayoría de pruebas en `unit/domain` (milisegundos, sin I/O), luego integración con `TestClient`, y arriba Karate y Playwright (otros skills).

## Reglas para escribir pruebas

1. **Marca cada prueba con su regla**: `@pytest.mark.rn("RN-04")`. El script de trazabilidad del skill `qa-documentacion` lee estos markers. Si una prueba cubre varias reglas, apila varios markers.
2. **Nombres que se lean como especificación**: `test_no_se_puede_enviar_una_orden_no_pagada`, no `test_estado_3`.
3. **Escribe los valores esperados de forma literal**. Nunca calcules el resultado esperado con el mismo código de producción (por ejemplo, leyendo `TRANSICIONES` dentro del test): esa prueba siempre pasa y deja vivos a los mutantes.
4. **Valores frontera** para cada desigualdad: si el código dice `cantidad <= 0`, prueba −1, 0 y 1. Así mueren los mutantes que cambian `<=` por `<`.
5. **Verifica el tipo de error y su `codigo`**, no solo que "falle": `pytest.raises(PagoRequeridoError)` y `assert exc.value.codigo == "RN-05"`.
6. **En integración, verifica el contrato completo**: código HTTP, `content-type: application/problem+json` y el campo `codigo`.
7. **Una app nueva por prueba** con `create_app()`, para que no haya estado compartido.

## Pruebas clave

Las plantillas completas están en `references/ejemplos.md`. Léelas antes de escribir pruebas nuevas. Incluyen:
- La matriz literal de 25 transiciones (la prueba que más mutantes mata).
- Pruebas de fronteras de RN-01 y RN-02.
- Prueba por propiedades con Hypothesis para RN-03.
- Pruebas de integración de los 5 endpoints, incluido el Problem Details.
- `conftest.py` y la configuración de `pyproject.toml`.

## Cobertura

```bash
pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=html --cov-report=xml
```

El umbral vive en `pyproject.toml` (`fail_under = 80`), así que el comando falla solo si la cobertura baja. Meta real: más de 90 %. Las líneas sin cubrir aparecen en `term-missing`; revisa primero las del dominio.

## Mutation testing con mutmut

- **mutmut 3 no funciona bien en Windows nativo.** Ejecútalo en WSL, en un contenedor Linux o deja que lo haga el CI.
- Se muta solo la lógica (`app/domain`, `app/application`); API, logging e infraestructura se excluyen en `do_not_mutate`. Justifícalo en el README: ahí hay poca lógica de negocio y mutarla infla el ruido.
- Flujo:

```bash
mutmut run
mutmut results                    # lista de sobrevivientes
mutmut show <nombre_del_mutante>  # diff del mutante
mutmut export-cicd-stats          # genera mutants/mutmut-cicd-stats.json
python scripts/check_mutation_score.py --umbral 70
```

- El script `scripts/check_mutation_score.py` de este skill calcula el score, lo escribe en el resumen de GitHub Actions y sale con código 1 si queda por debajo del umbral. Cópialo a `backend/scripts/`.
- Las opciones de configuración de mutmut cambian entre versiones; si algo no funciona, revisa `mutmut --help` y la documentación de la versión instalada antes de cambiar la estrategia.

### Cómo matar un mutante sobreviviente

1. Mira el diff con `mutmut show`.
2. Pregúntate qué comportamiento observable cambia. Si cambia, escribe la prueba que lo detecta (casi siempre una frontera o un valor literal que faltaba).
3. Si no cambia nada observable (mutante equivalente, por ejemplo un texto de log), anótalo en el README en "Mutantes aceptados" con la razón. Eso demuestra criterio; no intentes llegar al 100 % a cualquier costo.

---
name: docker-cicd-quality-gates
description: Dockerfiles, docker-compose y pipeline de GitHub Actions del reto técnico de órdenes (FastAPI + React + Karate + Playwright), con quality gates que fallan si la cobertura es menor a 80 %, el mutation score menor a 70 % o hay pruebas fallidas, más publicación de reportes y resumen del pipeline como evidencia. Usa este skill siempre que crees o modifiques un Dockerfile, docker-compose.yml, .dockerignore o archivos en .github/workflows, o el usuario hable de contenedores, CI/CD, pipeline, GitHub Actions, quality gates, artifacts o badges, aunque no mencione Docker explícitamente.
---

# Docker y CI/CD con quality gates

El enunciado pide que el pipeline incluya checkout, build, pruebas unitarias, cobertura, mutation testing, Karate y construcción de la imagen Docker, y que falle con cobertura < 80 %, mutation score < 70 % o pruebas fallidas. Este skill lo cubre todo, más E2E y evidencias.

## Archivos

```
backend/Dockerfile
backend/.dockerignore
frontend/Dockerfile           (plantilla en el skill react-frontend-ordenes)
docker-compose.yml            raíz del repo
.github/workflows/ci.yml
```

Plantillas completas en `references/plantillas.md`. Léelas antes de crear o modificar cualquiera de estos archivos.

## Docker

- **Backend**: multi-stage sobre `python:3.12-slim`, usuario no root, `HEALTHCHECK` contra `/health`, puerto **8080**. Así funcionan literalmente los comandos del enunciado: `docker build -t challenge-api ./backend` y `docker run -p 8080:8080 challenge-api`.
- **Compose**: servicio `api` (8080) con healthcheck y servicio `web` (3000 → 80) que espera con `condition: service_healthy`. Usa `docker compose up -d --build --wait` en local y en CI: `--wait` bloquea hasta que los healthchecks pasan, lo que evita fallos intermitentes de Karate y Playwright.
- El healthcheck usa Python (`urllib`) porque la imagen slim no trae `curl`.

## Pipeline

```
lint ──► unit-tests ──► mutation
              │
              ├──► docker-build
              └──► acceptance (Karate) ──┐
frontend ────────────────────────────────┴──► e2e (Playwright)
```

| Job | Quality gate |
|---|---|
| `lint` | ruff sin errores |
| `unit-tests` | pruebas en verde y cobertura ≥ 80 % (`fail_under` en pyproject) |
| `mutation` | `check_mutation_score.py --umbral 70` |
| `docker-build` | la imagen construye |
| `acceptance` | 0 escenarios Karate fallidos |
| `frontend` | Vitest en verde y build correcto |
| `e2e` | 0 pruebas Playwright fallidas |

Cada gate falla por código de salida, no por revisión manual. Si alguien baja el umbral para que pase, se nota en el diff del PR.

## Evidencias y observabilidad

- **Artifacts** (con `if: always()`, para tenerlos justo cuando algo falla): HTML de cobertura, `mutmut-cicd-stats.json` y resultados de mutmut, `karate-reports`, `playwright-report` y los logs de la API (`docker compose logs`).
- **Resumen del job** en `$GITHUB_STEP_SUMMARY`: tabla de cobertura (`coverage report --format=markdown`) y tabla de mutation (la escribe el script).
- **Badge** del workflow en el README:
  `![CI](https://github.com/<usuario>/<repo>/actions/workflows/ci.yml/badge.svg)`
- Para la sección "Evidencia del pipeline" del README, enlaza una ejecución en verde y agrega capturas en `docs/evidence/`.

## Versionamiento del pipeline

- Se dispara en `push` a `main`, en `pull_request` y manualmente (`workflow_dispatch`).
- `concurrency` cancela ejecuciones viejas de la misma rama.
- `permissions: contents: read` (mínimo privilegio).
- Configura `main` como rama protegida que exige estos checks antes de hacer merge.

## Problemas comunes

- **mutmut tarda mucho**: limita `paths_to_mutate` a dominio y aplicación (skill `pytest-calidad`) y deja el job en paralelo con los demás.
- **Karate o Playwright fallan al inicio**: faltó `--wait` o el healthcheck.
- **El job de e2e no encuentra navegadores**: falta `npx playwright install --with-deps chromium`.
- **Fallos que solo pasan en CI**: revisa el artifact de logs de la API; cada línea trae `request_id`, y Karate envía `X-Request-ID` con prefijo `karate-`, así se cruza la petición con su log.

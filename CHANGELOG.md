# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado semántico.

## [1.2.1] - 2026-10-18

### Corregido
- El comando del enunciado `docker build -t challenge-api .` funciona desde la raíz del repositorio: el `Dockerfile` de la API pasó de `backend/` a la raíz, con un `.dockerignore` de lista de permitidos. docker-compose y el CI usan ese mismo archivo, sin duplicar la receta.

## [1.2.0] - 2026-10-17

### Agregado
- Servidor MCP de QA (`mcp-qa/`) con cuatro herramientas de solo lectura: reglas de negocio, matriz de trazabilidad, transiciones sin prueba de aceptación (ordenadas por riesgo) y datos de prueba derivados del schema.
- `.mcp.json` para usarlo desde Claude Code.
- Job `mcp-qa` en el CI: ruff, mypy estricto y pytest.
- ADR-004.
- 7 escenarios Karate (dos `Scenario Outline`) para las transiciones críticas que detectó el servidor: salir de ENTREGADA o CANCELADA responde 409 y no modifica la orden.

## [1.1.1] - 2026-10-17

### Agregado
- mypy en modo estricto (con el plugin de Pydantic) como quality gate del CI.

### Corregido
- 11 errores de tipos detectados por mypy; entre ellos, el tipo de los logs JSON, que no reflejaba que `status` y `duracion_ms` son números desde la v1.0.0.

### Cambiado
- Los skills toman sus plantillas del código real del repositorio, para que no queden desactualizados.
- El README documenta la regla de idioma: español para el negocio; inglés donde el enunciado o el framework lo fijan.

## [1.1.0] - 2026-10-16

### Cambiado
- La interfaz del repositorio (`RepositorioOrdenes`) se movió a `app/application/puertos.py`: la capa de aplicación ya no depende de la infraestructura (inversión de dependencias).
- `Orden` encapsula su estado y sus productos: el estado solo cambia con `cambiar_estado()` y los productos son inmutables.
- `ServicioOrdenes.crear` recibe `LineaProducto` en lugar de tuplas.
- Los límites de paginación son constantes con nombre, definidas en un solo lugar.

## [1.0.0] - 2026-10-16

### Agregado
- API REST de órdenes de compra con FastAPI: crear, consultar, listar, actualizar estado y cancelar.
- Reglas de negocio RN-01 a RN-06 con máquina de estados explícita.
- Errores en formato Problem Details con código de regla y mensajes en español.
- Logs en JSON con `X-Request-ID`.
- 95 pruebas unitarias y de integración con pytest e Hypothesis, con 100 % de cobertura de líneas y ramas.
- Mutation testing con mutmut: score de 100 %.
- 15 escenarios de aceptación con Karate.
- Docker y docker-compose para la API y la web.
- Frontend en React + Vite + TypeScript con 7 pruebas Vitest.
- 6 flujos E2E con Playwright.
- Pipeline de GitHub Actions con 7 jobs y quality gates de lint, cobertura, mutation, trazabilidad, pruebas e imagen Docker.
- Estrategia de pruebas basada en riesgo y matriz de trazabilidad automática.
- 10 skills de Claude con las convenciones del proyecto.

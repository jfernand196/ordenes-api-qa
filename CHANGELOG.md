# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado semántico.

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

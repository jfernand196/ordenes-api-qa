---
name: playwright-e2e
description: Cómo escribir y ejecutar las pruebas end-to-end con Playwright (TypeScript) sobre el frontend React del reto técnico de órdenes de compra, con Page Objects, los 4 flujos (crear, consultar, actualizar estado, cancelar), tags de reglas para trazabilidad, evidencias (trace, video, screenshot) y ejecución en CI contra docker compose. Usa este skill siempre que trabajes en frontend/e2e o playwright.config.ts, o el usuario hable de pruebas E2E, end-to-end, de interfaz, de navegador o de Playwright.
---

# Pruebas E2E con Playwright

Las E2E están en la punta de la pirámide: pocas, lentas y caras de mantener. Cubren los 4 flujos de negocio a través de la interfaz real, contra el stack completo levantado con Docker (nginx + API). La lógica detallada ya la cubren pytest y Karate; aquí se prueba que todo está bien conectado.

## Estructura

```
frontend/
├── playwright.config.ts
└── e2e/
    ├── paginas/                Page Objects
    │   ├── ListadoPage.ts
    │   ├── NuevaOrdenPage.ts
    │   └── DetallePage.ts
    ├── datos.ts                creación de órdenes por API (arrange rápido)
    └── ordenes.spec.ts         los 4 flujos
```

Plantillas completas en `references/plantillas.md`. Léelas antes de crear o modificar estos archivos.

## Principios

- **Arrange por API, act y assert por UI.** Si un flujo necesita una orden ENVIADA, se crea y se avanza con `request` (la API) y solo la acción bajo prueba se hace en la interfaz. Las pruebas son más rápidas y fallan por la razón correcta.
- **Selectores por `data-testid`** (convención del skill `react-frontend-ordenes`). Nada de selectores CSS ni de textos que cambian.
- **Page Objects con métodos de negocio** (`crearOrden`, `cambiarEstadoA`, `cancelar`), no con clics sueltos. Los asserts viven en los specs.
- **Cada prueba crea sus datos**, sin depender de otras ni del orden de ejecución.
- **Esperas automáticas de Playwright** (`expect(...).toHaveText`, `toBeVisible`). Nunca `waitForTimeout`.
- **El diálogo de confirmación de cancelar** se acepta con `page.once('dialog', d => d.accept())` antes del clic.
- **Tags de regla** con la opción `tag` (`{ tag: ['@RN-04'] }`), que también lee el script de trazabilidad.

## Flujos

| Flujo | Qué valida | Tags |
|---|---|---|
| Crear orden | Formulario, total visual y redirección al detalle en estado CREADA | `@smoke @RN-03` |
| Consultar orden | La orden creada aparece en el listado y su detalle muestra los datos correctos | `@smoke` |
| Actualizar estado | CREADA → PAGADA → ENVIADA → ENTREGADA por la UI; al final no quedan botones | `@RN-05 @RN-06` |
| Cancelar orden | Cancelación con confirmación; una ENTREGADA no ofrece el botón | `@RN-04` |

## Ejecución

```bash
docker compose up -d --build --wait          # API en 8080 y web en 3000
cd frontend
npx playwright install --with-deps chromium  # la primera vez
npx playwright test                          # headless
npx playwright test --ui                     # modo interactivo para depurar
npx playwright show-report                   # reporte HTML
```

`E2E_BASE_URL` permite apuntar a otra URL (por defecto `http://localhost:3000`). Los datos de prueba se crean por `/api` a través del mismo nginx, así que no hace falta una segunda URL.

## Evidencias

La configuración guarda trace, video y screenshot solo en fallos, y el reporte HTML queda en `playwright-report/`. En CI se sube como artifact incluso si el job falla (skill `docker-cicd-quality-gates`). Para el README, agrega una captura del reporte en verde.

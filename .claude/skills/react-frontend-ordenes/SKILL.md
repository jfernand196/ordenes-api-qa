---
name: react-frontend-ordenes
description: Estructura, convenciones y plantillas del frontend del reto técnico en React + Vite + TypeScript que consume la API de órdenes (listado con filtro, crear orden, detalle con cambio de estado y cancelación), sus pruebas con Vitest y Testing Library, y su despliegue con nginx en Docker. Usa este skill siempre que trabajes dentro de frontend/ (excepto la carpeta e2e), crees componentes o pantallas de órdenes, configures Vite, nginx o el Dockerfile del frontend, o el usuario hable de la interfaz web, la UI o React.
---

# Frontend de órdenes: React + Vite + TypeScript

El frontend es un plus del reto. Su valor ante los evaluadores es mostrar los flujos de negocio funcionando y servir de base para Playwright. Prioriza que sea claro, estable y fácil de probar; no inviertas tiempo en diseño elaborado.

## Estructura

```
frontend/
├── src/
│   ├── api/
│   │   ├── tipos.ts          Orden, Producto, Estado, Problema
│   │   ├── carga.ts          tipo Carga<T> (cargando | ok | error)
│   │   └── ordenes.ts        cliente HTTP y ApiError
│   ├── hooks/
│   │   ├── useOrdenes.ts     listado con limpieza del efecto
│   │   └── useOrden.ts       detalle con limpieza del efecto
│   ├── paginas/
│   │   ├── ListadoOrdenes.tsx
│   │   ├── NuevaOrden.tsx
│   │   └── DetalleOrden.tsx
│   ├── componentes/
│   │   ├── Campo.tsx         input con label y error accesible
│   │   ├── EstadoBadge.tsx
│   │   └── MensajeError.tsx  y errorDeCampo()
│   ├── estilos.css           del skill ui-ux-experto
│   ├── App.tsx               rutas
│   └── main.tsx
├── src/test/setup.ts
├── e2e/                      Playwright (skill playwright-e2e)
├── nginx.conf
├── Dockerfile
├── .dockerignore
└── vite.config.ts
```

Rutas: `/` listado, `/ordenes/nueva` creación, `/ordenes/:id` detalle. Usa `react-router-dom`.

## Skills relacionados

- `react-experto`: criterio de código React (estado, efectos, keys, tipos, antipatrones). Síguelo al escribir o revisar cualquier componente.
- `ui-ux-experto`: estados de pantalla, microcopy, formularios, accesibilidad y la hoja `estilos.css`. Síguelo al maquetar o cambiar textos.
- `buenas-practicas-ingenieria`: SOLID, DRY y clean code también aplican al frontend.

## Convenciones

- **Todas las llamadas pasan por `src/api/ordenes.ts`** con prefijo `/api`. En desarrollo lo resuelve el proxy de Vite; en Docker, nginx. Así no hay CORS ni URLs distintas por entorno.
- **Datos con hooks** (`useOrdenes`, `useOrden`) que devuelven `Carga<T>`; las páginas nunca llaman a la API dentro de un `useEffect` propio.
- **Cada pantalla cubre carga, vacío, error y éxito**, y cada acción muestra un aviso (`data-testid="aviso"`).
- **Errores**: el cliente lanza `ApiError` con el Problem Details de la API. En formularios, cada error va junto a su campo con `errorDeCampo(error, 'productos.0.cantidad')`.
- **Los botones de estado salen de `transicionesPermitidas`** que devuelve la API. El frontend nunca replica la máquina de estados: la fuente de verdad es el backend.
- **CANCELADA se ofrece con un botón aparte** que llama a `DELETE` y pide confirmación; el resto de transiciones usan `PATCH`.
- **El total del formulario es solo visual.** No se envía; la API lo calcula (RN-03).
- **Dinero** formateado con `Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })`.
- **`data-testid` en todo lo que Playwright toque**, con estos nombres:

| Elemento | data-testid |
|---|---|
| Fila del listado | `fila-orden-{id}` |
| Filtro de estado | `filtro-estado` |
| Botón nueva orden | `btn-nueva-orden` |
| Campo cliente | `input-cliente` |
| Campos de producto (índice i) | `input-producto-id-{i}`, `input-cantidad-{i}`, `input-valor-{i}` |
| Agregar producto | `btn-agregar-producto` |
| Total visual | `total-orden` |
| Guardar orden | `btn-crear-orden` |
| Estado en detalle | `estado-orden` |
| Botón de transición | `btn-estado-{ESTADO}` |
| Botón cancelar | `btn-cancelar-orden` |
| Mensaje de error | `mensaje-error` |
| Aviso de éxito | `aviso` |

## Plantillas

Lee `references/plantillas.md` antes de crear archivos. Contiene el cliente de la API, tipos, la pantalla de detalle (la más delicada), `vite.config.ts` con proxy y Vitest, `nginx.conf`, `Dockerfile`, `.dockerignore` y un ejemplo de prueba con Testing Library.

## Comandos

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install react-router-dom
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm run dev          # http://localhost:5173 con la API en 8080
npm test -- --run    # Vitest una sola vez (modo CI)
npm run build
```

## Pruebas de componentes

Pocas y enfocadas en lógica de la UI, no en estilos: el detalle muestra solo los botones de `transicionesPermitidas`; el formulario suma el total visual y agrega/quita productos; un `ApiError` se muestra en `mensaje-error`. Mockea `src/api/ordenes.ts` con `vi.mock`, no `fetch`.

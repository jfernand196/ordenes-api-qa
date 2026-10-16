---
name: react-experto
description: Criterio de experto en React con TypeScript para escribir, revisar y refactorizar componentes y hooks con buenas prácticas (manejo de estado, efectos con limpieza y sin condiciones de carrera, estados de carga con uniones discriminadas, formularios controlados, keys estables, composición, tipado estricto, accesibilidad, rendimiento y pruebas por comportamiento) y una lista de antipatrones a evitar. Usa este skill siempre que escribas o revises código React o TSX, crees un hook o un componente, depures renders, efectos o estado, o el usuario pregunte por buenas prácticas, patrones o errores comunes de React, aunque no pida explícitamente una revisión.
---

# Experto en React + TypeScript

Este skill da el criterio general. El skill `react-frontend-ordenes` tiene la estructura y las plantillas concretas del proyecto; ambos se usan juntos.

## Modelo mental

Un componente es una función de sus props y su estado que devuelve UI. Todo lo demás se deriva de eso:
- Lo que se puede calcular a partir de props o estado **se calcula al renderizar**, no se guarda en otro estado.
- Los efectos (`useEffect`) son para **sincronizar con algo externo** (red, timers, APIs del navegador). Si no hay nada externo, probablemente no necesitas un efecto.
- Las acciones del usuario se manejan en **event handlers**, no en efectos que reaccionan a cambios de estado.

## Estado

- **Mínimo y sin duplicados.** Guarda la fuente y deriva lo demás: el total del formulario se calcula de las filas en cada render.
- **Uniones discriminadas para datos asíncronos** en vez de tres booleanos que pueden contradecirse:

```ts
export type Carga<T> =
  | { tipo: 'cargando' }
  | { tipo: 'ok'; datos: T }
  | { tipo: 'error'; error: ApiError };
```

  Con esto el compilador obliga a manejar cada caso y no existe "cargando y con error a la vez".
- **Actualizaciones funcionales** cuando el nuevo estado depende del anterior: `setFilas((fs) => [...fs, nueva])`.
- **Inmutabilidad**: nunca mutes arrays u objetos del estado; crea copias con spread, `map` o `filter`.
- **Estado lo más cerca posible de donde se usa.** Súbelo solo cuando dos componentes lo comparten. Para este tamaño de app no hace falta Redux ni Context global.

## Efectos

Toda carga de datos con `useEffect` necesita limpieza para evitar condiciones de carrera (una respuesta vieja que llega tarde y pisa a la nueva):

```ts
useEffect(() => {
  let vigente = true;
  setCarga({ tipo: 'cargando' });
  ordenesApi
    .obtener(id)
    .then((datos) => {
      if (vigente) setCarga({ tipo: 'ok', datos });
    })
    .catch((e) => {
      if (vigente) setCarga({ tipo: 'error', error: aApiError(e) });
    });
  return () => {
    vigente = false;
  };
}, [id]);
```

Reglas:
- **Todas las dependencias en el array.** Respeta la regla `react-hooks/exhaustive-deps` de ESLint (viene en el template de Vite); si molesta, el diseño está mal, no la regla.
- **Encapsula la carga en un hook** (`useOrden(id)`, `useOrdenes(filtro)`) para que las páginas no conozcan la API (inversión de dependencias).
- En modo desarrollo, `StrictMode` ejecuta los efectos dos veces a propósito para detectar efectos sin limpieza. No lo quites.

## Componentes

- **Pequeños y con una responsabilidad.** Si un componente pasa de unas 150 líneas o mezcla carga de datos, lógica y mucho marcado, divídelo.
- **Separa datos de presentación**: la página usa hooks y decide qué mostrar; componentes como `EstadoBadge` o `MensajeError` solo reciben props.
- **Composición antes que configuración**: pasa `children` o componentes en vez de acumular props booleanas (`mostrarX`, `modoY`).
- **Props tipadas con interfaces**, sin `React.FC` (no aporta y oculta `children` implícitos en versiones viejas).
- **Nunca definas un componente dentro de otro**: se recrea en cada render y pierde su estado.

## Listas y keys

- La `key` debe ser **estable y única**: el `id` del dato.
- **Nunca uses el índice** como key en listas que se reordenan, filtran o donde se pueden quitar elementos (como las filas de productos del formulario). Si el dato aún no tiene id, genera uno al crear el elemento (un contador o `crypto.randomUUID()`) y guárdalo con él.

## Formularios

- **Controlados**: el valor vive en el estado y cada input tiene `value` y `onChange`.
- Guarda los números como texto mientras se editan y conviértelos al enviar; así un campo vacío no se convierte en `0` mientras el usuario escribe.
- Deshabilita el botón de envío mientras se envía, para evitar dobles envíos.
- Muestra los errores de la API **junto al campo** usando `errores[].campo` del Problem Details.
- `<form onSubmit>` con `preventDefault`, no `onClick` en un botón, para que Enter funcione.

## TypeScript

- `strict: true` (ya viene en el template). Sin `any`, sin `as` para silenciar errores, sin `!` de aserción no nula.
- Tipos del contrato de la API en un solo archivo (`api/tipos.ts`), alineados con los schemas del backend.
- Uniones de literales para valores cerrados (`type Estado = 'CREADA' | ...`) y `as const` para listas.
- `import type` para importar solo tipos (`verbatimModuleSyntax`).

## Rendimiento

- **No optimices antes de medir.** `useMemo`, `useCallback` y `React.memo` tienen costo y ensucian el código; en una app de este tamaño casi nunca hacen falta.
- Usa React DevTools Profiler si algo va lento, y optimiza solo lo que el perfil señale.
- Listas de cientos de filas se renderizan bien; la paginación de la API ya limita el tamaño.

## Accesibilidad (base)

- Elementos semánticos: `button` para acciones, `a`/`Link` para navegación, `table` para datos tabulares, `label` asociado a cada input.
- `role="alert"` en errores y `role="status"` en avisos de éxito, para que los lectores de pantalla los anuncien.
- Todo usable con teclado y con foco visible. El skill `ui-ux-experto` profundiza.

## Pruebas

- Prueba **comportamiento, no implementación**: qué ve y hace el usuario, no el estado interno.
- Prioridad de selectores en Testing Library: `getByRole` y `getByLabelText` primero; `getByTestId` cuando no hay un rol claro o para elementos que también usa Playwright.
- `findBy*` para lo asíncrono; nada de `setTimeout` en pruebas.
- Mockea el módulo de la API (`vi.mock`), no `fetch` ni hooks de React.

## Antipatrones

| Antipatrón | Problema | Mejor |
|---|---|---|
| Estado derivado sincronizado con `useEffect` | Render extra y estados inconsistentes | Calcular en el render |
| `useEffect` de carga sin limpieza | Condición de carrera al cambiar rápido el filtro o la ruta | Bandera `vigente` o `AbortController` |
| Dependencias omitidas en efectos | Datos viejos ("stale closures") | Array completo |
| `key={index}` en listas editables | Inputs que muestran el valor de otra fila | Id estable |
| Mutar el estado (`filas.push(...)`) | React no detecta el cambio | Copias inmutables |
| Booleanos `cargando`/`error`/`datos` sueltos | Combinaciones imposibles | Unión discriminada `Carga<T>` |
| `fetch` regado por los componentes | Duplicación y difícil de probar | Cliente único y hooks |
| Lógica de negocio en la UI | Reglas duplicadas con el backend | Consumir `transicionesPermitidas` |
| Componentes definidos dentro de otros | Pierden estado en cada render | Definirlos fuera |
| `any`, `as any`, `!` | Errores que el compilador ya no detecta | Tipos correctos |
| `useMemo`/`useCallback` en todo | Complejidad sin beneficio medido | Solo tras perfilar |
| `div` con `onClick` como botón | Inaccesible por teclado | `button` |

## Checklist de revisión de un componente

- [ ] ¿El estado es mínimo y lo derivado se calcula?
- [ ] ¿Los efectos tienen todas sus dependencias y limpieza?
- [ ] ¿Los datos asíncronos usan `Carga<T>` y la UI cubre carga, vacío, error y éxito?
- [ ] ¿Las keys son ids estables?
- [ ] ¿Sin `any`, `as` forzados ni `!`?
- [ ] ¿Sin reglas de negocio duplicadas del backend?
- [ ] ¿Accesible con teclado, con labels y roles correctos?
- [ ] ¿La prueba verifica comportamiento visible?

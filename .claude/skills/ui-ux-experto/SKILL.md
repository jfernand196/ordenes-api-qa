---
name: ui-ux-experto
description: Criterio de experto en UI/UX para la interfaz web de gestión de órdenes de compra del reto técnico (pantallas de listado, creación y detalle con cambios de estado), con principios de usabilidad, estados de pantalla (carga, vacío, error, éxito), formularios, acciones destructivas, microcopy en español, accesibilidad WCAG 2.2 AA, diseño responsive, sistema visual de estados y una hoja de estilos lista para usar. Usa este skill siempre que diseñes, maquetes, estilices o revises cualquier pantalla, componente visual, formulario, mensaje o texto de la interfaz, o el usuario hable de diseño, usabilidad, experiencia de usuario, accesibilidad, CSS o "que se vea bien".
---

# Experto en UI/UX para la gestión de órdenes

## Para quién y para qué

La interfaz la usan dos públicos: los evaluadores del reto (la abren pocos minutos y juzgan si se entiende sin explicación) y, en el caso de negocio, un operador que crea órdenes y las hace avanzar. Ambos necesitan lo mismo: **ver el estado de cada orden de un vistazo, saber qué puede hacer con ella y recibir respuesta clara a cada acción.**

Dirección visual: una herramienta operativa, sobria y legible. El protagonista es el **estado de la orden**; todo lo demás queda en segundo plano. Nada de decoración, degradados ni animaciones de entrada.

## Principios

1. **El estado del sistema siempre visible.** Cada orden muestra su estado como insignia con color y texto. Después de cada acción, la pantalla confirma qué pasó.
2. **Solo se ofrece lo posible.** Los botones salen de `transicionesPermitidas`: no se muestra "Marcar como enviada" en una orden sin pagar. Prevenir el error es mejor que explicarlo.
3. **Cada acción tiene respuesta**: botón deshabilitado mientras se procesa, aviso de éxito o error claro después.
4. **Las acciones destructivas piden confirmación** y dicen la consecuencia.
5. **Consistencia**: la misma acción tiene el mismo nombre en botón, confirmación y aviso.
6. **Accesible por defecto**, no como paso final.

## Estados de cada pantalla

Toda pantalla con datos cubre los cuatro estados; un spinner eterno o una pantalla en blanco es el error de UX más común en pruebas técnicas.

| Estado | Qué mostrar |
|---|---|
| Cargando | Texto breve con `role="status"`: «Cargando órdenes…» |
| Vacío | Qué significa y qué hacer: «Todavía no hay órdenes. Crea la primera con Nueva orden.» Con filtro: «No hay órdenes en estado PAGADA.» |
| Error | Qué pasó y cómo seguir, con `role="alert"`: «No se pudo conectar con la API. Verifica que esté en ejecución y recarga la página.» |
| Éxito | Los datos, y tras una acción un aviso con `role="status"`: «Orden marcada como pagada.» |

## Pantallas

**Listado**
- Título, botón primario «Nueva orden» arriba a la derecha y filtro por estado.
- Tabla con cliente (enlace al detalle), cantidad de productos, total alineado a la derecha con números tabulares y estado como insignia.
- Orden más reciente primero (así lo devuelve la API).

**Nueva orden**
- Campo cliente y filas de producto (id, cantidad, valor unitario) con «Agregar producto» y «Quitar» por fila (oculto si solo hay una).
- Total en vivo, visible y alineado, con nota «Calculado automáticamente».
- Errores de la API junto a su campo (usa `errores[].campo`, por ejemplo `productos.0.cantidad`), más un resumen arriba si hay varios.
- Botón «Crear orden» deshabilitado y con texto «Creando…» mientras se envía. Al terminar, ir al detalle con el aviso «Orden creada.»

**Detalle**
- Encabezado con cliente y estado grande.
- Tabla de productos con subtotales y total.
- Acciones: el siguiente paso como botón primario (por ejemplo «Marcar como pagada»), «Cancelar orden» como botón secundario de peligro y separado del resto.
- Si la orden es terminal: «Esta orden ya no admite cambios de estado.» en lugar de botones.
- Opcional si sobra tiempo: una línea de progreso CREADA → PAGADA → ENVIADA → ENTREGADA que marque el paso actual.

## Sistema visual de estados

| Estado | Color | Significado para el usuario |
|---|---|---|
| CREADA | Gris azulado | Pendiente de pago |
| PAGADA | Azul | Lista para enviar |
| ENVIADA | Ámbar | En camino |
| ENTREGADA | Verde | Completada |
| CANCELADA | Rojo | Anulada |

El color nunca va solo: la insignia siempre lleva el texto del estado. La hoja `assets/estilos.css` ya define estas insignias para modo claro y oscuro.

## Microcopy

Español neutro, frases cortas, verbos concretos y voz activa. Sin disculpas, sin signos de exclamación, sin jerga técnica.

| Acción | Botón | Confirmación | Aviso de éxito |
|---|---|---|---|
| Crear | Crear orden | — | Orden creada. |
| Pagar | Marcar como pagada | — | Orden marcada como pagada. |
| Enviar | Marcar como enviada | — | Orden marcada como enviada. |
| Entregar | Marcar como entregada | — | Orden marcada como entregada. |
| Cancelar | Cancelar orden | ¿Cancelar esta orden? Esta acción no se puede deshacer. | Orden cancelada. |

Errores: di qué pasó y qué hacer. «La cantidad debe ser mayor que 0.» en vez de «Error de validación». Los mensajes de la API ya llegan en español; muéstralos tal cual.

## Formularios

- Label visible encima de cada campo; nunca solo placeholder.
- Campos numéricos con `inputmode="numeric"` y `min`.
- Errores debajo del campo, en rojo y con texto, enlazados con `aria-describedby` y `aria-invalid="true"`.
- Al fallar el envío, mueve el foco al primer campo con error.
- No borres lo que el usuario escribió cuando hay un error.

## Accesibilidad (WCAG 2.2 AA)

- Contraste mínimo 4.5:1 en texto normal y 3:1 en texto grande y bordes de controles. Los tokens de `estilos.css` lo cumplen.
- Foco visible en todos los elementos interactivos (`:focus-visible` con contorno de 2 px).
- Todo operable con teclado, en orden lógico. Acciones con `button`, navegación con enlaces.
- Áreas táctiles de al menos 24×24 px (se usan 40 px de alto en botones).
- `role="alert"` para errores, `role="status"` para cargas y avisos.
- `lang="es"` en el `index.html` y un `<title>` por pantalla.
- Respeta `prefers-reduced-motion` y `prefers-color-scheme`.

## Responsive

- Ancho máximo de contenido de unos 960 px, centrado.
- En móvil, la tabla se desplaza horizontalmente dentro de su contenedor; la página nunca.
- Las filas de producto del formulario pasan a una columna en pantallas angostas.
- Los botones de acción se apilan en móvil.

## Hoja de estilos

`assets/estilos.css` contiene tokens de color, tipografía del sistema, tablas, formularios, botones (primario, secundario, peligro), insignias de estado, avisos y errores, en modo claro y oscuro. Cópiala a `frontend/src/estilos.css`, impórtala en `main.tsx` (`import './estilos.css'`) y borra el CSS de ejemplo del template de Vite (`App.css` e `index.css`). Las clases coinciden con las plantillas del skill `react-frontend-ordenes`.

## Antipatrones

| Antipatrón | Mejor |
|---|---|
| Mostrar botones que darán error | Ofrecer solo `transicionesPermitidas` |
| Acciones sin respuesta visible | Deshabilitar mientras procesa y avisar el resultado |
| Error genérico «Algo salió mal» | Qué pasó y qué hacer |
| Placeholder como única etiqueta | Label visible |
| Color como único indicador de estado | Color más texto |
| Cancelar al lado del botón principal y con el mismo estilo | Separado y con estilo de peligro |
| Pantalla en blanco sin datos | Estado vacío con la siguiente acción |
| Montos sin formato o alineados a la izquierda | Formato COP y alineados a la derecha |

## Checklist de revisión (heurísticas de Nielsen aplicadas)

- [ ] Visibilidad del estado: insignias, carga y avisos tras cada acción.
- [ ] Lenguaje del usuario: orden, pagada, enviada; nada de "PATCH" ni "409" en pantalla.
- [ ] Control y libertad: «Volver al listado» siempre visible; confirmación antes de cancelar.
- [ ] Consistencia: mismos nombres de acción en botón, confirmación y aviso.
- [ ] Prevención de errores: solo acciones válidas; total calculado a la vista.
- [ ] Reconocer antes que recordar: el detalle muestra qué se puede hacer a continuación.
- [ ] Diseño minimalista: solo lo necesario para decidir y actuar.
- [ ] Ayuda a recuperarse de errores: mensaje junto al campo y foco en el primero.
- [ ] Accesibilidad: contraste, teclado, foco, roles y labels.

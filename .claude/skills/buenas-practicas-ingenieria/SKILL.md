---
name: buenas-practicas-ingenieria
description: Buenas prácticas y antipatrones de diseño de APIs REST, principios SOLID, DRY, KISS, YAGNI y clean code aplicados al reto técnico de órdenes (Python/FastAPI y TypeScript/React), con ejemplos de dónde se aplica cada principio en el proyecto y una checklist de revisión de código. Usa este skill siempre que diseñes o cambies un endpoint, refactorices, revises código o un PR, nombres algo, decidas dónde poner lógica, o el usuario pregunte por calidad de código, arquitectura, principios, patrones, antipatrones, code smells o cómo justificar decisiones técnicas.
---

# Buenas prácticas de ingeniería

Los evaluadores valoran "legibilidad y mantenibilidad del código" y "capacidad para justificar decisiones técnicas". Este skill da el criterio para ambas cosas. Aplica los principios con sentido común: el objetivo es código fácil de entender y de cambiar, no cumplir una lista.

## 1. API REST

### Buenas prácticas

| Práctica | En este proyecto |
|---|---|
| Recursos como sustantivos en plural | `/orders`, `/orders/{id}` |
| Métodos HTTP con su semántica | GET lee sin efectos, POST crea, PATCH modifica parcialmente, DELETE cancela |
| Códigos de estado precisos | 201 al crear, 404 inexistente, 409 conflicto de estado, 422 validación, 400 precondición de pago |
| `201 Created` con header `Location` | `Location: /orders/{id}` |
| Formato de error único y estándar | Problem Details (RFC 9457) con `codigo` de regla y `errores` por campo |
| Validar en el borde, confiar en el núcleo | Pydantic en la API; el dominio vuelve a proteger sus invariantes |
| No aceptar campos calculados por el servidor | `total` se rechaza (`extra="forbid"`) |
| Filtros y paginación por query string | `GET /orders?estado=PAGADA&limit=20&offset=0` |
| Colecciones siempre acotadas | `limit` máximo 100 |
| DTOs separados del modelo de dominio | `OrdenIn`/`OrdenOut` en `api/schemas.py`, `Orden` en `domain/` |
| Nombres JSON consistentes | camelCase en todo el contrato |
| Contrato documentado | OpenAPI automático en `/docs`, con ejemplos en los schemas |
| Correlación de peticiones | `X-Request-ID` en request, response y logs |
| Endpoint de salud | `GET /health` |

**Idempotencia.** GET, PUT y DELETE deben ser idempotentes en su efecto: repetirlos deja el sistema igual. Un segundo `DELETE` sobre una orden cancelada no cambia nada y responde 409; eso es válido, porque la idempotencia se refiere al estado del servidor, no al código de respuesta (RFC 9110). POST no es idempotente: dos POST crean dos órdenes.

**Desviaciones impuestas por el enunciado.** `PATCH /orders/{id}/status` y `DELETE` como cancelación vienen fijados. Se respetan y se explican en el README: cancelar es un borrado lógico porque una orden es un registro auditable. No se agrega versionado (`/v1`) porque las rutas son parte del enunciado; menciónalo como mejora futura.

### Antipatrones REST

| Antipatrón | Por qué es malo | Cómo se evita aquí |
|---|---|---|
| `200 OK` con `{"error": ...}` en el cuerpo | Los clientes y monitores creen que todo salió bien | Códigos 4xx/5xx reales |
| Verbos en la URL (`/createOrder`, `/orders/1/cancel` con GET) | Duplica la semántica de HTTP; GET con efectos se cachea o se repite por error | Métodos HTTP |
| `500` por errores de validación | Culpa al servidor de un error del cliente | Handlers que mapean cada excepción |
| Exponer trazas o el modelo interno | Filtra detalles de implementación y acopla al cliente | Problem Details y DTOs |
| Aceptar datos que el servidor debe calcular | Manipulación (por ejemplo, de precios) | `total` calculado y rechazado en entrada |
| Listados sin límite | Respuestas enormes y lentas | `limit` con máximo |
| Formatos de error distintos por endpoint | El cliente necesita lógica especial por caso | Un solo `problema()` |
| Nombres inconsistentes (`valor_unitario` y `valorUnitario`) | Errores de integración | `alias_generator=to_camel` |
| API "chatty" que obliga a muchas llamadas | Latencia y complejidad en el cliente | La respuesta trae `transicionesPermitidas` |

## 2. SOLID

| Principio | Qué dice | Dónde se aplica |
|---|---|---|
| **S** Responsabilidad única | Una razón para cambiar por módulo | `rutas.py` traduce HTTP, `servicio_ordenes.py` orquesta, `orden.py` aplica reglas, `repositorio.py` guarda |
| **O** Abierto/cerrado | Extender sin modificar | Nueva transición: una línea en `TRANSICIONES`. Nuevo error: una entrada en `ESTADOS_HTTP`; el handler no cambia |
| **L** Sustitución de Liskov | Un subtipo debe poder usarse donde se espera el tipo base | Toda excepción hereda de `OrdenError` y el handler la trata igual; cualquier repositorio que cumpla `RepositorioOrdenes` sirve |
| **I** Segregación de interfaces | Interfaces pequeñas y específicas | `RepositorioOrdenes` tiene solo `guardar`, `obtener` y `listar` |
| **D** Inversión de dependencias | Depender de abstracciones | `ServicioOrdenes` recibe un `RepositorioOrdenes` (Protocol); `create_app()` inyecta la implementación en memoria |

En el frontend: componentes de presentación que solo reciben props (S), hooks de datos como `useOrden` que encapsulan el acceso a la API (D), y el cliente `ordenesApi` como única puerta a HTTP.

## 3. DRY, KISS, YAGNI

- **DRY (no te repitas)** aplica al conocimiento, no al texto. La máquina de estados vive en un solo lugar (backend) y el frontend la consume vía `transicionesPermitidas`; si la UI replicara las reglas, un cambio exigiría tocar dos sitios. Otros ejemplos: la función `problema()` para todos los errores, las fixtures de pytest, los helpers de Karate y los Page Objects.
- **Regla de tres**: no abstraigas a la primera repetición. Espera a la tercera, cuando el patrón es claro.
- **En pruebas, legibilidad antes que DRY.** Un test debe leerse solo, de arriba abajo. La matriz de transiciones se escribe literal a propósito aunque "repita" el diccionario de producción (ver skill `pytest-calidad`).
- **KISS**: la solución más simple que cumple. Repositorio en memoria en vez de una base de datos; `window.confirm` en vez de un modal propio.
- **YAGNI**: no construyas lo que nadie pidió. Sin autenticación, sin caché, sin colas de eventos. Si crees que algo sería útil, va al README como "mejoras futuras", no al código.

## 4. Clean code

**Nombres**
- Revelan intención: `validar_transicion`, `transiciones_permitidas`, `crearOrdenPorApi`. Nada de `data`, `tmp`, `proc`, `x2`.
- Funciones con verbo; booleanos como pregunta (`puedeCancelar`, `es_terminal`).
- Lenguaje del negocio (ubiquitous language) en español y consistente en todas las capas: orden, producto, cliente, estado.

**Funciones**
- Pequeñas, una sola cosa, un solo nivel de abstracción.
- Cláusulas de guarda en vez de `if` anidados: `validar_transicion` sale temprano con cada error.
- Pocos parámetros; si son muchos, agrúpalos en un objeto.
- Sin efectos ocultos: `cambiar_estado` devuelve el estado anterior en vez de loguear por dentro.

**Comentarios**
- Explican el porqué, no el qué. Bien: `# Supuesto documentado: RN-04 solo prohíbe cancelar ENTREGADA`. Mal: `# incrementa i`.
- El código comentado se borra; para eso está git.

**Errores**
- Excepciones de dominio con nombre, nunca `except:` vacío ni `except Exception: pass`.
- Falla rápido en el borde y con un mensaje accionable.

**Datos**
- Sin números mágicos: `limit` máximo como parámetro con nombre, umbrales en configuración.
- Dinero en enteros, nunca `float`.
- Tipos explícitos: type hints en Python, `strict` en TypeScript, sin `any`.

**Formato**: lo decide la herramienta, no la persona. `ruff format` en Python y Prettier más ESLint en TypeScript.

## 5. Antipatrones de código a vigilar

| Antipatrón | Ejemplo | Corrección |
|---|---|---|
| Lógica de negocio en el controlador | Validar transiciones dentro de `rutas.py` | Al dominio |
| Modelo anémico | `Orden` solo con datos y reglas regadas en el servicio | Métodos en la entidad (`cambiar_estado`, `total`) |
| Objeto dios | Un `utils.py` o un componente de 500 líneas | Dividir por responsabilidad |
| Obsesión por primitivos | Estados como strings sueltos | `Enum Estado` y tipo `Estado` en TS |
| Argumentos mutables por defecto (Python) | `def f(items=[])` | `None` y crear dentro |
| `float` para dinero | `0.1 + 0.2` | `int` (pesos) |
| `any` y `!` en TypeScript | `data as any`, `orden!.id` | Tipos y estrechamiento |
| `useEffect` para datos derivados (React) | Guardar `total` en estado y sincronizarlo | Calcularlo al renderizar |
| Tests que replican la implementación | Esperado calculado con el código de producción | Valores literales |
| Copiar y pegar con pequeños cambios | Tres handlers casi iguales | Función con parámetros (regla de tres) |

## 6. Checklist de revisión de código

Úsala en cada PR antes de hacer merge:

- [ ] ¿Los nombres se entienden sin leer la implementación?
- [ ] ¿Cada función hace una sola cosa?
- [ ] ¿La lógica de negocio está en el dominio y no en la API ni en la UI?
- [ ] ¿Los errores tienen tipo, código HTTP correcto y `codigo` de regla?
- [ ] ¿El endpoint respeta la semántica REST y el formato de error?
- [ ] ¿Hay pruebas de éxito y de error, con marker o tag `RN-xx`?
- [ ] ¿Sin código muerto, comentado, `print`, `console.log` ni TODO sin ticket?
- [ ] ¿Sin duplicación de conocimiento (reglas, constantes, mensajes)?
- [ ] ¿Ruff, ESLint y los tipos pasan sin advertencias?
- [ ] ¿Si cambió una decisión, se actualizó README o ADR?

## 7. Cómo justificarlo ante el evaluador

En el README, sección "Decisiones técnicas", conecta cada principio con un ejemplo concreto del código, como en las tablas de arriba. Una frase como "el servicio depende de una interfaz de repositorio (DIP), por eso cambiar a PostgreSQL solo requiere una clase nueva" vale más que listar siglas.

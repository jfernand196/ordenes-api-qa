# Estrategia de pruebas

## Enfoque

Las pruebas se priorizan por **riesgo**: la probabilidad de que algo falle multiplicada por su impacto en el negocio. Los riesgos altos se cubren en varios niveles de la pirámide; los bajos, en uno.

El objetivo no es solo cumplir los mínimos del reto (80 % de cobertura y 70 % de mutation score), sino tener pruebas que **detecten errores reales**. Por eso la calidad de las pruebas se mide con mutation testing, no solo con cobertura.

## Matriz de riesgo

| Riesgo | Probabilidad | Impacto | Nivel | Mitigación |
|---|---|---|---|---|
| Se permite una transición de estado inválida (RN-04, RN-05, RN-06) | Media | **Alto**: se entrega sin pago o se cancela lo ya entregado | **Alto** | Matriz unitaria literal de las 25 combinaciones, integración HTTP, 5 escenarios Karate |
| Total mal calculado o manipulado por el cliente (RN-03) | Media | **Alto**: pérdida económica | **Alto** | Unitarias con valores conocidos, prueba por propiedades (Hypothesis), rechazo de `total` en API y Karate |
| Orden sin productos o con cantidades inválidas (RN-01, RN-02) | Alta | Medio: datos corruptos | **Medio** | Valores frontera (−1, 0, 1), validación en API y dominio, `Scenario Outline` en Karate |
| Contrato HTTP incorrecto (código, formato de error, headers) | Media | Medio: rompe a los consumidores | **Medio** | Integración con `TestClient` y validación de esquema en Karate (`match`, `Location`, `content-type`, `codigo`) |
| Fallo de despliegue (imagen que no arranca) | Baja | Alto | **Medio** | Healthcheck en el Dockerfile y prueba de humo del contenedor en CI |
| Pérdida de trazabilidad en producción (logs incompletos) | Media | Medio: diagnóstico lento | **Medio** | Pruebas de logs con `caplog` y `X-Request-ID` verificado en integración |
| Condiciones de carrera en el repositorio | Baja | Medio | **Bajo** | `Lock` en el repositorio en memoria; sin prueba de concurrencia dedicada |

## Pirámide de pruebas

| Nivel | Herramienta | Pruebas | Qué valida | Tiempo |
|---|---|---|---|---|
| Unitarias | pytest + Hypothesis | 79 | Reglas de dominio, máquina de estados, servicio, mensajes, logs, manejo de errores | ~2 s |
| Integración | pytest + `TestClient` | 20 | Contrato HTTP de los 5 endpoints y Problem Details | ~1 s |
| Aceptación | Karate | 15 escenarios | API desplegada en Docker, flujos de negocio de punta a punta | ~20 s |

La base es ancha porque el riesgo principal está en la **lógica de dominio**, que se prueba en milisegundos y sin dependencias. Los niveles superiores son más lentos y caros de mantener, así que no repiten las reglas: confirman que las piezas están bien conectadas y que el contrato HTTP se cumple.

El frontend (Vitest) y las pruebas E2E (Playwright) se agregan en la punta de la pirámide.

## Técnicas aplicadas

| Técnica | Dónde |
|---|---|
| **Tabla de decisión completa** | Las 25 combinaciones origen → destino de la máquina de estados, escritas de forma literal |
| **Valores frontera** | Cantidad y valor unitario: −1, 0 y 1 |
| **Partición de equivalencia** | Payloads válidos e inválidos en integración y en el `Scenario Outline` de Karate |
| **Pruebas basadas en propiedades** | Hypothesis genera cientos de órdenes para verificar que total = Σ cantidad × valor |
| **Dobles de prueba** | `RepositorioEspia` verifica la interacción del servicio con el puerto de persistencia |
| **Pruebas de contrato** | Esquema, códigos HTTP, `content-type`, `Location` y `codigo` de regla en cada error |
| **Mutation testing** | mutmut sobre `app/domain` y `app/application` |

## Mutation testing: por qué la cobertura no basta

La primera corrida de mutmut dio **58,4 %** con **100 % de cobertura**: el código se ejecutaba, pero 47 mutantes sobrevivían porque varias cosas no se verificaban (los logs, los mensajes de error, el límite de paginación, la llamada a `guardar`). Tras agregar las pruebas que faltaban, el score llegó a **100 % (113 de 113)**.

Se mutan solo el dominio y la aplicación, donde está la lógica de negocio. La API, el logging, la infraestructura y `main.py` se excluyen porque tienen poca lógica propia y ya los cubren las pruebas de integración y de aceptación; mutarlos agregaría ruido sin aportar información.

## Trazabilidad

Cada prueba se etiqueta con la regla que verifica: `@pytest.mark.rn("RN-xx")` en pytest y `@RN-xx` en Karate. `scripts/generar_trazabilidad.py` genera [TRACEABILITY.md](TRACEABILITY.md) con la matriz regla → pruebas por nivel.

## Quality gates

| Gate | Falla si | Dónde se configura |
|---|---|---|
| Lint y formato | ruff encuentra errores o código sin formatear | `pyproject.toml` |
| Pruebas | falla cualquier prueba (pytest o Karate) | CI |
| Cobertura | líneas o ramas < 80 % | `pyproject.toml` (`fail_under`) |
| Mutation score | < 70 % | `scripts/check_mutation_score.py` |
| Trazabilidad | una regla queda sin pruebas, o la matriz está desactualizada | `scripts/generar_trazabilidad.py` |
| Imagen Docker | no construye o no responde el healthcheck | CI |

Todos se evalúan automáticamente en cada pull request.

## Fuera de alcance

- **Rendimiento y carga**: el enunciado no los pide y el repositorio es en memoria.
- **Seguridad** (autenticación, autorización): no forma parte del caso de negocio.
- **Persistencia real**: la interfaz `RepositorioOrdenes` permite agregarla sin cambiar el dominio; sus pruebas serían de integración contra la base de datos.
- **Concurrencia**: el repositorio usa un `Lock`, pero no hay una prueba dedicada de acceso concurrente.

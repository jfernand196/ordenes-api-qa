# ADR-004: Servidor MCP de QA

- Estado: aceptada
- Fecha: 2026-10-17

## Contexto

El enunciado propone, como plus de innovación, usar LangChain, LangGraph, MCP o skills para tareas como generar casos de prueba, identificar escenarios faltantes, recomendar pruebas por riesgo, generar matrices de trazabilidad o datos de prueba. El proyecto ya tenía skills de Claude, que aportan **conocimiento** (convenciones), pero no **datos vivos** del proyecto.

## Decisión

Crear `mcp-qa/`, un servidor MCP con el SDK oficial de Python (v2, `MCPServer`) que expone cuatro herramientas:

| Herramienta | Qué devuelve |
|---|---|
| `reglas_de_negocio` | RN-01 a RN-06, dónde se implementan y cuántas pruebas las verifican por nivel |
| `matriz_trazabilidad` | Las pruebas de cada regla en cada nivel |
| `transiciones_sin_aceptacion` | Las transiciones sin escenario Karate, ordenadas por riesgo |
| `datos_de_prueba` | Payloads válidos, de frontera e inválidos, con la respuesta esperada |

Principios:

- **Determinista y sin LLM:** misma entrada, misma salida; no necesita clave de API y se prueba como el resto del código.
- **Solo lectura:** ninguna herramienta modifica el proyecto.
- **Una sola fuente de verdad:** importa `TRANSICIONES`, los schemas de la API y el escáner de trazabilidad en lugar de copiarlos. Los límites de los datos de prueba (`gt=0`, `min_length=1`) se leen del schema.
- **Lógica en funciones puras** (`qa/`), publicadas por una capa delgada (`servidor.py`).

## Alternativas consideradas

- **LangChain** para generar borradores de escenarios Karate: útil, pero requiere clave de API, no es determinista y lo generado necesita revisión humana. Queda como mejora futura.
- **LangGraph** para un agente que genere, ejecute y corrija escenarios: el más ambicioso, con el mismo problema de costo y determinismo, y mayor riesgo de producir pruebas que pasan sin verificar nada.
- **Solo skills:** ya existían, pero no pueden consultar el estado real del proyecto.

## Consecuencias

- Un asistente como Claude Code responde preguntas como "¿qué transiciones no tienen prueba de aceptación?" con datos reales, y puede usar el skill de Karate para escribir los escenarios que faltan, que luego pasan por revisión y por el CI.
- La herramienta de brechas detecta hoy 17 transiciones sin prueba de aceptación, 7 de ellas críticas (salir de un estado terminal); es información accionable para priorizar.
- El servidor depende del código del backend, por lo que se ejecuta con su entorno virtual.
- Se usa la v2 del SDK, publicada el 28 de julio de 2026, que renombró `FastMCP` a `MCPServer`.

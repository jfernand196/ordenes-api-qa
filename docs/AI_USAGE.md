# Uso de inteligencia artificial

## Herramientas

| Herramienta | Uso |
|---|---|
| Claude (Anthropic), en claude.ai | Planificación, código base, pruebas, revisión, diagnóstico de errores y documentación |
| Skills de Claude (`.claude/skills/`) | Convenciones del proyecto empaquetadas como instrucciones reutilizables |
| Servidor MCP propio (`mcp-qa/`) | Herramientas deterministas de QA que Claude consulta: trazabilidad, brechas de aceptación y datos de prueba |

## Cómo se usó

- **Planificación:** plan de trabajo por días con prioridades según el riesgo y el plazo, y decisión de qué plus incluir.
- **Skills:** se crearon 10 skills que fijan las convenciones (arquitectura, códigos HTTP, estilo de pruebas, Karate, Docker, CI, frontend, UX, buenas prácticas y documentación), para que el código generado fuera consistente entre sesiones.
- **Código y pruebas:** la IA propuso el código base; cada pieza se ejecutó en local (pytest, ruff, mutmut, Karate, Vitest, Playwright y Docker) y en el CI antes de integrarla.
- **Diagnóstico:** se usó para interpretar errores de herramientas (WSL, Docker, Maven, mutmut) y proponer correcciones.
- **Documentación:** borradores de este README, la estrategia de pruebas y los ADR, revisados y ajustados.

## Revisión humana

Nada se integró sin verificarlo:

- **Cada cambio pasó por un pull request** con el pipeline completo en verde.
- **El mutation testing sirvió como control de calidad de las pruebas generadas:** una prueba que pasa pero no mata mutantes no aporta.
- **La interfaz se probó a mano en el navegador** antes de escribir las pruebas E2E.

## Sugerencias que se corrigieron o descartaron

| Problema | Cómo se detectó | Corrección |
|---|---|---|
| Las primeras pruebas tenían 100 % de cobertura pero solo 58,4 % de mutation score: no verificaban logs, mensajes ni la llamada al repositorio | mutmut | 16 pruebas nuevas; score de 100 % |
| La versión de Karate propuesta (1.4.1 con groupId `io.karatelabs`) no existe en Maven Central | Fallo de Maven al resolver dependencias | Se verificó en Maven Central y se cambió a 1.5.1 |
| Faltaba `pythonpath` en la configuración de pytest | Error de importación al correr las pruebas | Configuración corregida, también en el skill |
| Comandos de PowerShell con `Get-Content -Raw` dañaron las tildes de varios archivos (Windows PowerShell 5.1 lee UTF-8 sin BOM como Windows-1252) | Revisión del diff de un PR | Reparación de los bytes con un script, y se dejó de usar ese comando |
| El `TestClient` de Starlette mostraba un aviso de deprecación de `httpx` | Warning de pytest | Se revisó la documentación y se cambió a `httpx2` |
| Los errores de validación seguían visibles después de corregir el campo | Prueba manual en el navegador | Corrección y prueba de regresión |
| El healthcheck de nginx fallaba aunque la web funcionaba (en Alpine, `localhost` resuelve a IPv6) | `docker compose ps` mostraba `unhealthy` | Healthcheck contra `127.0.0.1` |

## Límites

- **Los supuestos de negocio** (por ejemplo, que una orden ENVIADA puede cancelarse) y la política de códigos HTTP se decidieron y documentaron conscientemente en los ADR; la IA propuso opciones, pero la decisión fue humana.
- **La IA no tuvo acceso directo al equipo:** los comandos se ejecutaron y sus resultados se revisaron en cada paso.

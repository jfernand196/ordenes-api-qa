---
name: karate-aceptacion
description: Cómo montar y escribir las pruebas de aceptación con Karate (Maven + JUnit 5 + JDK 17) contra la API de órdenes del reto técnico, incluidos los 4 escenarios obligatorios (crear 201, consultar 200, enviar sin pagar 400, cancelar entregada 409), escenarios adicionales, tags de trazabilidad y ejecución en CI. Usa este skill siempre que trabajes en acceptance-tests/, escribas o edites archivos .feature, karate-config.js o el pom de Karate, o el usuario hable de pruebas de aceptación, BDD, Gherkin o escenarios Given/When/Then.
---

# Pruebas de aceptación con Karate

Karate prueba la API desplegada (en Docker) desde fuera, como lo haría un consumidor. No repite las pruebas unitarias: valida el contrato HTTP y los flujos de negocio de punta a punta.

## Estructura

```
acceptance-tests/
├── pom.xml
└── src/test/java/
    ├── karate-config.js
    └── ordenes/
        ├── OrdenesTest.java          runner JUnit 5 en paralelo
        ├── crear-orden.feature
        ├── consultar-orden.feature
        ├── transiciones.feature
        └── helpers/
            └── crear-orden.feature   @ignore, reutilizable con call
```

Las plantillas completas (pom, runner, config y features) están en `references/plantillas.md`. Léelas antes de crear o modificar cualquiera de estos archivos.

## Escenarios

Los 4 obligatorios del enunciado, con el código HTTP exacto que pide:

| Escenario | Esperado | Tags |
|---|---|---|
| Crear una orden válida | 201 | `@smoke @RN-03` |
| Consultar una orden existente | 200 | `@smoke` |
| Intentar enviar una orden no pagada | 400 | `@RN-05` |
| Intentar cancelar una orden entregada | 409 | `@RN-04` |

Adicionales, cada uno con su justificación en un comentario (el enunciado pide justificar los extra):
- Validaciones RN-01 y RN-02 con `Scenario Outline` (422).
- Rechazo de `total` enviado por el cliente (RN-03, 422).
- Ciclo de vida completo CREADA → PAGADA → ENVIADA → ENTREGADA.
- Transición inválida CREADA → ENTREGADA (RN-06, 409).
- Orden inexistente (404) y listado con filtro por estado.

## Convenciones

- **Tags de regla en cada escenario** (`@RN-04`): el script de trazabilidad del skill `qa-documentacion` los lee. Un tag a nivel de `Feature` aplica a todos sus escenarios.
- **Cada escenario crea sus propios datos** llamando al helper. Nada depende del orden de ejecución, por eso el runner puede ir en paralelo.
- **Valida el esquema, no solo el status**: `match response == { id: '#uuid', ... }` y para errores `match response.codigo == 'RN-05'` y el header `Content-Type` con `application/problem+json`.
- **Los comentarios justifican el escenario**, no repiten los pasos.
- `baseUrl` llega como propiedad de Maven (`-DbaseUrl=...`) con valor por defecto `http://localhost:8080`.

## Ejecución

Requiere JDK 17 y Maven, con la API levantada:

```bash
docker compose up -d --wait api
mvn -B test -f acceptance-tests/pom.xml
# contra otra URL:
mvn -B test -f acceptance-tests/pom.xml -DbaseUrl=http://localhost:9090
# solo humo:
mvn -B test -f acceptance-tests/pom.xml -Dkarate.options="--tags @smoke"
```

El reporte HTML queda en `acceptance-tests/target/karate-reports/karate-summary.html`. En CI se sube como artifact (skill `docker-cicd-quality-gates`) y se enlaza una captura en el README como evidencia.

## Errores comunes

- **Los `.feature` no se encuentran**: el pom debe declarar `src/test/java` como `testResource`.
- **Connection refused**: la API aún no está lista. Usa `docker compose up --wait`, que espera el healthcheck.
- **El build no falla aunque fallen escenarios**: el runner debe hacer `assertEquals(0, results.getFailCount(), ...)`.

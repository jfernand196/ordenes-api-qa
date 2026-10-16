# ADR-002: Persistencia en memoria

- Estado: aceptada
- Fecha: 2026-10-15

## Contexto

El enunciado no exige base de datos y el plazo es corto. Lo que se evalúa es la calidad: pruebas, quality gates, CI y documentación.

## Decisión

Usar un repositorio en memoria (`RepositorioEnMemoria`) con un `Lock` para el acceso concurrente, detrás de la interfaz `RepositorioOrdenes` (un `Protocol` con `guardar`, `obtener` y `listar`). El servicio depende de la interfaz, no de la implementación (inversión de dependencias).

## Alternativas consideradas

- **SQLite o PostgreSQL:** más realista, pero agrega configuración, migraciones y un servicio más en Docker sin aportar a lo que se evalúa.

## Consecuencias

- Los datos se pierden al reiniciar la API. Es aceptable para el reto y se documenta.
- Cambiar a una base de datos real solo requiere una nueva implementación de `RepositorioOrdenes`; el dominio y el servicio no cambian.
- Cada prueba usa una app nueva (`create_app()`) con su propio repositorio, sin estado compartido entre pruebas.
